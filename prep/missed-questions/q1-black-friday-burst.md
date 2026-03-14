# Q1 Study Material — Black Friday DB Burst (System Design)
**Study Days: Day 1 (read) + Day 2 (practice) · 4h total**

---

## The Question (verbatim)
> "For an eCommerce company, there is a Black Friday or Double Eleven. If there is a burst of requests, how should you handle that on the DB and the query? Think in System Design view."

## What the Interviewer Wants
They want **layered thinking** — not one trick, but a cohesive architecture where each layer absorbs a slice of the burst. Single-layer answers (e.g. "add an index") get partial credit. Full-stack answers win.

---

## The Core Mental Model (Draw This First)

```
 ┌─────────────────────────────────────────────────────────┐
 │                      INTERNET                           │
 └───────────────────────┬─────────────────────────────────┘
                         │ millions of users
           ┌─────────────▼─────────────┐
           │     CDN / Load Balancer   │  ← Layer 1: absorb static reads
           └─────────────┬─────────────┘
                         │
           ┌─────────────▼─────────────┐
           │  API Gateway + Rate Limiter│  ← Layer 2: throttle and protect
           └─────────────┬─────────────┘
                         │
           ┌─────────────▼─────────────┐
           │  App Tier (stateless pods) │  ← Layer 3: horizontal autoscale
           └──────┬──────────────┬──────┘
                  │              │
     ┌────────────▼──┐    ┌──────▼──────────┐
     │  Cache (Redis) │    │  Message Queue  │  ← Layer 4: reads from cache
     │  Memorystore   │    │  (Pub/Sub/SQS)  │    Layer 5: writes to queue
     └────────────┬──┘    └──────┬──────────┘
                  │              │ (async drain)
           ┌──────▼──────────────▼──────┐
           │  Primary DB (OLTP)         │  ← Layer 6: protected, writes only
           │  + Read Replicas (SELECTs) │
           └─────────────┬──────────────┘
                         │ (CDC / replication)
           ┌─────────────▼─────────────┐
           │  BigQuery / DWH (OLAP)    │  ← Layer 7: analytics isolated
           │  + BI Engine / Looker     │
           └───────────────────────────┘
```

**Rule of thumb:** READS go left (CDN → Cache → Read Replica). WRITES go right (Queue → async worker → Primary DB). Analytics never touches OLTP during the event.

---

## Layer-by-Layer Deep Dive

### Layer 1 — CDN (Client / Edge)
**Problem it solves:** Product catalog pages, images, and prices are read millions of times. Each hit should not reach the DB.

**Solution:**
- Cache static assets (images, JS, CSS) at CDN edge → Cloud CDN or CloudFront
- Cache API responses for product catalog: e.g., `GET /products/12345` → cache for 5 min at CDN
- **Virtual waiting room**: Use a queuing service (Queue-it or custom) to drip users into the site at a controlled rate. Users see a waiting page; the system doesn't see a sudden vertical spike.

**Trade-off to mention:** CDN caching means product price/inventory shown to user may be 5 min stale. Acceptable for catalog. NOT acceptable for final checkout (always bypass CDN for checkout flow).

---

### Layer 2 — API Gateway + Rate Limiting
**Problem it solves:** Even with CDN, API endpoints get hammered. Need to prevent any single client or bot from consuming all capacity.

**Solutions:**
| Mechanism | What it does |
|---|---|
| **Token bucket** | Each user/IP gets N tokens/sec; excess requests rejected with HTTP 429 |
| **Leaky bucket** | Requests queued and processed at fixed rate |
| **Circuit breaker** | If downstream latency > 500ms, return HTTP 503 immediately — stops pile-up |
| **Priority queues** | Checkout API gets higher priority than browsing API |

**GCP:** Apigee API Management — policy-based rate limiting, quotas per API key
**AWS:** API Gateway throttling, AWS WAF rate rules

**Circuit breaker pattern** (important to explain):
```
Normal state →  request → backend → response
Degraded:       backend p99 latency > threshold
                → circuit opens → return 503 in <10ms (no waiting for backend)
                → after 30s, probe one request → if healthy, circuit closes
```
This prevents a slow DB from taking down the entire app.

---

### Layer 3 — Application Tier (Autoscaling)
**Problem it solves:** More traffic means more app servers needed. Manual scaling is too slow.

**Solutions:**
- **Stateless pods**: No session state stored in the app process. Session data in Redis (Memorystore). This means any pod can handle any request — horizontal scaling works perfectly.
- **Horizontal autoscaling**: GKE HPA (Horizontal Pod Autoscaler) scales pod count on CPU/request rate metrics. Cloud Run autoscales to zero (great for cost management post-event).
- **Pre-scale for known events**: Black Friday is predictable — manually scale up to min=100 pods at midnight BF eve. Don't wait for autoscaler to react.
- **Connection pool discipline**: Each pod gets a fixed connection pool (e.g., PgBouncer with 10 server connections). Even if 200 pods × 10 = 2000 app connections, PgBouncer multiplexes them into 100 actual DB connections.

---

### Layer 4 — Cache (Read Burst Absorption)
**Problem it solves:** 90% of Black Friday traffic is reads (browsing, product detail). Without a cache, every read hits the DB.

**Pattern: Cache-Aside (Lazy Loading)**
```
1. App receives GET /product/12345
2. Check Redis key "product:12345"
3a. CACHE HIT  → return cached value (< 1ms)
3b. CACHE MISS → query DB → write to Redis with TTL → return value
```

**TTL Strategy — Critical for Black Friday:**
| Data | TTL | Reason |
|---|---|---|
| Product name, description, images | 60 min | Rarely changes |
| Product price | 5 min | May change during flash sales |
| Inventory count | 30 sec | Must be near-fresh to avoid oversell |
| User cart | 30 min session | Per-user, can't be shared |
| Final checkout availability | 0 (bypass cache) | Must be real-time |

**Cache Stampede Prevention:**
When a popular product's cache key expires simultaneously for 10,000 users → everyone hits DB at once.
Solutions:
1. **Mutex lock**: first miss acquires lock, fetches DB, writes cache. Others wait.
2. **Probabilistic early expiry**: re-fetch the key slightly before it expires (before the stampede).
3. **Staggered TTLs**: add `random.randint(0, 60)` seconds to TTL so keys don't expire in sync.

**GCP:** Cloud Memorystore (managed Redis). **AWS:** ElastiCache.

---

### Layer 5 — Message Queue (Write Burst Decoupling)
**This is the most important concept for the write path. Emphasize this.**

**Problem it solves:** An order placement is a write. If 100,000 users click "Buy" simultaneously, and each write goes directly to the DB, the DB connection pool saturates and the site crashes.

**Solution — Queue the writes:**
```
User → POST /order
         ↓
     API validates order (fast, no DB needed)
         ↓
     Publish to Pub/Sub / SQS (< 5ms)
         ↓
     Return "Order Placed!" to user (HTTP 202 Accepted)

                [Pub/Sub topic]
                     ↓ (async, controlled drain rate)
              Worker pool (auto-scaled, separate from web tier)
                     ↓
              DB write at sustainable rate (e.g., 500 writes/sec)
```

**User experience:** User sees confirmation instantly. Order processing happens in background. This is exactly how Amazon, Shopee, and JD.com handle 11.11 spikes.

**Dead Letter Queue (DLQ):** If a write fails after 3 retries (e.g., DB constraint violation) → route to DLQ → alert → manual review. Never silently drop orders.

**Idempotency key:** Each order message has a unique `idempotency_key`. If the worker processes the same message twice (at-least-once delivery), the DB insert is a no-op on duplicate key. Prevents double-orders.

---

### Layer 6 — Database (OLTP Protection)
**Problem it solves:** Even with caching and queuing, the DB still needs to handle writes and cache-miss reads. Need to maximise DB throughput and resilience.

**A. Read Replicas**
- Primary: ALL writes (inserts, updates)
- Read replicas (1–3): ALL SELECT queries
- Application routing: use read replica endpoint for GET requests; writer endpoint for POST/PUT
- GCP: Cloud SQL read replicas, AlloyDB read pool (PostgreSQL-compatible, up to 16 read nodes)

**B. Connection Pooling**
- Problem: PostgreSQL has connection overhead (~5MB per connection). 500 app threads × DB connection = 500 × 5MB = 2.5GB just for connection metadata.
- Solution: PgBouncer (Postgres) or ProxySQL (MySQL) sits between app and DB.
  ```
  200 app pods × 10 pool connections = 2000 app-side connections
  PgBouncer multiplexes → 50 actual PostgreSQL server connections
  ```
- GCP managed: Cloud SQL with built-in connection limit management. Use Cloud SQL Auth Proxy.

**C. Query Optimization (pre-event checklist)**
```sql
-- Run EXPLAIN ANALYZE on every Black Friday query before the event
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM orders WHERE user_id = 12345 AND status = 'pending';

-- Ensure these indexes exist:
CREATE INDEX CONCURRENTLY idx_orders_user_status ON orders(user_id, status);
CREATE INDEX CONCURRENTLY idx_orders_created     ON orders(created_at DESC);

-- Avoid:
SELECT * FROM orders                        -- never SELECT *
SELECT COUNT(*) FROM orders WHERE ...       -- expensive full counts; use approximations
UPDATE orders SET ... WHERE status IN (...)  -- large WHERE IN during peak hours
```

**D. Pre-event warmup**
- Send synthetic read traffic to read replicas 1h before event to warm the buffer pool (OS page cache). Cold reads from disk are 100× slower than cached reads.
- Pre-generate materialized views (`REFRESH MATERIALIZED VIEW CONCURRENTLY`) for top-N products, category aggregations.

**E. When to use Cloud Spanner instead of Cloud SQL?**
- Cloud SQL is sufficient for single-region up to ~10,000 writes/sec with replicas
- Spanner: global consistency, unlimited horizontal scaling, 99.999% SLA
- Cost: Spanner is ~5× more expensive — only use when multinational, multi-region, or > millions of TPS
- Rule: "If Black Friday breaks Cloud SQL, move to Spanner. Until then, replicas + PgBouncer is the right cost-optimized answer."

---

### Layer 7 — Analytics / OLAP (Isolation)
**Critical rule: NEVER run analytics queries on the OLTP database during a Black Friday event.**

**Why:** A poorly optimized analytics query can lock rows or saturate I/O, causing the checkout flow to stall.

**Solution:**
- Stream OLTP changes to BigQuery via **Cloud Datastream** (CDC) with ~1-5 min lag
- All dashboards, reports, and analyst queries run against BigQuery (serverless, isolated)
- BigQuery Flex Slots: purchase on-demand capacity pre-event for guaranteed query performance
- BI Engine: in-memory acceleration for Looker Studio dashboards — dashboard queries never hit BQ slots

---

## GCP vs AWS Service Mapping

| Problem | GCP Service | AWS Equivalent |
|---|---|---|
| CDN / edge caching | Cloud CDN | CloudFront |
| API rate limiting | Apigee | API Gateway + WAF |
| App autoscaling | GKE HPA / Cloud Run | EKS HPA / ECS Fargate |
| Read caching | Memorystore (Redis) | ElastiCache |
| Write queue | Pub/Sub | SQS / Kinesis |
| Connection pooling | PgBouncer + Cloud SQL Auth Proxy | RDS Proxy |
| OLTP DB | Cloud SQL / AlloyDB | Aurora |
| Analytics isolation | BigQuery + Datastream | Redshift + DMS |
| Load testing | (k6 / Locust on GCE) | AWS Distributed Load Testing |

---

## Pre-Event Operational Playbook

Run this checklist 1 week before Black Friday:

```
□ Load test at 2× expected peak (k6 or Locust)
□ Verify HPA triggers and scales to target pod count
□ Confirm all BF critical queries are indexed (EXPLAIN ANALYZE)
□ Refresh materialized views and confirm they're warm
□ Pre-scale app pods to minimum=50 (don't wait for autoscaler)
□ Purchase BigQuery Flex Slots for the event window
□ Verify DLQ alerts are firing correctly
□ Set DB connection pool max < 80% of DB connection limit
□ Confirm CDN cache rules are in place for catalog endpoints
□ Disable non-critical background jobs (analytics reruns, heavy batch ETL)
□ Set up 24h on-call rotation with runbook
```

---

## Answer Skeleton (Memorize This)
Use this structure in the interview. Takes 6–8 minutes to deliver fully.

```
"I'd approach this in layers, starting from the edge and working inward.

1. EDGE: CDN caches product catalog reads — keeps most traffic off the DB entirely.
   Virtual waiting room controls admission rate at the front door.

2. API GATEWAY: Token-bucket rate limiting per user. Circuit breaker prevents
   a slow DB from cascading into a total outage — fail fast with HTTP 503.

3. APP TIER: Stateless pods, horizontal autoscaling. Pre-scale before the event
   since Black Friday timing is known.

4. READS → CACHE: Redis (Memorystore) with TTL strategy.
   Inventory: 30s TTL. Catalog: 60min TTL. Checkout: bypass cache entirely.
   Stampede prevention via staggered TTLs.

5. WRITES → QUEUE: Order writes go to Pub/Sub first — user gets instant ACK,
   async workers drain the queue at a rate the DB can handle.
   DLQ for failed orders. Idempotency key prevents double-processing.

6. DB: Read replicas for all SELECTs. PgBouncer for connection pooling.
   Pre-warm buffer cache. No analytics queries on primary during the event.

7. ANALYTICS: Separate BigQuery layer via CDC/Datastream.
   Flex Slots pre-purchased. Dashboards via BI Engine (no BQ slot contention).

Trade-offs I'd highlight: queue adds latency to order confirmation vs. direct write.
Acceptable trade-off — users prefer fast UI to synchronous confirmation.
Cache TTLs mean inventory counts may be 30s stale — I'd handle final availability
check at checkout without cache."
```

---

## Practice Questions (Do These Out Loud, 8 Minutes Each)

1. **"How would you handle 10,000 users clicking 'Buy' on the last item simultaneously?"**
   Hint: optimistic locking + idempotency + queue. What happens to the 9,999 who don't get it?

2. **"Your read replica falls 5 minutes behind primary during peak load. What do you do?"**
   Hint: stale reads are acceptable for catalog; what about inventory? Where do you draw the line?

3. **"At what point would you migrate from Cloud SQL to Cloud Spanner for this scenario?"**
   Hint: global users, > millions TPS, strong consistency across regions.

4. **"Your PgBouncer connection pool is 95% saturated. What are your options?"**
   Hint: increase pool size (hits DB connection limit), add another PgBouncer instance, reduce query execution time.

5. **"How do you test the system handles Black Friday load before the event?"**
   Hint: load testing (k6/Locust), chaos engineering (kill a replica), game day rehearsal.

---

## Flash Cards (Review Night Before Interview)

| Question | Answer |
|---|---|
| What pattern absorbs write spikes? | Message queue — writes go to Pub/Sub, async workers drain at DB-safe rate |
| What pattern absorbs read spikes? | Cache-aside with Redis — CDN → Redis → DB fallback |
| What prevents DB connection storm? | PgBouncer / connection pooling — N app connections × M pool = few DB connections |
| What prevents cache stampede? | Staggered TTL + jitter, mutex lock, probabilistic early expiry |
| What prevents cascade failure? | Circuit breaker — fail fast with 503, don't wait for slow backend |
| What's the analytics isolation strategy? | CDC (Datastream) → BigQuery — never run OLAP queries on OLTP during events |
| What's the checkout cache rule? | Bypass cache entirely for final checkout — must read live inventory |
| When to use Spanner over Cloud SQL? | Multi-region, > millions TPS, global strong consistency needed |
