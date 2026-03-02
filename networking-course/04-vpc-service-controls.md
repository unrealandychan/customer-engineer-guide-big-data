# 04. VPC Service Controls (VPC-SC)

> **Pre-Sales Context:** This is the ultimate answer to "Data Exfiltration." If you are talking to a bank, healthcare provider, or government agency, you *must* bring up VPC Service Controls. It is a massive differentiator for Google Cloud.

---

## 1. The Threat: Data Exfiltration

**The Scenario:**
You have a rogue employee (or compromised credentials). They have legitimate IAM access to read your company's highly sensitive BigQuery dataset (`project-a:finance_data`).

**The Attack:**
The employee writes a simple script:
`SELECT * FROM project-a:finance_data`
and saves the output to their *personal* Google Cloud Storage bucket (`gs://hacker-personal-bucket`).

**Why IAM fails here:**
IAM controls *who* can access the data. The employee *is* authorized to read the data. IAM cannot control *where* the data goes after it is read.

## 2. The Solution: VPC Service Controls

VPC Service Controls (VPC-SC) allows you to draw a virtual, invisible "security perimeter" around your GCP projects and managed services (like BigQuery, GCS, Pub/Sub).

**How it stops the attack:**
1.  You create a VPC-SC perimeter around `project-a`.
2.  You configure the perimeter to block any data from leaving the perimeter.
3.  The rogue employee runs their script.
4.  BigQuery processes the query, but when the script tries to write the data to `gs://hacker-personal-bucket` (which is *outside* the perimeter), **VPC-SC blocks the request.**

## 3. Key Concepts of VPC-SC

*   **Perimeter:** The boundary you draw around projects. Services inside the perimeter can talk to each other freely.
*   **Ingress/Egress Rules:** You can explicitly define exceptions. (e.g., "Allow data to flow from Perimeter A to Perimeter B, but nowhere else").
*   **Access Levels (Context-Aware Access):** You can allow access from *outside* the perimeter based on context.
    *   *Example:* "Allow the CEO to access BigQuery from outside the perimeter, BUT ONLY IF they are using a company-issued laptop, running the latest OS, and located in the United States."

## 4. The Pre-Sales Pitch

**Customer:** "We are terrified of a malicious insider downloading our customer PII to a personal drive. How do you prevent that?"

**Your Answer:**
> "Identity and Access Management (IAM) is not enough to stop data exfiltration, because IAM only checks *who* you are. To solve this, Google Cloud offers **VPC Service Controls**. We can draw a hard security perimeter around your BigQuery and Cloud Storage environments. Even if an employee has full admin rights to the data, VPC Service Controls will physically block them from copying that data to a bucket or project outside of your corporate perimeter. It's a zero-trust architecture applied directly to our managed data services."
