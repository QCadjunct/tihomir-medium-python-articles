# Replace Cron and Airflow with pg_cron

#### Schedule jobs inside the database, with transactional guarantees and a history table that never lies about what actually ran

**By Tihomir Manushev**

*Jul 12, 2026 · 8 min read*

---

System cron has a memory problem: it has none. A job fires, writes to your database, and vanishes. Did it run at 3 AM? Did it finish? Did it silently error and leave half its work behind? You find out by grepping a log file on whichever box happens to hold the crontab — assuming the log rotated the way you think it did, and assuming you remember which of your twelve servers owns that particular schedule.

The usual escape hatch is Airflow: a scheduler, a metadata database, a web server, workers, and a Redis or Celery broker to glue them together. That is a lot of moving infrastructure to answer the question "run this query every five minutes." For a huge class of jobs — rollups, retention deletes, cache refreshes, reconciliation — the work already lives in Postgres. The scheduler doesn't need to.

`pg_cron` puts the schedule *inside* the database. Jobs are rows you can query, every run is recorded in a history table, and each job runs in its own transaction with the same durability guarantees as everything else in Postgres. This article builds a real scheduling setup for an EV charging network, with genuine `cron.job_run_details` output — including a job that fails on purpose so you can see exactly how the failure is captured.

---

### Installing pg_cron

`pg_cron` is a background worker, so it must be loaded at server start — it cannot be added with a plain `CREATE EXTENSION` alone. On Debian or Ubuntu with the PGDG apt repository, install the package that matches your major version:

```bash
sudo apt-get install -y postgresql-16-cron
```

Then tell Postgres to preload the worker and pick the database its scheduler lives in. Add two lines to `postgresql.conf`:

```conf
shared_preload_libraries = 'pg_cron'
cron.database_name = 'postgres'
```

`shared_preload_libraries` requires a full restart, not a reload — the background worker only starts during server boot. After restarting, create the extension in the database you named above:

```sql
CREATE EXTENSION pg_cron;
```

That single database now owns the scheduler. Jobs can still touch *other* databases on the same instance using `cron.schedule_in_database()`, but the `cron.job` and `cron.job_run_details` bookkeeping tables all live in this one. Everything below runs on Postgres 16.14 with pg_cron 1.6.

---

### Scheduling Your First Job

Here is the domain: a network of charging stations streams raw energy readings into `charge_events`, and we want a per-station hourly rollup in `station_hourly`.

```sql
CREATE TABLE charge_events (
    event_id    bigint GENERATED ALWAYS AS IDENTITY,
    station_id  int NOT NULL,
    session_ref uuid NOT NULL,
    kwh         numeric(8,3) NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE station_hourly (
    station_id   int NOT NULL,
    bucket       timestamptz NOT NULL,
    total_kwh    numeric(12,3) NOT NULL,
    event_count  int NOT NULL,
    refreshed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (station_id, bucket)
);
```

Scheduling is one function call. `cron.schedule` takes a job name, a schedule, and the SQL to run:

```sql
SELECT cron.schedule(
    'rollup-charge-events',
    '*/5 * * * *',
    'SELECT roll_up_charge_events()'
);
```

The `*/5 * * * *` is standard five-field cron syntax — every five minutes. Classic cron tops out at one-minute granularity, but pg_cron 1.5+ also accepts a plain interval string for sub-minute work, which is what I used to make this article's jobs fire quickly:

```sql
SELECT cron.schedule('rollup-fast', '15 seconds', 'SELECT roll_up_charge_events()');
```

Retention is the same one-liner. This job deletes raw events older than thirty days, every night at 3 AM, keeping the fact table lean without a maintenance script:

```sql
SELECT cron.schedule(
    'purge-old-events',
    '0 3 * * *',
    $$DELETE FROM charge_events WHERE recorded_at < now() - interval '30 days'$$
);
```

The `$$` dollar-quoting matters here: the job body contains single quotes, and dollar-quoting saves you from escaping them into an unreadable thicket of doubled apostrophes. Each scheduled job is a row in `cron.job`. You manage schedules with SQL, not by editing a file on a server you have to SSH into:

```
 jobid |  schedule   |       jobname        | active
-------+-------------+----------------------+--------
     1 | 15 seconds  | rollup-fast          | t
     2 | 20 seconds  | flaky-billing        | t
     3 | */5 * * * * | rollup-charge-events | t
     4 | 0 3 * * *   | purge-old-events     | t
```

---

### Why "Inside the Database" Changes Everything

The scheduling call is the boring part. The reason to run jobs inside Postgres is that each run executes in its own transaction — so a job either commits completely or leaves no trace. The classic cron failure mode, where a script dies halfway and leaves partial writes behind, cannot happen: an error rolls the whole run back.

That pairs naturally with **idempotent** jobs — jobs safe to run twice. The rollup function upserts, so re-running it recomputes the same buckets instead of double-counting:

```sql
CREATE OR REPLACE FUNCTION roll_up_charge_events() RETURNS void
LANGUAGE sql AS $$
    INSERT INTO station_hourly (station_id, bucket, total_kwh, event_count)
    SELECT station_id, date_trunc('hour', recorded_at), sum(kwh), count(*)
    FROM charge_events
    WHERE recorded_at >= now() - interval '3 hours'
    GROUP BY station_id, date_trunc('hour', recorded_at)
    ON CONFLICT (station_id, bucket) DO UPDATE
        SET total_kwh    = EXCLUDED.total_kwh,
            event_count  = EXCLUDED.event_count,
            refreshed_at = now();
$$;
```

The `ON CONFLICT ... DO UPDATE` is what makes this bulletproof under a scheduler. If a run is delayed, retried, or overlaps a manual invocation, the worst case is that a bucket gets recomputed to the same value. There is no "did it already run?" question to agonize over, because running it again is a no-op on the result. After a few firings against 5,000 seeded events, `station_hourly` held exactly what you'd expect — eight stations across three hourly buckets:

```
 station_id | hour  | total_kwh | event_count
------------+-------+-----------+-------------
          1 | 04:00 |  3587.266 |         163
          1 | 05:00 |  5506.269 |         234
          1 | 06:00 |  4960.356 |         228
          2 | 04:00 |  2965.909 |         143
          2 | 05:00 |  5243.908 |         247
```

Design every scheduled job this way. A job that is only correct if it runs *exactly* once is a job that will eventually corrupt your data, because no scheduler on earth guarantees exactly-once under restarts and failovers.

---

### The Job History You Always Wanted

Every run pg_cron performs is recorded in `cron.job_run_details`: when it started, when it ended, whether it succeeded, and the message the database returned. This is the table system cron never gave you. To prove it captures failures faithfully, I scheduled a job that divides by zero every 20 seconds alongside the healthy rollup:

```sql
SELECT j.jobname,
       d.status,
       d.return_message,
       to_char(d.start_time, 'HH24:MI:SS') AS started
FROM cron.job_run_details d
JOIN cron.job j USING (jobid)
ORDER BY d.runid DESC
LIMIT 6;
```

The result is the honest audit trail — successes and failures side by side, with the actual error text preserved:

```
    jobname    |  status   |    return_message     | started
---------------+-----------+-----------------------+----------
 flaky-billing | failed    | ERROR: division by zero | 06:52:00
 rollup-fast   | succeeded | 1 row                 | 06:51:55
 rollup-fast   | succeeded | 1 row                 | 06:51:40
 flaky-billing | failed    | ERROR: division by zero | 06:51:40
 rollup-fast   | succeeded | 1 row                 | 06:51:25
 flaky-billing | failed    | ERROR: division by zero | 06:51:20
```

Because the history is just a table, monitoring is just a query. A single statement tells you which jobs have been failing in the last hour — wire it to an alert and you have replaced a folder of log-scraping scripts:

```sql
SELECT j.jobname, count(*) AS failures, max(d.start_time) AS last_failure
FROM cron.job_run_details d
JOIN cron.job j USING (jobid)
WHERE d.status = 'failed'
  AND d.start_time > now() - interval '1 hour'
GROUP BY j.jobname;
```

```
    jobname    | failures |         last_failure
---------------+----------+-------------------------------
 flaky-billing |        5 | 2026-07-12 06:52:20.160755+00
```

One caveat worth knowing early: pg_cron does **not** retry failed jobs. A failure is recorded and the next scheduled run happens on time, but there is no automatic backoff-and-retry. If a job must retry, build that into the job's own logic — or schedule a companion job that inspects `cron.job_run_details` and re-runs the work. And that history table grows forever unless you prune it, which is itself a perfect pg_cron job: `DELETE FROM cron.job_run_details WHERE end_time < now() - interval '7 days'`.

---

### Stopping Jobs From Overlapping

Schedule a job every 15 seconds and assume it always finishes in 15 seconds, and one slow day you will have two copies running at once — fighting over the same rows. pg_cron will happily start a new run while the previous one is still going. The fix is a **transaction-level advisory lock**: a lightweight, application-defined lock keyed by an arbitrary integer, automatically released when the transaction ends.

```sql
CREATE OR REPLACE FUNCTION reconcile_billing() RETURNS text
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT pg_try_advisory_xact_lock(99) THEN
        RETURN 'skipped: a reconcile run already holds the lock';
    END IF;
    PERFORM pg_sleep(3);  -- stand-in for heavy reconciliation work
    RETURN 'done: billing reconciled';
END;
$$;
```

`pg_try_advisory_xact_lock` returns immediately: `true` if it grabbed the lock, `false` if someone else holds it. The `_try_` variant is the important part — it never blocks, so a skipped run exits instantly instead of piling up behind the one in flight. To prove it, I called the function from two sessions half a second apart:

```
 A -> done: billing reconciled
 B -> skipped: a reconcile run already holds the lock
```

Session A did the work; session B saw the lock was taken and bowed out cleanly. Because the lock is `xact`-scoped, it is released the instant A's transaction commits or rolls back — there is no stale lock to clean up if the worker crashes mid-run. This is the same coordination primitive people spin up Redis or Zookeeper for, already sitting inside the database.

---

### Schedules That Ship With Your Code

There is a quieter benefit to schedules being ordinary SQL: they belong in your migrations. A `cron.schedule` call is just a statement, so it lives in the same versioned migration file as the table and function it drives. Deploy the migration and the schedule ships atomically with the code that depends on it — no separate step where someone remembers to SSH in and edit a crontab, and no drift between what the code expects and what some server is actually running.

Because `cron.schedule` upserts by job name, re-running a migration is safe: scheduling `'rollup-charge-events'` again updates the existing job rather than creating a duplicate. Tearing a job down is equally declarative:

```sql
SELECT cron.unschedule('rollup-fast');
```

Your schedule becomes reviewable in pull requests, auditable in git history, and reproducible on a fresh database from the same migrations as everything else. Compare that to a crontab whose current state exists only on one machine, knowable only by reading that machine — and lost the moment it's reprovisioned.

---

### Where pg_cron Falls Short

`pg_cron` is not an Airflow replacement for every workload, and pretending otherwise will burn you. It runs jobs on the **primary** node only; jobs do not fire on physical replicas, and after a failover you need the extension configured on the new primary or your schedule silently stops. Every job also competes for the same CPU, memory, and connection slots as your live query traffic — a heavy rollup scheduled during peak load will contend with user requests, because it *is* just another backend on the same box.

More fundamentally, pg_cron schedules independent jobs; it does not model **dependencies**. There is no DAG, no "run C only after A and B succeed," no backfilling a date range, no dynamic task generation, and no UI for analysts to inspect. The moment your workflow spans multiple systems — pull from an API, transform in Postgres, push to a warehouse, notify Slack — or needs cross-task ordering and retries with backoff, a real orchestrator like Airflow, Dagster, or Temporal earns its operational weight.

The honest dividing line: reach for pg_cron when the work is **self-contained SQL on one database** and each job stands alone. Reach for an orchestrator when jobs depend on each other, span services, or need first-class retries and backfills. A great many "we need Airflow" projects are really a dozen independent SQL jobs wearing a trenchcoat — and those belong in `cron.schedule`.

---

### Conclusion

Most scheduled work in a Postgres shop is a query on a timer, and system cron makes that harder than it should be — no history, no transactions, no way to ask the database what it actually did. `pg_cron` collapses the whole problem into rows you can query: schedules in `cron.job`, an audit trail in `cron.job_run_details`, transactional runs, and advisory locks for coordination, all without a broker, a metadata database, or a web server to babysit.

Write your jobs to be idempotent, guard the long ones with an advisory lock, prune the history table, and remember that pg_cron won't retry for you or orchestrate dependencies. Do that, and you can delete a surprising amount of infrastructure — and finally answer "did the 3 AM job run?" with a `SELECT` instead of a shrug.
