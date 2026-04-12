# Time-Travel Queries in PostgreSQL

#### One trigger and one range column give you full history on every row — no extensions, no specialized databases, just Postgres.

**By Tihomir Manushev**

*Apr 11, 2026 · 9 min read*

---

A customer disputes a charge. You check the `subscription_plans` table — the price shows $39/month. The customer insists they signed up at $29/month. They are right. Someone raised the price last Tuesday, and the `UPDATE` that changed it overwrote the only evidence you had.

This is the fundamental problem with mutable state. An `UPDATE` destroys the previous version of a row. A `DELETE` erases it entirely. Your database only knows what is true *right now*, not what was true last week.

**Time-travel queries** solve this by keeping every version of every row, automatically, and making any historical state queryable with a single `WHERE` clause. Some databases — SQL Server, MariaDB — support this natively with system-versioned temporal tables defined in the SQL:2011 standard. PostgreSQL does not support them natively, even in version 17. But you do not need native support. You can build the same capability with one trigger function, one history table, and one range column. No extensions. No specialized infrastructure. Just Postgres — and a pattern you can apply to any table in about 20 lines of PL/pgSQL.

---

### The Schema: Main Table + History Table

The pattern has two parts: the **main table** holds the current version of each row, and the **history table** stores every previous version.

Start with the main table. Two extra columns track when each row version became valid and when it expired:

```sql
CREATE TABLE subscription_plans (
    plan_id    int PRIMARY KEY,
    name       text NOT NULL,
    price      numeric(10, 2) NOT NULL,
    features   text[] NOT NULL DEFAULT '{}',
    valid_from timestamptz NOT NULL DEFAULT now(),
    valid_to   timestamptz NOT NULL DEFAULT 'infinity'
);
```

`valid_from` records when this version of the row was created. `valid_to` defaults to `'infinity'` — a special PostgreSQL value that means "this row is still the current version." When an `UPDATE` or `DELETE` retires a row, `valid_to` gets set to the transaction timestamp, closing out that version's validity window.

The convention of using half-open intervals — `[valid_from, valid_to)` where the start is inclusive and the end is exclusive — matters. It ensures that consecutive versions of a row snap together with no gaps and no overlaps. The moment one version expires is the exact moment the next version begins.

The history table mirrors the main table's columns and adds a surrogate key for uniqueness:

```sql
CREATE TABLE subscription_plans_history (
    history_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_id    int NOT NULL,
    name       text NOT NULL,
    price      numeric(10, 2) NOT NULL,
    features   text[] NOT NULL DEFAULT '{}',
    valid_from timestamptz NOT NULL,
    valid_to   timestamptz NOT NULL
);
```

Every row in this table is an expired version of a row from the main table. The combination of `plan_id`, `valid_from`, and `valid_to` tells you exactly when that version was the truth.

Now the trigger function that connects them. This function fires before every `UPDATE` and `DELETE`, copying the old row to history before Postgres overwrites or removes it:

```sql
CREATE OR REPLACE FUNCTION track_plan_changes()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO subscription_plans_history (
            plan_id, name, price, features, valid_from, valid_to
        ) VALUES (
            OLD.plan_id, OLD.name, OLD.price, OLD.features,
            OLD.valid_from, now()
        );
        NEW.valid_from := now();
        NEW.valid_to := 'infinity';
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO subscription_plans_history (
            plan_id, name, price, features, valid_from, valid_to
        ) VALUES (
            OLD.plan_id, OLD.name, OLD.price, OLD.features,
            OLD.valid_from, now()
        );
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER plan_versioning
    BEFORE UPDATE OR DELETE ON subscription_plans
    FOR EACH ROW EXECUTE FUNCTION track_plan_changes();
```

Walk through what happens on an `UPDATE` to see why the trigger fires `BEFORE` and not `AFTER`. When you run `UPDATE subscription_plans SET price = 39.00 WHERE plan_id = 2`, Postgres finds the matching row and fires the trigger *before* modifying it. At this point, `OLD` contains the current row (price = 29.00) and `NEW` contains the incoming row (price = 39.00). The trigger takes three actions: it inserts a copy of `OLD` into the history table with `valid_to` set to `now()`, stamping the exact moment this version expired. It then overwrites `NEW.valid_from` with `now()` and `NEW.valid_to` with `'infinity'`, so the updated row starts a fresh validity window. Finally, it returns `NEW`, allowing Postgres to proceed with the actual `UPDATE`.

The `BEFORE` timing is essential. An `AFTER` trigger would not be able to modify `NEW` — the row would already be written. By firing before the update, the trigger can adjust the temporal columns on the incoming row before Postgres commits it to disk.

Deletes follow the same logic. The trigger archives the old row to history with `valid_to = now()`, then returns `OLD` to let the `DELETE` proceed. The row disappears from the main table but lives on in history, queryable forever.

---

### Building It: A Working Example

Insert three subscription plans:

```sql
INSERT INTO subscription_plans (plan_id, name, price, features) VALUES
    (1, 'Starter',    19.00, ARRAY['5 projects', '1 GB storage']),
    (2, 'Pro',        29.00, ARRAY['50 projects', '10 GB storage', 'API access']),
    (3, 'Enterprise', 99.00, ARRAY['Unlimited projects', '100 GB storage', 'API access', 'SSO']);
```

All three rows have `valid_from` set to the insertion timestamp and `valid_to` set to `'infinity'`. They are the current truth. Now simulate the kind of changes that happen in production over weeks and months — compressed here into a few statements.

Raise the Pro plan's price:

```sql
UPDATE subscription_plans SET price = 39.00 WHERE plan_id = 2;
```

Rename Starter to Essentials:

```sql
UPDATE subscription_plans SET name = 'Essentials' WHERE plan_id = 1;
```

Discontinue the Enterprise plan:

```sql
DELETE FROM subscription_plans WHERE plan_id = 3;
```

Each of these statements fired the trigger. The Pro plan's old $29 row was copied to history before the price changed. The Starter row was copied before the rename. The Enterprise row was copied before deletion. All of this happened automatically — no application code touched the history table.

Query the main table — you see two current plans (Enterprise is gone):

```sql
SELECT plan_id, name, price, valid_from FROM subscription_plans;
```

```
 plan_id |    name    | price |          valid_from
---------+------------+-------+-------------------------------
       1 | Essentials | 19.00 | 2026-04-11 10:05:12.483+00
       2 | Pro        | 39.00 | 2026-04-11 10:04:47.291+00
```

Now check the history table — every expired version is preserved:

```sql
SELECT plan_id, name, price, valid_from, valid_to
FROM subscription_plans_history
ORDER BY valid_from;
```

```
 plan_id |    name    | price |          valid_from          |           valid_to
---------+------------+-------+------------------------------+-------------------------------
       1 | Starter    | 19.00 | 2026-04-11 10:03:22.105+00   | 2026-04-11 10:05:12.483+00
       2 | Pro        | 29.00 | 2026-04-11 10:03:22.105+00   | 2026-04-11 10:04:47.291+00
       3 | Enterprise | 99.00 | 2026-04-11 10:03:22.105+00   | 2026-04-11 10:05:33.719+00
```

Three rows, three retired versions. The old Starter before it became Essentials. The old Pro at $29 before the price hike. The Enterprise plan before deletion. Every version has a precise `valid_from` to `valid_to` window — a closed interval that tells you exactly when that version of reality was the truth.

**The time-travel query.** This is where the pattern pays off. To see what the plans table looked like *before any changes*, pick a timestamp when all original rows were still current and query across both tables:

```sql
SELECT plan_id, name, price
FROM (
    SELECT plan_id, name, price, valid_from, valid_to FROM subscription_plans
    UNION ALL
    SELECT plan_id, name, price, valid_from, valid_to FROM subscription_plans_history
) AS all_versions
WHERE valid_from <= '2026-04-11 10:03:30+00'
  AND valid_to   >  '2026-04-11 10:03:30+00';
```

```
 plan_id |    name    | price
---------+------------+-------
       1 | Starter    | 19.00
       2 | Pro        | 29.00
       3 | Enterprise | 99.00
```

The full database state at 10:03:30, fully reconstructed from the union of current and historical rows. The `WHERE` clause filters for rows whose validity window contains the target timestamp — only rows that were "alive" at that moment pass through. The customer who signed up when Pro cost $29 is vindicated.

This query pattern — union both tables, filter by time window — is the core of every time-travel system. Wrap it into a view so you never have to write the `UNION ALL` again:

```sql
CREATE VIEW plans_timeline AS
SELECT plan_id, name, price, features, valid_from, valid_to
FROM subscription_plans
UNION ALL
SELECT plan_id, name, price, features, valid_from, valid_to
FROM subscription_plans_history;
```

Now any "as of" query is a one-liner:

```sql
SELECT * FROM plans_timeline
WHERE plan_id = 2
  AND valid_from <= '2026-04-11 10:04:00+00'
  AND valid_to   >  '2026-04-11 10:04:00+00';
```

You can also query the full change history of a single plan — every version it ever had, in chronological order:

```sql
SELECT name, price, valid_from, valid_to
FROM plans_timeline
WHERE plan_id = 2
ORDER BY valid_from;
```

```
 name | price |          valid_from          |           valid_to
------+-------+------------------------------+-------------------------------
 Pro  | 29.00 | 2026-04-11 10:03:22.105+00   | 2026-04-11 10:04:47.291+00
 Pro  | 39.00 | 2026-04-11 10:04:47.291+00   | infinity
```

Two versions. The price change from $29 to $39, with the exact second it happened. For audit trails, compliance reports, and customer support disputes, this kind of complete change log — automatically maintained, zero application code — is exactly what you need.

---

### Using Range Types for Cleaner Queries

The two-column approach (`valid_from`, `valid_to`) works, but PostgreSQL has a better tool for this: **range types**. A `tstzrange` column replaces both columns with a single value and unlocks the `@>` containment operator.

```sql
ALTER TABLE subscription_plans
    ADD COLUMN valid_during tstzrange
    GENERATED ALWAYS AS (tstzrange(valid_from, valid_to, '[)')) STORED;

CREATE INDEX idx_plans_valid_during ON subscription_plans USING gist (valid_during);
```

The `[)` notation means "closed start, open end" — the row is valid *from* `valid_from` up to but *not including* `valid_to`. This ensures adjacent versions snap together without gaps or overlaps.

Now the "as of" query uses the containment operator:

```sql
SELECT * FROM subscription_plans
WHERE valid_during @> '2026-04-11 10:04:00+00'::timestamptz;
```

The GiST index on `valid_during` makes this an index scan regardless of table size. The `@>` operator asks "does this range contain this point?" — a single operator replaces the two-part `valid_from <= X AND valid_to > X` comparison, and the GiST index is purpose-built for exactly this kind of containment query.

If you adopt range types from the start, apply the same generated column and GiST index to the history table. The timeline view then becomes even simpler — you can query any point in time with a single `WHERE valid_during @> $1::timestamptz` clause across the union.

---

### Performance and Production Gotchas

**Indexing the history table.** The right index depends on your query pattern. For entity lookups — "show me all versions of plan 2" — a composite B-tree on `(plan_id, valid_from)` is the right choice. Postgres can use it for both the equality filter on `plan_id` and the range scan on `valid_from`. For point-in-time queries across all entities — "show me every plan as of last Tuesday" — a GiST index on a `tstzrange` column is significantly faster because the containment operator `@>` is GiST-native.

For very large history tables — hundreds of millions of rows — consider a **BRIN index** on `valid_from`. History tables are append-only, which means `valid_from` is naturally correlated with physical row order. BRIN exploits this correlation. A BRIN index on a 500M-row history table can be 99% smaller than the equivalent B-tree while delivering comparable scan performance for time-range queries.

```sql
CREATE INDEX idx_history_valid_from ON subscription_plans_history
    USING brin (valid_from);
```

**Partitioning.** Range-partition the history table by month or year. Old partitions can be detached and archived to cold storage. This keeps the active history table compact and makes `VACUUM` faster.

```sql
CREATE TABLE subscription_plans_history (
    history_id bigint GENERATED ALWAYS AS IDENTITY,
    plan_id    int NOT NULL,
    name       text NOT NULL,
    price      numeric(10, 2) NOT NULL,
    features   text[] NOT NULL DEFAULT '{}',
    valid_from timestamptz NOT NULL,
    valid_to   timestamptz NOT NULL
) PARTITION BY RANGE (valid_to);

CREATE TABLE history_2026_q1 PARTITION OF subscription_plans_history
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE history_2026_q2 PARTITION OF subscription_plans_history
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
```

**Storage growth.** Every `UPDATE` or `DELETE` adds a row to history. Monitor growth with `pg_total_relation_size('subscription_plans_history')`. For tables with infrequent changes (pricing, configuration, permissions), growth is negligible. For tables with frequent writes, consider a TTL policy that purges history older than your compliance window.

**Bulk updates.** An `UPDATE` touching one million rows fires the trigger one million times inside a single transaction. This can exhaust memory and hold locks for minutes. Batch large updates into chunks of 10,000–50,000 rows with explicit commits between batches.

**Schema migrations.** Adding a column to the main table requires adding it to the history table too. If you forget, the trigger function breaks on the next `UPDATE` because the `INSERT INTO history` statement references columns that do not exist in the history table. Catch this with a migration check that compares column lists between the paired tables. Automate it in your migration framework — do not rely on memory. One forgotten `ALTER TABLE` on the history side will surface as a runtime error on the first write, which is exactly the worst time to discover it.

**When not to use this.** High-write, low-audit tables — session data, analytics events, real-time metrics, ephemeral caches — do not benefit from row-level history. The trigger overhead on every `UPDATE` and `DELETE`, combined with unbounded storage growth, is not justified when nobody will ever query the history. For those workloads, use append-only logging, event sourcing, or a dedicated time-series engine instead. Time-travel queries shine on tables where changes are infrequent but each change matters: pricing, permissions, configuration, contracts, and anything subject to regulatory compliance.

---

### Conclusion

Time-travel queries give you full row-level history with one trigger and one extra table. The pattern works on any Postgres version — no extensions, no specialized databases, no infrastructure changes. Insert and query costs are minimal for tables with moderate write volume, and the payoff is immediate: you can reconstruct any row's state at any point in time.

Index with BRIN for scale. Partition for manageability. Plan for schema migrations on both tables. And when a customer disputes a charge from last Tuesday, you will have the answer in a single query — not an apology and a refund.
