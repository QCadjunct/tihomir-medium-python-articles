# Your System Is Read-Heavy or Write-Heavy — And the Answer Changes Everything

#### The same database, cache, and storage engine that flies for reads will crawl for writes — here is how to optimize for each

**By Tihomir Manushev**

*Mar 26, 2026 · 5 min read*

---

Twitter processes 300,000 home timeline reads per second and 6,000 tweets per second. A 50:1 read-to-write ratio. Their original design computed timelines on every read — query every followed account's tweets, merge, sort, return. It worked until it did not. At 300,000 reads per second, computing timelines on the fly crushed the database. The fix was to flip the model: precompute every user's timeline when a tweet is published, trading expensive reads for expensive writes. One architectural decision, dictated entirely by the read-to-write ratio.

Every system leans one way. A product catalog is read thousands of times for every update. An IoT sensor pipeline writes millions of data points that may never be read individually. The caching strategy, the database engine, and the storage model that works for one will fail spectacularly for the other. Knowing which side your system leans toward is the first design decision that matters.

---

### Read-Heavy: Cache Everything, Compute Nothing

When reads outnumber writes by 100:1 or more, the goal is simple: never compute the same thing twice. Every repeated query that hits the database is wasted work.

**Cache-aside** is the workhorse pattern. The application checks the cache first. On a hit, it returns immediately — Redis responds in under a millisecond. On a miss, it queries the database, populates the cache, and returns. Wikipedia serves over 90% of its 21 billion monthly read requests from cache. The database barely sees traffic.

The alternative is **read-through**, where the cache itself manages database fetches on a miss. Simpler application code, but the first access to any item is always a cache miss. **Cache warming** — pre-populating the cache after deploys or restarts — prevents the cold-cache stampede where thousands of simultaneous misses flood the database at once.

**Read replicas** scale reads horizontally. The primary handles all writes; replicas serve read-only queries. Add more replicas as read traffic grows. The catch is replication lag — typically 1 to 10 milliseconds in PostgreSQL within a data center, but it can spike to seconds under heavy write load. Reading your own writes from a replica immediately after writing to the primary can return stale data. Route read-after-write queries to the primary for a short window, or accept eventual consistency explicitly.

**Denormalization** trades write complexity for read speed. Instead of joining three tables on every request, store the precomputed result in a single row. Reads become a simple lookup. The cost: every write must update multiple locations, and inconsistency becomes possible if one update fails. This is the same trade-off Twitter made — precompute at write time so reads are instant.

---

### Write-Heavy: Append Fast, Index Later

When write throughput is the bottleneck — IoT ingestion, logging pipelines, analytics, time-series data — the optimization strategy inverts. Stop making writes wait.

The foundation is the **write-ahead log (WAL)**. Every serious database uses one: log the change to disk first, acknowledge the client immediately, then apply the change to data structures asynchronously. The WAL turns random writes into sequential appends, which are fundamentally faster — 2 to 10 times faster on spinning disks, 1.5 to 3 times on SSDs.

**LSM trees** take this principle further. Writes go to an in-memory buffer. When the buffer fills, it flushes to disk as a sorted file. Background compaction merges these files periodically. The result: write throughput 1.5 to 2 times higher than B-trees, with 5 to 10 times less write amplification. Cassandra and RocksDB use LSM trees for exactly this reason. The trade-off is read performance — point lookups require checking multiple sorted files, making reads 1.5 to 3 times slower than B-tree databases. Bloom filters mitigate this, but the gap remains.

**Batching** reduces per-write overhead dramatically. Processing a thousand writes in a single batch is almost always faster than processing them individually. TimescaleDB at Cloudflare switched from individual INSERTs to bulk COPY operations and achieved over 100,000 rows per second. Aurora PostgreSQL's adaptive batching improved throughput by 18%. The principle is universal: fewer round trips to disk means higher throughput.

**Write-behind caching** absorbs write spikes by buffering in cache and flushing to the database asynchronously. The application writes to Redis, gets an immediate acknowledgment, and a background process drains the buffer to the database in batches. This is the fastest write pattern from the application's perspective, but it carries data loss risk — if the cache crashes before flushing, those writes are gone.

For workloads that outgrow a single node, **sharding** distributes writes across multiple database instances. Cassandra hit 1.1 million client writes per second by distributing across a cluster with consistent hashing. Without sharding, a single primary handles all writes — that is the throughput ceiling.

---

### The Engine Under the Hood

The database engine itself embodies the read-write trade-off.

**B-trees** (PostgreSQL, MySQL InnoDB) are balanced. Good read performance, acceptable write performance. The general-purpose choice. But for small records in large pages, write amplification can reach 256x — updating a 32-byte record rewrites an entire 8KB page.

**LSM trees** (Cassandra, RocksDB) are write-optimized. Sequential I/O, lower write amplification, higher ingestion throughput. TiKV chose LSM trees because "promoting read performance with caching is much easier than promoting write performance." Reads can be improved with bloom filters and block cache. Write throughput is structural — you cannot cache your way to faster writes.

**Column-oriented engines** (ClickHouse, Redshift) are analytical-read-optimized. They read only the columns a query needs, compress same-type data efficiently, and use vectorized execution. ClickHouse benchmarks show 10 to 100 times faster analytical queries than PostgreSQL — one team went from 20-minute queries to milliseconds. But they are poor for point lookups, updates, and transactional workloads.

---

### The Cheat Sheet

| Dimension | Read-Heavy | Write-Heavy |
|-----------|-----------|-------------|
| **Caching** | Cache-aside or read-through | Write-behind with async flush |
| **Database engine** | B-tree (PostgreSQL, MySQL) | LSM tree (Cassandra, RocksDB) |
| **Scaling** | Read replicas | Sharding / partitioning |
| **Data model** | Denormalized, precomputed | Append-only, batch-friendly |
| **Analytics** | Materialized views | Column-oriented (ClickHouse) |
| **Compute strategy** | Precompute at write time (fanout on write) | Append fast, compute at read time |

---

### Conclusion

The read-write ratio is not a detail you figure out later. It is the first question that shapes every decision downstream — which database engine, which caching pattern, which scaling strategy, which data model. Get it wrong and you optimize the side that does not need it while starving the side that does. Measure your actual workload. Count the reads, count the writes. Then build for the ratio you have, not the one you assume.
