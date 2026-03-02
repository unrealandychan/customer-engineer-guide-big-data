# 01. VPC Fundamentals (The Global Advantage)

> **Pre-Sales Context:** When talking to AWS veterans, GCP's global VPC is a massive "Aha!" moment. It simplifies network design significantly.

---

## 1. What is a VPC?
A Virtual Private Cloud (VPC) is your private, isolated network within Google Cloud. It's the foundation for all your compute resources (Compute Engine, GKE, Dataproc).

## 2. The GCP Differentiator: Global VPCs
This is the most important concept to understand if you are coming from AWS.

*   **AWS VPC:** Tied to a specific region (e.g., `us-east-1`). If you want resources in `us-west-2` to talk to `us-east-1`, you have to set up VPC Peering or a Transit Gateway.
*   **GCP VPC:** **Global.** A single VPC can span the entire world.
*   **Subnets:** **Regional.** You create subnets within the global VPC and assign them to specific regions.

**Example:**
You create `my-global-vpc`.
You create `subnet-us-central1` (10.0.1.0/24) and `subnet-europe-west1` (10.0.2.0/24).
A VM in the US subnet can talk to a VM in the Europe subnet using **internal private IP addresses** right out of the box. No peering required. The traffic travels entirely on Google's private fiber backbone.

**Pre-Sales Soundbite:**
> "Unlike other clouds where networks are siloed by region, Google's VPCs are global by default. This means your data pipelines can span continents using private IP addresses without the complexity and cost of managing transit gateways or peering connections."

---

## 3. Firewall Rules
*   In GCP, firewall rules are applied at the **VPC network level**, not the subnet level.
*   They are stateful (if a request is allowed in, the response is automatically allowed out).
*   **Tags & Service Accounts:** Instead of writing firewall rules based on IP addresses (which change), you can write rules based on Network Tags or Service Accounts.
    *   *Example:* "Allow traffic on port 8080 from any VM with the tag `web-server` to any VM running as the `database-service-account`."

---

## 4. Cloud Router & Cloud NAT
*   **Cloud Router:** Used for dynamic routing (BGP) between your GCP VPC and your on-premise network.
*   **Cloud NAT (Network Address Translation):** If you have a Dataproc cluster on a private subnet (no public IPs), but it needs to download a package from the public internet (e.g., `pip install`), you use Cloud NAT. It allows outbound internet access without allowing inbound connections.
