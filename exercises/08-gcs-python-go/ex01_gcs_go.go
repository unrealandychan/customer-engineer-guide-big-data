// Exercise 01 — Cloud Storage: Upload, Download, List, Signed URLs (Go)
// -------------------------------------------------------------------
// Goal:
//   - Upload bytes and files to GCS
//   - Download blobs (streaming and buffered)
//   - List objects with prefix filtering
//   - Generate V4 signed URLs
//   - Copy and delete objects
//   - Set and read object metadata
//
// Interview relevance:
//   Same as the Python version — but Go is ideal for high-throughput
//   ingestion services that write to GCS (e.g., microservice that archives
//   events to GCS before loading to BigQuery).
//
// Setup:
//   go mod tidy
//   export GOOGLE_CLOUD_PROJECT=your-project-id
//   export BUCKET_NAME=your-bucket-name
//
// Run:
//   go run ex01_gcs_go.go

package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"cloud.google.com/go/storage"
	"google.golang.org/api/iterator"
)

// ---------------------------------------------------------------------------
// Client helpers
// ---------------------------------------------------------------------------

func newStorageClient(ctx context.Context) *storage.Client {
	client, err := storage.NewClient(ctx)
	if err != nil {
		log.Fatalf("storage.NewClient: %v", err)
	}
	return client
}

func bucketName() string {
	name := os.Getenv("BUCKET_NAME")
	if name == "" {
		log.Fatal("BUCKET_NAME environment variable not set")
	}
	return name
}

// ---------------------------------------------------------------------------
// EXERCISE 1: Upload
// ---------------------------------------------------------------------------

// UploadBytes uploads in-memory data to a GCS object.
func UploadBytes(ctx context.Context, client *storage.Client, bucket, objectName string, data []byte, contentType string) error {
	bkt := client.Bucket(bucket)
	obj := bkt.Object(objectName)

	// TODO: Open a writer and copy data into it
	w := obj.NewWriter(ctx)
	w.ContentType = contentType

	if _, err := io.Copy(w, bytes.NewReader(data)); err != nil {
		return fmt.Errorf("io.Copy: %w", err)
	}

	// IMPORTANT: always Close the writer — this finalises the upload
	if err := w.Close(); err != nil {
		return fmt.Errorf("writer.Close: %w", err)
	}

	fmt.Printf("Uploaded %d bytes → gs://%s/%s\n", len(data), bucket, objectName)
	return nil
}

// UploadFile reads a local file and uploads it to GCS.
func UploadFile(ctx context.Context, client *storage.Client, bucket, objectName, localPath string) error {
	f, err := os.Open(localPath)
	if err != nil {
		return fmt.Errorf("os.Open: %w", err)
	}
	defer f.Close()

	obj := client.Bucket(bucket).Object(objectName)
	w := obj.NewWriter(ctx)

	// Detect content type from file extension
	buf := make([]byte, 512)
	n, _ := f.Read(buf)
	w.ContentType = http.DetectContentType(buf[:n])
	f.Seek(0, io.SeekStart) // Rewind after reading for content type detection

	if _, err := io.Copy(w, f); err != nil {
		return fmt.Errorf("io.Copy: %w", err)
	}
	if err := w.Close(); err != nil {
		return fmt.Errorf("writer.Close: %w", err)
	}

	fmt.Printf("Uploaded file %s → gs://%s/%s\n", localPath, bucket, objectName)
	return nil
}

// ---------------------------------------------------------------------------
// EXERCISE 2: Download
// ---------------------------------------------------------------------------

// DownloadToMemory downloads a GCS object into a byte slice.
func DownloadToMemory(ctx context.Context, client *storage.Client, bucket, objectName string) ([]byte, error) {
	obj := client.Bucket(bucket).Object(objectName)

	// TODO: Use obj.NewReader(ctx) to open a streaming reader
	r, err := obj.NewReader(ctx)
	if err != nil {
		return nil, fmt.Errorf("obj.NewReader: %w", err)
	}
	defer r.Close()

	data, err := io.ReadAll(r)
	if err != nil {
		return nil, fmt.Errorf("io.ReadAll: %w", err)
	}

	fmt.Printf("Downloaded %d bytes from gs://%s/%s\n", len(data), bucket, objectName)
	return data, nil
}

// StreamDownload streams a large GCS object chunk by chunk.
// Returns a reader; the caller is responsible for closing it.
func StreamDownload(ctx context.Context, client *storage.Client, bucket, objectName string) (io.ReadCloser, error) {
	obj := client.Bucket(bucket).Object(objectName)
	r, err := obj.NewReader(ctx)
	if err != nil {
		return nil, fmt.Errorf("obj.NewReader: %w", err)
	}
	fmt.Printf("Opened streaming reader for gs://%s/%s (size: %d)\n",
		bucket, objectName, r.Attrs.Size)
	return r, nil
}

// DownloadToFile downloads a GCS object and writes it to a local file.
func DownloadToFile(ctx context.Context, client *storage.Client, bucket, objectName, localPath string) error {
	r, err := StreamDownload(ctx, client, bucket, objectName)
	if err != nil {
		return err
	}
	defer r.Close()

	f, err := os.Create(localPath)
	if err != nil {
		return fmt.Errorf("os.Create: %w", err)
	}
	defer f.Close()

	written, err := io.Copy(f, r)
	if err != nil {
		return fmt.Errorf("io.Copy: %w", err)
	}

	fmt.Printf("Downloaded %d bytes → %s\n", written, localPath)
	return nil
}

// ---------------------------------------------------------------------------
// EXERCISE 3: List objects
// ---------------------------------------------------------------------------

// BlobInfo holds essential metadata about a GCS object.
type BlobInfo struct {
	Name        string
	SizeBytes   int64
	ContentType string
	Updated     time.Time
	StorageClass string
}

// ListObjects lists all objects in a bucket with an optional prefix.
// delimiter="" lists all objects recursively.
// delimiter="/" simulates directory listing at the prefix level.
func ListObjects(ctx context.Context, client *storage.Client, bucket, prefix, delimiter string) ([]BlobInfo, error) {
	query := &storage.Query{
		Prefix:    prefix,
		Delimiter: delimiter,
	}

	var results []BlobInfo
	it := client.Bucket(bucket).Objects(ctx, query)

	for {
		attrs, err := it.Next()
		if err == iterator.Done {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("iterator.Next: %w", err)
		}

		if attrs.Name == "" {
			// This is a "virtual directory" prefix entry (when delimiter is set)
			fmt.Printf("  Sub-prefix (folder): %s\n", attrs.Prefix)
			continue
		}

		results = append(results, BlobInfo{
			Name:         attrs.Name,
			SizeBytes:    attrs.Size,
			ContentType:  attrs.ContentType,
			Updated:      attrs.Updated,
			StorageClass: attrs.StorageClass,
		})
	}

	fmt.Printf("Found %d objects with prefix=%q\n", len(results), prefix)
	return results, nil
}

// ---------------------------------------------------------------------------
// EXERCISE 4: Copy and delete
// ---------------------------------------------------------------------------

// CopyObject performs a server-side copy within GCS.
func CopyObject(ctx context.Context, client *storage.Client,
	srcBucket, srcObject, dstBucket, dstObject string) error {

	src := client.Bucket(srcBucket).Object(srcObject)
	dst := client.Bucket(dstBucket).Object(dstObject)

	// TODO: Use dst.CopierFrom(src).Run(ctx)
	if _, err := dst.CopierFrom(src).Run(ctx); err != nil {
		return fmt.Errorf("CopierFrom.Run: %w", err)
	}

	fmt.Printf("Copied gs://%s/%s → gs://%s/%s\n", srcBucket, srcObject, dstBucket, dstObject)
	return nil
}

// DeleteObject deletes a single GCS object.
func DeleteObject(ctx context.Context, client *storage.Client, bucket, objectName string) error {
	obj := client.Bucket(bucket).Object(objectName)

	// TODO: Use obj.Delete(ctx)
	if err := obj.Delete(ctx); err != nil {
		return fmt.Errorf("obj.Delete: %w", err)
	}

	fmt.Printf("Deleted gs://%s/%s\n", bucket, objectName)
	return nil
}

// DeleteObjectsByPrefix deletes all objects with a given prefix.
func DeleteObjectsByPrefix(ctx context.Context, client *storage.Client, bucket, prefix string) (int, error) {
	objects, err := ListObjects(ctx, client, bucket, prefix, "")
	if err != nil {
		return 0, err
	}

	count := 0
	for _, obj := range objects {
		if err := DeleteObject(ctx, client, bucket, obj.Name); err != nil {
			log.Printf("Failed to delete %s: %v", obj.Name, err)
			continue
		}
		count++
	}
	return count, nil
}

// ---------------------------------------------------------------------------
// EXERCISE 5: Object metadata
// ---------------------------------------------------------------------------

// SetObjectMetadata sets custom metadata on a GCS object.
func SetObjectMetadata(ctx context.Context, client *storage.Client,
	bucket, objectName string, metadata map[string]string) error {

	obj := client.Bucket(bucket).Object(objectName)

	// TODO: Use obj.Update(ctx, storage.ObjectAttrsToUpdate{Metadata: metadata})
	_, err := obj.Update(ctx, storage.ObjectAttrsToUpdate{
		Metadata: metadata,
	})
	if err != nil {
		return fmt.Errorf("obj.Update: %w", err)
	}

	fmt.Printf("Set metadata on gs://%s/%s: %v\n", bucket, objectName, metadata)
	return nil
}

// GetObjectAttrs returns all attributes (metadata) for a GCS object.
func GetObjectAttrs(ctx context.Context, client *storage.Client, bucket, objectName string) (*storage.ObjectAttrs, error) {
	obj := client.Bucket(bucket).Object(objectName)

	// TODO: Use obj.Attrs(ctx)
	attrs, err := obj.Attrs(ctx)
	if err != nil {
		return nil, fmt.Errorf("obj.Attrs: %w", err)
	}

	return attrs, nil
}

// ---------------------------------------------------------------------------
// EXERCISE 6: Signed URLs
// ---------------------------------------------------------------------------

// GenerateSignedURLV4 creates a time-limited V4 signed URL for unauthenticated access.
// Requires the Google credentials to have signing permission (service account key or IAM).
func GenerateSignedURLV4(ctx context.Context, client *storage.Client,
	bucket, objectName string, expiration time.Duration, method string) (string, error) {

	opts := &storage.SignedURLOptions{
		Scheme:  storage.SigningSchemeV4,
		Method:  method,
		Expires: time.Now().Add(expiration),
	}

	// TODO: Use client.Bucket(bucket).SignedURL(objectName, opts)
	url, err := client.Bucket(bucket).SignedURL(objectName, opts)
	if err != nil {
		return "", fmt.Errorf("SignedURL: %w", err)
	}

	fmt.Printf("Signed URL (%s, expires %v): %s...\n", method, expiration, url[:min(80, len(url))])
	return url, nil
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

func main() {
	ctx := context.Background()
	client := newStorageClient(ctx)
	defer client.Close()

	bkt := bucketName()

	// 1. Upload
	payload := []byte(`{"message": "Hello from Go!", "timestamp": "` + time.Now().Format(time.RFC3339) + `"}`)
	if err := UploadBytes(ctx, client, bkt, "exercises-go/hello.json", payload, "application/json"); err != nil {
		log.Printf("Upload error: %v", err)
	}

	// 2. Download
	data, err := DownloadToMemory(ctx, client, bkt, "exercises-go/hello.json")
	if err != nil {
		log.Printf("Download error: %v", err)
	} else {
		var obj map[string]interface{}
		json.Unmarshal(data, &obj)
		fmt.Printf("Downloaded: %v\n", obj)
	}

	// 3. List
	blobs, err := ListObjects(ctx, client, bkt, "exercises-go/", "")
	if err != nil {
		log.Printf("List error: %v", err)
	} else {
		for _, b := range blobs {
			fmt.Printf("  - %s (%d bytes)\n", b.Name, b.SizeBytes)
		}
	}

	// 4. Metadata
	if err := SetObjectMetadata(ctx, client, bkt, "exercises-go/hello.json",
		map[string]string{"owner": "go-exercise", "env": "dev"}); err != nil {
		log.Printf("Metadata error: %v", err)
	}

	attrs, err := GetObjectAttrs(ctx, client, bkt, "exercises-go/hello.json")
	if err != nil {
		log.Printf("GetAttrs error: %v", err)
	} else {
		fmt.Printf("Attrs: size=%d, contentType=%s, metadata=%v\n",
			attrs.Size, attrs.ContentType, attrs.Metadata)
	}

	// 5. Copy
	if err := CopyObject(ctx, client, bkt, "exercises-go/hello.json",
		bkt, "exercises-go/hello-copy.json"); err != nil {
		log.Printf("Copy error: %v", err)
	}

	// 6. Delete
	if err := DeleteObject(ctx, client, bkt, "exercises-go/hello-copy.json"); err != nil {
		log.Printf("Delete error: %v", err)
	}

	n, err := DeleteObjectsByPrefix(ctx, client, bkt, "exercises-go/")
	if err != nil {
		log.Printf("DeleteByPrefix error: %v", err)
	} else {
		fmt.Printf("Cleaned up %d objects\n", n)
	}
}

// ---------------------------------------------------------------------------
// CHALLENGES
// ---------------------------------------------------------------------------
// 1. Add a function that uploads a large file using a parallel composite upload:
//    Use storage.Writer with ChunkSize set to 16 MiB and upload concurrently.
//
// 2. Implement object versioning:
//    - Enable versioning on a bucket via BucketHandle.Update(ctx, BucketAttrsToUpdate{VersioningEnabled: true})
//    - Upload the same object twice
//    - List all generations of the object using Query{Versions: true}
//    - Download a specific generation by: obj.Generation(genID).NewReader(ctx)
//
// 3. Implement a "directory sync" function:
//    SyncDir(ctx, client, bucket, prefix, localDir) that:
//    - Lists objects under prefix
//    - Downloads only objects newer than the local file modification time
//
// 4. Add retry logic using google.golang.org/api/option WithRetry:
//    client, _ = storage.NewClient(ctx, option.WithRetryConfig(&retryConfig))
