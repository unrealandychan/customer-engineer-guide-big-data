// Exercise 01 — Pub/Sub: Publish and Subscribe (Go)
// ---------------------------------------------------
// Goal:
//   - Publish messages to a Pub/Sub topic using Go
//   - Pull messages with a subscriber callback
//   - Handle concurrent message processing safely
//   - Use context cancellation for clean shutdown
//
// Run:
//   go mod init pubsub-go-exercises
//   go get cloud.google.com/go/pubsub
//   export GOOGLE_CLOUD_PROJECT=your-project-id
//
//   gcloud pubsub topics create events-topic
//   gcloud pubsub subscriptions create events-sub --topic=events-topic
//
//   go run ex01_publish_subscribe.go

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"cloud.google.com/go/pubsub"
)

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
var (
	projectID      = os.Getenv("GOOGLE_CLOUD_PROJECT")
	topicID        = "events-topic"
	subscriptionID = "events-sub"
)

// ---------------------------------------------------------------------------
// Event — payload struct for messages
// ---------------------------------------------------------------------------
type Event struct {
	EventID   string  `json:"event_id"`
	EventType string  `json:"event_type"`
	Country   string  `json:"country"`
	UserID    string  `json:"user_id"`
	Amount    float64 `json:"amount"`
	Timestamp int64   `json:"timestamp"`
}

func main() {
	if projectID == "" {
		log.Fatal("GOOGLE_CLOUD_PROJECT not set")
	}

	ctx := context.Background()
	client, err := pubsub.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("pubsub.NewClient: %v", err)
	}
	defer client.Close()

	// Run exercises
	setupTopicAndSubscription(ctx, client)
	publishEvents(ctx, client, 30)

	time.Sleep(2 * time.Second) // Allow messages to be available

	pullMessagesConcurrently(ctx, client, 15*time.Second)
}

// ---------------------------------------------------------------------------
// EXERCISE 1a: Create topic and subscription
// ---------------------------------------------------------------------------
func setupTopicAndSubscription(ctx context.Context, client *pubsub.Client) {
	// TODO: Get or create the topic
	// client.CreateTopic(ctx, topicID) returns (*pubsub.Topic, error)
	topic, err := client.CreateTopic(ctx, topicID)
	if err != nil {
		// Topic likely already exists
		topic = client.Topic(topicID)
		fmt.Printf("Topic %s: using existing\n", topicID)
	} else {
		fmt.Printf("Topic %s: created\n", topic.String())
	}
	_ = topic

	// TODO: Get or create the subscription
	sub, err := client.CreateSubscription(ctx, subscriptionID, pubsub.SubscriptionConfig{
		Topic:            client.Topic(topicID),
		AckDeadline:      30 * time.Second,
		RetentionDuration: 24 * time.Hour,
	})
	if err != nil {
		sub = client.Subscription(subscriptionID)
		fmt.Printf("Subscription %s: using existing\n", subscriptionID)
	} else {
		fmt.Printf("Subscription %s: created\n", sub.String())
	}
}

// ---------------------------------------------------------------------------
// EXERCISE 1b: Publish events concurrently (using goroutines + futures)
// ---------------------------------------------------------------------------
func publishEvents(ctx context.Context, client *pubsub.Client, count int) {
	topic := client.Topic(topicID)
	// Set batching settings for throughput
	topic.PublishSettings.ByteThreshold  = 5000
	topic.PublishSettings.CountThreshold = 10
	topic.PublishSettings.DelayThreshold = 100 * time.Millisecond
	defer topic.Stop() // Flush remaining messages on exit

	actions   := []string{"purchase", "click", "view", "add_to_cart", "refund"}
	countries := []string{"US", "GB", "DE", "JP", "BR"}

	var wg sync.WaitGroup
	var published int64

	for i := 0; i < count; i++ {
		event := Event{
			EventID:   fmt.Sprintf("evt-%05d", i),
			EventType: actions[rand.Intn(len(actions))],
			Country:   countries[rand.Intn(len(countries))],
			UserID:    fmt.Sprintf("user-%04d", rand.Intn(50)+1),
			Amount:    float64(rand.Intn(20000)) / 100.0,
			Timestamp: time.Now().UnixMilli(),
		}

		data, err := json.Marshal(event)
		if err != nil {
			log.Printf("json.Marshal: %v", err)
			continue
		}

		// TODO: Publish the message with attributes
		// topic.Publish(ctx, &pubsub.Message{...}) returns a *pubsub.PublishResult
		result := topic.Publish(ctx, &pubsub.Message{
			Data: data,
			Attributes: map[string]string{
				"event_type": event.EventType,
				"country":    event.Country,
			},
		})

		wg.Add(1)
		go func(r *pubsub.PublishResult, id string) {
			defer wg.Done()
			// TODO: Block until the publish completes and get the server-assigned message ID
			_, err := r.Get(ctx)
			if err != nil {
				log.Printf("Publish failed for %s: %v", id, err)
				return
			}
			atomic.AddInt64(&published, 1)
		}(result, event.EventID)
	}

	wg.Wait()
	fmt.Printf("Published %d/%d events to %s\n", published, count, topicID)
}

// ---------------------------------------------------------------------------
// EXERCISE 1c: Pull messages with a concurrent subscriber callback
// ---------------------------------------------------------------------------
func pullMessagesConcurrently(ctx context.Context, client *pubsub.Client, duration time.Duration) {
	sub := client.Subscription(subscriptionID)

	// Configure concurrency — how many messages to process in parallel
	// TODO: Set sub.ReceiveSettings to control concurrency
	sub.ReceiveSettings.MaxOutstandingMessages = 50
	sub.ReceiveSettings.NumGoroutines          = 4  // parallel goroutines

	var (
		received int64
		mu       sync.Mutex
		counts   = make(map[string]int)
	)

	// Timeout context — stop pulling after `duration`
	receiveCtx, cancel := context.WithTimeout(ctx, duration)
	defer cancel()

	fmt.Printf("\n=== Pulling messages for %v ===\n", duration)

	// TODO: Call sub.Receive(ctx, callback) — blocks until ctx is cancelled
	// The callback is called concurrently for each received message
	err := sub.Receive(receiveCtx, func(ctx context.Context, msg *pubsub.Message) {
		var event Event
		if err := json.Unmarshal(msg.Data, &event); err != nil {
			log.Printf("json.Unmarshal error: %v — nacking", err)
			// TODO: Nack the message to trigger redelivery
			msg.Nack()
			return
		}

		atomic.AddInt64(&received, 1)
		mu.Lock()
		counts[event.EventType]++
		mu.Unlock()

		// TODO: Acknowledge the message after successful processing
		msg.Ack()

		// Simulate processing time
		time.Sleep(10 * time.Millisecond)
	})

	if err != nil && err != context.DeadlineExceeded {
		log.Printf("Receive error: %v", err)
	}

	fmt.Printf("\nPull complete. Total received: %d\n", received)
	fmt.Println("Events by type:")
	for eventType, count := range counts {
		fmt.Printf("  %-15s %d\n", eventType, count)
	}
}

// ---------------------------------------------------------------------------
// CHALLENGES
// ---------------------------------------------------------------------------
// 1. Add a PublishResult error handler that retries failed publishes
//    up to 3 times with exponential backoff.
//
// 2. Implement a metrics counter: track messages/second received.
//    Sample the atomic counter every second in a goroutine.
//
// 3. Create a filtered subscription (server-side filtering):
//    pubsub.SubscriptionConfig{
//        Filter: `attributes.event_type = "purchase"`,
//    }
//    Compare how many messages you receive vs without the filter.
//
// 4. Research: what is Pub/Sub "exactly-once delivery" mode?
//    How is it different from the default "at-least-once"?
//    When would you enable it and what's the trade-off?
