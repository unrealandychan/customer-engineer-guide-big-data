# 02. Hybrid Connectivity (Connecting On-Prem to GCP)

> **Pre-Sales Context:** Enterprise customers rarely start 100% in the cloud. They have legacy data centers. You must know how to securely connect their on-premise Hadoop cluster or Oracle database to GCP.

---

## 1. The Options

When a customer asks, "How do we connect our data center to Google Cloud?", you have three main answers, depending on their bandwidth needs and budget.

### A. Cloud VPN (IPsec)
*   **What it is:** An encrypted tunnel over the public internet.
*   **Bandwidth:** Up to 3 Gbps per tunnel (you can bundle them for more).
*   **Pros:** Fast to set up (minutes/hours), cheap.
*   **Cons:** Relies on the public internet, so latency can be unpredictable.
*   **When to use:** Proof of Concepts (POCs), small data transfers, or as a backup to Interconnect.

### B. Dedicated Interconnect
*   **What it is:** A direct, physical fiber-optic connection between the customer's on-premise router and Google's edge router in a colocation facility.
*   **Bandwidth:** 10 Gbps or 100 Gbps per link.
*   **Pros:** Massive bandwidth, highly predictable low latency, traffic never touches the public internet.
*   **Cons:** Expensive, takes weeks/months to provision (requires physical hardware installation).
*   **When to use:** Massive data migrations (e.g., moving petabytes from on-prem Hadoop to GCS), real-time CDC from heavy transactional databases.

### C. Partner Interconnect
*   **What it is:** Connectivity provided through a supported service provider (like Equinix, AT&T, Verizon). The provider already has a physical connection to Google; you just connect to the provider.
*   **Bandwidth:** 50 Mbps to 50 Gbps.
*   **Pros:** Faster to set up than Dedicated, good for customers who don't need a full 10 Gbps or aren't physically located near a Google edge facility.
*   **Cons:** You rely on a third party.

---

## 2. The "Data Migration" Whiteboard Scenario

**Customer:** "We have 500 TB of data in our on-premise Hadoop cluster. We want to migrate it to Cloud Storage. We currently have a 1 Gbps internet connection. How should we do this?"

**Your Pre-Sales Answer:**
1.  **Do the Math:** 500 TB over a 1 Gbps connection will take roughly **46 days** (assuming perfect conditions, which never happen).
2.  **The Recommendation:** "For a migration of this size, relying on a standard internet connection or VPN will take too long and impact your daily operations. I recommend setting up a **Partner Interconnect** or **Dedicated Interconnect** to give you a dedicated 10 Gbps pipe. This will reduce the transfer time to under a week and ensure the traffic is completely private."
3.  **The Alternative (Transfer Appliance):** "If setting up an Interconnect takes too long, we can ship you a **Transfer Appliance** (a physical ruggedized server). You load the data onto it locally, ship it back to Google, and we upload it to GCS for you."
