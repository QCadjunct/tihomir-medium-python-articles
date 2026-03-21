# 5 System Design Patterns That Will Save Your Next On-Call Shift

#### These are the patterns that keep your phone silent at 3 AM — and the mistakes that make it ring

**By Tihomir Manushev**

*Mar 20, 2026 · 5 min read*

---

Your payment service starts timing out. Within thirty seconds, the checkout service backs up because every thread is waiting on a response that will never come. The recommendation service shares the same thread pool — it stalls too. The homepage stops loading. Your phone rings at 3 AM.

The root cause was a single slow dependency. The outage was the system's inability to contain the damage. Every production incident I have investigated shares this pattern: the initial failure is small, but the blast radius is enormous because no one built the walls to contain it.

These five patterns are those walls. They are not clever optimizations or theoretical exercises — they are the difference between a blip on your dashboard and an all-hands incident that wakes up the entire engineering team.

---

### Circuit Breaker

A circuit breaker sits between your service and each downstream dependency. It starts **closed** — requests pass through normally. When failures exceed a threshold, it trips **open** — all requests fail immediately without even attempting the call. After a cooldown period, it enters **half-open** — a handful of test requests probe whether the dependency has recovered. If they succeed, the circuit closes. If they fail, it reopens.

Without a circuit breaker, a slow dependency is worse than a dead one. A crashed service returns errors in milliseconds. A slow service holds your threads for seconds — long enough to exhaust every connection in your pool and cascade the failure upstream.

Shopify's production configuration protects 42 Redis instances with a threshold of 3 failures to trip, a 30-second cooldown, and 2 consecutive successes to close. Their key insight: the half-open timeout should match the dependency's p99 latency, not some arbitrary default. Getting this wrong took their overhead from 4% to 263%.

---

### Retry with Exponential Backoff

When a request fails, retry it — but not immediately and not in lockstep with every other client that also failed at the same moment. Naive retries create a **thundering herd**: thousands of clients fail at once, compute the same backoff delay, and retry simultaneously. The retries themselves become the denial-of-service attack.

Exponential backoff spaces retries apart: wait 1 second, then 2, then 4, then 8. Adding **jitter** — a random component to each delay — prevents synchronized retries across clients. AWS tested three jitter strategies at scale and found **decorrelated jitter** performs best: each sleep is a random value between the base delay and three times the previous sleep, capped at a maximum.

The AWS SDK defaults tell you what production systems actually use: 3 total attempts, 20-second maximum backoff, with a global token bucket that throttles retries when the system is already under pressure.

**The mistake that burns teams:** retrying at every layer. Service A retries 3 times to Service B, which retries 3 times to Service C. One user request generates 9 calls to Service C. Retry at exactly one level of the call chain and fail fast everywhere else. And never retry non-transient errors — a 400 Bad Request will never succeed on the fourth attempt.

---

### Bulkhead

Named after the watertight compartments in ship hulls — if one section floods, the others stay dry. In software, a bulkhead gives each downstream dependency its own isolated resource pool. If the payment service is slow and exhausts its 10 threads, the recommendation service's separate thread pool is completely unaffected.

Netflix learned this the hard way in 2012. Slow user-rating calls consumed a shared thread pool, which took down recommendations, search, and the homepage simultaneously. The fix was Hystrix's thread pool isolation — each dependency gets its own pool with a strict maximum. At the infrastructure level, Kubernetes resource limits serve the same purpose — explicit CPU and memory limits per container ensure one runaway process cannot starve the node.

**The mistake that burns teams:** using bulkheads without circuit breakers. A bulkhead isolates the blast radius, but the isolated pool still wastes all its threads calling a dead service. Use both together — the bulkhead contains the damage, the circuit breaker stops the bleeding.

---

### Rate Limiting

One misconfigured partner integration sends 10,000 requests per second instead of 100. Without rate limiting, that single client consumes all your server capacity and every other customer gets timeouts. With rate limiting, you reject the excess and everyone else is unaffected.

Rate limiting works in layers. At the **API gateway**, enforce global limits that protect all downstream services — this is your first line of defense against abuse and accidental load. At the **per-service** level, protect against internal callers that can be just as destructive as external ones. At the **per-user** level, prevent one tenant from monopolizing shared capacity.

**The mistake that burns teams:** only rate limiting at the edge. A batch job from an internal service, a misconfigured cron, or a partner's retry loop can generate just as much load as an external DDoS. Rate limit internal service-to-service calls too.

---

### Health Checks

A process is running. It responds to TCP connections. It returns 200 on the health endpoint. And it cannot serve a single user request because its database connection pool is exhausted and every worker thread is deadlocked. This is a **zombie process** — alive according to every simple check, dead for any practical purpose.

Kubernetes separates this into three probe types for a reason. **Liveness** probes answer "is this process fundamentally broken?" — check only internal state, keep it lightweight. If it fails, Kubernetes restarts the pod. **Readiness** probes answer "can this pod handle traffic right now?" — check critical dependencies like database connectivity and cache warmup. If it fails, the pod is removed from the load balancer but not restarted. **Startup** probes answer "has the application finished initializing?" — they run once and disable liveness/readiness until the application is ready.

**The mistake that burns teams:** using the same endpoint for liveness and readiness. They serve fundamentally different purposes. Liveness should almost always return 200 — unless the process itself is broken. Readiness should check whether the pod can actually do useful work. If your database goes down and your *liveness* probe checks the database, Kubernetes restarts every pod simultaneously — a restart storm that compounds the original problem. Mixing them up turns a recoverable dependency outage into a cascading restart loop.

---

### The Cheat Sheet

| Pattern | What It Prevents | Key Metric | Common Mistake |
|---------|-----------------|------------|----------------|
| **Circuit Breaker** | Cascade failures from slow dependencies | 3-5 failures to trip, 30s cooldown | Half-open timeout not matching p99 latency |
| **Retry + Backoff** | Thundering herd from synchronized retries | 3 attempts max, 20s cap, add jitter | Retrying at every layer (1 request → 9 calls) |
| **Bulkhead** | One slow dependency exhausting all resources | Separate thread/connection pool per dependency | Using bulkheads without circuit breakers |
| **Rate Limiting** | One noisy client killing the service for everyone | Per-user and per-service limits, not just edge | Only rate limiting external traffic |
| **Health Checks** | Zombie processes that pass simple checks but cannot serve traffic | Separate liveness (internal) and readiness (dependencies) | Same endpoint for liveness and readiness |

---

### Conclusion

None of these patterns are complicated in isolation. A circuit breaker is a state machine with three states. Retry with backoff is a loop with a sleep. A bulkhead is a separate thread pool. Rate limiting is a counter. Health checks are HTTP endpoints that return a status code. The complexity is not in implementing any one of them — it is in understanding which failure each one prevents and what happens when you skip it. Start with timeouts on every outgoing call. Add retries with backoff. Then circuit breakers on your least reliable dependencies. Build the walls before the flood, not during it.
