# 03. Private Google Access (PGA)

> **Pre-Sales Context:** This is a fundamental security concept for data pipelines. Customers will demand that their compute resources do not have public IP addresses. But if they don't have public IPs, how do they reach Google APIs like BigQuery or Cloud Storage?

---

## 1. The Problem

Imagine you deploy a Dataproc cluster. For security reasons, you place it on a private subnet and do **not** assign external (public) IP addresses to the worker nodes.

Now, your PySpark job needs to read a file from Cloud Storage (`gs://my-bucket/data.csv`) and write the results to BigQuery.

*   Cloud Storage and BigQuery are public APIs (they are accessed via URLs like `storage.googleapis.com`).
*   Your Dataproc nodes have no public internet access.
*   **Result:** The job fails. The nodes cannot reach the APIs.

## 2. The Solution: Private Google Access (PGA)

**Private Google Access** is a subnet-level setting. When you enable it on a subnet, VMs on that subnet (even those without external IP addresses) can reach Google APIs and services using Google's internal network.

**How it works:**
1.  You enable PGA on the subnet where your Dataproc cluster lives.
2.  When the Dataproc node tries to reach `storage.googleapis.com`, the GCP network intercepts the request.
3.  Instead of routing the request out to the public internet, it routes it internally over Google's private backbone directly to the Cloud Storage service.

## 3. Why Customers Care (The Pre-Sales Pitch)

**Customer:** "Our CISO mandates that no compute instances can have public IP addresses. How can we use your managed services like BigQuery if they are public APIs?"

**Your Answer:**
> "We completely agree with that security posture. In Google Cloud, you use **Private Google Access**. By simply flipping a switch on your subnet, your private Dataproc clusters or Dataflow workers can securely communicate with BigQuery, Cloud Storage, and Pub/Sub entirely over Google's private fiber network. The traffic never touches the public internet, and your compute instances remain completely isolated from external threats."

---

## 4. On-Premises Private Google Access

What if the customer has an on-premise server that needs to reach BigQuery privately?

You can configure **Private Google Access for On-Premises**.
1.  The customer connects their data center to GCP via Cloud VPN or Interconnect.
2.  They configure their on-premise DNS to resolve `*.googleapis.com` to a specific set of private virtual IP addresses (VIPs) provided by Google (`restricted.googleapis.com` or `private.googleapis.com`).
3.  The traffic flows from their on-prem server, over the private Interconnect, and directly to the Google API, bypassing the public internet.
