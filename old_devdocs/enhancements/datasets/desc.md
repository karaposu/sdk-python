# Bright Data Datasets API

## What are Datasets?

Datasets are **pre-collected, structured data repositories** maintained by Bright Data. Unlike web scrapers that collect data on-demand when you provide URLs, datasets contain already-scraped and regularly-updated data from various platforms.

Think of it this way:
- **Web Scrapers**: "Go scrape this specific LinkedIn profile URL for me now"
- **Datasets**: "Give me all LinkedIn profiles that match these criteria from your existing collection"

### Available Datasets

Each dataset has a unique ID and contains millions of pre-collected records:

| Dataset | ID | Size (approx) |
|---------|-----|---------------|
| LinkedIn Profiles | `gd_l1viktl72bvl7bjuj0` | 620M+ records |
| LinkedIn Companies | `gd_l1vikfnt1wgvvqz95w` | - |
| Amazon Products | `gd_l7q7dkf244hwjntr0` | - |
| Crunchbase Companies | `gd_l1vijqt9jfj7olije` | 2.3M+ records |
| Instagram Profiles | `gd_l1vikfch901nx3by4` | 620M+ records |

## How Datasets Work

### 1. List Available Datasets
```python
GET /datasets/list
```
Returns all datasets you can access with their IDs, names, and record counts.

### 2. Get Dataset Metadata
```python
GET /datasets/{dataset_id}/metadata
```
Returns the schema: field names, types, descriptions, and whether they're required.

### 3. Filter & Create Snapshot
```python
POST /datasets/filter
```
Apply filters to create a snapshot of matching records. For example:
- "All LinkedIn profiles where `industry = 'Technology'`"
- "All Amazon products where `rating > 4.5`"

### 4. Download or Deliver Snapshot
```python
GET /datasets/snapshots/{id}/download   # Direct download
POST /datasets/snapshots/{id}/deliver   # Deliver to S3, Azure, Snowflake, etc.
```

## How Datasets Differ from Web Scrapers

| Aspect | Web Scrapers | Datasets |
|--------|--------------|----------|
| **Data Source** | Fresh scrape on-demand | Pre-collected, regularly updated |
| **Input** | URLs or search parameters | Filter criteria |
| **Speed** | Slower (real-time scraping) | Faster (querying existing data) |
| **Use Case** | Specific targets you know | Bulk data, discovery, filtering |
| **Freshness** | Real-time | Updated periodically |
| **Volume** | Per-request limits | Millions of records |
| **Cost Model** | Per-scrape | Per-record in snapshot |

### When to Use Web Scrapers
- You have specific URLs to scrape
- You need real-time, fresh data
- You're monitoring specific profiles/products
- You need data not in datasets

### When to Use Datasets
- You need bulk data (e.g., "all tech companies in SF")
- You're doing market research or analysis
- You want to filter by attributes (industry, location, size)
- Speed matters more than absolute freshness
- You need to deliver data to a data warehouse

## SDK Integration Approach

The current SDK has web scrapers:
```python
# Web Scraper approach - provide URLs
async with BrightDataClient() as client:
    result = await client.scraper.linkedin.profiles(
        urls=["https://linkedin.com/in/satyanadella"]
    )
```

Datasets would work differently:
```python
# Dataset approach - filter existing data
async with BrightDataClient() as client:
    # List available datasets
    datasets = await client.datasets.list()

    # Get LinkedIn profiles dataset metadata
    metadata = await client.datasets.metadata("gd_l1viktl72bvl7bjuj0")

    # Filter and create snapshot
    snapshot = await client.datasets.filter(
        dataset_id="gd_l1viktl72bvl7bjuj0",
        filter={
            "operator": "and",
            "filters": [
                {"name": "industry", "operator": "=", "value": "Technology"},
                {"name": "followers", "operator": ">", "value": 10000}
            ]
        },
        records_limit=1000
    )

    # Download snapshot content
    data = await client.datasets.download(snapshot.id, format="jsonl")

    # Or deliver to S3
    await client.datasets.deliver(
        snapshot_id=snapshot.id,
        destination={
            "type": "s3",
            "bucket": "my-bucket",
            "credentials": {...}
        }
    )
```

## Key Differences Summary

1. **Scrapers pull specific data** - you say "get this URL"
2. **Datasets filter existing data** - you say "find records matching X"

3. **Scrapers are real-time** - data is scraped when you request
4. **Datasets are pre-collected** - data already exists, you query it

5. **Scrapers return small results** - single profiles, products
6. **Datasets return bulk results** - thousands/millions of records

7. **Scrapers poll for completion** - wait for scrape job
8. **Datasets poll for snapshot** - wait for filter/snapshot job
