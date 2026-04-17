# Bloom Filters: The Data Structure That Tells You "Definitely Not" or "Probably Yes" — And Why That's Enough

#### Cassandra, Chrome, and Medium all use a 1970s invention to skip billions of unnecessary lookups. Here's how it works and what it costs.

**By Tihomir Manushev**

*Apr 11, 2026 · 5 min read*

---

Your database reads a key from disk. The key is not there. The disk seek, the I/O wait, the page decompression — all wasted. Now multiply that by millions of queries per second. In most large-scale systems, a significant fraction of lookups are for keys that do not exist, and every one of them touches disk for nothing.

A **Bloom filter** sits in front of the disk and answers "definitely not here" in constant time, using a few kilobytes of memory. It is a probabilistic data structure — it can say "probably yes" when the answer is actually "no" (a **false positive**), but it *never* says "not here" when the item is actually present. Zero false negatives, guaranteed. That asymmetry is the entire value proposition, and it is enough to skip billions of unnecessary disk reads per day.

---

### How It Works: Bit Array + Hash Functions

A Bloom filter is a bit array of *m* bits, all initialized to zero, combined with *k* independent hash functions. That is the entire data structure — no pointers, no linked lists, no tree nodes.

**To insert an element**, hash it with all *k* functions. Each hash produces an index into the bit array. Set those *k* positions to 1. If a bit is already 1, leave it — bits only ever go from 0 to 1, never back.

**To query an element**, hash it with the same *k* functions and check the corresponding bit positions. If *any* position is 0, the element was never inserted — this is certain, because inserting it would have set that bit to 1. If *all* positions are 1, the element *might* be present. Another element (or a combination of elements) could have set those same bits by coincidence.

This is why false negatives are impossible. When you insert an element, you set *k* specific bits. Those bits can never be cleared. Any future query for that element will always find them set. The guarantee is structural — it does not depend on the data, the hash functions, or the fill rate.

False positives happen because the bit array is shared. As more elements are inserted, more bits flip to 1. Eventually, a query for a never-inserted element might find all *k* positions already set by other insertions. The more crowded the array, the higher the false positive rate.

This shared-bit design also means **deletion is not supported**. Clearing a bit to remove one element could erase evidence of another element that hashed to the same position. You cannot remove without risking false negatives — and the "no false negatives" guarantee is the entire reason Bloom filters exist.

Both insert and query run in O(*k*) time — constant, regardless of how many elements the filter contains. Memory is fixed at *m* bits. No resizing, no rebalancing, no garbage collection.

---

### Where Bloom Filters Run in Production

**Cassandra and RocksDB** are built on LSM trees — a storage architecture that writes data to sorted, immutable files called SSTables. A point lookup for a single key might need to check dozens of SSTables. Without a filter, each check means opening a file, decompressing a block, and scanning for the key. With a Bloom filter on each SSTable, the database asks "is this key *definitely not* in this file?" and skips the entire read if the answer is yes. Cassandra defaults to a 1% false positive rate under its SizeTiered compaction strategy. RocksDB's newer Ribbon filter achieves 1% at just 7 bits per key — roughly one byte of memory per element to avoid a disk read that costs milliseconds.

**Akamai CDN** discovered that 75% of objects in their disk cache were **one-hit-wonders** — requested exactly once and never again. Caching them was pure waste. They deployed a Bloom filter to track whether an object had been requested before. The first request for any URL passes through uncached. On the *second* request, the filter confirms the URL was seen before, and the object gets cached. This "second hit" policy freed 75% of cache disk space for content that actually gets reused. The occasional false positive — caching a genuine one-hit-wonder because the filter incorrectly says "seen before" — is a tiny price for reclaiming three-quarters of the cache.

**Medium** uses Bloom filters for recommendation deduplication. Before suggesting an article, the system checks "has this user already read this?" Storing the exact set of read article IDs for every user across millions of users and millions of articles would require hundreds of gigabytes of RAM. A Bloom filter compresses each user's read history into a compact bit array, answering "already read" queries in constant time with a controllable false positive rate. The worst case — occasionally hiding an unread article — is invisible to the user.

The pattern extends beyond these examples. Bitcoin SPV nodes use Bloom filters to request only relevant transactions from full nodes without downloading the entire blockchain. Ethereum embeds Bloom filters in block headers so applications can search for log events without scanning every transaction in every block.

---

### The Math: Sizing the Filter

The engineering decision behind a Bloom filter comes down to three numbers: the expected number of elements *n*, the desired false positive rate *p*, and the resulting memory cost *m*.

The optimal number of hash functions is *k* = (*m*/*n*) × ln(2). The false positive probability is approximately *p* ≈ (1 − *e*^(−*kn*/*m*))^*k*. In practice, the rule of thumb is simple: **9.6 bits per element gives a 1% false positive rate**. Around 14 bits per element drops it to 0.1%.

Run the numbers for a concrete case. One million elements at 1% FPR requires 9.6 million bits — about 1.2 megabytes. That is the total memory cost to avoid disk reads on a table with one million keys. The filter is orders of magnitude smaller than the data it protects.

The trade-off is always memory versus accuracy. Halving the false positive rate roughly doubles the memory. But even aggressive targets are cheap — a 0.1% FPR for 10 million elements costs about 17 MB. For a database doing thousands of reads per second, that 17 MB pays for itself in avoided I/O within minutes.

When you need deletion support, two alternatives exist. **Counting Bloom filters** replace each bit with a counter, allowing decrements on removal — at the cost of 3–4× more memory. **Cuckoo filters** offer better space efficiency at low false positive rates *and* support deletion, making them an increasingly popular drop-in replacement for standard Bloom filters.

---

### Conclusion

Bloom filters trade a tunable false positive rate for constant-time membership queries in negligible memory. The guarantee that matters is the one they never break: no false negatives. "Definitely not here" is always correct. Cassandra skips disk reads. Akamai skips caching one-hit-wonders. Medium skips recommending articles you have already read. All of them tolerate the occasional false positive — because the cost of one unnecessary lookup is trivially small compared to the billions of lookups they avoid.
