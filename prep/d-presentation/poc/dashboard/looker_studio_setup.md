# Looker Studio Dashboard Setup Guide
**For Interview D Presentation Demo — Cross-Brand Sales Dashboard**

---

## Overview

This guide walks you through connecting Google Looker Studio to the BigQuery `mart.customer_360` table and building the live cross-brand sales dashboard for your presentation demo.

**Estimated setup time:** 30 minutes  
**Looker Studio URL:** https://lookerstudio.google.com  
**Cost:** Free (Looker Studio is free; BigQuery query costs apply for large datasets)

---

## Step 1: Create a New Looker Studio Report

1. Go to https://lookerstudio.google.com
2. Click **"+ Create"** → **"Report"**
3. When prompted to add a data source, click **"Add data"**
4. Select **"BigQuery"** from the connector list
5. Sign in with your Google account (the same one that owns the GCP project)

---

## Step 2: Connect to BigQuery — customer_360

1. In the BigQuery connector panel:
   - **Project:** Select `YOUR_PROJECT_ID`
   - **Dataset:** `mart`
   - **Table:** `customer_360`
2. Click **"Add"** → **"Add to Report"**
3. You now have a data source connected to the unified mart table

> **Tip for demo:** Pre-connect and pre-load this data source the day before.
> Do NOT live-connect during the interview. The connection may take 10–30 seconds.

---

## Step 3: Configure Data Field Types

In the **"Edit data source"** panel, verify or set these field types:

| Field | Type | Notes |
|---|---|---|
| `customer_key` | Text | Unique customer identifier |
| `brand_id` | Text | Dimension — use for color coding |
| `total_orders` | Number | Metric |
| `total_spend_usd` | Currency (USD) | Metric |
| `first_order_date` | Date | Filter dimension |
| `last_order_date` | Date | Time axis |
| `cross_brand_flag` | Boolean | KEY KPI for demo |
| `total_brands_shopped` | Number | |

Click **"Done"** to save field configuration.

---

## Step 4: Build Chart 1 — Cross-Brand Revenue by Brand (Bar Chart)

1. Click **"Add a chart"** → **"Bar chart"**
2. Dimension: `brand_id`
3. Metric: `total_spend_usd` (set to **SUM**)
4. Sort: `total_spend_usd DESC`
5. Style: Color-code bars by brand (Brand A = blue, Brand B = green, Brand C = orange)
6. Add chart title: **"Total Revenue by Brand (Portfolio View)"**

**Presentation talking point:**
> "This chart gives the CIO a portfolio view of revenue across all three brands —
> something that was previously impossible because each brand had a separate analytics stack."

---

## Step 5: Build Chart 2 — Cross-Brand Customers (Scorecard)

1. Click **"Add a chart"** → **"Scorecard"**
2. Metric: `customer_key` → set aggregation to **COUNT DISTINCT**
3. Add a **"Filter"** to this chart: `cross_brand_flag = true`
4. Label: **"Cross-Brand Customers"**
5. Add comparison: a second scorecard showing COUNT DISTINCT of all customers
6. Style: Large font, prominent position (this is the headline KPI)

**Presentation talking point:**
> "We currently have [X] customers who have shopped at more than one of our brands.
> Today these customers are invisible — no brand knows the other serves them.
> This number represents our best personalization and cross-sell opportunity."

---

## Step 6: Build Chart 3 — Revenue Trend Over Time (Time Series)

1. Click **"Add a chart"** → **"Time series chart"**
2. Dimension: `last_order_date` (set to **Week** granularity)
3. Breakdown dimension: `brand_id`
4. Metric: `total_spend_usd` (SUM)
5. Style: Line chart, three lines (one per brand), no fill
6. Add a **Date range control** widget (filters all charts on the page)

**Presentation talking point:**
> "The weekly revenue trend by brand — this updates every 15 minutes from the streaming pipeline.
> For Brand B, you'll notice a dip on weekends, which is expected for their brick-and-mortar stores.
> Brand C's Shopify traffic shows the opposite pattern."

---

## Step 7: Build Chart 4 — Customer Spend Distribution (Histogram)

1. Click **"Add a chart"** → **"Bar chart"** (horizontal)
2. Dimension: Create a calculated field:
   - Name: `spend_bucket`
   - Formula: `CASE WHEN total_spend_usd < 100 THEN "$0–$100" WHEN total_spend_usd < 500 THEN "$100–$500" WHEN total_spend_usd < 1000 THEN "$500–$1K" ELSE "$1K+" END`
3. Metric: `customer_key` → COUNT DISTINCT
4. Sort: Custom (ascending bucket order)
5. Title: **"Customer Spend Distribution"**

---

## Step 8: Add a Cross-Brand Flag Filter

1. Click **"Add a control"** → **"Drop-down list"**
2. Control field: `cross_brand_flag`
3. Default: **(All)**
4. Label: **"Show cross-brand customers only?"**

This allows William to interactively filter to only cross-brand customers during Q&A.

---

## Step 9: Dashboard Layout (For Presentation)

Arrange the 4 charts in this 2×2 grid layout:

```
┌─────────────────────┬─────────────────────┐
│  Scorecard          │  Bar: Revenue by    │
│  Cross-Brand        │  Brand              │
│  Customers          │                     │
├─────────────────────┼─────────────────────┤
│  Time Series:       │  Horizontal Bar:    │
│  Weekly Revenue     │  Spend Distribution │
│  by Brand           │                     │
└─────────────────────┴─────────────────────┘
```

Add a **title banner** at the top: **"Retail Portfolio Analytics — Cross-Brand Customer 360"**

---

## Step 10: Pre-Demo Checklist

Run through this the morning of Interview D:

- [ ] Open Looker Studio report and verify it loads without errors
- [ ] Confirm all 4 charts show data (≥1,000 rows from ingest_batch.py)
- [ ] Test the cross-brand filter — toggle to "true" and back
- [ ] Check the scorecard shows a number > 0 for cross-brand customers
- [ ] Verify the time series shows multiple weeks of data
- [ ] Test screen sharing in Google Meet — Looker Studio should be visible, not blurry
- [ ] **Do NOT refresh data or re-run queries during the interview** — pre-load ahead of time
- [ ] Have the Looker Studio URL bookmarked in a dedicated browser tab

---

## Live Demo Script (2 minutes, during Slide 8)

1. **[30 sec]** Show the scorecard: "We identified X cross-brand customers — invisible before this platform."
2. **[30 sec]** Show the brand revenue bar chart: "For the first time, we see consolidated portfolio revenue — $X total, with Brand A the largest contributor."
3. **[30 sec]** Toggle the cross-brand filter: "If I filter to cross-brand customers only, I can see their spend distribution. These are our highest-LTV customers and the primary target for personalization."
4. **[30 sec]** Show the time series: "This data updates every 15 minutes from the Brand A streaming pipeline we just saw."

---

## Troubleshooting

| Issue | Solution |
|---|---|
| "No data" on charts | Run `ingest_batch.py` first, then `transform_canonical.sql` |
| Looker Studio can't find the BQ dataset | Check IAM: your email needs `BigQuery Data Viewer` on the project |
| Charts load slowly | Add a date filter (last 90 days) to reduce scan size |
| cross_brand_flag shows as string not boolean | Edit data source → change field type to "Boolean" |
| Screen share looks blurry | Share the specific browser tab, not the full screen |
