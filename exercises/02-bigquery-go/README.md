# Category 02 — BigQuery (Go)

## What you will practice

| File                    | Topics                                                       |
|-------------------------|--------------------------------------------------------------|
| `ex01_run_query.go`     | Execute queries, bind rows to structs, inspect job stats     |
| `ex02_load_and_insert.go`| Load from GCS, streaming insert, partitioned table creation |

---

## Setup

```bash
cd exercises/02-bigquery-go
go mod tidy
export GOOGLE_CLOUD_PROJECT=your-project-id
go run ex01_run_query.go
```

---

## Key Go BigQuery Patterns

```go
// 1. Create client
client, _ := bigquery.NewClient(ctx, projectID)
defer client.Close()

// 2. Run a query
q := client.Query("SELECT ...")
it, _ := q.Read(ctx)

// 3. Bind rows to a struct
type Row struct {
    Name  string  `bigquery:"name"`
    Count int64   `bigquery:"count"`
}
var row Row
it.Next(&row)

// 4. Stream insert
inserter := client.Dataset("ds").Table("t").Inserter()
inserter.Put(ctx, rows)
```

---

## Interview One-Liner

**Why use Go for BigQuery over Python?**
Go's concurrency model (goroutines) makes it ideal for high-throughput streaming insert services that need to publish thousands of events per second with low latency and minimal memory footprint.
