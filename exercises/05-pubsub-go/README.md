# Category 05 — Pub/Sub (Go)

## What you will practice

| File                        | Topics                                                              |
|-----------------------------|---------------------------------------------------------------------|
| `ex01_publish_subscribe.go` | Concurrent publish with goroutines, atomic counters, Receive + Ack  |

---

## Setup

```bash
cd exercises/05-pubsub-go
go mod tidy
export GOOGLE_CLOUD_PROJECT=your-project-id
go run ex01_publish_subscribe.go
```

---

## Key Go Pub/Sub Patterns

```go
import "cloud.google.com/go/pubsub"

client, _ := pubsub.NewClient(ctx, projectID)
defer client.Close()

// Publish
topic := client.Topic(topicID)
result := topic.Publish(ctx, &pubsub.Message{
    Data:       []byte("payload"),
    Attributes: map[string]string{"key": "val"},
})
msgID, _ := result.Get(ctx)  // Blocks until acked by server

// Subscribe
sub := client.Subscription(subID)
sub.Receive(ctx, func(ctx context.Context, msg *pubsub.Message) {
    fmt.Println(string(msg.Data))
    msg.Ack()  // or msg.Nack() to redeliver
})
```

---

## Go vs Python for Pub/Sub

| Factor              | Python                     | Go                           |
|---------------------|----------------------------|------------------------------|
| Concurrency model   | Threads + asyncio          | Goroutines (lightweight)     |
| Throughput          | Moderate                   | Very high (thousands/sec)    |
| Memory per goroutine| —                          | ~4KB vs ~1MB for OS thread   |
| Best for            | Data pipelines, ML, scripts| Microservices, ingestion APIs|
