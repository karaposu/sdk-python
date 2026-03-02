ere's how sync users would work with an async-only SDK:

  🎯 Best Solution: Provide SyncBrightDataClient

  We give sync users a separate adapter class:

  # For async users (main client)
  from brightdata import BrightDataClient

  async with BrightDataClient() as client:
      result = await client.scrape.amazon.products(url)


  # For sync users (adapter)
  from brightdata import SyncBrightDataClient

  with SyncBrightDataClient() as client:
      result = client.scrape.amazon.products(url)  # Looks sync!

  How SyncBrightDataClient Works

  class SyncBrightDataClient:
      """Sync wrapper with persistent event loop"""

      def __enter__(self):
          # Create ONE event loop (reused for all calls)
          self._loop = asyncio.new_event_loop()
          self._loop.run_until_complete(
              self._async_client.__aenter__()
          )
          return self

      def __exit__(self, *args):
          # Cleanup loop once at the end
          self._loop.run_until_complete(
              self._async_client.__aexit__(*args)
          )
          self._loop.close()

      def list_zones(self):
          """Sync method using persistent loop"""
          return self._loop.run_until_complete(
              self._async_client.list_zones()
          )

      def scrape_amazon_products(self, url):
          """Sync method using persistent loop"""
          return self._loop.run_until_complete(
              self._async_client.scrape.amazon.products(url)
          )

  📊 Comparison: Old vs New

  Current SDK (Mixed)

  client = BrightDataClient()

  # Every call creates NEW loop
  result1 = client.scrape.amazon.products(url1)  # Loop 1
  result2 = client.scrape.amazon.products(url2)  # Loop 2
  result3 = client.scrape.amazon.products(url3)  # Loop 3

  # 3 calls = 3 loops created! ❌

  With SyncBrightDataClient

  with SyncBrightDataClient() as client:
      # All calls use SAME loop
      result1 = client.scrape.amazon.products(url1)  # ✅
      result2 = client.scrape.amazon.products(url2)  # ✅
      result3 = client.scrape.amazon.products(url3)  # ✅

  # 3 calls = 1 loop reused! ✅

  🎯 Why This is Better

  | Aspect              | Current (Mixed)          | With SyncAdapter    |
  |---------------------|--------------------------|---------------------|
  | Async client        | ❌ Has sync baggage       | ✅ Pure async, clean |
  | Sync users          | ❌ New loop each call     | ✅ Persistent loop   |
  | Concurrency (async) | ❌ Broken                 | ✅ Works perfectly   |
  | Performance (sync)  | ❌ Poor                   | ✅ Good              |
  | Code complexity     | ❌ Mixed responsibilities | ✅ Clear separation  |

  💡 Alternative Options for Sync Users

  Option 1: Manual asyncio.run (Simple scripts)

  import asyncio

  # Quick one-off call
  result = asyncio.run(
      async with BrightDataClient() as client:
          return await client.scrape.amazon.products(url)
  )

  Option 2: Jupyter Notebooks

  # Jupyter has built-in async support
  async with BrightDataClient() as client:
      result = await client.scrape.amazon.products(url)
      # Can use await directly!

  Option 3: Best Choice - Migrate to Async!

  # Best performance, supports concurrency
  async def my_scraper():
      async with BrightDataClient() as client:
          # Can run 100 URLs concurrently!
          results = await asyncio.gather(*(
              client.scrape.amazon.products(url)
              for url in urls
          ))
          return results

  asyncio.run(my_scraper())

  🎓 Summary

  Q: "How do sync users use async-only SDK?"

  A: We provide SyncBrightDataClient - a separate adapter class

  The Architecture

  ┌──────────────────────────┐
  │ BrightDataClient         │ ◄── Pure async, no sync code
  │ (Async-only, clean)      │     Best performance
  └──────────────────────────┘
           ▲
           │ Wraps
           │
  ┌────────┴─────────────────┐
  │ SyncBrightDataClient     │ ◄── Sync adapter
  │ (Persistent loop inside) │     Good performance
  └──────────────────────────┘

  Users choose which to import based on their needs!

  Migration Path

  # Old code
  from brightdata import BrightDataClient
  client = BrightDataClient()
  result = client.scrape.amazon.products(url)  # Sync

  # New code (minimal change)
  from brightdata import SyncBrightDataClient  # Just change import
  with SyncBrightDataClient() as client:       # Add context manager
      result = client.scrape.amazon.products(url)  # Same!

  This way:
  - ✅ Async users get clean, fast async client
  - ✅ Sync users get good-performance sync adapter
  - ✅ Clear separation, no confusion
  - ✅ Everyone wins!
