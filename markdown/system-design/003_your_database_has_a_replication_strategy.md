# Your Database Has a Replication Strategy — Here Is Why It Matters

#### Leader-follower, multi-leader, and leaderless replication solve different problems — and choosing wrong costs you consistency, availability, or your sanity

**By Tihomir Manushev**

*Mar 24, 2026 · 5 min read*

---

GitHub, October 2018. A 43-second network partition between data centers causes the MySQL cluster manager to promote a West Coast database as the new primary. The East Coast primary is still alive. Both data centers accept writes. Neither has the other's data. Recovery takes 24 hours and 11 minutes. Roughly 200,000 webhook deliveries are lost.

The root cause was not a bug. It was a replication topology — leader-follower — that could not handle a split-brain scenario gracefully. Every database replicates data across multiple nodes for durability and availability. The question is not whether to replicate. It is who accepts writes, and what happens when two nodes disagree. Three models answer this question differently, and each trades something the others do not.

---

### One Writer, Many Readers — Leader-Follower

All writes go to a single node — the leader. The leader streams changes to followers through a replication log. Reads can go to any node.

The consistency model is straightforward. Reads from the leader are always current. Reads from followers are eventually consistent, lagging behind by the time it takes to propagate changes. In PostgreSQL with asynchronous replication, this lag is typically 1 to 10 milliseconds within the same data center. Under heavy write load, it can spike to seconds. Under extreme load — or across data centers — it can grow to minutes.

The biggest advantage of leader-follower replication is what it avoids: **conflicts**. With a single writer, there are no concurrent writes to reconcile. No merge logic, no conflict resolution strategies, no silent data loss. One node is the authority, and everyone else follows.

The biggest risk is that the leader is a single point of failure. When it dies, the system must detect the failure, elect a new leader, and redirect clients. This failover window typically takes 6 to 60 seconds depending on the system. PostgreSQL with Patroni achieves 15 to 30 seconds. During this window, writes are blocked.

The catastrophic failure mode is split-brain — exactly what happened to GitHub. A network partition leads two nodes to both believe they are the leader. Both accept writes. When the partition heals, those writes conflict in ways that cannot be automatically resolved. Prevention requires consensus protocols, quorum-based leader election, and fencing tokens that reject operations from deposed leaders.

Despite these risks, leader-follower is the right choice for the vast majority of applications. A single PostgreSQL leader handles over 10,000 transactions per second. Most teams will never outgrow it.

---

### Everyone Writes — Multi-Leader

Multiple nodes accept writes simultaneously. Each leader processes writes locally and replicates them asynchronously to the others.

There are exactly three scenarios where multi-leader replication earns its complexity. **Multi-datacenter deployments** where users must write to their nearest data center with low latency. **Offline-capable applications** where each device acts as a local leader and synchronizes when connectivity returns — CouchDB and PouchDB are built for this. **Real-time collaborative editing** where multiple users modify the same document simultaneously — Google Docs uses operational transformation, Figma uses CRDTs.

Outside these three use cases, multi-leader replication is almost never worth the cost. And the cost is conflict resolution.

Two users update the same row in different data centers at the same instant. Who wins? **Last-Write-Wins** picks the highest timestamp and silently discards the other write — fast, simple, and data-lossy. **CRDTs** (Conflict-free Replicated Data Types) are mathematically guaranteed to converge but only work for specific data structures like counters, sets, and registers. **Application-level resolution** pushes the problem to your developers, who must write custom merge logic for every entity type.

Every conflict resolution strategy either loses data or adds significant complexity. Conflicts surface only under specific concurrent write patterns, making them difficult to test and brutal to debug. Do not use multi-leader replication within a single data center. The conflict complexity is never justified when nodes are on the same network.

---

### No Leader at All — Leaderless

No node is special. Every node accepts both reads and writes. Consistency is achieved through **quorum voting**: a write must be acknowledged by W nodes, and a read must query R nodes. As long as R + W > N (the total replica count), at least one node in the read set will have the latest write.

With N=3, W=2, R=2, the system tolerates one node failure for both reads and writes. The overlap guarantees that the freshest value appears in every read. Cassandra lets you tune this per query: `ONE` for speed (1-3ms, weak consistency), `LOCAL_QUORUM` for strong consistency within a data center (2-5ms), or `ALL` for the strongest guarantee at the cost of availability.

When a read detects that one replica has stale data, **read repair** writes the newer value back immediately. For data that is rarely read, a background **anti-entropy** process periodically scans replicas for differences and reconciles them.

The gotcha that catches teams: **R + W > N does not guarantee linearizability**. Concurrent writes with no global clock, clock skew between nodes, sloppy quorums during network partitions, and partial write failures can all produce stale reads even when the quorum math checks out. Leaderless replication offers tunable consistency, but "tunable" does not mean "free."

This model fits high-availability key-value and wide-column workloads at massive scale — Cassandra, DynamoDB, ScyllaDB.

---

### The Decision

| Model | Consistency | Conflicts | Failover | Best For |
|-------|------------|-----------|----------|----------|
| **Leader-Follower** | Strong (leader) / Eventual (followers) | None | 6-60 seconds, split-brain risk | 90% of applications |
| **Multi-Leader** | Eventual only | Complex (LWW / CRDTs / custom) | Not needed | Multi-DC, offline apps, collaboration |
| **Leaderless** | Tunable (eventual to strong) | LWW or CRDTs | Not needed | High-availability KV at scale |

Start with single-leader. Need writes in multiple regions with sub-50ms latency? If you also need strong consistency, use consensus-based systems like CockroachDB or Spanner. If your data model is key-value or wide-column and you can reason about per-query consistency, leaderless fits. Multi-leader is the last resort — use it only when the three specific use cases demand it, and budget engineering time for conflict resolution.

---

### Conclusion

The default is leader-follower. It handles more than most teams think, and its operational simplicity is worth more than theoretical scalability you may never need. Multi-leader and leaderless replication earn their place only when single-leader's limitations — write availability during failover, geographic write latency, or single-node throughput — become real bottlenecks in production. Not theoretical bottlenecks in a whiteboard session. Real ones, measured under real load. Choose the simplest model that meets your actual requirements, because the complexity you add to your replication layer is complexity you carry forever.
