# Run A/B Tests Entirely in PostgreSQL

#### Deterministic assignment with no assignment table, a real chi-square p-value in pure SQL, and the sample-ratio check that catches broken experiments

**By Tihomir Manushev**

*Jul 17, 2026 · 10 min read*

---

An experimentation platform like LaunchDarkly or Optimizely does two things that actually matter for a controlled experiment: it decides which variant each user sees, and it tells you whether the difference in outcomes is real or noise. Everything else is a dashboard. Both of those core jobs are, at their heart, arithmetic — and Postgres is very good at arithmetic.

The instinct when a team wants A/B testing is to buy a platform or wire up a service, which means another vendor, another SDK, and experiment data living somewhere other than the database where your conversions already are. But assignment is a hash function, significance is a chi-square test, and Postgres 16 quietly shipped the one math function — `erfc` — needed to turn a chi-square statistic into a real p-value. You can run a statistically honest experiment in a few hundred lines of SQL and a nightly job.

This article builds one end to end for a checkout-flow experiment: deterministic bucketing that needs no storage, a genuine significance test computed in SQL with real numbers, the sample-ratio-mismatch check that most homegrown setups skip, and a clear account of where a real platform still earns its price.

---

### Deterministic Assignment Without an Assignment Table

The naive approach stores a row per user saying which variant they got. That table becomes a liability: it needs to exist before a user's first request, it has to be consistent across every server, and it grows with your audience. **Hash-based bucketing** eliminates it entirely. Feed the user's ID and the experiment's name through a hash, map the result to a bucket, and the bucket decides the variant. The same input always produces the same output, so assignment is a pure function — no storage, no lookup, identical on every machine.

```sql
CREATE FUNCTION bucket_of(p_key text, p_buckets int DEFAULT 100)
RETURNS int LANGUAGE sql IMMUTABLE AS $$
    SELECT (('x' || substr(md5(p_key), 1, 8))::bit(32)::bigint % p_buckets)::int;
$$;
```

The function takes the first 32 bits of an MD5 digest, reads them as a non-negative integer, and reduces modulo the bucket count. MD5 distributes uniformly, so the buckets come out evenly filled. Marking it `IMMUTABLE` is not decoration — it tells the planner the result depends only on the inputs, which is exactly the property that makes assignment reproducible. The same user in the same experiment lands in the same bucket every single time:

```sql
SELECT bucket_of('checkout-v2:12345') AS first_call,
       bucket_of('checkout-v2:12345') AS second_call;
--  first_call | second_call
-- ------------+-------------
--          33 |          33
```

Namespacing the key with the experiment name (`checkout-v2:`) matters: it ensures a user's bucket in *this* experiment is independent of their bucket in any other, so running many experiments at once doesn't correlate their assignments.

---

### Running the Experiment

Assign 40,000 users by splitting the bucket space in half — buckets 0–49 are control, 50–99 are treatment. In production the `converted` column would come from your real events table; here I simulate outcomes with a *second, independent* hash so the whole experiment is reproducible, giving control a true conversion rate of 12% and treatment 13.5%:

```sql
CREATE TABLE exp_events AS
WITH assigned AS (
    SELECT user_id,
           CASE WHEN bucket_of('checkout-v2:' || user_id) < 50
                THEN 'control' ELSE 'treatment' END AS variant
    FROM generate_series(1, 40000) AS user_id
)
SELECT user_id, variant,
       bucket_of('checkout-v2:outcome:' || user_id, 10000)
         < CASE variant WHEN 'control' THEN 1200 ELSE 1350 END AS converted
FROM assigned;
```

Aggregating the outcome per variant is a single grouped query, with `FILTER` doing the conditional counting:

```sql
SELECT variant,
       count(*) AS users,
       count(*) FILTER (WHERE converted) AS conversions,
       round(100.0 * count(*) FILTER (WHERE converted) / count(*), 2) AS conv_rate_pct
FROM exp_events GROUP BY variant ORDER BY variant;
```

```
  variant  | users | conversions | conv_rate_pct
-----------+-------+-------------+---------------
 control   | 19900 |        2379 |         11.95
 treatment | 20100 |        2701 |         13.44
```

Treatment converted at 13.44% against control's 11.95% — a lift of about 1.5 percentage points. It *looks* like a win. But "looks like" is where experiments go to die, because a difference that size can easily appear from pure chance. We need a number that says how surprised we should be.

---

### Is the Difference Real? Chi-Square in SQL

The right test for two variants and a binary outcome is a **chi-square test of independence** on the 2×2 table of variant against converted. It asks: if variant and conversion were truly unrelated, how likely is a gap at least this large? That likelihood is the **p-value**; below 0.05 we conventionally call the result significant.

The chi-square statistic for a 2×2 table has a compact closed form, `N(ad − bc)² / ((a+b)(c+d)(a+c)(b+d))`, where the four cells are the converted/not-converted counts for each variant. Turning the statistic into a p-value is the part people assume you need Python for — but a chi-square distribution with one degree of freedom is just a squared normal, so its upper-tail probability is `erfc(√(χ²/2))`, and Postgres 16 ships `erfc`:

```sql
WITH t AS (
    SELECT
        count(*) FILTER (WHERE variant='control'   AND converted)     AS a,
        count(*) FILTER (WHERE variant='control'   AND NOT converted) AS b,
        count(*) FILTER (WHERE variant='treatment' AND converted)     AS c,
        count(*) FILTER (WHERE variant='treatment' AND NOT converted) AS d
    FROM exp_events
), chi AS (
    SELECT ((a+b+c+d)::numeric * power((a*d - b*c)::numeric, 2))
             / (((a+b)*(c+d)*(a+c)*(b+d))::numeric) AS chi2
    FROM t
)
SELECT round(chi2, 3) AS chi_square,
       round(erfc(sqrt((chi2/2)::float8))::numeric, 5) AS p_value,
       (erfc(sqrt((chi2/2)::float8)) < 0.05) AS significant_at_95
FROM chi;
```

```
 chi_square | p_value | significant_at_95
------------+---------+-------------------
     19.837 | 0.00001 | t
```

A chi-square of 19.837 gives a p-value around 0.00001 — roughly a one-in-a-hundred-thousand chance of seeing a gap this big if the variants were actually equivalent. That is real, and the whole calculation ran in the database, over the same rows that hold your conversions, with no export step. Sanity-check the formula the easy way: the 0.05 threshold corresponds to `χ² = 3.841`, and `erfc(sqrt(3.841/2))` returns exactly `0.0500`.

One discipline the p-value alone won't give you: report the **effect size** next to it. A p-value says an effect exists, not how large it is — so always surface the actual lift (here, the 1.49-point jump from 11.95% to 13.44%, a relative gain near 12.5%) alongside the significance. A microscopic p-value on a lift too small to care about is a real result and a business non-event, and conflating the two is how teams ship changes that move the needle statistically but not commercially.

---

### The Check Everyone Skips: Sample Ratio Mismatch

A significant p-value is worthless if the experiment was broken to begin with, and the most common breakage is invisible: the two groups didn't actually receive the traffic split you designed. A bug in assignment, a redirect that drops on one variant, an analytics filter that quietly excludes some treatment events — any of these skews the ratio, and once the groups aren't comparable, every downstream number is fiction. **Sample Ratio Mismatch (SRM)** detection is a second chi-square, this time comparing observed group sizes against the expected 50/50:

```sql
WITH c AS (
    SELECT count(*) FILTER (WHERE variant='control')   AS n_c,
           count(*) FILTER (WHERE variant='treatment') AS n_t,
           count(*)::numeric AS n
    FROM exp_events
), srm AS (
    SELECT n_c, n_t,
           power(n_c - n/2, 2)/(n/2) + power(n_t - n/2, 2)/(n/2) AS chi2
    FROM c
)
SELECT n_c AS control_n, n_t AS treatment_n,
       round(100.0*n_t/(n_c+n_t), 2) AS treatment_share_pct,
       round(erfc(sqrt((chi2/2)::float8))::numeric, 6) AS srm_p_value,
       CASE WHEN erfc(sqrt((chi2/2)::float8)) < 0.05
            THEN 'SRM! results invalid' ELSE 'ok' END AS verdict
FROM srm;
```

Our healthy experiment passes — a 50.25% share is well within chance:

```
 control_n | treatment_n | treatment_share_pct | srm_p_value | verdict
-----------+-------------+---------------------+-------------+---------
     19900 |       20100 |               50.25 |    0.317311 | ok
```

Now watch it earn its keep. Simulate a logging bug that silently drops about 8% of treatment events, and rerun the identical check:

```
 control_n | treatment_n | treatment_share_pct | srm_p_value |       verdict
-----------+-------------+---------------------+-------------+----------------------
     19900 |       18483 |               48.15 |    0.000000 | SRM! results invalid
```

A 48.15% treatment share looks close enough to 50% that a human eyeballing it would shrug. SRM does not shrug — at this sample size that deviation has a p-value of essentially zero, and the verdict is unambiguous: something is broken, do not trust the conversion numbers. Run this check *before* you look at the result of any experiment. A failing SRM means the experiment is invalid, full stop, regardless of how beautiful the lift looks.

---

### Scheduling and Gotchas

Wire the analysis into a nightly refresh with `pg_cron` — compute each active experiment's rates, chi-square, and SRM verdict into a small results table, and your "dashboard" is a `SELECT`. But there are real statistical traps to respect, and SQL will not warn you about any of them.

**Don't peek and stop early.** The chi-square p-value is valid only for a sample size fixed *in advance*. If you rerun the query every hour and stop the moment it dips below 0.05, you will declare victory on experiments that are pure noise — repeated peeking inflates the false-positive rate dramatically. Decide the sample size up front, or switch to a sequential test designed for continuous monitoring. This is the single most common way homegrown experimentation goes wrong.

**Mind the test's assumptions.** The chi-square approximation degrades when any expected cell count is small (a rule of thumb is fewer than five), so it is unreliable for tiny samples or extremely rare conversions; reach for Fisher's exact test there. And every additional metric or variant you test multiplies your chances of a spurious "win" — correct for multiple comparisons rather than testing ten things and celebrating whichever crosses 0.05.

**Pick your hash deliberately.** MD5 is portable and stable across Postgres versions, which is what you want for assignment that must stay consistent forever. Do not swap in `hashtext` for this: it is faster but its output is explicitly not guaranteed stable across major versions, and a hash that changes under an upgrade reshuffles every user's variant mid-experiment.

---

### When LaunchDarkly Still Wins

Postgres gives you honest assignment and honest statistics, but an experimentation platform sells more than that, and some of it is genuinely hard to replicate. **Real-time flag control** is the big one: flipping a feature on, ramping it from 1% to 50%, or hitting a kill switch when errors spike — all without a deploy — is a platform's core competency, and a hash function in your database does not do it. If your experiments need to change exposure live, buy the platform.

The rest is a list of things you *can* build but probably shouldn't. A targeting UI so product managers launch experiments without SQL. Sequential testing with always-valid p-values, so peeking is safe by construction. Automated guardrail metrics that halt a rollout when a core number regresses. Mutually exclusive experiment groups so overlapping tests don't contaminate each other. Each is real engineering, and a mature platform delivers all of them maintained.

The honest dividing line: run experiments in Postgres when assignment can be static for the experiment's duration, your analysts are comfortable in SQL, and you value keeping experiment data in the same transactional system as the conversions it measures. Reach for a platform when you need live flag changes, non-engineers launching tests through a UI, or the statistical guardrails that stop a team from fooling itself. A great many teams shipping one experiment a month are firmly in the first camp — and for them, the platform is a subscription standing in for a few hundred lines of SQL.

---

### Conclusion

A controlled experiment is assignment plus a significance test, and both are arithmetic Postgres already does well. Hash the user and the experiment name for deterministic, storage-free bucketing; fold the outcomes with a grouped query; compute a real chi-square p-value using the `erfc` function Postgres 16 added for exactly this kind of work; and — above all — run the sample-ratio check that tells you whether the experiment was even valid before you trust its result.

Respect the statistics that SQL won't enforce for you: fix your sample size instead of peeking, watch the small-sample assumptions, and keep your assignment hash stable. Do that, and you get a statistically sound experimentation system living right next to your data, for the cost of some SQL and a nightly job — with clear eyes about the day you'll need live flags and a UI, and reach for a platform instead.
