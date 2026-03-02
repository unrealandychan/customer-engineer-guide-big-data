# 06. Network Tiers & Peering

> **Pre-Sales Context:** These are two distinct concepts that often come up in architectural discussions. Network Tiers are about cost vs. performance on the public internet. Peering is about connecting different internal networks.

---

## 1. Network Service Tiers

Google Cloud is unique in offering two different tiers for network traffic routing over the public internet.

### Premium Tier (The Default)
*   **How it works:** Traffic enters Google's private fiber network at the edge Point of Presence (PoP) *closest to the user*, and travels the rest of the way on Google's highly optimized, uncongested backbone.
*   **Example:** A user in Tokyo accesses a VM in Iowa. The traffic enters Google's network in Tokyo and travels under the ocean on Google's private cables to Iowa.
*   **Pros:** Lowest latency, highest reliability, best performance.
*   **Cons:** More expensive.

### Standard Tier
*   **How it works:** Traffic travels over the public internet (via transit ISPs) for as long as possible, and only enters Google's network at the data center where the resource lives.
*   **Example:** A user in Tokyo accesses a VM in Iowa. The traffic bounces across various public internet providers across the Pacific and the US, finally entering Google's network in Iowa.
*   **Pros:** Cheaper (comparable to AWS/Azure standard egress pricing).
*   **Cons:** Higher latency, subject to public internet congestion and routing issues.

**Pre-Sales Soundbite:**
> "Google owns the largest private fiber network in the world. With our Premium Network Tier, your customers' traffic enters our private backbone almost immediately, bypassing the congestion of the public internet. This is why YouTube and Google Search are so fast, and you get to ride on that exact same infrastructure."

---

## 2. VPC Network Peering

**The Problem:**
You have two different VPC networks (maybe in different GCP projects, or even different GCP organizations). You want a VM in VPC-A to talk to a VM in VPC-B using private IP addresses.

**The Solution: VPC Network Peering**
*   **What it is:** A decentralized way to connect two VPCs so they can communicate using internal IP addresses.
*   **How it works:** You set up a peering connection from VPC-A to VPC-B, and another from VPC-B to VPC-A. Once established, the networks share routing information.
*   **Key Limitation (Non-Transitive):** Peering is *not* transitive. If VPC-A is peered with VPC-B, and VPC-B is peered with VPC-C, VPC-A **cannot** talk to VPC-C. You would have to explicitly peer A and C.

### When to use Peering vs. Shared VPC

*   **Shared VPC:** Best for a centralized organization where a central IT team manages one massive network, and different departments (projects) just attach their VMs to it. (Centralized control).
*   **VPC Peering:** Best for connecting decentralized, autonomous teams, or connecting your network to a third-party SaaS provider hosted on GCP (like MongoDB Atlas or Elastic Cloud). (Decentralized control).
