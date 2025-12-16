# Bright Data Python SDK

The official Python SDK for [Bright Data](https://brightdata.com) APIs. Use it to scrape any website, get SERP results, bypassing bot detection and CAPTCHAs.

[![Tests](https://img.shields.io/badge/tests-502%2B%20passing-brightgreen)](https://github.com/brightdata/sdk-python)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code Quality](https://img.shields.io/badge/quality-enterprise--grade-gold)](https://github.com/brightdata/sdk-python)
[![Notebooks](https://img.shields.io/badge/jupyter-5%20notebooks-orange)](notebooks/)

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
  - [Generic Web Scraping](#generic-web-scraping)
  - [Search Engines (SERP)](#search-engines-serp)
  - [Amazon](#amazon)
  - [LinkedIn](#linkedin)
  - [Social Media](#social-media)
- [Async Usage](#async-usage)
- [Using Dataclass Payloads](#using-dataclass-payloads)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Installation

```bash
pip install brightdata-sdk
```

## Configuration

1. Get your API Token from the [Bright Data Control Panel](https://brightdata.com/cp/api_keys).
2. Set it as an environment variable:

```bash
export BRIGHTDATA_API_TOKEN="your_api_token_here"
```

## Quick Start

This SDK is **async-native** for maximum performance. Sync wrappers are provided for convenience and simpler use cases.

### Synchronous (Simple)
```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient() as client:
    result = client.scrape_url("https://example.com")
    print(result.data)
```

### Asynchronous (High Performance)
```python
import asyncio
from brightdata import BrightDataClient

async def main():

    
    async with BrightDataClient() as client:
        result = await client.scrape_url("https://example.com")
        print(result.data)

asyncio.run(main())
```

## Usage Examples

### Generic Web Scraping

Scrape any URL with automatic unlocking.

**Sync:**
```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient() as client:
    result = client.scrape_url("https://example.com")
    print(result.data)
```

**Async:**
```python
async with BrightDataClient() as client:
    result = await client.scrape_url("https://example.com")
    print(result.data)
```

### Search Engines (SERP)

**Google Search**
```python
# Sync
with SyncBrightDataClient() as client:
    result = client.search.google(
        query="python scraping",
        location="United States",
        num_results=10
    )
    for item in result.data:
        print(item)

# Async
async with BrightDataClient() as client:
    result = await client.search.google(
        query="python scraping",
        location="United States",
        num_results=10
    )
```

**Bing Search**
```python
with SyncBrightDataClient() as client:
    result = client.search.bing(query="python tutorial", num_results=10)
```

**Yandex Search**
```python
with SyncBrightDataClient() as client:
    result = client.search.yandex(query="python tutorial", language="ru")
```

### Amazon

**Scrape Product Details**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.amazon.products(url="https://amazon.com/dp/B0CRMZHDG8")
    print(result.data)
```

**Scrape Reviews**
```python
with SyncBrightDataClient() as client:
    # Get reviews with optional filters
    result = client.scrape.amazon.reviews(
        url="https://amazon.com/dp/B0CRMZHDG8",
        days_range=30
    )
```

**Scrape Sellers**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.amazon.sellers(url="https://amazon.com/dp/B0CRMZHDG8")
```

**Search Products by Keyword**
```python
with SyncBrightDataClient() as client:
    result = client.search.amazon.products(
        keyword="laptop",
        country="us"
    )
    for product in result.data:
        print(product.get("name"), product.get("final_price"))
```

### LinkedIn

**Get Profile Data**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.linkedin.profiles(url="https://linkedin.com/in/johndoe")
    print(result.data)
```

**Get Company Data**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.linkedin.companies(url="https://linkedin.com/company/example")
```

**Get Posts**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.linkedin.posts(url="https://linkedin.com/posts/example")
```

**Get Job Details**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.linkedin.jobs(url="https://linkedin.com/jobs/view/123456")
```

**Search Jobs**
```python
with SyncBrightDataClient() as client:
    result = client.search.linkedin.jobs(
        keyword="python developer",
        location="New York"
    )
```

**Search Profiles**
```python
with SyncBrightDataClient() as client:
    result = client.search.linkedin.profiles(
        firstName="John",
        lastName="Doe"
    )
```

### Social Media

**Instagram Profile**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.instagram.profiles(url="https://instagram.com/username")
```

**Instagram Posts**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.instagram.posts(url="https://instagram.com/p/ABC123")
```

**Instagram Comments**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.instagram.comments(url="https://instagram.com/p/ABC123")
```

**Instagram Reels**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.instagram.reels(url="https://instagram.com/reel/ABC123")
```

**Facebook Posts by Profile**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.facebook.posts_by_profile(
        url="https://facebook.com/profile_id",
        num_of_posts=10
    )
```

**Facebook Posts by Group**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.facebook.posts_by_group(url="https://facebook.com/groups/example")
```

**Facebook Comments**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.facebook.comments(
        url="https://facebook.com/post/123456",
        num_of_comments=100
    )
```

**Facebook Reels**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.facebook.reels(url="https://facebook.com/profile")
```

**ChatGPT Prompts**
```python
with SyncBrightDataClient() as client:
    result = client.scrape.chatgpt.prompt(
        prompt="Explain Python async programming",
        web_search=True
    )
    print(result.data)
```

## Async Usage

For high-performance scraping, use the async client. This allows you to run multiple requests concurrently.

```python
import asyncio
from brightdata import BrightDataClient

async def main():
    async with BrightDataClient() as client:
        # Scrape multiple URLs concurrently
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]

        # Run multiple scrapes concurrently
        tasks = [client.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks)

        for res in results:
            print(f"Success: {res.success}, Size: {len(res.data)} chars")

asyncio.run(main())
```

### Async with Manual Trigger/Poll/Fetch

For long-running scrapes, you can manually control the trigger/poll/fetch cycle:

```python
async with BrightDataClient() as client:
    # Trigger the scrape
    job = await client.scrape.amazon.products_trigger(url="https://amazon.com/dp/B123")
    print(f"Job started: {job.snapshot_id}")

    # Poll for status
    while True:
        status = await client.scrape.amazon.products_status(job.snapshot_id)
        if status == "ready":
            break
        await asyncio.sleep(5)

    # Fetch results
    result = await client.scrape.amazon.products_fetch(job.snapshot_id)
    print(result.data)
```

## Using Dataclass Payloads

The SDK provides dataclasses for strict type checking and IDE auto-completion.

```python
from brightdata import SyncBrightDataClient
from brightdata.payloads import AmazonProductPayload, LinkedInProfilePayload

# Amazon product with validated parameters
payload = AmazonProductPayload(
    url="https://amazon.com/dp/B123456789",
    reviews_count=50
)

with SyncBrightDataClient() as client:
    result = client.scrape.amazon.products(**payload.to_dict())

# LinkedIn profile with validated parameters
payload = LinkedInProfilePayload(
    url="https://linkedin.com/in/johndoe"
)

with SyncBrightDataClient() as client:
    result = client.scrape.linkedin.profiles(**payload.to_dict())
```

### Available Payload Classes

**Amazon:**
- `AmazonProductPayload` - Product scraping
- `AmazonReviewPayload` - Review scraping
- `AmazonSellerPayload` - Seller scraping

**LinkedIn:**
- `LinkedInProfilePayload` - Profile scraping
- `LinkedInJobPayload` - Job scraping
- `LinkedInCompanyPayload` - Company scraping
- `LinkedInPostPayload` - Post scraping
- `LinkedInProfileSearchPayload` - Profile search
- `LinkedInJobSearchPayload` - Job search
- `LinkedInPostSearchPayload` - Post search

**Instagram:**
- `InstagramProfilePayload` - Profile scraping
- `InstagramPostPayload` - Post scraping
- `InstagramCommentPayload` - Comment scraping
- `InstagramReelPayload` - Reel scraping
- `InstagramPostsDiscoverPayload` - Posts discovery
- `InstagramReelsDiscoverPayload` - Reels discovery

**Facebook:**
- `FacebookPostsProfilePayload` - Posts by profile
- `FacebookPostsGroupPayload` - Posts by group
- `FacebookPostPayload` - Single post
- `FacebookCommentsPayload` - Comments
- `FacebookReelsPayload` - Reels

**ChatGPT:**
- `ChatGPTPromptPayload` - Prompt scraping

## Troubleshooting

**SSL Certificate Errors**
If you encounter `SSL: CERTIFICATE_VERIFY_FAILED`, ensure your local certificates are updated:
```bash
pip install --upgrade certifi
```

**RuntimeError: SyncBrightDataClient cannot be used inside async context**
You're trying to use `SyncBrightDataClient` inside an async function. Use `BrightDataClient` with `async/await` instead:
```python
# Wrong
async def main():
    with SyncBrightDataClient() as client:  # Error!
        ...

# Correct
async def main():
    async with BrightDataClient() as client:
        result = await client.scrape_url("https://example.com")
```

**RuntimeError: BrightDataClient not initialized**
You forgot to use the context manager:
```python
# Wrong
client = BrightDataClient()
result = await client.scrape_url("...")  # Error!

# Correct
async with BrightDataClient() as client:
    result = await client.scrape_url("...")
```

## License

MIT License
