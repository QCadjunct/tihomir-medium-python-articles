# Event Sourcing Is Not What You Think It Is — And That Is Why You Should Care

#### Store what happened, not where you are — and gain audit trails, time travel, and replay for free

**By Tihomir Manushev**

*Mar 22, 2026 · 5 min read*

---

Your e-commerce platform processes a refund. The database updates the order status to "refunded" and the balance to zero. A week later, the customer disputes the transaction. Your team needs to reconstruct exactly what happened — when the order was placed, when payment was captured, whether a partial shipment occurred before the cancellation. But the database only has the final state. The intermediate steps are gone. You are debugging from a snapshot with no history.

This is the fundamental limitation of CRUD. Every update overwrites the previous state. Every delete removes information permanently. The database tells you where you are, but never how you got there. Event sourcing inverts this entirely. Instead of storing current state, you store every state change as an immutable event in an append-only log. The event log is the source of truth. Current state is derived by replaying the events — and nothing is ever lost.

---

### How It Actually Works

In a CRUD system, an order has a row: `{id: 42, status: "shipped", total: 89.99}`. When the order ships, you update the status field. The previous value — "paid" — disappears.

In an event-sourced system, the same order is a stream of events: `OrderPlaced`, `PaymentCaptured`, `ItemPicked`, `OrderShipped`. Each event is immutable — once written, it never changes. To know the current state of order 42, you replay its event stream from the beginning. To know the state at any point in the past, you replay up to that moment and stop. Time travel is built into the data model.

Events represent **business facts**, not field changes. `CustomerRelocated` is a good event. `AddressFieldUpdated` is not — that is CRUD wearing an event sourcing costume. The distinction matters because business events carry meaning that survives schema changes and tells you *why* something happened, not just *what* changed.

This design creates a natural separation. The **write side** validates commands against the current aggregate state and produces events. The **read side** builds query-optimized projections from those events — denormalized views in PostgreSQL, Elasticsearch, or Redis, each shaped for a specific access pattern. This is **CQRS** (Command Query Responsibility Segregation), and it appears alongside event sourcing so often that the two are practically inseparable. You cannot efficiently query an event stream directly — you need read models.

---

### Where It Shines

Event sourcing is not a general-purpose architecture. It solves specific problems exceptionally well and creates unnecessary complexity everywhere else.

**Financial systems** are the canonical fit. Regulatory compliance demands a complete audit trail of every transaction. Event sourcing provides this by design — every deposit, withdrawal, and transfer is an immutable event. Rabobank processes real-time financial alerts across 300+ DevOps teams using Kafka-based event sourcing, with round-trip latency of 1-2 seconds from transaction to alert.

**E-commerce order processing** maps naturally to event streams. An order's lifecycle — placed, paid, approved, shipped, delivered, returned — is already a sequence of business events. Walmart's inventory system uses event sourcing to provide accurate availability across billions of products, with read and write models scaling independently.

**Netflix** built their entire download licensing service on event sourcing with Cassandra as the event store. They needed a stateful service that could evolve rapidly and scale to 260 million subscribers. The architecture gave them the ability to replay events to rebuild state after schema changes — something impossible with traditional CRUD.

**Any domain where "how did we get here?" matters as much as "where are we?"** — version control, multiplayer games, IoT sensor streams, collaborative editing. Git itself is event-sourced: every commit is an immutable event, and the repository state is derived by replaying the commit history.

---

### Where It Will Hurt You

Event sourcing is hard. Not conceptually — the idea is simple. Operationally.

**Simple CRUD applications** gain nothing. The plumbing is staggering: commands, command handlers, validators, events, aggregates, projections, and custom materialization code. For a basic user profile service, this is architectural overhead with zero return.

**Eventual consistency** is the default for read models. When a command produces an event, the projection that updates the read model processes it asynchronously. There is a window — usually milliseconds, sometimes seconds — where the read model is stale. For most applications this is fine. For a banking balance check immediately after a transfer, it requires careful handling.

**Event schema versioning** is one of the hardest operational challenges. When you add a field to an event, every consumer must handle both the old and new schema. When you rename a field, you need upcasters that transform historical events during replay. Schema evolution in an append-only log is fundamentally harder than running an `ALTER TABLE`.

**Storage grows without bound.** Events are never deleted. An e-commerce system processing a million orders per day with six events per order generates roughly 6 GB daily — 2.2 TB per year. One IoT team with 50,000 sensors reporting every second produced 200 GB per day and ran out of disk in three months. **Snapshots** mitigate replay cost by periodically saving aggregate state, but the events themselves remain.

**GDPR and the right to erasure** conflict directly with an immutable log. The standard solution is **crypto shredding**: encrypt each user's events with a per-user key, and destroy the key to "forget" them. It works, but adds key management complexity at scale.

The clearest anti-pattern: applying event sourcing to the entire system. Event sourcing belongs in specific bounded contexts — the complex, audit-critical domains. Everything else should stay CRUD. A whole system built on event sourcing is, as one widely-cited InfoQ article put it, an anti-pattern.

---

### The Decision Framework

Use event sourcing when you need **all three**: a complete audit trail, the ability to rebuild state from scratch, and temporal queries (what was the state at time T?). If you only need one, simpler solutions exist. An audit log table gives you a trail. Database backups let you rebuild. Temporal tables in PostgreSQL give you time queries. Event sourcing is the architecture that delivers all three as structural properties — but at the cost of operational complexity that is not worth paying unless you genuinely need the full package.

---

### Conclusion

Event sourcing trades simplicity for information. You pay with storage, eventual consistency, schema versioning complexity, and a steeper learning curve. You gain a complete, immutable history of every business decision your system has ever made — and the ability to derive any view of that data, at any point in time, by replaying the log. The right question is not "should we use event sourcing?" It is "does this specific part of our system need the guarantees that only event sourcing provides?" If the answer is yes, nothing else comes close. If the answer is no, a database row works fine.
