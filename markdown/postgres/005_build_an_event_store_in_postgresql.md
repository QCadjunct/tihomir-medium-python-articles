# Build an Event Store in PostgreSQL

#### Append-only tables, a unique constraint that gives you lock-free concurrency, and projections rebuilt from history — no Kafka, no EventStoreDB

**By Tihomir Manushev**

*Jul 17, 2026 · 10 min read*

---

Most databases store the *current* state of the world: this SKU has 40 units, this order is shipped, this account holds $1,200. The history — how it got there — is thrown away on every `UPDATE`. Event sourcing inverts that. You store the *facts that happened* as an append-only log, and you derive current state by replaying them. The balance isn't a column you overwrite; it's the sum of every deposit and withdrawal that ever occurred.

The moment a team decides to do this, someone proposes standing up EventStoreDB or a Kafka cluster, and the project acquires a distributed log, a new operational burden, and a second source of truth to keep in sync with the database. But an event store is, at its core, a table you only ever `INSERT` into, plus a way to stop two writers from corrupting the same stream. Postgres does both — and the concurrency guard is a single `UNIQUE` constraint doing work you'd otherwise reach for locks or a consensus log to achieve.

This article builds a working event store on Postgres 16 for a warehouse inventory system: the append-only schema, lock-free optimistic concurrency demonstrated with two racing writers and real conflict output, projections for the read side, snapshots for long streams, and an honest account of where a dedicated log still beats it.

---

### The Append-Only Log

Everything hangs off one table. Each row is an immutable event belonging to a **stream** — the sequence of events for one aggregate, such as a single SKU. Two numbers matter: a **global sequence** for total ordering across all streams, and a per-stream **version** for ordering and concurrency within one aggregate.

```sql
CREATE TABLE events (
    global_seq  bigint GENERATED ALWAYS AS IDENTITY,
    stream_id   text  NOT NULL,
    version     int   NOT NULL,
    event_type  text  NOT NULL,
    payload     jsonb NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (global_seq),
    UNIQUE (stream_id, version)
);
```

The `global_seq` identity column gives every event a monotonically increasing position — this is what a projection consumes to process events in order. `stream_id` plus `version` identifies an event's place within its aggregate's history, and `payload` holds the event's data as `jsonb`, so different event types carry different shapes without schema churn.

That `UNIQUE (stream_id, version)` line looks like ordinary hygiene. It is actually the entire concurrency-control mechanism, and we'll see it earn its keep shortly.

An event store is worthless if history can be rewritten, so make "append-only" a guarantee the database enforces, not a convention you hope everyone follows. Rules that turn `UPDATE` and `DELETE` into no-ops do exactly that:

```sql
CREATE RULE events_no_update AS ON UPDATE TO events DO INSTEAD NOTHING;
CREATE RULE events_no_delete AS ON DELETE TO events DO INSTEAD NOTHING;
```

Now an errant `UPDATE events SET ...` or `DELETE FROM events` silently affects zero rows instead of quietly corrupting your only source of truth.

---

### Appending Events

Writing an event means claiming the next version number for its stream. The caller passes the version it *expects* the stream to be at; the function writes the next one. If that version is already taken, the insert violates the unique constraint and we translate it into a clean concurrency error:

```sql
CREATE FUNCTION append_event(p_stream text, p_expected int,
                             p_type text, p_payload jsonb)
RETURNS int LANGUAGE plpgsql AS $$
DECLARE next_version int := p_expected + 1;
BEGIN
    INSERT INTO events (stream_id, version, event_type, payload)
    VALUES (p_stream, next_version, p_type, p_payload);
    RETURN next_version;
EXCEPTION WHEN unique_violation THEN
    RAISE EXCEPTION 'concurrency conflict on % : version % already exists',
                    p_stream, next_version
        USING errcode = 'serialization_failure';
END; $$;
```

Building a stream is a series of appends, each passing the version it saw last. A SKU is received into the warehouse, then two shipments go out:

```sql
SELECT append_event('sku-4471', 0, 'StockReceived', '{"qty": 100, "from": "supplier-A"}');
SELECT append_event('sku-4471', 1, 'StockShipped',  '{"qty": 30, "order": "ord-9001"}');
SELECT append_event('sku-4471', 2, 'StockShipped',  '{"qty": 25, "order": "ord-9002"}');
```

The log now holds three immutable facts, each stamped with a global position and a stream version:

```
 global_seq | stream_id | version |  event_type   |              payload
------------+-----------+---------+---------------+------------------------------------
          1 | sku-4471  |       1 | StockReceived | {"qty": 100, "from": "supplier-A"}
          2 | sku-4471  |       2 | StockShipped  | {"qty": 30, "order": "ord-9001"}
          3 | sku-4471  |       3 | StockShipped  | {"qty": 25, "order": "ord-9002"}
```

---

### Rebuilding State by Folding

There is no `qty_on_hand` column anywhere. Current state is a **left fold** over the stream: start from nothing, apply each event in version order, and whatever you end with is the truth. In SQL that fold is an aggregate:

```sql
SELECT stream_id,
       max(version) AS current_version,
       sum(CASE event_type WHEN 'StockReceived' THEN  (payload->>'qty')::int
                           WHEN 'StockShipped'  THEN -(payload->>'qty')::int
                           ELSE 0 END) AS qty_on_hand
FROM events
WHERE stream_id = 'sku-4471'
GROUP BY stream_id;
```

```
 stream_id | current_version | qty_on_hand
-----------+-----------------+-------------
 sku-4471  |               3 |          45
```

One hundred received, thirty and twenty-five shipped, leaves forty-five on hand at version 3. The number was never stored; it was computed from history. That is the defining property of an event store — state is a *view* of the log, and you can compute any past state just as easily by folding events up to whatever version you care about.

---

### Optimistic Concurrency Without Locks

Now the payoff hidden in that unique constraint. Two warehouse workers process shipments for the same SKU at the same instant. Both read the stream, both see it at version 3, and both try to append version 4. Without coordination, one silently overwrites the other's decision and you ship stock you don't have.

Here is the crucial move: **neither writer takes a lock**. Each simply tries to insert version 4. The `UNIQUE (stream_id, version)` constraint guarantees only one can succeed. Running both concurrently — writer A commits while writer B is mid-append — produces this:

```
[A] A appended v4
[A] COMMIT
[B] ERROR:  concurrency conflict on sku-4471 : version 4 already exists
[B] ROLLBACK
```

Writer A won the race and committed version 4. Writer B blocked on the unique index until A committed, then failed with our translated conflict error and rolled back cleanly. The final stream contains exactly one version 4 — B's event never entered the log. This is **optimistic concurrency control**: assume no conflict, attempt the write, and let the database reject the loser. It costs nothing when there's no contention (the common case), and it needs no advisory lock, no `SELECT ... FOR UPDATE`, no external coordinator. The version number *is* the optimistic lock.

The caller's job on conflict is simple and mechanical: re-read the stream to its new head, re-evaluate the business rule against the now-current state, and retry. That retry loop is the entire concurrency protocol — and because a conflict means "someone else advanced the aggregate," re-reading is exactly the right response.

---

### Projections: The Read Side

Folding the whole log on every read is fine for one SKU and ruinous for a dashboard querying ten thousand. The answer is a **projection**: a read model you precompute from the log and query cheaply. A materialized view is the simplest form — it folds once and stores the result:

```sql
CREATE MATERIALIZED VIEW stock_levels AS
SELECT stream_id,
       max(version) AS version,
       sum(CASE event_type WHEN 'StockReceived' THEN  (payload->>'qty')::int
                           WHEN 'StockShipped'  THEN -(payload->>'qty')::int
                           ELSE 0 END) AS qty_on_hand
FROM events GROUP BY stream_id;
```

```
 stream_id | version | qty_on_hand
-----------+---------+-------------
 sku-4471  |       4 |          40
```

Reads now hit a tiny precomputed table. `REFRESH MATERIALIZED VIEW stock_levels` rebuilds it — schedule that on an interval (a natural job for `pg_cron`), and use the `CONCURRENTLY` option so readers aren't blocked during the refresh.

Full rebuilds don't scale forever, so production projections are usually **incremental**: a small projector process reads events with `global_seq` greater than the last position it processed, updates the read model, and records the new high-water mark as a checkpoint. Because `global_seq` gives a total order over every event, the projector never misses or double-applies an event — it just resumes from its checkpoint. This is also what makes multiple, independent read models cheap: each consumer keeps its own checkpoint and folds the same log into whatever shape it needs.

---

### Snapshots: Taming Long Streams

An aggregate with fifty thousand events is slow to fold from scratch every time you load it. A **snapshot** caches an aggregate's state at a known version so you replay only what came after:

```sql
CREATE TABLE snapshots (
    stream_id text PRIMARY KEY,
    version   int  NOT NULL,
    state     jsonb NOT NULL,
    taken_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO snapshots (stream_id, version, state)
VALUES ('sku-4471', 3, '{"qty_on_hand": 45}');
```

Loading the aggregate becomes "take the snapshot, then fold only the events newer than its version":

```sql
SELECT (s.state->>'qty_on_hand')::int
       + COALESCE(sum(CASE e.event_type
                          WHEN 'StockReceived' THEN  (e.payload->>'qty')::int
                          WHEN 'StockShipped'  THEN -(e.payload->>'qty')::int
                          ELSE 0 END), 0) AS qty_on_hand,
       max(e.version) AS loaded_to_version
FROM snapshots s
LEFT JOIN events e ON e.stream_id = s.stream_id AND e.version > s.version
WHERE s.stream_id = 'sku-4471'
GROUP BY s.version, s.state;
```

```
 qty_on_hand | loaded_to_version
-------------+-------------------
          40 |                 4
```

The snapshot supplied 45 at version 3; only version 4's shipment of five was replayed, landing at 40. A stream of any length now costs "snapshot plus the handful of events since." Snapshots are a pure optimization — they are always rederivable from the log, so you can delete and rebuild them at will, and you never treat them as a source of truth.

---

### Gotchas Worth Knowing Before Production

**The global sequence has gaps.** Postgres sequences are not transactional — a number handed out to a transaction that rolls back is *not* returned. After the concurrency conflict above, the next successful append does not land at `global_seq` 5; it lands at 6, because the failed writer already consumed 5:

```
 global_seq | version |  event_type
------------+---------+---------------
          4 |       4 | StockShipped
          6 |       5 | StockAdjusted
```

Use `global_seq` only for *ordering* — it is reliably monotonic. Never treat it as a gapless count or infer "how many events exist" from its maximum value. Projectors must compare with `>`, never assume the next value is exactly current-plus-one.

**Events are immutable, but their shape isn't forever.** A `StockShipped` event you wrote last year may lack a field today's code expects. You cannot migrate old events — the log is append-only by design. Instead, version your event schemas (a `schema_version` in the payload, or typed names like `StockShipped.v2`) and **upcast** on read: projection code transforms old shapes into the current one as it folds. Planning for this from day one is far cheaper than discovering on a two-year-old stream that your projector crashes on an event it can't parse.

**Refreshes and folds compete with your write load.** A materialized-view refresh over a large log is a heavy scan on the same instance taking the writes. Index the log for how projections read it — typically on `global_seq` for incremental consumers and `(stream_id, version)` for aggregate loads (the latter you get free from the unique constraint) — and refresh on a cadence your write throughput can absorb.

---

### When Kafka or EventStoreDB Still Wins

Postgres is a single primary for writes, and an event store concentrates *all* writes into one append-only table. That table has a throughput ceiling — high tens of thousands of events per second on good hardware, not the millions a partitioned Kafka cluster sustains by spreading load across brokers. If your event volume is genuinely in that range, a distributed log is the right tool and no amount of clever SQL changes that.

Dedicated systems also give you things Postgres only approximates. Kafka offers durable, replayable, partitioned streams with consumer groups and retention policies built in; a real event-store product offers push-based **subscriptions** so consumers are notified of new events instead of polling. Postgres has `LISTEN`/`NOTIFY`, which covers low-volume notification but is not a durable, replayable subscription — a consumer that's offline misses the notification and must fall back to polling `global_seq` anyway. And multi-datacenter fan-out to many independent consumers is squarely a log-broker's job.

The honest dividing line: use Postgres as your event store when your write volume fits one primary, your consumers are a handful of projectors polling a checkpoint, and you value having history, current state, and read models in one transactional system you already operate. Reach for Kafka or a dedicated event store when write throughput exceeds a single node, when you need many independent consumers with push subscriptions and retention, or when the log must span datacenters. Most systems adopting event sourcing are comfortably in the first camp — and pretending otherwise buys you a cluster you didn't need.

---

### Conclusion

An event store is less exotic than its tooling suggests: an append-only table, a unique constraint that turns version numbers into lock-free optimistic concurrency, and folds that derive state and read models from history. Postgres gives you all of it transactionally, so your events, your current state, and your projections stay consistent without a second system to synchronize.

Enforce append-only in the database, treat `global_seq` as an ordering and not a count, plan for event-schema evolution before you need it, and precompute read models rather than folding on every query. Do that, and you get the real prize of event sourcing — a perfect, replayable audit of everything that ever happened — without operating a distributed log to hold it. Just keep clear eyes on the write-throughput ceiling that decides when you've outgrown a single node.
