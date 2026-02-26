# Category 04 — Pub/Sub (Python)

## What you will practice

| File                        | Topics                                                            |
|-----------------------------|-------------------------------------------------------------------|
| `ex01_publish_subscribe.py` | Publish with futures, sync pull, streaming pull, ack/nack, flow control |

---

## Setup

```bash
pip install google-cloud-pubsub
export GOOGLE_CLOUD_PROJECT=your-project-id
python ex01_publish_subscribe.py
```

---

## Key Pub/Sub Patterns

```python
from google.cloud import pubsub_v1

# Publish
publisher = pubsub_v1.PublisherClient()
future = publisher.publish(topic_path, data=b"payload", attr="value")
msg_id = future.result(timeout=10)

# Streaming subscribe
def callback(message):
    print(message.data)
    message.ack()   # or message.nack() to redeliver

subscriber = pubsub_v1.SubscriberClient()
streaming_pull = subscriber.subscribe(sub_path, callback=callback)
streaming_pull.result(timeout=30)
```

---

## Push vs Pull

| Factor          | Pull                      | Push                         |
|-----------------|---------------------------|------------------------------|
| Who initiates?  | Subscriber calls receive  | Pub/Sub calls your endpoint  |
| Best for        | Long-running services     | Cloud Run, App Engine, FaaS  |
| Auth            | IAM on subscription       | OIDC token on endpoint       |
| Scaling         | Manual or autoscaled      | HTTP endpoint scales auto    |

---

## At-Least-Once vs Exactly-Once

- **Default:** at-least-once (message may be redelivered after ack deadline)
- **Exactly-once:** set `enable_exactly_once_delivery=True` on subscription
  - Requires StreamingPull; adds ~50ms latency; best effort in practice
