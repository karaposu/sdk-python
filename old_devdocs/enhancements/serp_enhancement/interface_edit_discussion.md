# Interface Edit Discussion

How to integrate pagination into the current SERP interface without breaking changes.

## Current Interface

```python
# search_service.py
async def google(
    self,
    query: Union[str, List[str]],
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    zone: Optional[str] = None,
    **kwargs,
) -> Union[SearchResult, List[SearchResult]]

# base.py BaseSERPService.search()
async def search(
    self,
    query: Union[str, List[str]],
    zone: str,
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    mode: str = "sync",          # "sync" or "async"
    poll_interval: int = 2,
    poll_timeout: int = 30,
    **kwargs,
) -> Union[SearchResult, List[SearchResult]]
```

## Option A: Add `pagination` Parameter

Add a new `pagination` parameter to control pagination strategy.

### Interface Change

```python
async def google(
    self,
    query: Union[str, List[str]],
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    zone: Optional[str] = None,
    pagination: Literal["auto", "sequential", "concurrent"] = "auto",  # NEW
    **kwargs,
) -> Union[SearchResult, List[SearchResult]]
```

### Behavior

| `pagination` | `num_results` | Behavior |
|--------------|---------------|----------|
| `"auto"` | 1-10 | Single request (no pagination) |
| `"auto"` | 11+ | Sequential pagination |
| `"sequential"` | any | Sequential pagination (follow next links) |
| `"concurrent"` | any | Concurrent pagination (parallel requests) |

### Pros

- Clear, explicit control
- Single parameter covers all cases
- String enum is self-documenting

### Cons

- New parameter to learn
- `"auto"` behavior may surprise users
- Need to document what each option means

---

## Option B: Add `concurrent_pagination` Boolean Flag

User's original patch approach - simple boolean flag.

### Interface Change

```python
async def google(
    self,
    query: Union[str, List[str]],
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    zone: Optional[str] = None,
    concurrent_pagination: bool = False,  # NEW
    **kwargs,
) -> Union[SearchResult, List[SearchResult]]
```

### Behavior

| `concurrent_pagination` | Behavior |
|------------------------|----------|
| `False` (default) | Sequential pagination when num_results > page_size |
| `True` | Concurrent pagination |

### Pros

- Simple binary choice
- Matches user's patch exactly
- Easy to understand: off = safe/slow, on = fast/parallel

### Cons

- Less flexible than enum approach
- Name is long
- Doesn't support future strategies (batched, etc.)

---

## Option C: Implicit Pagination (No New Parameters)

Always paginate automatically based on `num_results`. No new parameters.

### Interface Change

None - existing interface unchanged.

### Behavior

```python
# Internally:
if num_results <= 10:
    return self._single_page_search(...)
else:
    return self._paginated_search(...)  # Sequential by default
```

### Pros

- **No breaking changes**: Existing code works identically
- **No learning curve**: Users don't need to know about pagination
- **"Just works"**: Request 100, get 100 (if available)

### Cons

- **Hidden behavior**: Users may not realize multiple requests are happening
- **No control**: Can't opt into concurrent mode
- **Surprise latency**: Requesting 100 results suddenly takes 10x longer

---

## Option D: Separate Method for Paginated Search

Add a new method specifically for paginated searches.

### Interface Change

```python
# Existing method unchanged
async def google(self, query, num_results=10, ...) -> SearchResult

# New method for explicit pagination control
async def google_paginated(
    self,
    query: str,
    total_results: int,
    strategy: Literal["sequential", "concurrent"] = "sequential",
    max_pages: int = 10,
    **kwargs,
) -> SearchResult
```

### Pros

- Clear separation of concerns
- Existing API completely unchanged
- Explicit method name signals different behavior

### Cons

- API surface grows
- Users need to choose which method to use
- Duplication of parameter handling

---

## Option E: Configuration at Client Level

Set pagination strategy as client-wide configuration.

### Interface Change

```python
client = BrightDataClient(
    token="...",
    serp_pagination_strategy="sequential",  # NEW: client-wide default
)

# Individual calls can still override
result = await client.search.google(
    query="test",
    num_results=100,
    pagination="concurrent",  # Override client default
)
```

### Pros

- Set once, apply everywhere
- Reduces repetition for users who always want same behavior
- Clean per-request override

### Cons

- Hidden default behavior
- More configuration to manage
- Unusual pattern (most params are per-request)

---

## Recommended Approach: Option A + C Hybrid

### Design

1. **Implicit pagination by default** (Option C): When `num_results > 10`, automatically paginate sequentially. This is the safe, "just works" behavior.

2. **Explicit `pagination` parameter** (Option A): Allow users to override with `pagination="concurrent"` for power users who want speed.

### Final Interface

```python
async def google(
    self,
    query: Union[str, List[str]],
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    zone: Optional[str] = None,
    pagination: Optional[Literal["sequential", "concurrent"]] = None,  # NEW
    **kwargs,
) -> Union[SearchResult, List[SearchResult]]
```

### Behavior Matrix

| `pagination` | `num_results` | Actual Behavior |
|--------------|---------------|-----------------|
| `None` | 1-10 | Single request |
| `None` | 11+ | Sequential pagination |
| `"sequential"` | any | Sequential pagination |
| `"concurrent"` | any | Concurrent pagination |

### Usage Examples

```python
# Simple case - single page
result = await client.search.google(query="test")

# Request many results - auto sequential pagination
result = await client.search.google(query="test", num_results=50)

# Power user - explicit concurrent
result = await client.search.google(
    query="test",
    num_results=100,
    pagination="concurrent"
)
```

---

## Implementation Layers

### Layer 1: URL Builder Changes

```python
# url_builder.py
class GoogleURLBuilder(BaseURLBuilder):
    def build(
        self,
        query: str,
        location: Optional[str] = None,
        language: str = "en",
        device: str = "desktop",
        num_results: int = 10,
        start: int = 0,  # NEW: pagination offset
        **kwargs,
    ) -> str:
        url = f"https://www.google.com/search?q={quote_plus(query)}"

        if start > 0:
            url += f"&start={start}"

        # ... rest unchanged
```

### Layer 2: Base SERP Service Changes

```python
# base.py
class BaseSERPService:
    async def search(
        self,
        query: Union[str, List[str]],
        zone: str,
        num_results: int = 10,
        pagination: Optional[Literal["sequential", "concurrent"]] = None,
        **kwargs,
    ) -> Union[SearchResult, List[SearchResult]]:
        # Determine strategy
        if num_results <= self.PAGE_SIZE:
            return await self._search_single_page(...)
        elif pagination == "concurrent":
            return await self._search_concurrent_pagination(...)
        else:
            return await self._search_sequential_pagination(...)
```

### Layer 3: Search Service Changes

```python
# search_service.py
class SearchService:
    async def google(
        self,
        query: Union[str, List[str]],
        num_results: int = 10,
        pagination: Optional[Literal["sequential", "concurrent"]] = None,
        **kwargs,
    ) -> Union[SearchResult, List[SearchResult]]:
        # Pass through to service
        return await self._google_service.search(
            query=query,
            num_results=num_results,
            pagination=pagination,
            **kwargs,
        )
```

---

## Migration & Backwards Compatibility

### Breaking Changes: None

- All existing parameters remain
- Default behavior unchanged for `num_results <= 10`
- New parameter is optional with sensible default

### Behavioral Changes (Non-Breaking)

- `num_results > 10` now actually returns more results (previously silently ignored)
- This is a bug fix, not a breaking change

### Deprecation: None Required

No existing APIs are deprecated.
