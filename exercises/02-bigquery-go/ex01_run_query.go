// Exercise 01 — Run a BigQuery Query in Go
// ------------------------------------------
// Goal:
//   - Connect to BigQuery using the Go client library
//   - Run a SQL query against a public dataset
//   - Iterate over results using an iterator
//   - Inspect job statistics (bytes processed, slot milliseconds)
//
// Run:
//   go mod init bq-go-exercises
//   go get cloud.google.com/go/bigquery
//   export GOOGLE_CLOUD_PROJECT=your-project-id
//   go run ex01_run_query.go

package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"cloud.google.com/go/bigquery"
	"google.golang.org/api/iterator"
)

// ---------------------------------------------------------------------------
// Result struct — maps to the query output columns
// ---------------------------------------------------------------------------
type WordCount struct {
	Word       string `bigquery:"word"`
	TotalCount int64  `bigquery:"total_count"`
}

type CorpusSummary struct {
	Corpus      string `bigquery:"corpus"`
	UniqueWords int64  `bigquery:"unique_words"`
	TotalWords  int64  `bigquery:"total_words"`
}

func main() {
	ctx       := context.Background()
	projectID := os.Getenv("GOOGLE_CLOUD_PROJECT")
	if projectID == "" {
		log.Fatal("GOOGLE_CLOUD_PROJECT environment variable not set")
	}

	// ---------------------------------------------------------------------------
	// STEP 1: Create a BigQuery client
	// The client automatically picks up Application Default Credentials.
	// ---------------------------------------------------------------------------
	client, err := bigquery.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("bigquery.NewClient: %v", err)
	}
	defer client.Close()

	// ---------------------------------------------------------------------------
	// EXERCISE 1a: Run a basic query and iterate results
	// ---------------------------------------------------------------------------
	runBasicQuery(ctx, client)

	// ---------------------------------------------------------------------------
	// EXERCISE 1b: Query with struct row binding
	// ---------------------------------------------------------------------------
	runQueryWithStructs(ctx, client)

	// ---------------------------------------------------------------------------
	// EXERCISE 1c: Inspect job metadata
	// ---------------------------------------------------------------------------
	inspectJobMetadata(ctx, client)
}

// ---------------------------------------------------------------------------
// Exercise 1a — Iterate over raw RowIterator values
// ---------------------------------------------------------------------------
func runBasicQuery(ctx context.Context, client *bigquery.Client) {
	query := client.Query(`
		SELECT
			word,
			SUM(word_count) AS total_count
		FROM
			` + "`bigquery-public-data.samples.shakespeare`" + `
		GROUP BY word
		ORDER BY total_count DESC
		LIMIT 10
	`)

	// TODO: Run the query
	// it, err := query.Read(ctx)
	it, err := query.Read(ctx)
	if err != nil {
		log.Fatalf("query.Read: %v", err)
	}

	fmt.Println("=== Top 10 most frequent words ===")
	for {
		var row WordCount
		// TODO: Call it.Next(&row) — returns iterator.Done when finished
		err := it.Next(&row)
		if err == iterator.Done {
			break
		}
		if err != nil {
			log.Fatalf("it.Next: %v", err)
		}
		fmt.Printf("  %-20s %8d\n", row.Word, row.TotalCount)
	}
}

// ---------------------------------------------------------------------------
// Exercise 1b — Use struct-based row binding for cleaner code
// ---------------------------------------------------------------------------
func runQueryWithStructs(ctx context.Context, client *bigquery.Client) {
	query := client.Query(`
		SELECT
			corpus,
			COUNT(DISTINCT word) AS unique_words,
			SUM(word_count)      AS total_words
		FROM ` + "`bigquery-public-data.samples.shakespeare`" + `
		GROUP BY corpus
		ORDER BY total_words DESC
		LIMIT 10
	`)

	it, err := query.Read(ctx)
	if err != nil {
		log.Fatalf("query.Read: %v", err)
	}

	fmt.Println("\n=== Words per Shakespeare work (top 10) ===")
	for {
		var row CorpusSummary
		err := it.Next(&row)
		if err == iterator.Done {
			break
		}
		if err != nil {
			log.Fatalf("it.Next: %v", err)
		}
		fmt.Printf("  %-40s unique=%6d  total=%8d\n",
			row.Corpus, row.UniqueWords, row.TotalWords)
	}
}

// ---------------------------------------------------------------------------
// Exercise 1c — Inspect job statistics
// ---------------------------------------------------------------------------
func inspectJobMetadata(ctx context.Context, client *bigquery.Client) {
	q := client.Query(`
		SELECT word, word_count
		FROM ` + "`bigquery-public-data.samples.shakespeare`" + `
		WHERE word = 'love'
		LIMIT 100
	`)

	// Run the query and get the Job object (not just the iterator)
	// TODO: Use q.Run(ctx) to get a *bigquery.Job
	job, err := q.Run(ctx)
	if err != nil {
		log.Fatalf("q.Run: %v", err)
	}

	// TODO: Wait for the job to complete using job.Wait(ctx)
	status, err := job.Wait(ctx)
	if err != nil {
		log.Fatalf("job.Wait: %v", err)
	}
	if err := status.Err(); err != nil {
		log.Fatalf("job failed: %v", err)
	}

	// TODO: Read job.LastStatus().Statistics to get bytes processed etc.
	stats := job.LastStatus().Statistics
	qStats := stats.Details.(*bigquery.QueryStatistics)

	fmt.Println("\n=== Job metadata ===")
	fmt.Printf("  Bytes processed : %d\n", qStats.TotalBytesProcessed)
	fmt.Printf("  Bytes billed    : %d\n", qStats.TotalBytesBilled)
	fmt.Printf("  Slot ms         : %d\n", qStats.SlotMillis)
	fmt.Printf("  Duration        : %v\n", time.Duration(stats.EndTime.Sub(stats.StartTime)))
}

// ---------------------------------------------------------------------------
// CHALLENGES
// ---------------------------------------------------------------------------
// 1. Add a goroutine-based producer: run 3 different queries concurrently
//    using goroutines and a WaitGroup. Print results as they arrive.
//
// 2. Modify runBasicQuery to accept a word length filter parameter
//    and use a parameterized query (query.Parameters field).
//
// 3. Add retries: if query.Read returns a transient error, retry up to 3 times
//    with exponential backoff using time.Sleep(2^attempt * time.Second).
