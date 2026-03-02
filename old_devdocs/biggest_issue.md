🎯 The BIGGEST Design Issue: CONFUSED LIFECYCLE OWNERSHIP

  Current Problem: Everyone Manages Lifecycle

  In the current code:

  # Current - WHO owns the engine lifecycle?

  # 1. The Client has a context manager
  class BrightDataClient:
      async def __aenter__(self):
          await self.engine.__aenter__()  # Client manages engine

      # 2. But EVERY utility method ALSO manages engine
      async def list_zones(self):
          async with self.engine:  # Method manages engine ❌
              return await self._zone_manager.list_zones()

      async def get_account_info(self):
          async with self.engine:  # Method manages engine ❌
              # ...

  # 3. And EVERY sync wrapper creates its OWN loop + engine
  def products(self):
      async def _run():
          async with self.engine:  # Sync wrapper manages engine ❌
              return await self.products_async()
      return asyncio.run(_run())  # Creates NEW loop ❌

  Three different owners fighting over the same engine!

  The Core Issue

  # Question: Who initializes the engine?
  # Answer: 😵 Client? Methods? Sync wrappers? All of them?

  # Question: Who cleans up the engine?
  # Answer: 😵 Whoever exits their context first!

  # Question: Can I use methods concurrently?
  # Answer: 😵 No! They all fight over engine lifecycle!

  ---
  💡 Async + Sync Adapter: CLEAR OWNERSHIP

  The Key Difference

  Current Approach:
  class BrightDataClient:
      # Both async AND sync mixed in SAME class

      async def products_async(self, url):
          # Async implementation
          pass

      def products(self, url):
          # Sync wrapper in SAME class
          return asyncio.run(self.products_async(url))  # New loop each time!

      async def list_zones(self):
          async with self.engine:  # Method manages lifecycle
              pass

  Async + Sync Adapter Approach:
  # ============================================
  # CLASS 1: Pure Async Client (PRIMARY)
  # ============================================
  class BrightDataClient:
      """ONLY async methods, CLEAR lifecycle"""

      async def __aenter__(self):
          await self.engine.__aenter__()  # ✅ Client owns lifecycle
          return self

      async def __aexit__(self, *args):
          await self.engine.__aexit__(*args)  # ✅ Client owns cleanup

      # Methods DON'T manage engine - they ASSUME it's initialized
      async def products(self, url):
          # ✅ NO nested context, NO lifecycle management
          return await self._scrape(url)

      async def list_zones(self):
          # ✅ NO nested context, assumes engine ready
          return await self._zone_manager.list_zones()


  # ============================================
  # CLASS 2: Sync Adapter (SEPARATE)
  # ============================================
  class SyncBrightDataClient:
      """Wraps async client with persistent loop"""

      def __init__(self):
          self._async_client = BrightDataClient()  # The async client
          self._loop = None  # OUR persistent loop

      def __enter__(self):
          # ✅ Adapter owns the loop
          self._loop = asyncio.new_event_loop()
          asyncio.set_event_loop(self._loop)

          # Initialize async client in our loop
          self._loop.run_until_complete(
              self._async_client.__aenter__()
          )
          return self

      def __exit__(self, *args):
          # ✅ Adapter cleans up loop
          self._loop.run_until_complete(
              self._async_client.__aexit__(*args)
          )
          self._loop.close()

      def products(self, url):
          # ✅ Uses SAME loop for all calls
          return self._loop.run_until_complete(
              self._async_client.products(url)
          )

      def list_zones(self):
          # ✅ Uses SAME loop for all calls
          return self._loop.run_until_complete(
              self._async_client.list_zones()
          )

  ---
  🔍 The Difference Visualized

  Current: Chaos

  ┌─────────────────────────────────────┐
  │   BrightDataClient                  │
  │   (Mixed async + sync)              │
  ├─────────────────────────────────────┤
  │                                     │
  │  async def list_zones():            │
  │    async with self.engine: ◄─┐     │  ❌ Method owns engine
  │      ...                      │     │
  │                               │     │
  │  def list_zones_sync():       │     │
  │    loop = new_event_loop()  ◄─┼─┐   │  ❌ Sync wrapper owns loop
  │    loop.run_until_complete()  │ │   │
  │      async with self.engine: ◄┘ │   │  ❌ Also owns engine
  │                                 │   │
  │  async def __aenter__():        │   │
  │    self.engine.__aenter__()   ◄─┘   │  ❌ Client also owns engine
  │                                     │
  └─────────────────────────────────────┘

  Result: 3 different owners, race conditions, "Connector is closed"

  Async + Sync Adapter: Clarity

  ┌──────────────────────────────────┐
  │  BrightDataClient (ASYNC ONLY)   │
  │                                  │
  │  async def __aenter__():         │
  │    self.engine.__aenter__() ◄────┼─── ✅ ONLY owner
  │                                  │
  │  async def __aexit__():          │
  │    self.engine.__aexit__()  ◄────┼─── ✅ ONLY cleanup
  │                                  │
  │  async def list_zones():         │
  │    # NO context management      │
  │    return await ...              │
  │                                  │
  │  async def products():           │
  │    # NO context management      │
  │    return await ...              │
  └──────────────────────────────────┘
           ▲
           │ Uses
           │
  ┌────────┴─────────────────────────┐
  │  SyncBrightDataClient (WRAPPER)  │
  │                                  │
  │  def __enter__():                │
  │    self._loop = new_loop() ◄─────┼─── ✅ Adapter owns loop
  │    self._loop.run_until_complete(│
  │      self._async_client.__aenter__()
  │    )                             │
  │                                  │
  │  def list_zones():               │
  │    # Uses persistent loop        │
  │    return self._loop.run_until... │
  └──────────────────────────────────┘

  Result: Clear ownership, no conflicts, concurrent operations work

  ---
  📋 Comparison Table

  | Aspect                                  | Current (Mixed)                                | Async + Sync Adapter
         |
  |-----------------------------------------|------------------------------------------------|-----------------------
  -------|
  | Who owns engine lifecycle?              | 😵 Client, methods, sync wrappers (confusion!) | ✅ Async client ONLY
          |
  | Who owns event loop?                    | 😵 Each sync call creates new loop             | ✅ Sync adapter owns
  ONE loop |
  | Can methods run concurrently?           | ❌ No, race conditions                          | ✅ Yes, clean
  separation      |
  | How many event loops for 10 sync calls? | ❌ 10 new loops                                 | ✅ 1 persistent loop
           |
  | Do methods manage contexts?             | ❌ Yes, nested async with everywhere            | ✅ No, assume
  initialized     |
  | Sync performance                        | ❌ Poor (new loop each time)                    | ✅ Good (reused loop)
           |
  | Async performance                       | ✅ Good                                         | ✅ Excellent
           |

  ---
  🎯 The BIGGEST Design Issue Revealed

  SINGLE RESPONSIBILITY PRINCIPLE VIOLATION

  Current code violates SRP:
  - BrightDataClient is responsible for: Configuration, async ops, sync ops, engine lifecycle
  - Each method is responsible for: Its operation AND engine lifecycle
  - Each sync wrapper is responsible for: Calling async version AND creating loop AND managing engine

  Everything does too much!

  The Solution

  Separation of Concerns:

  1. AsyncEngine: Manages HTTP session, nothing else
  2. BrightDataClient (async): Manages engine lifecycle at client level ONLY
  3. Methods: Do their job, assume engine is ready
  4. SyncBrightDataClient: Manages event loop, wraps async client

  Each class has ONE clear responsibility!

  ---
  💡 Real-World Example

  Current (Broken Concurrency)

  client = BrightDataClient()

  # ❌ This fails with "Connector is closed"
  zones, info, conn = await asyncio.gather(
      client.list_zones(),        # Enters engine context
      client.get_account_info(),  # Enters engine context (race!)
      client.test_connection()    # Enters engine context (race!)
  )
  # First to exit closes connector, others crash!

  Async + Sync Adapter (Works)

  # Async usage
  async with BrightDataClient() as client:  # ✅ Engine initialized ONCE
      zones, info, conn = await asyncio.gather(
          client.list_zones(),        # ✅ Just uses engine
          client.get_account_info(),  # ✅ Just uses engine
          client.test_connection()    # ✅ Just uses engine
      )
      # ✅ Engine cleaned up ONCE at end

  # Sync usage
  with SyncBrightDataClient() as client:  # ✅ Loop created ONCE
      zones = client.list_zones()         # ✅ Uses same loop
      info = client.get_account_info()    # ✅ Uses same loop
      conn = client.test_connection()     # ✅ Uses same loop
      # ✅ Loop closed ONCE at end

  ---
  🎓 Summary

  The BIGGEST design issue: Confused ownership of resources

  - Current: Everyone manages engine/loop lifecycle → race conditions
  - Solution: Clear separation → one owner per resource

  Why Async + Sync Adapter is different:
  - NOT just "having both async and sync"
  - It's about SEPARATING them into different classes with clear responsibilities
  - Async client: Pure async, manages engine at client level
  - Sync adapter: Separate class, manages loop, wraps async client

  The key insight: "Having both" vs "Separating both"
