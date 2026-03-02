# Scraper Studio - SDK Enhancement Overview

## What is Scraper Studio?

Bright Data's platform for building custom web scrapers. Users create scrapers through:
- **AI Agent** - No-code: enter a URL, chat with AI to define data requirements, get a working scraper
- **IDE** - Browser-based JavaScript IDE with interaction code + parser code
- **Templates** - Pre-built starting points for common websites

Once created, each scraper gets a **collector ID** and can be triggered programmatically via API.

## What the SDK Should Support

The SDK should wrap the **Scraper Studio API** - the programmatic interface for triggering and managing scrapers. The AI builder itself is UI-only (no API).

### Endpoints to Implement

| # | Operation | Method | Endpoint | Priority |
|---|-----------|--------|----------|----------|
| 1 | Trigger batch collection | `POST` | `/dca/trigger` | High |
| 2 | Get batch data | `GET` | `/dca/dataset` | High |
| 3 | Trigger real-time async | `POST` | `/dca/trigger_immediate` | High |
| 4 | Get real-time result | `GET` | `/dca/get_result` | High |
| 5 | Trigger real-time sync | `POST` | `/dca/crawl` | High |
| 6 | Get job status | `GET` | `/dca/log/{job_id}` | Medium |

### Access Pattern

```python
client.scraper_studio.trigger(...)           # Batch
client.scraper_studio.get_batch_data(...)    # Batch results
client.scraper_studio.trigger_immediate(...) # Real-time async
client.scraper_studio.get_result(...)        # Real-time async results
client.scraper_studio.crawl(...)             # Real-time sync
client.scraper_studio.get_job_status(...)    # Job info
```

### Key Design Decisions

1. **Namespace**: `client.scraper_studio` - separate from `client.scrape` (Web Scraper API) and `client.datasets`
2. **Polling**: `get_batch_data()` and `get_result()` should support auto-polling with configurable timeout/interval
3. **Input flexibility**: Input is `Dict[str, Any]` or `List[Dict[str, Any]]` - schema varies per scraper
4. **Sync client**: All methods available via `SyncBrightDataClient` as well

## Relationship to Existing SDK Features

| Feature | What it does | API base |
|---------|-------------|----------|
| `client.scrape.<platform>` | Pre-built scrapers (Web Scraper API) | `/datasets/v3/trigger` |
| `client.datasets.<dataset>` | Pre-collected datasets | `/datasets/filter` |
| `client.scraper_studio` | **User's custom scrapers** | `/dca/*` |
| `client.scrape_url()` | Raw URL scraping (Web Unlocker) | `/unblocker/req` |

## Files Reference

- `api_reference.md` - Full API endpoint documentation with request/response examples
- `docs/a.md` - IDE interface reference + all interaction/parser functions
- `docs/c.md` - Self-Healing Tool (AI code refactor)
- `docs/d.md` - Collection initiation & delivery options
- `docs/e.md` - Dashboard features & statistics
- `docs/f.md` - Best practices for scraper code
- `docs/g.md` - AI Agent (no-code scraper builder)
