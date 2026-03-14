# Interview B — GCA: Estimation Questions

Estimation (Fermi) questions are less common now but still appear in data/CE rounds. The point is never the exact answer — it's your decomposition logic.

**Rule:** State your formula out loud → make assumptions explicit → compute → sanity-check → say what you'd do to refine the estimate.

---

## The Estimation Formula Template

```
1. Define the scope (what exactly are we estimating?)
2. Choose a decomposition approach:
   - Top-down: Total market → narrow to relevant slice
   - Bottom-up: Unit × rate × time → aggregate up
3. State your assumptions explicitly ("I'll assume...")
4. Compute step by step
5. Sanity check ("This feels high/low because...")
6. Refine: "To get a better estimate, I'd look at..."
```

---

## The 10 Questions + Worked Formulas

### Q1: Estimate the number of videos watched on YouTube per day

**Decomposition (bottom-up):**
```
Daily Active Users (DAU)    = ~2B (YouTube has 2.7B MAU; assume 75% daily → ~2B)
Sessions per user per day   = ~2
Videos per session          = ~5
────────────────────────────────
Total views/day             = 2B × 2 × 5 = 20 billion views/day
```
**Assumptions to state:** DAU/MAU ratio, avg session length. Google themselves have said ~1B hours/day watched; sanity check: 20B views × avg 3 min = 1B hours. ✓

---

### Q2: Estimate Google Photos storage needed for all Pixel phones in the world

**Decomposition (top-down):**
```
Pixel phones sold (total, all time) ≈ 50M units
% still active                      ≈ 60% → 30M active devices
Photos per active device per month  ≈ 100
Avg photo size                      ≈ 4 MB (compressed HEIC)
Avg device lifetime on Photos       ≈ 3 years = 36 months
────────────────────────────────────────────────────────
Total storage = 30M × 100 photos × 4 MB × 36 months
              = 30M × 14,400 MB
              = ~432 petabytes
```
**Sanity check:** Google stores exabytes across all products; 432 PB for Pixel-only sounds reasonable.

---

### Q3: Estimate total internet bandwidth needed for a campus of 1,000 graduate students

**Decomposition (bottom-up):**
```
Students                            = 1,000
Concurrent usage ratio (peak)       = 40% → 400 concurrent users
Avg bandwidth per user (peak)       = 10 Mbps (video calls, streaming, research tools)
Overhead multiplier (shared infra)  = 1.5x
────────────────────────────────────────────────────
Peak bandwidth = 400 × 10 Mbps × 1.5 = 6,000 Mbps = 6 Gbps
```
**Refine:** Break into residential vs classroom vs lab usage patterns. Labs may spike to 40+ Gbps for ML training.

---

### Q4: How many windows are in New York City?

```
Buildings in NYC    ≈ 1M buildings
Avg floors          ≈ 4 (skewed by density; mostly low-rise outer boroughs)
Avg windows/floor   ≈ 8
────────────────────────────────
Total = 1M × 4 × 8 = 32 million windows
```
**Refine split:** Manhattan skyline adds high-rises (~70K buildings × 30 floors × 20 windows), outer boroughs are mostly 2-story homes. Blended estimate: ~30–35M windows.

---

### Q5: How many tennis balls fit in a typical car?

```
Car interior volume (sedan)  ≈ 3.5 m³ (passenger + trunk)
Tennis ball diameter          = 6.7 cm → radius = 3.35 cm
Volume per ball (sphere)      = (4/3)π r³ = ~157 cm³
Packing efficiency (random)   = ~64%
─────────────────────────────────────────────
Effective volume = 3.5 m³ × 0.64 = 2.24 m³ = 2,240,000 cm³
Number of balls  = 2,240,000 / 157 ≈ 14,300 balls
```

---

### Q6: Estimate the number of Gmail users in the US

```
US population               ≈ 335M
Internet users (85%)        ≈ 285M
Email users (95% of online) ≈ 270M
Gmail market share (US)     ≈ 53%
────────────────────────────────
Gmail users in US ≈ 145M
```

---

### Q7: Estimate total internet bandwidth needed on a typical trading day in the US market

```
Professional traders + algos ≈ 500K active connections
Retail traders online        ≈ 20M, peak concurrent 10% → 2M
Data per connection (market data feeds) ≈ 50 Mbps (institutional) / 1 Mbps (retail)
──────────────────────────────────────────
Institutional: 500K × 50 = 25,000 Gbps = 25 Tbps
Retail: 2M × 1 Mbps = 2,000 Gbps = 2 Tbps
Total ≈ 27 Tbps peak
```

---

### Q8: Estimate how much revenue Google Cloud generates per GCP free-tier user who converts to paid

*This is a CE-flavored estimation. Frame it as a sales funnel analysis.*
```
Free-tier signups per month  ≈ 500K (assumption)
Conversion rate to paid      ≈ 5% → 25K new paying customers/month
Avg first-year spend (SMB)   ≈ $5,000/year
──────────────────────────────────────────
Monthly cohort revenue year 1 = 25K × $5K = $125M ARR per monthly cohort
```
**Key point for CE interview:** Frame this as a pipeline efficiency question — which segments convert fastest? What triggers conversion?

---

### Q9: How many data centers does Google need to serve all YouTube traffic?

```
YouTube bandwidth (global peak) ≈ 15 Tbps (rough estimate from public data)
A typical hyperscale data center capacity ≈ 100–200 Gbps usable egress
Safety/redundancy multiplier    ≈ 3x
──────────────────────────────────────────────────────────────────────
Data centers ≈ (15,000 Gbps × 3) / 150 Gbps avg = ~300 locations
```
**Note:** YouTube uses edge CDN caching aggressively — the actual origin serving is much smaller.

---

### Q10: Estimate the market size for multi-cloud data management tools in 2026

```
Enterprise companies globally   ≈ 500K (revenue > $50M)
% with multi-cloud strategy     ≈ 85% → 425K companies
Avg annual spend on data mgmt tools ≈ $150K/year (conservative)
──────────────────────────────────────────────────────────────────
Total market ≈ 425K × $150K = ~$64B TAM
```
**Refine:** Segment by company size — Fortune 500 spends $2M+, mid-market $50–200K. This gives a weighted average.

---

## The Killer Closing Line for Any Estimation

After computing, always say:
> *"To refine this further, I'd want [specific data source or methodology]. The key uncertainty in my estimate is [X assumption], which could move the answer by ±[order of magnitude]."*

This shows analytical maturity — knowing what you don't know.
