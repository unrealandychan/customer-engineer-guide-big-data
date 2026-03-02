# 05. Serverless Networking

> **Pre-Sales Context:** Modern data architectures rely heavily on serverless compute (Cloud Functions, Cloud Run) to trigger pipelines or serve data. You need to know how these serverless environments interact with private networks.

---

## 1. The Problem with Serverless

By default, serverless products like Cloud Functions, Cloud Run, and App Engine run in a Google-managed environment, *outside* of your VPC.

**The Scenario:**
You have a Cloud Function that triggers when a file lands in GCS. The function needs to connect to a private Cloud SQL database (or an on-premise database via Interconnect) to update a record.

Because the Cloud Function is outside your VPC, it cannot reach the private IP address of the database.

## 2. The Solution: Serverless VPC Access

**Serverless VPC Access** allows your serverless environments to send traffic directly into your VPC network using internal IP addresses.

**How it works:**
1.  You create a "Serverless VPC Access Connector" in a specific region and subnet of your VPC.
2.  You configure your Cloud Function or Cloud Run service to use this connector.
3.  When the function needs to reach the database, the traffic flows through the connector, into your VPC, and securely to the database's private IP.

## 3. Ingress vs. Egress

When talking about serverless networking, you must distinguish between traffic going *out* (Egress) and traffic coming *in* (Ingress).

### Egress (Traffic leaving the serverless app)
*   **Default:** Traffic goes to the public internet.
*   **With Serverless VPC Access:** You can route traffic to your VPC (to reach private databases or on-prem resources).
*   **Route All Traffic:** You can force *all* outbound traffic from the Cloud Function to go through your VPC (useful if you want to force the traffic through a centralized firewall or NAT gateway).

### Ingress (Traffic coming to the serverless app)
*   **Default:** Anyone on the internet can call your Cloud Function URL.
*   **Internal Only:** You can restrict the function so it can *only* be triggered by resources inside your VPC (or via VPC Service Controls). This is crucial for internal microservices that shouldn't be exposed to the web.

## 4. The Pre-Sales Pitch

**Customer:** "We want to use Cloud Run to build a lightweight API that queries our on-premise Oracle database. But our security team says Cloud Run is a public service and can't access our private network."

**Your Answer:**
> "That's a common misconception. While Cloud Run is fully managed, we use a feature called **Serverless VPC Access**. We deploy a connector inside your private VPC. Your Cloud Run service uses this connector to route traffic securely into your VPC, across your Interconnect, and directly to your on-premise Oracle database using private IP addresses. The traffic never touches the public internet, satisfying your security team's requirements while still giving your developers a serverless experience."
