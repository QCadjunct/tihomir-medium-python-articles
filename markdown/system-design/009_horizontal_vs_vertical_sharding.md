# Horizontal vs. Vertical Sharding: The Database Split Nobody Gets Right the First Time

#### One splits rows. The other splits columns. Discord, Notion, and Instagram each learned the hard way which one to pick — and when to switch.

**By Tihomir Manushev**

*Apr 17, 2026 · 5 min read*

---

Your database handles 2,000 queries per second. Then you launch a feature and it hits 15,000. Read replicas absorb the extra reads, but writes still funnel through one primary. Vertical scaling — bigger CPU, more RAM — has a ceiling, and you are approaching it. At some point, you need to split the database itself.

The question is *how* to split it. **Vertical sharding** separates entire tables into different database instances by domain. **Horizontal sharding** distributes rows of the same table across multiple databases by a shard key. Most teams start vertical and graduate to horizontal. The trade-offs between them — simplicity versus scale, convenience versus operational cost — shape your data architecture for years.

---

### Vertical Sharding: Split by Feature

Vertical sharding moves groups of related tables to separate database instances based on the domain they serve. Users and authentication go to one server. Orders and payments go to another. Analytics goes to a third. Each domain gets its own database with its own connection pool, its own replication, and its own scaling path.

The win is simplicity. No routing logic is needed — the application already knows which database handles which feature because the code is organized by domain. All related tables within a domain stay together, so queries within a domain still get full SQL capabilities: joins, transactions, foreign keys. The migration is straightforward: move tables, update connection strings, test.

The cost is that each domain database is still a single server. If the users table grows to 500 million rows and handles 30,000 writes per second, vertical sharding does not help — you have just moved the bottleneck from one server to another. You also lose cross-domain joins at the SQL level. If the orders service needs user data, the application must fetch it separately and compose the result in code.

Vertical sharding scales linearly with the number of features, not the number of users. It buys time — often months or years — but it has a ceiling. Once any single domain outgrows its server, you need horizontal sharding for that domain. Most companies hit this wall somewhere between 10,000 and 50,000 queries per second on a single domain.

---

### Horizontal Sharding: Split by Row

Horizontal sharding distributes rows of the same table across multiple databases using a **shard key** — a column value that determines which shard stores each row. Every row with shard key 1–1000 goes to shard A, 1001–2000 to shard B, and so on (range-based), or the key is hashed and the hash determines the shard (hash-based).

Instagram's approach is the textbook example of getting this right. They created 4,096 logical shards mapped to far fewer physical PostgreSQL servers. The shard key is user ID, and their 64-bit ID format encodes the shard directly: 41 bits for timestamp, 13 bits for shard ID, 10 bits for sequence number. Adding capacity means moving logical shards between physical machines — no rebucketing, no ID changes, no application-level migration. Discord takes a similar approach, sharding by guild (server) ID with roughly 1,000 guilds per shard.

The shard key decision is the most consequential choice you will make. A bad key creates **hot shards** — one shard receives disproportionate traffic while others sit idle. Sequential IDs and timestamps are catastrophic: all recent writes cluster on a single shard because the newest values always hash to the same range. Hash-based distribution spreads load evenly but makes range queries impossible — you cannot scan "all orders from last week" without hitting every shard. The ideal key produces even distribution *and* matches your dominant access pattern. For Instagram, that is user ID because most queries are "show me this user's posts." For Discord, it is guild ID because most queries are scoped to a single server.

The cost of horizontal sharding hits you on every query that touches more than one shard. Cross-shard queries become scatter-gather operations: the application fans the query out to all N shards, waits for all N responses, and merges the results. Each additional shard adds 15–25 milliseconds to the p99 tail latency because you wait for the slowest responder. Joins across shards are effectively impossible at scale. The standard workaround is to denormalize aggressively and replicate lookup tables across all shards so that every query can be answered by a single shard.

---

### The Trade-offs That Haunt You

**Resharding** is the tax you pay for growing. Range-based partitioning is easy to reason about but hard to rebalance — moving a range of rows from one shard to two requires copying data while the system is live. Hash-based partitioning distributes evenly but creates the "double the shards" problem: adding one shard requires rehashing and moving nearly all data. **Consistent hashing** solves this by moving only about 20% of data when a shard is added or removed. DynamoDB and CockroachDB use this approach. Instagram's logical-to-physical mapping achieves a similar result without consistent hashing — the logical shard count never changes, only the physical servers behind them.

**Transactions** work normally within a single shard. Across shards, you need distributed transactions (two-phase commit) or accept eventual consistency. Most teams choose eventual consistency and design around it — idempotent operations, saga patterns, and reconciliation jobs. Two-phase commit is correct but slow and operationally fragile at scale.

**Operational complexity** scales linearly with shard count. N shards means N databases to monitor, back up, upgrade, and failover independently. Schema migrations must execute on every shard — a column rename becomes an N-step rollout instead of one `ALTER TABLE`. One degraded shard can impact all queries that touch it, and debugging which shard is slow requires shard-aware observability tooling.

**Tools that help** exist but do not eliminate the complexity — they move it from application code to infrastructure. **Vitess**, built at YouTube, adds a proxy layer that routes queries to the correct shard and supports online resharding. **Citus** extends PostgreSQL with transparent sharding, letting you treat a sharded cluster as a single database for many query patterns. These tools are worth evaluating, but they add their own operational surface area.

The progression most companies follow is predictable: single database → read replicas → vertical sharding → horizontal sharding. Skip steps and you inherit complexity you do not need yet. Every stage buys time and defers the next stage's costs until the traffic justifies them.

---

### Conclusion

Vertical sharding is simple and buys time. Horizontal sharding scales further but costs you cross-shard queries, resharding headaches, and the permanent weight of a shard key decision. Start vertical. Graduate to horizontal when a single domain outgrows its server. When you do, invest heavily in the shard key — it is the one decision you cannot easily change later. Instagram's logical-to-physical mapping let them scale PostgreSQL to billions of rows without ever rebucketing. Most teams are not that lucky on the first try, which is why the best shard key is the one you choose *after* understanding your access patterns, not before.
