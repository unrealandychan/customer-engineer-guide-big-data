# GCP Networking for Data Engineers

> **Pre-Sales Context:** As a Data Pre-Sales Engineer, you don't need to be a CCIE-level network architect. However, you *must* understand how data securely moves between on-premise data centers, other clouds, and GCP. Customers will constantly ask: "How do we keep our data off the public internet?"

This course covers the essential networking concepts you need to design secure data architectures and pass the interview.

## 📚 Course Modules

| Module | Topic | What You'll Learn |
| :--- | :--- | :--- |
| **01** | [VPC Fundamentals](01-vpc-fundamentals.md) | Global VPCs, Subnets, Firewall Rules, and the difference between AWS and GCP VPCs. |
| **02** | [Hybrid Connectivity](02-hybrid-connectivity.md) | Cloud VPN vs. Cloud Interconnect (Dedicated/Partner). How to connect on-prem to GCP. |
| **03** | [Private Google Access](03-private-google-access.md) | How VMs without public IPs can securely reach BigQuery and Cloud Storage. |
| **04** | [VPC Service Controls](04-vpc-service-controls.md) | The ultimate data exfiltration defense. Creating security perimeters around GCP APIs. |
| **05** | [Serverless Networking](05-serverless-networking.md) | Serverless VPC Access. How Cloud Run, Cloud Functions, and Dataflow connect to your VPC. |
| **06** | [Network Tiers & Peering](06-network-tiers-and-peering.md) | Premium vs. Standard Tier. VPC Network Peering for cross-project communication. |

---

## 🧠 The "Data Engineer's Networking Cheat Sheet"

If you only remember three things for your interview, remember these:

1.  **GCP VPCs are Global:** Unlike AWS (where VPCs are tied to a specific region), a single GCP VPC can span the entire globe. Subnets are regional. This makes multi-region architectures vastly simpler.
2.  **Private Google Access (PGA):** This is how your private Dataproc cluster (no public IP) talks to BigQuery or GCS without the traffic ever hitting the public internet.
3.  **VPC Service Controls (VPC-SC):** This is the answer to "How do we prevent a malicious insider from downloading our BigQuery data to their personal laptop?" It creates a hard perimeter around managed services.
