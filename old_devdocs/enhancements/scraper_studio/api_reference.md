# Scraper Studio API Reference

> Complete API reference for Bright Data's Scraper Studio.
> Source: https://docs.brightdata.com/api-reference/scraper-studio-api/

## Overview

Scraper Studio lets you build custom web scrapers (via AI agent, IDE, or templates) and run them at scale. Once a scraper is created, it gets a **collector ID** (e.g., `c_m9im5n7v82p2y35la`) that you use to trigger it programmatically.

### Authentication

All endpoints use Bearer token authentication:

```
Authorization: Bearer YOUR_API_KEY
```

Get your API key from: https://brightdata.com/cp/setting/users

### Base URL

```
https://api.brightdata.com
```

---

## API Workflows

| Workflow | Trigger Endpoint | Data Retrieval | Use Case |
|----------|-----------------|----------------|----------|
| Batch + Polling | `POST /dca/trigger` | `GET /dca/dataset` | Large-scale, many URLs |
| Real-time Async | `POST /dca/trigger_immediate` | `GET /dca/get_result` | Single URL, non-blocking |
| Real-time Sync | `POST /dca/crawl` | Response body (direct) | Single URL, blocking |

---

## Endpoints

### 1. Trigger Batch Collection

Starts a batch scraping job with one or more inputs. Returns immediately with a `collection_id`.

```
POST /dca/trigger
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collector` | string | Yes | Scraper collector ID |
| `queue_next` | integer | No | Queue job if scraper is busy (default: 1) |
| `queue` | string | No | Schedule after current job completes |
| `confirm_cancel` | integer | No | Cancel running job and start new one (1) |
| `no_downloads` | integer | No | Disable media file downloads (1) |
| `deadline` | string | No | Job termination time (e.g., `30m`, `2h`) |
| `version` | string | No | `dev` for development version |
| `name` | string | No | Human-readable batch name |

**Request Body** (JSON array of input objects):

```json
[
  {"url": "https://example.com/product/1"},
  {"url": "https://example.com/product/2"}
]
```

**Response** `200 OK`:

```json
{
  "collection_id": "c_abc123",
  "start_eta": "2025-01-07T13:26:22.702Z"
}
```

---

### 2. Receive Batch Data

Retrieves results from a completed batch job. Returns `202` if still processing.

```
GET /dca/dataset
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dataset_id` | string | Yes | The collection_id from trigger response |

**Response** `200 OK` (ready):

```json
[
  {
    "Title": "Product Name",
    "Price": "$29.99",
    "Image": "https://example.com/img.png",
    "input": {"url": "https://example.com/product/1"}
  }
]
```

**Response** `202 Accepted` (still processing):

```json
{
  "status": "building",
  "message": "Dataset is not ready yet, try again in 30s"
}
```

> Data is available for download for **16 days** after collection.

---

### 3. Trigger Real-time Async

Triggers a single-input scrape and returns a `response_id` for polling.

```
POST /dca/trigger_immediate
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collector` | string | Yes | Scraper collector ID |
| `version` | string | No | `dev` for development version |
| `name` | string | No | Human-readable identifier |

**Request Body** (single JSON object):

```json
{
  "url": "https://example.com/product/1"
}
```

**Response** `200 OK`:

```json
{
  "response_id": "resp_xyz789"
}
```

---

### 4. Receive Real-time Data

Polls for results from a real-time async job.

```
GET /dca/get_result
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `response_id` | string | Yes | From trigger_immediate response |

**Response** `200 OK`:

```json
[
  {
    "Title": "Product Name",
    "Price": "$29.99"
  }
]
```

> Data is available for **16 days** after collection.

---

### 5. Trigger Real-time Sync

Triggers a scrape and waits for the result in the same request. Blocks until data is ready or timeout.

```
POST /dca/crawl
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `collector` | string | Yes | Scraper collector ID |
| `timeout` | string | Yes | Wait duration, 25s-50s (e.g., `50s`) |
| `version` | string | No | `dev` for development version |
| `name` | string | No | Human-readable identifier |

**Request Body** (single JSON object):

```json
{
  "url": "https://example.com/product/1"
}
```

**Response** `200 OK` (data ready within timeout):

```json
[
  {
    "Title": "Product Name",
    "Price": "$29.99"
  }
]
```

**Response** `202 Accepted` (timed out, use polling):

```json
{
  "response_id": "resp_xyz789"
}
```

> If `202` is returned, poll with `GET /dca/get_result?response_id=...`

---

### 6. Get Job Status

Retrieves metadata and status of a scraping job.

```
GET /dca/log/{job_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string | Yes | Job ID (e.g., `j_ma13y9ay1piehrso8r`) |

**Response** `200 OK`:

```json
{
  "Id": "j_ma13y9ay1piehrso8r",
  "Status": "done",
  "Collector": "c_m9im5n7v82p2y35la",
  "Inputs": 1,
  "Lines": 60,
  "Fails": 0,
  "Pages": 1,
  "Pages_left": 0,
  "Success": 1,
  "Success_rate": 1,
  "created": "2025-04-28T13:22:16.857Z",
  "started": "2025-04-28T13:22:17.502Z",
  "finished": "2025-04-28T13:23:28.961Z",
  "Job_time": 71459,
  "Queue_time": 645,
  "trigger": "user@example.com"
}
```

**Status values:** `queued`, `running`, `done`, `failed`, `cancelled`

---

## Rate Limits

| Method | Limit |
|--------|-------|
| Batch | Up to 1,000 concurrent jobs per collector |
| Real-time | No limit |

---

## Input Format

Input objects vary by scraper. The most common field is `url`, but scrapers can define custom input parameters (e.g., `keyword`, `location`, `page`). Check the scraper's input schema in the IDE.

```json
// URL-based scraper
{"url": "https://example.com/product/123"}

// Search-based scraper
{"keyword": "laptop", "location": "US", "page": 1}
```

---

## SDK Integration Notes

### Proposed Python SDK Interface

```python
# Batch workflow
async with BrightDataClient() as client:
    # Trigger batch
    job = await client.scraper_studio.trigger(
        collector="c_abc123",
        inputs=[
            {"url": "https://example.com/product/1"},
            {"url": "https://example.com/product/2"},
        ]
    )
    print(job.collection_id)  # "c_abc123"

    # Poll for results
    data = await client.scraper_studio.get_batch_data(
        dataset_id=job.collection_id,
        timeout=300,
        poll_interval=10
    )

# Real-time sync workflow
async with BrightDataClient() as client:
    data = await client.scraper_studio.crawl(
        collector="c_abc123",
        input={"url": "https://example.com/product/1"},
        timeout=50
    )

# Real-time async workflow
async with BrightDataClient() as client:
    response = await client.scraper_studio.trigger_immediate(
        collector="c_abc123",
        input={"url": "https://example.com/product/1"}
    )
    data = await client.scraper_studio.get_result(
        response_id=response.response_id
    )

# Job status
async with BrightDataClient() as client:
    status = await client.scraper_studio.get_job_status(job_id="j_abc123")
    print(status.Status, status.Success_rate)
```
