# Token Bucket vs. Sliding Window: The Rate Limiting Choice That Shapes Your API's Behavior

#### One forgives bursts. The other enforces fairness. Stripe, Cloudflare, and AWS each picked a side — and the reason matters.

**By Tihomir Manushev**

*Apr 9, 2026 · 5 min read*

---

You hit a 429 Too Many Requests. But which algorithm decided you were "too fast"? The answer changes what your retry strategy should be — and whether bursting 50 requests in one second is a bug or a feature.

Two algorithms dominate API rate limiting: **token bucket** and **sliding window**. Both limit request rates. Both protect backends from overload. But they produce fundamentally different behavior under pressure, and the choice shapes how your API feels to every client that uses it. One rewards patience with burst capacity. The other enforces smooth, predictable throughput. The trade-off between them is the trade-off between flexibility and fairness.

---

### Token Bucket: Burst Now, Pay Later

A token bucket works like a prepaid balance. The bucket holds up to B tokens (the **burst capacity**). Tokens refill at a steady rate R per second. Each request costs one token. If the bucket is empty, the request gets a 429.

The key property is **burst allowance**. A client that stays idle accumulates tokens up to the maximum B. When it suddenly needs to send 50 requests at once — opening a mobile app, loading a dashboard, hydrating a cache — the bucket has tokens waiting. The burst goes through instantly. After that, the client is throttled to R requests per second until the bucket refills.

AWS API Gateway uses token bucket with a steady-state rate of 10,000 requests per second and a burst capacity of 5,000 requests. Stripe runs token bucket as one of four rate limiters stacked in production, each protecting a different layer. The algorithm dominates user-facing APIs because real traffic *is* bursty. Humans open apps, click buttons, and trigger parallel requests in clusters — not at evenly spaced intervals.

The cost is real. A client can legally send B requests in a single millisecond. If your backend cannot absorb that spike, the rate limiter did its job but your service still falls over. That is why production systems pair token bucket with a **concurrency limiter** — capping how many requests from one client can be in-flight simultaneously, regardless of how many tokens they have.

A quick distinction: the **leaky bucket** algorithm is token bucket's stricter cousin. It enforces uniform output regardless of input burstiness — requests drain at a fixed rate like water through a hole. ISPs use leaky bucket for traffic shaping. API teams almost never do, because most APIs *want* to allow bursts.

---

### Sliding Window: Smooth and Predictable

To understand why sliding window exists, you first need to see the bug it fixes.

**Fixed-window rate limiting** divides time into discrete intervals. Limit: 100 requests per minute. A client sends 100 requests at 11:59:59. The window resets at 12:00:00. The client immediately sends another 100 requests at 12:00:01. Both windows approve every request — 200 requests in two seconds. That is double the intended rate, concentrated at the boundary. For login endpoints, this is a brute-force vulnerability. For public APIs, it creates predictable load spikes every time windows reset.

The **sliding window counter** eliminates boundary spikes by blending two windows. It tracks the request count from both the current window and the previous window, then weights the previous window's count by the fraction of time that overlaps with the current position. If you are 30% into the current minute, the algorithm counts 100% of current-window requests plus 70% of previous-window requests. The result is smooth enforcement with no exploitable boundary.

Cloudflare runs this approach across their entire network. They tested it against 400 million requests and measured a 0.003% error rate — 99.997% accuracy compared to a theoretically perfect sliding window, at a fraction of the memory cost.

The alternative, **sliding window log**, stores the exact timestamp of every request and counts how many fall within the trailing window. It is perfectly accurate but costs O(N) memory per client, where N is the number of requests in the window. At high volume, this does not scale.

Cloudflare chose sliding window counter because they need predictable, fair enforcement across millions of concurrent clients. Burst tolerance would let attackers concentrate requests at window edges. Smoothness is not a nice-to-have — it is a security property.

---

### When to Pick Which

**Choose token bucket** when traffic is naturally bursty, you want to reward idle clients with accumulated capacity, and your backend can absorb short spikes. This covers most user-facing APIs — mobile apps, SPAs, webhook deliveries. The algorithm is simple to reason about: clients understand "I have a budget, and it refills."

**Choose sliding window** when fairness matters more than flexibility. Public APIs where abuse prevention is critical. Security-sensitive endpoints like authentication and password reset. Multi-tenant systems where one client's burst should not degrade another's experience.

Memory cost is comparable for both. Token bucket stores two values per client: current token count and last refill timestamp. Sliding window counter stores two to three values: current and previous window counts plus the window start time. Sliding window log is the outlier at O(N) per client — avoid it unless you need exact precision at low volume.

In distributed systems, both algorithms need shared state, typically Redis. Token bucket is slightly simpler to implement atomically — a single compare-and-decrement. Sliding window counter needs an atomic read-and-increment across two keys. Both are well-supported by Redis scripts.

Most production systems do not pick one. Stripe runs four different limiters simultaneously. The practical answer is often to layer token bucket for per-user rate limiting with sliding window for global fairness — burst tolerance where it helps, smooth enforcement where it matters.

---

### Conclusion

Token bucket forgives bursts. Sliding window enforces smoothness. Neither is universally better — your workload dictates the choice. Most APIs start with token bucket because real traffic is bursty and clients expect burst capacity. Add sliding window when fairness, abuse prevention, or predictable enforcement becomes the priority. The fixed-window boundary spike is the bug that makes this decision non-trivial. Whichever algorithm you choose, understand what "fair" means for your specific clients — because that is the question rate limiting actually answers.
