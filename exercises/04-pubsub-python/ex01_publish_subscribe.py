"""
Exercise 01 — Pub/Sub: Publish and Subscribe (Python)
------------------------------------------------------
Goal:
    - Publish messages to a Pub/Sub topic
    - Pull messages from a subscription
    - Use streaming pull (push-style async consumer)
    - Handle message acknowledgement and error cases

Interview relevance:
    "What is Pub/Sub and how does it fit in a GCP streaming pipeline?"
    Answer: Pub/Sub is the event ingestion layer — like Kafka on GCP.
    Producers publish → Pub/Sub buffers → Consumers (Dataflow, Dataproc, Cloud Functions) pull

Setup:
    pip install google-cloud-pubsub
    export GOOGLE_CLOUD_PROJECT=your-project-id

    Create topic and subscription:
    gcloud pubsub topics create events-topic
    gcloud pubsub subscriptions create events-sub --topic=events-topic
"""

import os
import json
import time
import uuid
import random
import threading
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1

PROJECT_ID    = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
TOPIC_ID      = "events-topic"
SUBSCRIPTION_ID = "events-sub"


# ---------------------------------------------------------------------------
# EXERCISE 1a: Create topic and subscription programmatically
# ---------------------------------------------------------------------------
def setup_topic_and_subscription() -> None:
    """
    Create a Pub/Sub topic and pull subscription via the Admin API.
    In production you'd do this with Terraform (see exercises/07-terraform-gcp/).
    """
    publisher   = pubsub_v1.PublisherClient()
    subscriber  = pubsub_v1.SubscriberClient()

    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
    sub_path   = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    # TODO: Create topic — ignore AlreadyExists error
    try:
        publisher.create_topic(request={"name": topic_path})
        print(f"Topic created: {topic_path}")
    except Exception as e:
        print(f"Topic exists or error: {e}")

    # TODO: Create subscription pointing to the topic
    try:
        subscriber.create_subscription(request={
            "name": sub_path,
            "topic": topic_path,
            "ack_deadline_seconds": 30,
        })
        print(f"Subscription created: {sub_path}")
    except Exception as e:
        print(f"Subscription exists or error: {e}")


# ---------------------------------------------------------------------------
# EXERCISE 1b: Publish messages to a topic
# ---------------------------------------------------------------------------
def publish_events(num_events: int = 20) -> None:
    """
    Publish JSON-encoded event messages to a Pub/Sub topic.

    Key concepts:
    - Messages are bytes — encode your payload (JSON, Avro, Protobuf)
    - Attributes are key-value string metadata on each message
    - publisher.publish() is async — returns a future
    - Call future.result() to block until published (or timeout)
    """
    publisher  = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    actions   = ["purchase", "click", "view", "add_to_cart", "refund"]
    countries = ["US", "GB", "DE", "JP", "BR"]

    futures = []
    for i in range(num_events):
        event = {
            "event_id":   str(uuid.uuid4()),
            "event_type": random.choice(actions),
            "country":    random.choice(countries),
            "user_id":    f"user_{random.randint(1, 50):04d}",
            "amount":     round(random.uniform(1.0, 200.0), 2),
            "timestamp":  time.time(),
        }

        # Encode the payload as bytes (Pub/Sub requires bytes)
        data = json.dumps(event).encode("utf-8")

        # TODO: Publish the message with attributes
        # publisher.publish(topic_path, data=data, event_type=event["event_type"])
        future = publisher.publish(
            topic_path,
            data=data,
            # Attributes are string key-value pairs — useful for filtering
            event_type=event["event_type"],
            country=event["country"],
        )
        futures.append((future, event["event_id"]))

    # Wait for all publishes to complete
    for future, event_id in futures:
        try:
            message_id = future.result(timeout=10)
            # print(f"  Published {event_id} → message_id={message_id}")
        except Exception as e:
            print(f"  Publish failed for {event_id}: {e}")

    print(f"Published {num_events} events to {topic_path}")


# ---------------------------------------------------------------------------
# EXERCISE 1c: Pull messages synchronously (simple polling)
# ---------------------------------------------------------------------------
def pull_messages_sync(max_messages: int = 10) -> None:
    """
    Synchronous pull — pull up to max_messages at once, process, acknowledge.
    Good for batch processing or scheduled consumers.

    NOT recommended for high-throughput — use streaming pull instead.
    """
    subscriber = pubsub_v1.SubscriberClient()
    sub_path   = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    print(f"\n=== Synchronous pull (up to {max_messages} messages) ===")

    with subscriber:
        # TODO: Call subscriber.pull(request={...}) with max_messages
        response = subscriber.pull(
            request={
                "subscription": sub_path,
                "max_messages":  max_messages,
            },
            timeout=10,
        )

        ack_ids = []
        for msg in response.received_messages:
            payload = json.loads(msg.message.data.decode("utf-8"))
            attrs   = dict(msg.message.attributes)
            print(f"  [{msg.message.message_id}] {payload['event_type']:<15} "
                  f"country={attrs.get('country', '??')}  "
                  f"amount=${payload['amount']:.2f}")
            ack_ids.append(msg.ack_id)

        # TODO: Acknowledge the messages so they are not redelivered
        if ack_ids:
            subscriber.acknowledge(request={"subscription": sub_path, "ack_ids": ack_ids})
            print(f"Acknowledged {len(ack_ids)} messages.")
        else:
            print("No messages available.")


# ---------------------------------------------------------------------------
# EXERCISE 1d: Streaming pull (async subscriber — production pattern)
# ---------------------------------------------------------------------------
def streaming_pull(timeout_seconds: int = 15) -> None:
    """
    Streaming pull — the recommended production pattern.
    The subscriber library manages a long-lived connection and delivers
    messages to a callback as they arrive.

    Key behaviour:
    - callback() is called in a thread pool for each message
    - You MUST call message.ack() or message.nack() in the callback
    - nack() = redeliver after ack_deadline expires
    """
    subscriber = pubsub_v1.SubscriberClient()
    sub_path   = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    received_count = {"n": 0}
    lock = threading.Lock()

    def callback(message: pubsub_v1.types.PubsubMessage) -> None:
        """
        Called for each incoming message.
        Process the message and ack (or nack on failure).
        """
        try:
            payload = json.loads(message.data.decode("utf-8"))
            with lock:
                received_count["n"] += 1
                print(f"  Received #{received_count['n']}: "
                      f"{payload['event_type']:<15} "
                      f"user={payload['user_id']}  "
                      f"amount=${payload['amount']:.2f}")

            # TODO: Acknowledge the message after successful processing
            message.ack()

        except Exception as e:
            print(f"  Processing failed: {e} — nacking")
            # TODO: Nack on failure — message will be redelivered
            message.nack()

    # Flow control: limit inflight messages to avoid memory issues
    flow_control = pubsub_v1.types.FlowControl(max_messages=100)

    print(f"\n=== Streaming pull (running for {timeout_seconds}s) ===")
    with subscriber:
        streaming_pull_future = subscriber.subscribe(
            sub_path,
            callback=callback,
            flow_control=flow_control,
        )
        try:
            streaming_pull_future.result(timeout=timeout_seconds)
        except TimeoutError:
            streaming_pull_future.cancel()
            streaming_pull_future.result()

    print(f"Streaming pull finished. Received {received_count['n']} messages.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Pub/Sub Python Exercise ===\n")
    setup_topic_and_subscription()

    print("\n--- Publishing events ---")
    publish_events(num_events=30)

    time.sleep(2)   # Brief wait for messages to be available

    print("\n--- Sync pull ---")
    pull_messages_sync(max_messages=10)

    print("\n--- Streaming pull ---")
    # Publish more events for the streaming pull to consume
    publish_events(num_events=20)
    streaming_pull(timeout_seconds=10)

# ---------------------------------------------------------------------------
# CHALLENGES
# ---------------------------------------------------------------------------
# 1. Add a filter subscription: create a subscription with a filter
#    that only delivers messages where event_type = "purchase".
#    How does the subscriber.create_subscription request change?
#    Hint: add "filter": 'attributes.event_type = "purchase"' to the request.
#
# 2. Implement a dead-letter topic: create a second topic "events-dlq"
#    and configure the subscription to send unacked messages there after
#    5 delivery attempts. Simulate a nack loop and watch messages move to DLQ.
#
# 3. Measure end-to-end latency: record time.time() in the published message,
#    and subtract it in the callback. What's the typical Pub/Sub latency?
#
# 4. Research: in a real pipeline, the Dataflow Beam job would replace
#    your streaming_pull() callback. Pub/Sub → Dataflow = fully managed.
#    What are the advantages over a custom streaming_pull consumer?
