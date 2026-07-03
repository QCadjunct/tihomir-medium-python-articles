# Build Your LLM's Memory with pgvector

#### Your agent's long-term memory is just rows with an embedding column — semantic recall, hybrid search, and HNSW indexes without bolting a second database onto your stack.

**By Tihomir Manushev**

*Jul 3, 2026 · 9 min read*

---

You shipped an LLM agent, and to give it long-term memory you reached for a dedicated vector database — Pinecone, Weaviate, Milvus. Now every fact the agent learns lives in a second system. You sync IDs between it and your primary database, reconcile writes when one of them fails, pay a second bill, and watch your "memories" sit in a datastore that cannot join to the user, the session, or the billing row they actually describe. The memory of your agent is architecturally divorced from everything it remembers *about*.

Strip away the marketing and a memory is three things: a short piece of text, a numeric embedding of that text, and some metadata. That is a row. PostgreSQL has stored rows since before you were writing code, and with the **pgvector** extension it stores the embedding alongside them and runs nearest-neighbor search directly over that column. No second database, no synchronization layer, no reconciliation job — just an `ORDER BY` next to the relational data the memory belongs to.

This article walks the whole path: store and recall memories with the correct distance operator, choose between the two ANN index types with real recall-versus-latency numbers, add keyword-aware **hybrid search**, and find the exact point where a specialized vector database genuinely earns its cost. Every measurement below comes from pgvector 0.8.4 on PostgreSQL 16, over a table of 100,000 synthetic memories.

---

### Setup

pgvector is an extension, not a fork. It ships in the official Postgres 16 and 17 Docker images and is available on RDS, Cloud SQL, and Supabase. One statement turns it on and introduces the `vector` type — an array of `float4` with a fixed width:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE agent_memories (
    memory_id  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    content    text         NOT NULL,
    kind       text         NOT NULL,      -- 'preference' | 'fact' | 'episodic' | 'instruction'
    embedding  vector(1536) NOT NULL,      -- one row per remembered fact
    created_at timestamptz  NOT NULL DEFAULT now()
);

CREATE INDEX idx_memories_kind ON agent_memories (kind);
```

The `embedding` column is `vector(1536)` because 1536 is the width of OpenAI's `text-embedding-3-small`; the dimension is fixed when the column is defined and every row must match it. The `kind` column tags each memory so the agent can later ask only for standing preferences or only for episodic recollections, and the plain btree index on it matters more than it looks — we will come back to it when filtering collides with the vector index. `created_at` gives you a lever for memory decay.

One habit worth forming: confirm the version, because features referenced later depend on it.

```sql
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

```
 extversion
------------
 0.8.4
```

Iterative index scans, which fix a nasty filtering bug near the end of this article, require pgvector 0.8 or newer.

---

### Storing and Recalling Memories

Embeddings come from a model, not from Postgres. You send text to an embedding endpoint, get back a list of floats, and store it. pgvector's psycopg adapter registers the `vector` type so you can pass a Python list straight into a query parameter:

```python
import psycopg
from pgvector.psycopg import register_vector
from openai import OpenAI

client = OpenAI()
conn = psycopg.connect("dbname=memdb")
register_vector(conn)

def remember(text: str, kind: str) -> None:
    vec = client.embeddings.create(
        model="text-embedding-3-small", input=text
    ).data[0].embedding                      # 1536 floats
    conn.execute(
        "INSERT INTO agent_memories (content, kind, embedding) VALUES (%s, %s, %s)",
        (text, kind, vec),
    )
    conn.commit()
```

That is the entire write path. The model turns text into a point in 1536-dimensional space; Postgres stores the point. One design note before recall: what you embed matters as much as how you search it. Embedding an entire document into a single vector averages every distinct idea in it into one blurred point, which is why long source material gets **chunked** — split into passages of a few hundred tokens, each embedded and stored as its own row. Recall then surfaces the specific paragraph that answers the question instead of the whole file it happened to live in. Recall is the inverse of the write path — you embed the incoming user message and ask for the nearest stored points. But pgvector ships three distance operators, and choosing the wrong one silently returns wrong rankings:

```sql
SELECT memory_id,
       embedding <-> :query AS l2_distance,
       embedding <#> :query AS neg_inner_product,
       embedding <=> :query AS cosine_distance
FROM agent_memories
ORDER BY embedding <=> :query
LIMIT 3;
```

```
 memory_id | l2_distance | neg_inner_product | cosine_distance
-----------+-------------+-------------------+-----------------
     73296 |      0.5766 |           -0.8338 |          0.1662
     90430 |      0.5776 |           -0.8332 |          0.1668
     30781 |      0.5781 |           -0.8329 |          0.1671
```

`<->` is L2 (Euclidean) distance, `<#>` is the inner product, and `<=>` is cosine distance — three different numbers for the same pair of vectors. For text embeddings you almost always want **cosine**. Two subtleties bite people here. First, `<=>` returns cosine *distance*, not similarity: `0` means identical, `1` means orthogonal, so you `ORDER BY` it *ascending* and convert to a human-friendly score with `1 - (embedding <=> query)`. Second, `<#>` returns the *negative* inner product — Postgres index scans only walk in ascending order, and negating the dot product makes "most similar" sort first. For unit-length embeddings (OpenAI's are normalized) `<#>` and `<=>` produce identical rankings, and `<#>` is marginally cheaper. Getting this recall query right is the whole game:

```sql
SELECT memory_id, kind,
       1 - (embedding <=> :query) AS cosine_similarity
FROM agent_memories
ORDER BY embedding <=> :query
LIMIT 5;
```

```
 memory_id |    kind    | cosine_similarity
-----------+------------+-------------------
     73296 | fact       |            0.8338
     90430 | episodic   |            0.8332
     30781 | preference |            0.8329
     21893 | preference |            0.8327
     22405 | fact       |            0.8318
```

Given the embedding of the current user message, those are the five memories the agent should have in its context window.

---

### Indexing: IVFFlat vs HNSW

That query is correct, but it does not scale. With no index, pgvector computes the distance from the query to *every* row and sorts the results:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT memory_id, content
FROM agent_memories
ORDER BY embedding <=> :query
LIMIT 10;
```

```
 Limit  (actual time=833.242..833.246 rows=10)
   ->  Sort  (actual time=833.241..833.243 rows=10)
         Sort Key: (embedding <=> $0)
         Sort Method: top-N heapsort  Memory: 27kB
         ->  Seq Scan on agent_memories  (actual time=0.188..811.983 rows=100000)
 Execution Time: 833.289 ms
```

833 milliseconds to remember one thing, and it grows linearly with the table. You need an **approximate nearest neighbor** (ANN) index, and pgvector offers two that are genuinely different tools.

**IVFFlat** partitions the vectors into `lists` clusters using k-means, and a query scans only the `ivfflat.probes` nearest clusters instead of the whole table. That design has a sharp consequence: k-means needs data, so you build the index *after* loading representative rows — build it on an empty table and the centroids are meaningless. The rule of thumb is `lists = rows / 1000` up to a million rows:

```sql
CREATE INDEX idx_memories_ivfflat
    ON agent_memories USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

**HNSW** builds a multi-layer proximity graph instead — each vector links to its `m` nearest neighbors (default 16), `ef_construction` sets how hard the builder searches while wiring the graph (default 64), and `hnsw.ef_search` sets how wide the query walks it (default 40). It has no training step, so you can create it on an empty table and it stays correct as data changes:

```sql
SET maintenance_work_mem = '1GB';

CREATE INDEX idx_memories_hnsw
    ON agent_memories USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

With the graph in place, the same recall query stops scanning:

```
 Limit  (actual time=1.706..1.820 rows=10)
   ->  Index Scan using idx_memories_hnsw on agent_memories  (actual time=1.705..1.818 rows=10)
         Order By: (embedding <=> $0)
         Buffers: shared hit=732
 Execution Time: 1.875 ms
```

From 833 ms and 600,000 buffer accesses down to under 2 ms and 732 — the index touches a few hundred graph nodes instead of every row. The lever that trades accuracy for speed is `hnsw.ef_search`. **Recall@10** here means the fraction of the *true* top-10 (measured by an exact brute-force scan) that the approximate search actually returned:

```
 ef_search | recall@10 | mean latency
-----------+-----------+--------------
        40 |     0.967 |       1.5 ms
       100 |     0.985 |       1.7 ms
       200 |     0.994 |       2.3 ms
```

Push `ef_search` up and recall climbs toward exact at the cost of latency; keep it at least as large as your `LIMIT` or recall falls apart. Two traps hide in this section. The operator class must match the operator: a `vector_cosine_ops` index accelerates only `<=>`. Query the same column with `<->` and the planner silently ignores the index and seq-scans — back to 750 ms. And the index only applies to `ORDER BY <operator> ... LIMIT k`; drop the `LIMIT` and you lose it.

Which one? **HNSW is the default recommendation today** — a better recall-versus-latency frontier and no training step — and you pay for it in build time (52 seconds here versus under 8 for IVFFlat) and memory. Both indexes land near 780 MB on this table — roughly the footprint of the vectors themselves — so plan for your storage to nearly double when you add one. IVFFlat wins when builds must be cheap and the dataset is fairly static. One honest caveat about these numbers: on this cleanly clustered synthetic data IVFFlat reached full recall at `probes = 1`, because the clusters line up neatly with its k-means lists. Real embeddings are messier; there you raise `probes`, and latency with it, to claw recall back — which is exactly why HNSW's frontier usually wins in production.

---

### Hybrid Search

Vector search has one blind spot: exact tokens. A user asks "is PagerDuty still our escalation path," and the semantically closest memory might be about *Opsgenie* — adjacent in meaning, wrong in fact. The fix is not to replace vector search but to run keyword search beside it and fuse the two. Postgres already has full-text search built in; add a generated `tsvector` column and a GIN index:

```sql
ALTER TABLE agent_memories
    ADD COLUMN content_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

CREATE INDEX idx_memories_tsv ON agent_memories USING gin (content_tsv);
```

Be precise about what this ranking is: it is **not BM25**. `ts_rank` weights by term frequency, and `ts_rank_cd` adds cover density (how close the matched terms sit). Neither uses inverse document frequency or document-length normalization, because Postgres keeps no corpus-wide term statistics — and BM25 is defined by exactly those. Call it a lexical score, not BM25. If you truly need BM25 inside Postgres, ParadeDB's `pg_search` extension (backed by tantivy) implements it.

To combine two rankings measured on incomparable scales — a cosine distance and a lexical score — use **Reciprocal Rank Fusion**. Rank each list independently, then score every document by `sum(1 / (k + rank))` with `k` conventionally 60. Because it fuses on rank *position*, the raw scores never have to be reconciled:

```sql
WITH vector_ranked AS (
    SELECT memory_id,
           row_number() OVER (ORDER BY embedding <=> :query) AS rnk
    FROM agent_memories
    ORDER BY embedding <=> :query
    LIMIT 20
),
keyword_ranked AS (
    SELECT memory_id,
           row_number() OVER (ORDER BY ts_rank_cd(content_tsv, q) DESC) AS rnk
    FROM agent_memories, plainto_tsquery('english', 'PagerDuty escalation') q
    WHERE content_tsv @@ q
    LIMIT 20
)
SELECT COALESCE(v.memory_id, k.memory_id) AS memory_id,
       round(COALESCE(1.0/(60 + v.rnk), 0) + COALESCE(1.0/(60 + k.rnk), 0), 5) AS rrf_score,
       v.rnk AS vec_rank, k.rnk AS kw_rank
FROM vector_ranked v
FULL OUTER JOIN keyword_ranked k USING (memory_id)
ORDER BY rrf_score DESC
LIMIT 5;
```

```
 memory_id | rrf_score | vec_rank | kw_rank
-----------+-----------+----------+---------
         1 |   0.03227 |        3 |       1
         2 |   0.01639 |        1 |
         3 |   0.01613 |        2 |
         4 |   0.01563 |        4 |
         5 |   0.01538 |        5 |
```

Pure vector search had ranked memory 1 — the one that literally names PagerDuty — third, behind two semantically closer memories. Keyword search found only memory 1. Fused, its two strong ranks (`1/63 + 1/61`) lift it to the top, ahead of the vector winner that scored on a single list. The `FULL OUTER JOIN` keeps documents that appear in only one ranking, and `COALESCE` treats a missing rank as a zero contribution.

---

### Production Gotchas and When a Vector Database Wins

**The 2,000-dimension ceiling.** The `vector` type stores up to 16,000 dimensions, but the HNSW and IVFFlat indexes only support up to 2,000. The day you upgrade to `text-embedding-3-large` at 3,072 dimensions, index creation fails outright:

```sql
CREATE INDEX ON large_embeddings USING hnsw (embedding vector_cosine_ops);
-- ERROR:  column cannot have more than 2000 dimensions for hnsw index

CREATE INDEX ON large_embeddings
    USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops);
-- CREATE INDEX
```

Casting to **`halfvec`** (16-bit floats) raises the index ceiling to 4,000 dimensions, halves the storage, and costs almost nothing in recall for most models.

**Filtering collides with the ANN index.** This one is silent and dangerous. Write `WHERE kind = 'preference' ORDER BY embedding <=> :query LIMIT 10` and the index returns its `ef_search` nearest candidates *first*, then the `WHERE` clause throws away the ones that do not match — so you can get fewer than ten rows, sometimes zero. At `ef_search = 20` with a filter matching a quarter of the table, my 100 test queries averaged **5.3** rows returned instead of 10, and some returned none. Two fixes: pre-filter exactly with a btree or partial index on `kind`, or turn on **iterative index scans** (pgvector 0.8+), which keep pulling from the graph until enough rows survive the filter:

```sql
SET hnsw.iterative_scan = strict_order;   -- keeps scanning until LIMIT is satisfied
```

It is `off` by default, bounded by `hnsw.max_scan_tuples` (20,000), and IVFFlat supports only the looser `relaxed_order`.

**Build memory is real.** HNSW builds quickly only when the graph fits in `maintenance_work_mem`; otherwise it crawls. Raise it for the build. And parallel builds allocate a shared-memory segment sized to that setting — I watched one die with `could not resize shared memory segment ... No space left on device` because the container's `/dev/shm` was only a gigabyte. Size your shared memory, or drop `max_parallel_maintenance_workers` to zero, before building large indexes.

**When a dedicated vector database wins.** Postgres carries you comfortably into the low hundreds of millions of vectors on a single box. Past that — billions of vectors, sharded ANN across nodes, sub-millisecond p99 at very high QPS, or product-quantization and DiskANN tricks to fit the index in RAM — a purpose-built store like Pinecone, Milvus, or Qdrant earns its bill. If vectors are your primary workload at extreme scale, use the specialized tool. If they are one feature of an application whose source of truth is already Postgres, a second database is operational overhead you have not earned.

---

### Conclusion

An agent's memory is rows plus an embedding column. Recall them with `<=>`, remembering it returns a distance and not a similarity. Index with HNSW by default and reach for IVFFlat only when build cost dominates a static dataset. Fuse vector and keyword search with Reciprocal Rank Fusion the moment exact tokens matter. Watch the two ceilings — the 2,000-dimension index limit and the post-filter surprise — because both fail quietly. And keep the whole thing in Postgres until scale genuinely forces your hand. Do that, and your agent's memories join directly to the user, the session, and the audit rows they describe: one database, one backup, one transaction.
