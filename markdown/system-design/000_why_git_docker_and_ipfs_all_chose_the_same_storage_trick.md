# Why Git, Docker, and IPFS All Chose the Same Storage Trick

#### Content addressing turns data into its own address — and that one decision solves integrity, deduplication, and caching in a single stroke

**By Tihomir Manushev**

*Mar 20, 2026 · 5 min read*

---

You rename a file. The URL breaks. Someone downloads your package — how do they know it was not tampered with in transit? Your CI pipeline pulls the same Docker image on three build machines — it stores three identical copies.

Three different problems. One underlying cause: the address describes *where* the data lives, not *what* the data is. A file path, a URL, a registry tag — these are all location-based addresses. They point to a spot in a filesystem or on a network. Nothing in the address guarantees what you will find when you get there. The content can change, corrupt, or disappear while the address stays the same.

Content addressing flips this. Instead of naming data by its location, you compute a cryptographic hash of the content and use that hash as the address. The same content always produces the same hash. Different content always produces a different hash. Git, Docker, IPFS, pnpm, and Nix all converged on this pattern independently — because it solves integrity, deduplication, and caching in a single design decision.

---

### The Address IS the Checksum

Consider a traditional file path: `/data/reports/quarterly.pdf`. Nothing in this string tells you anything about what is inside the file. It could be last quarter's report, this quarter's report, or a corrupted zero-byte file. The path is a promise about location, not content. To verify that the file is what you expect, you need a separate mechanism — a checksum file, a manifest, a database entry.

Content addressing eliminates this gap entirely. The address `sha256:e3b0c44298fc1c14...` is not an arbitrary label. It is the output of running the file's contents through a hash function. To verify integrity, you re-hash the data you received and compare it to the address. If they match, the data is bit-for-bit identical to what was originally stored. If they do not match, the data is corrupt or tampered with. No separate checksum database. No trust required in the server that delivered it. The address itself is the proof.

This property is what makes `docker pull nginx@sha256:a3f2b7c9...` fundamentally different from `docker pull nginx:latest`. The tag `latest` is a mutable pointer — someone can push a new image and the tag silently points to different content. The digest `sha256:a3f2b7c9...` is immutable. No matter which registry serves it, no matter when you pull it, the content behind that digest is always the same. If it is not, the hash will not match and the pull fails.

The **avalanche effect** in cryptographic hashes makes this even stronger. Changing a single bit in the input flips roughly half the bits in the output. There is no way to make a subtle, undetectable change — any modification produces a completely different hash, and the mismatch is immediately visible.

The choice of hash function matters. Docker and most modern systems use **SHA-256** — 256-bit output, no known practical attacks. Git still uses **SHA-1** by default, a 160-bit hash that was practically broken in 2017 when researchers produced a collision for roughly $110,000 in compute. Git is transitioning to SHA-256. Newer systems like LLVM, Cargo, and OpenZFS have adopted **BLAKE3**, which runs at six to twelve gigabytes per second — roughly four times faster than SHA-256 — while maintaining equivalent security.

---

### Store Once, Reference Forever

Content addressing makes deduplication automatic. Before writing any data, the system computes the hash. If an object with that hash already exists in the store, the write is skipped. No comparison of file contents needed. No deduplication daemon running in the background. The hash match is sufficient.

The storage savings in production systems are substantial. Docker images achieve roughly a 6.9x deduplication ratio at the file level — fifty microservices based on similar base images share most of their layers instead of storing redundant copies. The package manager pnpm uses a global content-addressable store and hard-links packages into project directories, saving 50 to 70 percent of disk space compared to npm's copy-per-project approach. For daily backups with a typical 2 percent change rate, content addressing reduces thirty days of 1 TB backups from 30 TB to roughly 1.6 TB — a 95 percent reduction.

Retrieval is equally efficient. A hash is a direct lookup key — O(1) in a hash table or a flat directory structure. There is no path resolution, no directory traversal, no searching. You have the hash, you get the data.

Caching follows naturally. Content behind a hash is immutable by definition. A cache entry keyed by a content hash never needs invalidation — the content cannot change without changing the hash. This is why frontend build tools produce filenames like `style.f2a3b4c5.css`. The browser can cache it forever. When the content changes, the hash changes, the filename changes, and the browser fetches the new version. Cache invalidation — famously one of the two hard problems in computer science — becomes trivial.

---

### What Breaks

Content addressing gives you immutable data by design. That is its greatest strength and its primary limitation. Real systems need mutable references — "the latest version," "the current branch," "my home page." Content addressing cannot represent these directly because the hash changes every time the content changes.

Every content-addressed system solves this with an **indirection layer**: Git has refs and branches, Docker has tags, IPFS has IPNS records. You end up with two systems — an immutable content store and a mutable namespace — instead of one. The complexity does not disappear; it moves.

**Garbage collection** is the second challenge. When content is immutable and deduplicated, deleting it becomes dangerous. Other references might still point to it. The garbage collector must traverse the full reference graph to determine which objects are still reachable. In distributed systems like container registries, race conditions emerge when a client caches a blob's existence while GC simultaneously deletes it.

**Partial updates** are expensive. Changing one byte in a file re-hashes the entire file, producing a completely new object. Systems mitigate this with chunking — breaking large files into smaller pieces, each independently hashed — but this adds index overhead and complicates the storage layer.

Finally, **encrypted or compressed data** defeats deduplication entirely. The output of encryption looks random, so identical plaintext encrypted with different keys produces different hashes. If your data pipeline encrypts before storing, content addressing still provides integrity guarantees, but you lose the deduplication benefit.

---

### Conclusion

Content addressing is not a storage optimization. It is a design philosophy: make the data its own identifier, and integrity verification, deduplication, and cache invalidation become structural properties of the system rather than bolted-on mechanisms. The trade-off is real — you sacrifice native mutability and accept the complexity of a separate naming layer. But when Git, Docker, IPFS, pnpm, and Nix all converge on the same pattern independently, that is not coincidence. It is convergent evolution toward a fundamentally sound idea.
