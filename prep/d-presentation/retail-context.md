# Retail Industry Context — Making the 3-Brand Scenario Real

**For:** Interview D Presentation + GCA Hypothetical Q7 ("design an analytics platform for a retail merger")
**Purpose:** When you describe "3 brands with different cloud and on-prem data platforms," you need to make it credible and specific — not generic. Use this to pre-build the realistic scenario.

---

## The Scenario Made Concrete

The prompt is deliberately generic. The more specific and realistic you make it, the more credible you sound. Here's a realistic set of brand archetypes:

| Brand | Type | Scale | Existing Data Stack | Cloud Platform |
|---|---|---|---|--|
| **Brand A** | Mid-market specialty retail, digitally mature | $800M revenue, 300 stores + eComm | Redshift + Firehose, Segment CDP, Salesforce Commerce Cloud | AWS |
| **Brand B** | Traditional department store, legacy stack | $600M revenue, 500 stores, thin eComm | Oracle Retail, on-prem Oracle DB, SAP BI (BusinessObjects) | On-premise (minimal cloud) |
| **Brand C** | Direct-to-consumer, born-digital brand | $200M revenue, pure eComm, 20 pop-up stores | Databricks on Azure + Azure Synapse, Shopify | Azure |

**Total portfolio:** $1.6B combined revenue, 3 very different technical profiles.

**Why this is realistic:** Retail M&A in 2024–2026 has been dominated by private equity roll-ups of omnichannel + digital brands. This exact pattern (AWS-native + Oracle on-prem + Azure/DTC) appears routinely in real mergers.

---

## The Source Systems Per Brand (Know These for Credibility)

### Brand A (AWS / Digitally Mature)
- **POS system:** Lightspeed Retail → real-time transactions via Kinesis → Redshift
- **eCommerce:** Salesforce Commerce Cloud → order/customer data via Segment CDP
- **Customer loyalty:** Custom internal → MySQL, customer IDs are email-based
- **Existing analytics:** Redshift + Tableau dashboards per department
- **Challenge:** Segment's unified customer profile doesn't translate to a canonical key across brands; Redshift cluster sizing is a migration risk

### Brand B (On-Prem / Legacy)
- **POS system:** Oracle Retail POS → Oracle DB (on-prem) → nightly batch export to SAP BI
- **eCommerce:** Minimal — a third-party hosted site with 48-hour batch order feeds into Oracle
- **Customer data:** Oracle customer table with internal customer numbers; NO cross-brand identity
- **Existing analytics:** SAP BusinessObjects reports, weekly batch refresh, exported to Excel
- **Migration path:** Google Datastream CDC → Oracle → Pub/Sub in Phase 2; nightly export to GCS in Phase 1

### Brand C (Azure / DTC)
- **eCommerce:** Shopify → Azure Event Hubs → Azure Synapse Analytics
- **No physical stores yet:** POS data = pop-up store terminals → Shopify
- **Customer data:** Email-first identity (Klaviyo for email marketing); customer IDs are Shopify customer IDs
- **Existing analytics:** Databricks Delta Lake on Azure Synapse + Power BI
- **Migration path:** Azure Data Factory → GCS batch export (Phase 1); Pub/Sub via event bridge (Phase 2)

---

## Common Retail Source System Vocabulary (Know These Names)

**Point of Sale (POS) Systems:**
- Lightspeed, Square for Retail, Oracle MICROS, Shopify POS, NCR Counterpoint
- Generate: transaction records, SKU-level sales, store-level inventory, cashier-level events

**eCommerce Platforms:**
- Salesforce Commerce Cloud (formerly Demandware) — mid-to-enterprise
- Shopify / Shopify Plus — DTC and SMB
- SAP Commerce Cloud — large enterprises, especially B2B hybrids
- Magento (Adobe Commerce) — mid-market, highly customizable

**ERP / Inventory:**
- Oracle Retail — legacy department stores
- SAP S/4HANA — enterprise backbone for inventory, financials, supply chain
- Manhattan Associates — supply chain, warehouse management (WMS)

**Customer Data / CDP:**
- Salesforce Data Cloud (formerly CDP)
- Segment (Twilio) — event streaming + identity resolution
- Adobe Experience Platform
- mParticle

**BI / Reporting:**
- SAP BusinessObjects — legacy enterprise BI
- Tableau, Power BI, Looker — modern self-serve

---

## The Identity Resolution Problem — Made Concrete

This is the HARDEST problem in the merger and your key technical differentiator. Make it concrete:

**Brand A customer:** Email = `john.doe@gmail.com`, CustomerID = `SEG-8837792` (Segment ID)
**Brand B customer:** Email = `johndoe@gmail.com`, CustomerID = `CUST-00043892` (Oracle number)
**Brand C customer:** Email = `j.doe@gmail.com`, ShopifyID = `gid://shopify/Customer/9182736455`

**The problem:** These are likely the same person — but:
1. Email normalization required: `john.doe` vs `johndoe` vs `j.doe`
2. No shared identifier exists across systems
3. Brand B doesn't have email as a primary key — it's a secondary field that 30% of customers haven't provided

**Your deterministic + probabilistic solution:**
- **Deterministic (definitive):** `SHA-256(brand_id + source_system_id)` = canonical `customer_key` — every record gets a unique, stable key regardless of cross-brand match
- **Probabilistic (cross-brand linking):** normalized email hash + normalized phone hash → Entity resolution → `has_cross_brand_match` flag on `customer_360`
- **Email normalization:** remove dots from Gmail local part, lowercase, strip aliases (e.g., `john.doe+brand = john.doe`) to improve match rate

**Phase 1 coverage estimate:**
- Cross-brand matches via email: ~15–25% of customers (realistic for post-merger with limited data sharing)
- Cross-brand matches via phone: adds another 5–10%
- Unmatched (single-brand customers): ~65–75% — still useful for single-brand analytics, just not cross-brand recommendation

---

## The POS Streaming Problem — Made Concrete

**What happens in a physical store every minute:**
- Scanner: customer loyalty card swipe → event
- Scanner: each SKU scanned → line item event  
- Register: tender event (payment type, amount)
- Scanner: receipt printed → transaction close event

**Volume estimate for 1,000 stores (Brands A + B combined):**
- 3 peak transactions/minute/store × 1,000 stores = 3,000 events/minute
- Black Friday peak: 5–10x spike = 15,000–30,000 events/minute
- Pub/Sub handles this without sharding. State it boldly.

**What the streaming pipeline does with these events:**
1. Pub/Sub topic per brand → schema validation (Avro or Proto schema registry)
2. Dataflow job: parse → enrich (join to product catalog for category, margin) → apply window aggregations → write to BigQuery `streaming_orders` table
3. BigQuery `streaming_orders` table: `INSERT` streaming via Dataflow Storage Write API (exactly-once, high throughput)
4. Looker Studio real-time dashboard: live store sales vs prior year, by brand, by region

---

## Why "Off-the-Shelf" Fails — The Technical Case

Ready to say in Section 2 of your presentation:

**Tool:** Any single cloud warehouse (Snowflake, Redshift, Synapse)
**Why it fails:**
1. It's a storage layer — it doesn't solve identity resolution, schema transformation, or streaming ingestion
2. You still need the ingestion and processing layer (Fivetran? doesn't do identity resolution. Airbyte? Same issue.)

**Tool:** An off-the-shelf CDP (Salesforce Data Cloud, mParticle)
**Why it fails for this scenario:**
1. CDPs solve identity within one brand's ecosystem, not cross-brand post-merger identity resolution at the schema level
2. CDPs don't generate the AI training features or handle the ML pipeline — they're activation/marketing tools, not analytics platforms
3. A CDP layered over 3 different source systems without a canonical warehouse still has three siloed analytics instances underneath

**Tool:** A single migration tool (Fivetran + cloud warehouse)
**Why it fails:**
1. Fivetran moves data, it doesn't resolve identity, standardize schemas, or define semantic meaning
2. You'd land 3 brands' raw data in one warehouse — still 3 separate schema namespaces, no customer_360, no cross-brand analytics
3. The 12-month AI activation mandate requires ML feature pipelines, which no lift-and-shift migration tool provides

**Your counter:** "The specialist engagement is required precisely because the data engineering problem and the business intelligence problem and the AI activation problem are all coupled. No single SaaS tool covers all three."

---

## The 1-Year AI Activation — What's Realistic

This is a board mandate. William will test if you're being realistic or overselling.

**Month 1–2 (Phase 0: Foundation)**
- GCP project structure, networking, IAM
- Data discovery per brand (schema mapping, volume estimates, PII inventory)
- Brand A migration pilot: GCS landing + BigQuery canonical for Brand A only

**Month 3–4 (Phase 1a: Core Platform)**
- All 3 brands in GCS raw zone
- BigQuery canonical layer live: canonical Customer, Order, Product tables
- Identity resolution running (deterministic) — cross-brand customer_360 view
- First Looker Studio portfolio dashboard live

**Month 5–6 (Phase 1b: Streaming + Governance)**
- POS streaming pipeline live for Brand A (Pub/Sub → Dataflow → BQ)
- Dataplex/BigQuery universal catalog governance: PII tagged, policy tags enforced
- Data quality scans running nightly

**Month 7–9 (Phase 2: AI Activation)**
- Demand forecasting model (ARIMA_PLUS or TimesFM) trained on unified order history
- Cross-brand product recommendation model (BigQuery ML or Vertex AI)
- A/B test framework for recommendation engine

**Month 10–12 (Phase 3: Monetization + Optimization)**
- Recommendation engine in production for Brand C digital (highest digital revenue)
- Brand analytics self-service via Looker + Gemini in BigQuery for natural language querying
- Data clean room POC for CPG partner collaboration (Google ADH)
- Phase 3 scope and cost model for board Q4 presentation

**Board-facing success metrics at 12 months:**
- All 3 brands reporting from single platform (yes/no)
- Cross-brand customer_360 coverage: ≥25% of customers matched
- Recommendation engine lift: proof of concept with A/B test data (projected $5M+ annual impact)
- Reporting latency: from 7 days → same day for portfolio metrics
- Cost: GCP platform cost vs legacy stack + analyst time (target: cost-neutral to positive)

---

## Competitor Awareness: Retail Data Platform Alternatives

William or Gene may challenge: "Why wouldn't the customer just use [X]?"

**Databricks Lakehouse:**
> "Databricks is an excellent choice if the data team is Python-native and wants maximum ML flexibility. For this scenario, the CEO mandate is 'AI activation,' which includes business analysts, not just data scientists. BigQuery's SQL-native approach + Gemini natural language interface means the brand GMs can self-serve from day one. If the team was 10 ML engineers with no business analyst users, I'd reconsider — but for this mixed audience, BigQuery's accessibility is the differentiator."

**Snowflake:**
> "Snowflake is a strong warehouse option. The key constraint for this migration is that we don't know final data volumes until we're 6 months in — Brand B's Oracle export sizes are unknown until we profile them. BigQuery's serverless model means we never pick the wrong cluster size. Also, BigQuery ML and TimesFM keep ML training co-located with the data, eliminating movement. If the customer has existing Snowflake contracts, we'd evaluate the migration cost vs benefit — it's not always worth it."

**Azure Synapse:**
> "Brand C is already on Azure Synapse + Databricks. The question is whether to consolidate to GCP or federate. Given the CIO's mandate is a 1-year plan with board accountability, I'd recommend a phased consolidation to a single canonical BigQuery layer — Brand C's team migrates their Spark workloads to Dataproc or runs against BQ metastore via Iceberg. The governance and reporting story is much cleaner with a single platform."
