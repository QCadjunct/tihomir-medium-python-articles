# Fan-Out and Fan-In: The Two Patterns Behind Every Scalable System You Use

#### One input becomes many. Many inputs become one. Twitter, Netflix, and MapReduce all depend on getting this right.

**By Tihomir Manushev**

*Apr 6, 2026 · 5 min read*

---

When you open Twitter, your timeline appears in milliseconds. Behind that instant load, a system decided — for every person you follow — whether to precompute your timeline when they tweeted or compute it now when you asked. One path writes to millions of caches. The other queries hundreds of feeds in real time.

These two strategies are **fan-out** and **fan-in**. Fan-out takes one input and turns it into many parallel operations. Fan-in takes many parallel results and combines them into one response. Together they form **scatter-gather** — the fundamental pattern behind timelines, search engines, notification systems, and data pipelines. The tension between them shapes every scalable system you use.

---

### Fan-Out: One Becomes Many

Fan-out comes in two flavors, and the choice between them changes everything about your system's performance profile.

**Fan-out on write** (push model) precomputes results at write time. Twitter's timeline delivery is the canonical example. When a user tweets, a fanout daemon looks up every follower's timeline in a Redis cluster and inserts the tweet ID into each one. Home timelines are capped at 800 entries, replicated three times, and pipelined in batches of 4,000 destinations at a time. The result: reads are trivially fast because the timeline is already built. The cost: one tweet can trigger millions of cache writes.

**Fan-out on read** (pull model) defers computation to read time. Instead of precomputing, the system stores each tweet once and assembles the timeline on demand — querying every followed user's tweet list, merging, sorting, and returning. Writes are cheap (store once), but reads are expensive because the system must gather and rank tweets from potentially thousands of sources in real time.

Beyond timelines, fan-out appears everywhere. **Message fan-out** uses a pub/sub broker like AWS SNS to distribute a single event to multiple SQS queues — one publish, many consumers, fully decoupled. **API gateway fan-out** is what Netflix does on every client request: a single API call triggers six to seven parallel backend service invocations, composing a unified response in under 100 milliseconds. The gateway scatters work across services and gathers the results before the user notices any latency.

---

### Fan-In: Many Become One

Fan-in is the inverse — collecting parallel results into a single output. If fan-out is the scatter, fan-in is the gather.

**Search engines** are the textbook example. A query fans out to dozens of index shards, each returning its top-ranked results. The aggregator fans in those partial results, merges the ranked lists, deduplicates, and returns a single page. Google runs this pattern billions of times per day across thousands of shards.

**Log aggregation** follows the same shape. Hundreds of microservices emit logs independently — each one a fan-out source. A centralized system like the ELK stack or Datadog acts as the fan-in point, collecting, indexing, and making those logs searchable from a single interface.

**MapReduce** makes the pattern explicit in its name. The map phase fans out — distributing data chunks across worker nodes for parallel processing. The reduce phase fans in — combining intermediate results into a final output. Every batch processing pipeline from Hadoop to Spark follows this structure.

**API composition** in microservice architectures is fan-in at the application layer. One client request triggers calls to a user service, a recommendations service, and a pricing service. The API gateway waits for all three, merges the responses, and returns a single JSON payload.

Here is the critical availability math. If you scatter a request to four nodes, each with 99% uptime, the probability that *all four* respond successfully is 0.99⁴ = 96.1%. Add more parallel nodes and the math gets worse. Every additional fan-out target increases the chance that at least one fails — which means your fan-in aggregator must handle partial failures gracefully.

---

### The Celebrity Problem

Twitter's fan-out on write works beautifully — until a celebrity tweets. When Lady Gaga posts to her 31 million followers, the fanout daemon must perform roughly 93 million cache writes (31M followers × 3 replicas). Delivery latency balloons: median delivery to one million followers takes around 3.5 seconds, but the P99 stretches to five minutes.

This latency gap created a visible bug Twitter engineers called **"headless tweets."** Replies to a celebrity's tweet would appear in followers' timelines *before* the original tweet, because the reply (from a user with fewer followers) fanned out faster than the celebrity's tweet.

Twitter's solution: a **hybrid approach**. Regular users (under roughly 10,000 followers) use fan-out on write — their tweets land in followers' Redis caches immediately. Celebrities use fan-out on read — their tweets are fetched and merged into the timeline at read time. This hybrid saved what Twitter described as "tens of percent of computational resources."

The celebrity problem illustrates two broader failure modes. **Unbounded fan-out** without backpressure overwhelms downstream services and triggers cascading failures. The fix: bounded queues, Kafka as a buffer between producer and consumers, and rate limiting at the producer. **Fan-in bottleneck** is the opposite risk — the aggregator becomes a single point of failure. If it dies, all parallel work is wasted. Production systems handle this with aggressive timeouts and partial results: serve what you have, do not block on the slowest node.

---

### Conclusion

Fan-out distributes work. Fan-in collects results. Together they form scatter-gather — the pattern behind timelines, search, notifications, and data pipelines. The trade-off is always the same: push (precompute, fast reads, expensive writes) versus pull (compute on demand, cheap writes, expensive reads). The right answer is usually hybrid — push for the common case, pull for the edge cases. Twitter learned this the hard way. Your system will face the same choice.
