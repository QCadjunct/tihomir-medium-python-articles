# Replace Zookeeper with PostgreSQL Advisory Locks

#### Leader election and distributed mutexes using the database you already run — and the one guarantee it cannot give you

**By Tihomir Manushev**

*Jul 13, 2026 · 9 min read*

---

A team needs exactly one worker to run the nightly report. Three instances are deployed behind a load balancer, all identical, all waking at the same hour. Someone says the word "coordination," and within a week the architecture diagram has grown a three-node Zookeeper ensemble — quorum, JVM tuning, a new failure domain, and an on-call rotation — all to answer a single yes/no question: *am I the one who runs this?*

Postgres has had a general-purpose lock manager for decades. **Advisory locks** let you lock anything you can name: a job, a tenant, a resource, a workflow step. Postgres doesn't know or care what the lock means — it only guarantees that one session at a time holds a given key. If your workers already connect to the same database, coordination costs you a function call and zero new infrastructure.

This article builds real leader election on Postgres 16, with genuine multi-session output. It also does the thing most "just use Postgres" posts skip: it shows the guarantee advisory locks *don't* give you, why that gap is exactly where Zookeeper and etcd earn their keep, and how to close it with fencing tokens.

---

### Advisory Locks in Sixty Seconds

Every lock you normally meet in Postgres is attached to something real — a row, a table, an index. An advisory lock is attached to nothing. It is a bare integer key in a shared namespace, and its meaning lives entirely in your head. Postgres enforces mutual exclusion on that key and nothing else; it will not stop anyone from touching the rows you *think* the lock protects. The name is literal: the lock is advisory, and only cooperating code respects it.

The key is a `bigint`, or a pair of `int`s. Nobody wants to remember that job 4 is `8675309`, so name your locks and hash them:

```sql
SELECT pg_try_advisory_lock(hashtext('nightly-report-leader'));
```

`hashtext` turns a readable name into an integer key. It is convenient and I use it below, with one production caveat I'll return to: it is an internal function, and its output is not contractually stable across major versions.

---

### Session or Transaction: Pick Your Scope

Advisory locks come in two families, and picking the wrong one is the most common way to get this wrong. **Transaction-scoped** locks (`pg_advisory_xact_lock`) release automatically when the transaction ends. **Session-scoped** locks (`pg_advisory_lock`) ignore transaction boundaries entirely and live until you unlock them or the connection drops.

```sql
-- Transaction-scoped: released by COMMIT, no cleanup code needed
BEGIN;
SELECT pg_advisory_xact_lock(hashtext('nightly-report-leader'));
SELECT count(*) AS held FROM pg_locks WHERE locktype = 'advisory';  -- 1
COMMIT;
SELECT count(*) AS held FROM pg_locks WHERE locktype = 'advisory';  -- 0

-- Session-scoped: survives COMMIT, released only on unlock or disconnect
SELECT pg_advisory_lock(hashtext('nightly-report-leader'));
SELECT count(*) AS held FROM pg_locks WHERE locktype = 'advisory';  -- 1
SELECT pg_advisory_unlock(hashtext('nightly-report-leader'));
SELECT count(*) AS held FROM pg_locks WHERE locktype = 'advisory';  -- 0
```

The transaction-scoped lock vanished at `COMMIT` without a single line of cleanup. That is the right default for guarding a unit of work: you cannot leak it, because the transaction ending *is* the release, even if your code crashes mid-way.

Session scope is what you want for leader election, precisely because the lock must outlive any single transaction — a leader holds its claim across many transactions, for as long as it lives.

---

### Electing a Leader

Leader election reduces to one line: everyone races to grab the same key, and `pg_try_advisory_lock` returns `true` to exactly one winner. The `try_` prefix is essential — it returns immediately rather than blocking, so the losers find out instantly that they are standbys instead of queueing up to become leader later.

```sql
SELECT CASE WHEN pg_try_advisory_lock(hashtext('nightly-report-leader'))
            THEN 'LEADER (acquired lock)'
            ELSE 'standby (lock already held)' END AS role;
```

Running that from three concurrent sessions gives exactly what you want:

```
worker-1 -> LEADER (acquired lock)
worker-2 -> standby (lock already held)
worker-3 -> standby (lock already held)
```

The genuinely valuable part is what happens when worker-1 dies. Its session ends, and Postgres releases the lock **immediately** — no TTL to tune, no heartbeat loop to write, no lease to renew. The lock's lifetime is the TCP connection's lifetime, which the database already tracks with total precision. Compare that to a Redis-based mutex, where you pick a TTL, and every choice is wrong: too short and a slow leader loses its lock mid-job, too long and a dead leader blocks the fleet for minutes.

You can see who holds what through `pg_locks`, which makes this the rare distributed lock you can debug with a `SELECT`:

```sql
SELECT locktype, classid, objid, objsubid, mode, granted
FROM pg_locks WHERE locktype = 'advisory';
```

```
 locktype |  classid   |   objid    | objsubid |     mode      | granted
----------+------------+------------+----------+---------------+---------
 advisory | 4294967295 | 2815970904 |        1 | ExclusiveLock | t
```

A single `bigint` key gets split across `classid` (high 32 bits) and `objid` (low 32 bits), with `objsubid = 1` marking it as the one-argument form.

---

### When You Can't Wait Forever

There are three waiting strategies, and production code should almost never use the middle one. `pg_try_advisory_lock` returns instantly. `pg_advisory_lock` blocks **forever** — a fine way to accumulate stuck connections. The middle ground is a bounded wait via `lock_timeout`, which is what you want when the work is worth queueing for briefly but not indefinitely:

```sql
SET lock_timeout = '500ms';
SELECT pg_advisory_lock(hashtext('nightly-report-leader'));
```

With another session already holding the key, the non-blocking call returns `false` right away, and the bounded wait gives up cleanly after half a second:

```
try -> false
ERROR:  canceling statement due to lock timeout
```

That error is a normal, catchable condition — treat it as "someone else is doing it" and move on.

---

### The Guarantee Advisory Locks Don't Give You

Here is where honest engineering starts, and where most "replace X with Postgres" posts quietly stop.

Holding a lock does not make you the leader. It makes you *the session that most recently acquired a key*. Those differ the moment your process stalls — a long GC pause, a blocked syscall, a network partition. Your connection drops, Postgres releases your lock instantly, another worker becomes leader, and your process wakes up seconds later still believing it is in charge. It then writes to the resource it "owns." No lock was violated. The data is corrupt anyway.

This failure mode is not a Postgres flaw — it is inherent to every lock-with-a-lease system, Redis and Zookeeper included. The fix is a **fencing token**: a monotonically increasing number handed out with the lock, which the protected resource checks and refuses to go backwards on. A sequence is exactly that:

```sql
CREATE SEQUENCE leader_token_seq;

CREATE TABLE report_output (
    resource_key text PRIMARY KEY,
    last_token   bigint NOT NULL,
    payload      text NOT NULL,
    written_at   timestamptz NOT NULL DEFAULT now()
);

CREATE FUNCTION write_with_fence(p_key text, p_token bigint, p_payload text)
RETURNS text LANGUAGE plpgsql AS $$
DECLARE current_token bigint;
BEGIN
    SELECT last_token INTO current_token FROM report_output WHERE resource_key = p_key;
    IF current_token IS NOT NULL AND p_token <= current_token THEN
        RETURN format('REJECTED: token %s is stale (resource already at %s)',
                      p_token, current_token);
    END IF;
    INSERT INTO report_output (resource_key, last_token, payload)
    VALUES (p_key, p_token, p_payload)
    ON CONFLICT (resource_key) DO UPDATE
        SET last_token = EXCLUDED.last_token,
            payload    = EXCLUDED.payload,
            written_at = now();
    RETURN format('ACCEPTED: token %s wrote %s', p_token, p_payload);
END; $$;
```

The rule is one line: a write carrying a token less than or equal to the resource's current token is refused. Now replay the stalled-leader disaster. Worker A becomes leader and takes token 1, then stalls and loses its connection. Worker B acquires the freed lock, takes token 2, and writes. Worker A finally wakes and writes with its stale token:

```
A acquired lock: true
A fencing token: 1
B acquired lock: true
B fencing token: 2
ACCEPTED: token 2 wrote report-from-B
REJECTED: token 1 is stale (resource already at 2)
```

The zombie leader's write bounced off the resource. Note carefully what did the saving: **not** the lock. The lock let A through — as far as Postgres was concerned, A was a session making a legal function call. The *token check* is what preserved correctness. Advisory locks are an optimization that keeps workers from trampling each other in the common case; the fencing token is the actual correctness guarantee. Ship the lock without the token and you have built something that works in testing and corrupts data in production.

---

### Gotchas That Will Bite You

**Session locks are reference counted.** Acquire the same key twice in one session and you must unlock it twice. `pg_locks` shows one row either way, which makes this delightfully hard to spot:

```sql
SELECT pg_advisory_lock(42);
SELECT pg_advisory_lock(42);
SELECT pg_advisory_unlock(42);   -- returns true, but the lock is STILL held
SELECT pg_advisory_unlock(42);   -- now it's actually released
```

Wrap acquisition in one code path, or use `pg_advisory_unlock_all()` to reset a session wholesale. Unlocking a key you never held returns `false` with a `WARNING: you don't own a lock of type ExclusiveLock` — a warning, not an error, so it will scroll past unnoticed.

**Locks are per-database, not per-cluster.** This one surprises people. The same key in two databases on the same instance does not conflict:

```
postgres db  -> true
other_app db -> true       <- same key 777, no conflict
postgres db (2nd session) -> false
```

If half your workers connect to `app` and half to `analytics` on the same cluster, they will not coordinate at all — each database has its own advisory namespace.

**The key space is flat and 32-bit-ish.** Every feature in a database shares one `bigint` namespace, so a hard-coded `42` in two unrelated modules is a silent deadlock waiting to happen. `hashtext` collapses names into a 32-bit integer, and the birthday bound means roughly 77,000 distinct lock names give you a coin-flip chance of at least one collision. For a dozen named locks that is a non-issue; for keys generated per tenant or per row, it is a real risk — use the two-argument form `pg_try_advisory_lock(classid, objid)` to carve out separate namespaces. And since `hashtext` is internal and its output is not guaranteed stable across major versions, never persist a hashed key and expect it to match after an upgrade.

---

### When Zookeeper Still Wins

Advisory locks live in the primary's shared memory. They are not replicated, not written to WAL, and not durable. **Restart Postgres and every lock in the cluster vanishes at once** — every standby can become leader simultaneously, which is a split-brain window that fencing tokens contain but do not prevent. Fail over to a replica and the same thing happens, because the new primary has no idea what the old one was holding.

That is the crux: Postgres is a single node for this purpose. Zookeeper and etcd are consensus systems that survive losing a node, because a quorum still remembers who holds what. If your coordination must outlive the loss of any single machine, a database whose lock table dies with its process is the wrong tool, and no amount of clever SQL fixes that.

They also offer primitives Postgres lacks: **watches** (be notified the instant a leader dies, rather than polling — though `LISTEN`/`NOTIFY` covers some of this), ephemeral sequential znodes for fair queueing, and linearizable ordering across the whole keyspace. And every lock holder in Postgres burns a connection, so coordination at ten-thousand-lock scale collides with `max_connections` long before Zookeeper would flinch.

The honest dividing line: use advisory locks when your workers already share a Postgres, the lock is an optimization rather than a safety property, and the resource is fenced. Reach for a consensus system when the coordination decision itself must be highly available and survive node loss — and be equally honest that the vast majority of teams electing a leader for one nightly job are not that team.

---

### Conclusion

Most coordination is one worker asking "is it my turn?", and standing up a quorum-based cluster to answer it is infrastructure you will maintain forever. Postgres answers it with `pg_try_advisory_lock`: exactly one winner, automatic release when the connection dies, no TTL to guess, and a `pg_locks` view that makes the whole thing debuggable with a `SELECT`.

The discipline is remembering what the lock actually promises. It promises one holder at a time — not that the holder is still alive, still sane, or still leader. Pair it with a fencing token so the resource itself rejects stale writers, pick transaction scope unless you specifically need the lock to outlive the transaction, and keep your key namespace deliberate. Do that, and you can delete an entire stateful service from your architecture — with clear eyes about the failover window you're accepting in exchange.
