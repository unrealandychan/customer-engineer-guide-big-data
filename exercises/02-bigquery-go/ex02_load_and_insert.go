// Exercise 02 — Load Data from GCS and Insert Rows (Go)
// -------------------------------------------------------
// Goal:
//   - Create a dataset and table programmatically in Go
//   - Load a GCS file into BigQuery
//   - Insert rows using the Put method (streaming)
//   - Use struct tags to map Go structs to BigQuery rows
//
// Run:
//   go run ex02_load_and_insert.go

package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"cloud.google.com/go/bigquery"
)

// ---------------------------------------------------------------------------
// CONFIG
// ---------------------------------------------------------------------------
var (
	projectID = os.Getenv("GOOGLE_CLOUD_PROJECT")
	datasetID = "bq_go_exercises"
	tableID   = "orders"
	bucketName = os.Getenv("GCS_BUCKET") // set to your GCS bucket name
)

// ---------------------------------------------------------------------------
// Order — Go struct that maps to a BigQuery table row
// Use `bigquery:"column_name"` tags to control column mapping
// ---------------------------------------------------------------------------
type Order struct {
	OrderID    string    `bigquery:"order_id"`
	CustomerID string    `bigquery:"customer_id"`
	Product    string    `bigquery:"product"`
	Amount     float64   `bigquery:"amount"`
	OrderDate  time.Time `bigquery:"order_date"`
	Status     string    `bigquery:"status"`
}

// ---------------------------------------------------------------------------
// Implement bigquery.ValueSaver for custom row saving (optional, advanced)
// ---------------------------------------------------------------------------

func main() {
	ctx := context.Background()

	if projectID == "" {
		log.Fatal("GOOGLE_CLOUD_PROJECT not set")
	}

	client, err := bigquery.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("bigquery.NewClient: %v", err)
	}
	defer client.Close()

	// Run exercises in sequence
	createDatasetAndTable(ctx, client)
	insertRowsStreaming(ctx, client)
	loadFromGCS(ctx, client)
}

// ---------------------------------------------------------------------------
// EXERCISE 2a: Create a dataset and table
// ---------------------------------------------------------------------------
func createDatasetAndTable(ctx context.Context, client *bigquery.Client) {
	// Create dataset
	dataset := client.Dataset(datasetID)
	meta := &bigquery.DatasetMetadata{
		Location: "US",
	}
	// TODO: Call dataset.Create(ctx, meta) — ignore AlreadyExists error
	if err := dataset.Create(ctx, meta); err != nil {
		// Check if it already exists — that's fine
		fmt.Printf("Dataset %s: already exists or created\n", datasetID)
	} else {
		fmt.Printf("Dataset %s created\n", datasetID)
	}

	// Define schema using bigquery.InferSchema from our Order struct
	// TODO: Use bigquery.InferSchema(Order{}) to derive schema automatically
	schema, err := bigquery.InferSchema(Order{})
	if err != nil {
		log.Fatalf("InferSchema: %v", err)
	}

	// Create table with the inferred schema
	tableRef := dataset.Table(tableID)
	tableMetadata := &bigquery.TableMetadata{
		Schema: schema,
		// Partition by order_date (DAY granularity)
		TimePartitioning: &bigquery.TimePartitioning{
			Type:  bigquery.DayPartitioningType,
			Field: "order_date",
		},
		// Cluster by customer_id and status
		Clustering: &bigquery.Clustering{
			Fields: []string{"customer_id", "status"},
		},
	}

	// TODO: Call tableRef.Create(ctx, tableMetadata)
	if err := tableRef.Create(ctx, tableMetadata); err != nil {
		fmt.Printf("Table %s: already exists or created\n", tableID)
	} else {
		fmt.Printf("Table %s.%s created with partition + clustering\n", datasetID, tableID)
	}
}

// ---------------------------------------------------------------------------
// EXERCISE 2b: Stream rows using the Inserter (legacy streaming API)
// ---------------------------------------------------------------------------
func insertRowsStreaming(ctx context.Context, client *bigquery.Client) {
	tableRef := client.Dataset(datasetID).Table(tableID)

	// TODO: Create an Inserter from the table reference
	// inserter := tableRef.Inserter()
	inserter := tableRef.Inserter()

	// Sample rows to insert
	rows := []*Order{
		{
			OrderID:    "ord-001",
			CustomerID: "cust-a",
			Product:    "Widget Pro",
			Amount:     149.99,
			OrderDate:  time.Date(2025, 1, 15, 0, 0, 0, 0, time.UTC),
			Status:     "completed",
		},
		{
			OrderID:    "ord-002",
			CustomerID: "cust-b",
			Product:    "Widget Lite",
			Amount:     49.99,
			OrderDate:  time.Date(2025, 1, 16, 0, 0, 0, 0, time.UTC),
			Status:     "pending",
		},
		{
			OrderID:    "ord-003",
			CustomerID: "cust-a",
			Product:    "Widget Ultra",
			Amount:     299.00,
			OrderDate:  time.Date(2025, 1, 17, 0, 0, 0, 0, time.UTC),
			Status:     "completed",
		},
	}

	// TODO: Call inserter.Put(ctx, rows) to stream the rows
	// inserter.Put accepts a slice of structs or ValueSavers
	if err := inserter.Put(ctx, rows); err != nil {
		log.Fatalf("inserter.Put: %v", err)
	}
	fmt.Printf("Streamed %d rows into %s.%s\n", len(rows), datasetID, tableID)
}

// ---------------------------------------------------------------------------
// EXERCISE 2c: Load a file from GCS into BigQuery
// ---------------------------------------------------------------------------
func loadFromGCS(ctx context.Context, client *bigquery.Client) {
	if bucketName == "" {
		fmt.Println("GCS_BUCKET not set — skipping GCS load exercise")
		return
	}

	gcsRef := bigquery.NewGCSReference(
		fmt.Sprintf("gs://%s/exercises/orders.csv", bucketName),
	)
	gcsRef.SourceFormat    = bigquery.CSV
	gcsRef.SkipLeadingRows = 1
	gcsRef.AutoDetect      = true

	tableRef := client.Dataset(datasetID).Table(tableID + "_from_gcs")

	// TODO: Create a LoadConfig and set the Dst and Src fields
	loader := tableRef.LoaderFrom(gcsRef)
	loader.WriteDisposition = bigquery.WriteTruncate

	// TODO: Call loader.Run(ctx) to start the load job
	job, err := loader.Run(ctx)
	if err != nil {
		log.Fatalf("loader.Run: %v", err)
	}

	// TODO: Poll until the job is complete using job.Wait(ctx)
	status, err := job.Wait(ctx)
	if err != nil {
		log.Fatalf("job.Wait: %v", err)
	}
	if err := status.Err(); err != nil {
		log.Fatalf("load job failed: %v", err)
	}

	fmt.Printf("Load job complete. Table: %s.%s_from_gcs\n", datasetID, tableID)
}

// ---------------------------------------------------------------------------
// CHALLENGES
// ---------------------------------------------------------------------------
// 1. Add an InsertID to each Order (use OrderID) to enable deduplication
//    in the streaming API. See bigquery.StructSaverForSchema with InsertID field.
//
// 2. Use bigquery.Schema directly instead of InferSchema and define
//    the schema fields manually.
//
// 3. Create a goroutine that continuously generates random Order rows
//    and streams them every 2 seconds for 30 seconds.
//    Track total rows inserted using an atomic counter.
