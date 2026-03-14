# Q2 Study Material — PII Discovery Without Patterns (GCP Cloud DLP)
**Study Day: Day 3 · 2h total**

---

## The Question (verbatim)
> "How do you identify PII in the DB if there is no pattern? Any GCP way to fix that?"

## What the Interviewer Wants
- Awareness that regex alone fails for unstructured / context-dependent PII
- Knowledge of **Cloud DLP** — Google's native answer
- A complete pipeline: discover → classify → protect → enforce access
- Knowing the difference between structured PII (credit card) and unstructured PII (free text notes)

---

## Why "No Pattern" Is the Hard Case

| PII Type | Has Pattern? | Regex? | DLP Needed? |
|---|---|---|---|
| Credit card (4242-4242-4242-4242) | ✅ Yes | ✅ Yes | Optional |
| SSN (123-45-6789) | ✅ Yes | ✅ Yes | Optional |
| Email (user@domain.com) | ✅ Yes | ✅ Yes | Optional |
| Person name ("John Smith") | ❌ No | ❌ No | **Required** |
| Address ("123 Maple St, Toronto") | ❌ Partial | ❌ Unreliable | **Required** |
| Free-text notes ("Call patient re: diabetes") | ❌ No | ❌ No | **Required** |
| Internal IDs with sensitive context | ❌ Context-based | ❌ No | **Required** |

**The core insight:** Cloud DLP uses **ML-based contextual models** — it understands the *meaning* of surrounding text, not just character patterns.

---

## What is Cloud DLP?

**Full name:** Cloud Data Loss Prevention API (Cloud DLP)  
**What it does:** Inspects text, structured data (BigQuery/GCS/Datastore), images, and binary content for 150+ built-in PII types (called **infoTypes**) using ML.  
**Key differentiator vs. regex:** Even if PII has no consistent pattern, DLP understands context.  
Example: `"Patient John was diagnosed on March 3rd"` → DLP identifies `John` as `PERSON_NAME` even though there's no pattern to match.

---

## The Three Scenarios

### Scenario A: Structured Data (BigQuery table with known columns)
Use DLP **Inspection Job** on BigQuery — scans column by column, reports which columns contain which infoTypes.

### Scenario B: Semi-structured data (JSON/CSV in GCS)
Use DLP Inspection Job on Cloud Storage — scans files, identifies PII within field values.

### Scenario C: Unstructured free text (comment fields, notes, chat logs)
Use DLP `content.inspect` API inline in your pipeline — send text to DLP, receive findings in real time.

---

## Implementation — Step by Step

### Step 1: Single-table DLP Scan (quick POC)

```python
from google.cloud import dlp_v2

dlp = dlp_v2.DlpServiceClient()
PROJECT_ID = "your-project-id"

# ─── What to look for ───────────────────────────────────────
inspect_config = dlp_v2.InspectConfig(
    info_types=[
        # Patterned PII — DLP still catches these better than raw regex
        {"name": "EMAIL_ADDRESS"},
        {"name": "PHONE_NUMBER"},
        {"name": "CREDIT_CARD_NUMBER"},
        {"name": "US_SOCIAL_SECURITY_NUMBER"},
        {"name": "PASSPORT"},
        {"name": "IBAN_CODE"},
        # No-pattern PII — requires ML context
        {"name": "PERSON_NAME"},
        {"name": "STREET_ADDRESS"},
        {"name": "DATE_OF_BIRTH"},
        {"name": "AGE"},
        # Medical
        {"name": "MEDICAL_RECORD_NUMBER"},
        {"name": "MEDICAL_TERM"},
        # IP / device
        {"name": "IP_ADDRESS"},
        {"name": "MAC_ADDRESS"},
    ],
    # POSSIBLE catches more (more false positives)
    # LIKELY is the sweet spot for BigQuery column scanning
    min_likelihood=dlp_v2.Likelihood.LIKELY,
    include_quote=True,          # show the actual value matched (for auditing)
    limits=dlp_v2.InspectConfig.FindingLimits(max_findings_per_item=10),
)

# ─── Where to look ───────────────────────────────────────────
storage_config = dlp_v2.StorageConfig(
    big_query_options=dlp_v2.BigQueryOptions(
        table_reference=dlp_v2.BigQueryTable(
            project_id=PROJECT_ID,
            dataset_id="raw_brand_a",
            table_id="orders",
        ),
        rows_limit=50_000,           # sample; set to 0 for full scan
        sample_method=dlp_v2.BigQueryOptions.SampleMethod.RANDOM_START,
    )
)

# ─── Where to save findings ──────────────────────────────────
save_findings_action = dlp_v2.Action(
    save_findings=dlp_v2.Action.SaveFindings(
        output_config=dlp_v2.OutputStorageConfig(
            table=dlp_v2.BigQueryTable(
                project_id=PROJECT_ID,
                dataset_id="security",
                table_id="dlp_findings",   # findings land here as BQ rows
            )
        )
    )
)

# ─── Create async DLP job ────────────────────────────────────
job = dlp.create_dlp_job(
    parent=f"projects/{PROJECT_ID}",
    inspect_job=dlp_v2.InspectJobConfig(
        storage_config=storage_config,
        inspect_config=inspect_config,
        actions=[save_findings_action],
    ),
)
print(f"DLP job created: {job.name}")
print("Check status: cloud.google.com/dlp → Jobs")
```

---

### Step 2: Handling Free Text — Inline Inspection (Scenario C)

For `order_notes`, `customer_feedback`, `support_tickets` — fields where PII hides in natural language:

```python
def inspect_free_text(text: str, project_id: str) -> list[dict]:
    """
    Send a free-text string to DLP inline inspection.
    Returns list of findings: [{infoType, likelihood, quote}]
    
    Use this in your data pipeline to route rows with PII to a secure table.
    """
    dlp = dlp_v2.DlpServiceClient()
    
    item = dlp_v2.ContentItem(value=text)
    inspect_config = dlp_v2.InspectConfig(
        info_types=[
            {"name": "PERSON_NAME"},
            {"name": "PHONE_NUMBER"},
            {"name": "MEDICAL_TERM"},
            {"name": "STREET_ADDRESS"},
        ],
        min_likelihood=dlp_v2.Likelihood.POSSIBLE,
        include_quote=True,
    )
    
    response = dlp.inspect_content(
        parent=f"projects/{project_id}",
        inspect_config=inspect_config,
        item=item,
    )
    
    findings = []
    for finding in response.result.findings:
        findings.append({
            "info_type":  finding.info_type.name,
            "likelihood": finding.likelihood.name,
            "quote":      finding.quote,   # the actual matched text
        })
    return findings

# Example usage in a pipeline:
note = "Please call John Smith at 416-555-0192 regarding his prescription."
findings = inspect_free_text(note, PROJECT_ID)
# → [{"info_type": "PERSON_NAME", "likelihood": "VERY_LIKELY", "quote": "John Smith"},
#    {"info_type": "PHONE_NUMBER", "likelihood": "VERY_LIKELY", "quote": "416-555-0192"}]

if findings:
    route_to_secure_table(note)   # write to restricted dataset
else:
    route_to_standard_table(note)
```

---

### Step 3: Custom InfoTypes + Hotword Rules (the "no pattern" answer for internal IDs)

When you have internal IDs that aren't standard PII but are sensitive in your company's context:

```python
# Scenario: Internal employee IDs like "EMP-12345" are PII in HR tables
# No global standard — DLP doesn't know what "EMP-12345" means without context

custom_info_type = dlp_v2.CustomInfoType(
    info_type={"name": "EMPLOYEE_ID"},  # you define the name
    
    # Base pattern: detect the format
    regex=dlp_v2.CustomInfoType.Regex(pattern=r"EMP-\d{5}"),
    likelihood=dlp_v2.Likelihood.POSSIBLE,  # uncertain by default
    
    # Hotword rule: if "employee", "staff", "worker" appears nearby → HIGH confidence
    detection_rules=[
        dlp_v2.CustomInfoType.DetectionRule(
            hotword_rule=dlp_v2.CustomInfoType.DetectionRule.HotwordRule(
                hotword_regex=dlp_v2.CustomInfoType.Regex(
                    pattern=r"employee|staff|worker|payroll"
                ),
                proximity=dlp_v2.CustomInfoType.DetectionRule.Proximity(
                    window_before=20,   # 20 characters before the match
                    window_after=20,    # 20 characters after the match
                ),
                likelihood_adjustment=dlp_v2.CustomInfoType.DetectionRule.LikelihoodAdjustment(
                    fixed_likelihood=dlp_v2.Likelihood.VERY_LIKELY
                ),
            )
        )
    ],
)

# Use this custom_info_type in your InspectConfig alongside built-in types
```

---

### Step 4: Remediation — What to Do After Finding PII

Once DLP identifies PII in column `X`, apply one of these transformations:

| Technique | Use Case | BQ DLP Config | Reversible? |
|---|---|---|---|
| **Masking** | Logs, debugging displays | `CharacterMaskConfig` (`***-**-6789`) | No |
| **Tokenization** (format-preserving) | Join keys — need same-length output | `CryptoReplaceFfxFpeConfig` | Yes (with key) |
| **Pseudonymization** (deterministic) | Analytics — need consistent token but not real value | `CryptoDeterministicConfig` | Yes (with vault key) |
| **Bucketing** | Age (27 → "25–30"), salary ranges | `BucketingConfig` | No |
| **Redaction** | Free text / logs — full removal | `ReplaceWithInfoTypeConfig` replaces with `[PERSON_NAME]` | No |
| **Date shifting** | Birth dates — shift randomly per patient | `DateShiftConfig` | No |

**Example: Pseudonymize email before landing in analytics warehouse**
```python
deidentify_config = dlp_v2.DeidentifyConfig(
    record_transformations=dlp_v2.RecordTransformations(
        field_transformations=[
            dlp_v2.FieldTransformation(
                fields=[dlp_v2.FieldId(name="email")],
                primitive_transformation=dlp_v2.PrimitiveTransformation(
                    crypto_deterministic_config=dlp_v2.CryptoDeterministicConfig(
                        crypto_key=dlp_v2.CryptoKey(
                            kms_wrapped=dlp_v2.KmsWrappedCryptoKey(
                                wrapped_key=b"<your-KMS-wrapped-key>",
                                crypto_key_name=f"projects/{PROJECT_ID}/locations/global/keyRings/dlp-ring/cryptoKeys/dlp-key",
                            )
                        ),
                        surrogate_info_type={"name": "EMAIL_TOKEN"},
                    )
                ),
            )
        ]
    )
)
```

---

### Step 5: Enforce Access — BigQuery Column-Level Security

After DLP finds PII columns, tag them so only authorized users can read the raw value:

```sql
-- Step 1: Create a policy tag taxonomy in Data Catalog
-- (do this in GCP Console: BigQuery → Policy Tags → New Taxonomy)
-- Taxonomy: "PII Classification"
--   └── Sensitive
--       └── Highly Sensitive (SSN, passport)

-- Step 2: Grant IAM role to authorized users only
-- roles/bigquery.fineGrainedReader → only data stewards get this

-- Step 3: Tag the column in BigQuery schema
-- In BQ UI: Schema → email column → Edit → Policy Tag → "Sensitive"

-- Effect: users WITHOUT fineGrainedReader see NULL instead of the real value
SELECT email FROM raw_brand_c.orders LIMIT 1;
-- Unauthorized user → NULL
-- Authorized user  → user@example.com
```

---

### Step 6: Continuous PII Monitoring Pipeline

```
New data partition lands in BigQuery
          ↓
Eventarc trigger → Cloud Function
          ↓
DLP Inspection Job (async, scans new partition only)
          ↓
Findings → security.dlp_findings (BQ table)
          ↓
BigQuery scheduled query: check for VERY_LIKELY findings in unexpected columns
          ↓
Cloud Monitoring custom metric: dlp/unexpected_pii_count
          ↓
Alert if > 0 → Pub/Sub → Cloud Function → Slack #data-security channel
          ↓
Data steward reviews → applies policy tag → restricts access
```

Scan only new partitions (not the full table every time) to control DLP cost:
```python
# Partition filter: only scan today's data
storage_config = dlp_v2.StorageConfig(
    big_query_options=dlp_v2.BigQueryOptions(
        table_reference=dlp_v2.BigQueryTable(...),
        # Scan only the partition matching today
        row_condition=dlp_v2.RowCondition(
            expressions=dlp_v2.RowCondition.Expressions(
                conditions=dlp_v2.RowCondition.Conditions(
                    conditions=[
                        dlp_v2.RowCondition.Condition(
                            field=dlp_v2.FieldId(name="_PARTITIONDATE"),
                            operator=dlp_v2.RelationalOperator.EQUAL_TO,
                            value=dlp_v2.Value(date_value=today_date),
                        )
                    ]
                )
            )
        ),
    )
)
```

---

## Non-GCP Alternatives (mention for completeness)

| Tool | Platform | Notes |
|---|---|---|
| AWS Macie | AWS (S3, RDS) | ML-based, similar to DLP, S3-focused |
| Microsoft Purview | Azure | Data catalog + sensitivity labels |
| Presidio (open source) | Any | NLP-based, runs on-prem/k8s, integrates with spaCy |
| Immuta | On-prem / multi-cloud | Policy-based access + PII tagging |
| Privacera | On-prem / multi-cloud | Apache Ranger-based, data governance |

---

## Answer Skeleton (Memorize This)
```
"I'd approach PII discovery in four layers:

1. DISCOVERY: Cloud DLP Inspection Job on BigQuery.
   DLP uses ML-based infoType detection — it identifies PERSON_NAME, STREET_ADDRESS,
   MEDICAL_TERM even without a regex pattern because it understands context.
   For internal IDs that aren't standard PII, I'd define Custom InfoTypes
   with hotword detection rules — for example, 'EMP-12345' near the word 'payroll'
   gets upgraded from POSSIBLE to VERY_LIKELY.

2. CLASSIFICATION: DLP findings land in a security.dlp_findings BigQuery table.
   A scheduled query checks for VERY_LIKELY findings in columns that weren't
   expected to contain PII — fires a Cloud Monitoring alert for data steward review.

3. REMEDIATION: Depending on use case:
   - Analytics key needed: pseudonymize via deterministic encryption (consistent token, not reversible without KMS key)
   - Display/logs: mask (***-**-6789)
   - Free text: redact and replace with [PERSON_NAME]

4. ENFORCEMENT: Apply BigQuery policy tags from Data Catalog taxonomy.
   Unauthorized users see NULL. Authorized data stewards have fineGrainedReader role.
   Ongoing: DLP scans only new daily partitions — cost-efficient and continuous.
"
```

---

## Flash Cards

| Question | Answer |
|---|---|
| What is Cloud DLP? | Google's ML-based PII detection API — 150+ built-in infoTypes, works without patterns |
| Why can't regex alone detect all PII? | Names, addresses, free-text PII have no consistent pattern — only context reveals they're PII |
| What is a DLP infoType? | The category of sensitive data (PERSON_NAME, EMAIL_ADDRESS, etc.) — built-in or custom |
| What is a hotword rule? | Increases likelihood of a match if a keyword appears nearby (e.g. "employee" near "EMP-12345") |
| What is the difference between tokenization and pseudonymization? | Tokenization: format-preserving (same length, reversible). Pseudonymization: hash/token, not format-preserving. |
| What is a BigQuery policy tag? | A label applied to a column. Users without Fine-Grained Reader IAM role see NULL. |
| How do you scan DLP cost-efficiently on large tables? | Partition filter — only scan today's new partition, not the full table |
| What is the DLP findings output? | A BigQuery table with: info_type, likelihood, column_name, row_count — queryable for reports |
| Non-GCP equivalent of DLP? | AWS Macie (S3/RDS), Microsoft Presidio (open-source), Immuta (on-prem) |

---

## Practice Questions (6 Minutes Each)

1. **"You inherit a 5TB BigQuery table with 200 columns. No data dictionary. How do you identify which columns have PII?"**
   → DLP inspection job, RANDOM_START sampling (50K rows), findings → BQ security table, review VERY_LIKELY hits

2. **"The `order_notes` free-text column might contain customer phone numbers typed in by call centre agents. How do you detect and handle this?"**
   → Inline DLP `content.inspect` in the pipeline; route rows with PHONE_NUMBER findings to restricted secure dataset; mask before landing in analytics warehouse

3. **"After DLP tags a column as PII, a junior analyst still queries it. How did that happen and how do you fix it?"**
   → BigQuery policy tags weren't applied OR analyst has fineGrainedReader role they shouldn't. Fix: audit IAM bindings + apply policy tag if missing

4. **"How would you prove to a GDPR auditor that no PII is in your analytics warehouse?"**
   → Show DLP scan results (PASS/no findings), show policy tag enforcement, show pseudonymization applied in transform layer, show IAM audit logs
