# Removing customer_id from SDK

## Discovery

Testing revealed that `customer_id` is **NOT required** for async unblocker endpoints. Bright Data derives the customer from the bearer token.

### Test Results

```bash
# WITH customer_id
POST /unblocker/req?customer=hl_67e5ed38&zone=serp_api4
✅ Works - Got response_id

# WITHOUT customer_id
POST /unblocker/req?zone=serp_api4
✅ Works - Got response_id

# Conclusion: customer_id is OPTIONAL
```

## Current State

The SDK currently has `customer_id` in several places, anticipating it would be required for async mode. Since it's not required, we should remove it to simplify the API.

## Where customer_id Currently Exists

### 1. Client Initialization

**File:** `src/brightdata/client.py`

**Current:**
```python
def __init__(
    self,
    token: Optional[str] = None,
    customer_id: Optional[str] = None,  # ← Remove this
    timeout: int = DEFAULT_TIMEOUT,
    ...
):
    """
    Args:
        customer_id: Customer ID (optional, can also be set via BRIGHTDATA_CUSTOMER_ID)
    """
    self.customer_id = customer_id or os.getenv("BRIGHTDATA_CUSTOMER_ID")
```

**Lines:** 74-122

### 2. Environment Variable Check

**File:** `src/brightdata/client.py`

**Current:**
```python
self.customer_id = customer_id or os.getenv("BRIGHTDATA_CUSTOMER_ID")
```

**Line:** 122

### 3. Documentation References

**Files to check:**
- `README.md`
- `docs/` (if exists)
- Docstrings mentioning customer_id

## Removal Plan

### Phase 1: Remove from Core Client (Breaking Change)

#### Step 1.1: Update Client Constructor

**File:** `src/brightdata/client.py:74-122`

**Before:**
```python
def __init__(
    self,
    token: Optional[str] = None,
    customer_id: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    web_unlocker_zone: Optional[str] = None,
    serp_zone: Optional[str] = None,
    browser_zone: Optional[str] = None,
    auto_create_zones: bool = True,
    validate_token: bool = False,
    rate_limit: Optional[float] = None,
    rate_period: float = 1.0,
):
    """
    Initialize Bright Data client.

    Args:
        token: API token
        customer_id: Customer ID (optional, can also be set via BRIGHTDATA_CUSTOMER_ID)
        timeout: Default timeout in seconds
        ...
    """
    self.token = self._load_token(token)
    self.customer_id = customer_id or os.getenv("BRIGHTDATA_CUSTOMER_ID")
    self.timeout = timeout
    # ... rest of init
```

**After:**
```python
def __init__(
    self,
    token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    web_unlocker_zone: Optional[str] = None,
    serp_zone: Optional[str] = None,
    browser_zone: Optional[str] = None,
    auto_create_zones: bool = True,
    validate_token: bool = False,
    rate_limit: Optional[float] = None,
    rate_period: float = 1.0,
):
    """
    Initialize Bright Data client.

    Args:
        token: API token
        timeout: Default timeout in seconds
        ...
    """
    self.token = self._load_token(token)
    self.timeout = timeout
    # ... rest of init (no customer_id line)
```

**Changes:**
- ❌ Remove `customer_id: Optional[str] = None` parameter
- ❌ Remove docstring mention of `customer_id`
- ❌ Remove `self.customer_id = ...` assignment

#### Step 1.2: Remove Environment Variable

**Before:**
```python
TOKEN_ENV_VAR = "BRIGHTDATA_API_TOKEN"
# Implicit: BRIGHTDATA_CUSTOMER_ID
```

**After:**
```python
TOKEN_ENV_VAR = "BRIGHTDATA_API_TOKEN"
# No BRIGHTDATA_CUSTOMER_ID needed
```

**Note:** If users have `BRIGHTDATA_CUSTOMER_ID` in their `.env`, it will be ignored (harmless).

### Phase 2: Remove from Tests

#### Step 2.1: Search for customer_id in Tests

```bash
cd /Users/ns/Desktop/projects/sdk-python
grep -r "customer_id" tests/
grep -r "CUSTOMER_ID" tests/
```

#### Step 2.2: Update Test Files

**Example test that might need updating:**

**Before:**
```python
def test_client_with_customer_id():
    client = BrightDataClient(
        token="test_token",
        customer_id="hl_12345678"
    )
    assert client.customer_id == "hl_12345678"
```

**After:**
```python
# Remove this test entirely, or rename to test something else
def test_client_initialization():
    client = BrightDataClient(token="test_token")
    assert client.token == "test_token"
```

### Phase 3: Remove from Documentation

#### Step 3.1: Update README.md

**Search for:**
- "customer_id"
- "BRIGHTDATA_CUSTOMER_ID"
- "customer ID"

**Remove or update examples:**

**Before:**
```markdown
### Configuration

Set environment variables:
```bash
export BRIGHTDATA_API_TOKEN="your_token"
export BRIGHTDATA_CUSTOMER_ID="hl_67e5ed38"  # ← Remove this line
```

**After:**
```markdown
### Configuration

Set environment variable:
```bash
export BRIGHTDATA_API_TOKEN="your_token"
```

#### Step 3.2: Update Docstrings

Search all Python files for customer_id mentions:

```bash
grep -r "customer_id" src/brightdata/ --include="*.py"
```

Update any docstrings that mention it.

### Phase 4: Update Enhancement Documents

#### Step 4.1: Update serp_async_endpoint_improvement.md

**File:** `devdocs/enhancements/serp_async_endpoint_improvement.md`

**Changes needed:**

1. Remove customer_id from AsyncUnblockerClient:

**Before:**
```python
class AsyncUnblockerClient:
    def __init__(self, engine: AsyncEngine, customer_id: str):
        self.engine = engine
        self.customer_id = customer_id  # ← Remove
```

**After:**
```python
class AsyncUnblockerClient:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        # No customer_id needed!
```

2. Update endpoint calls:

**Before:**
```python
params = {
    "customer": self.customer_id,  # ← Remove
    "zone": zone,
}
```

**After:**
```python
params = {
    "zone": zone,
}
```

3. Remove from initialization sections:

**Before:**
```python
client = AsyncBrightDataClient(
    token="...",
    customer_id="hl_67e5ed38"  # Required for async mode
)
```

**After:**
```python
client = AsyncBrightDataClient(
    token="..."  # That's all you need!
)
```

#### Step 4.2: Update critic.md

**File:** `devdocs/enhancements/critic.md`

**Remove ISSUE 2:** "customer_id Availability" section entirely

**Update ISSUE 3:** "Async Mode Requires Extra Config"

**Before:**
```
Friction Points:
1. User must know about customer_id
2. User must know to set mode="async"
3. User must understand polling parameters

Usability Concern: Async mode has 4 configuration points vs sync's 0.
```

**After:**
```
Friction Points:
1. User must know to set mode="async"
2. User must understand polling parameters

Usability Concern: Async mode has 2 configuration points vs sync's 0.
```

### Phase 5: Verify Removal

#### Step 5.1: Search Entire Codebase

```bash
cd /Users/ns/Desktop/projects/sdk-python

# Search Python files
grep -r "customer_id" src/ --include="*.py"
grep -r "CUSTOMER_ID" src/ --include="*.py"

# Search docs
grep -r "customer_id" devdocs/ README.md CHANGELOG.md

# Search tests
grep -r "customer_id" tests/ --include="*.py"
```

**Expected result:** Zero matches (or only in comments explaining removal)

#### Step 5.2: Check for Attribute Access

Search for code that accesses `client.customer_id`:

```bash
grep -r "\.customer_id" src/ --include="*.py"
```

Remove or update any code that reads this attribute.

### Phase 6: Update CHANGELOG

**File:** `CHANGELOG.md`

**Add entry:**

```markdown
## [Unreleased]

### Removed
- **BREAKING:** Removed `customer_id` parameter from `BrightDataClient`
  - Reason: Not required by Bright Data API (customer derived from token)
  - Migration: Remove `customer_id` from client initialization
  - Before: `client = BrightDataClient(token="...", customer_id="hl_...")`
  - After: `client = BrightDataClient(token="...")`
```

## Migration Guide for Users

### For Users Who Have customer_id

**Old code:**
```python
from brightdata import BrightDataClient

client = BrightDataClient(
    token="your_token",
    customer_id="hl_67e5ed38"  # ← Remove this
)
```

**New code:**
```python
from brightdata import BrightDataClient

client = BrightDataClient(
    token="your_token"
)
```

**Impact:** None - functionality unchanged

### For Users Using Environment Variables

**Old `.env`:**
```bash
BRIGHTDATA_API_TOKEN=your_token
BRIGHTDATA_CUSTOMER_ID=hl_67e5ed38  # ← Can remove (harmless to keep)
```

**New `.env`:**
```bash
BRIGHTDATA_API_TOKEN=your_token
```

**Impact:** None - SDK will ignore `BRIGHTDATA_CUSTOMER_ID` if present

## Benefits of Removal

### 1. Simpler API

**Before:**
```python
# Users wonder: "Do I need customer_id?"
client = BrightDataClient(token="...", customer_id="???")
```

**After:**
```python
# Clear and simple
client = BrightDataClient(token="...")
```

### 2. Less Configuration

**Before:** 2 things to configure (token + customer_id)
**After:** 1 thing to configure (token only)

### 3. No Discovery Problem

Users don't need to find their customer_id in the Bright Data dashboard.

### 4. Cleaner Code

Less parameters to pass around internally.

### 5. Fewer Error Cases

No more "customer_id mismatch with token" or "missing customer_id" errors.

## Potential Issues

### Issue 1: Explicit Customer Routing

**Question:** Could `customer` parameter be useful for multi-tenant scenarios?

**Answer:** Unlikely - if you have multiple customers, you'd use different tokens.

**Mitigation:** If needed in future, can add back as optional parameter.

### Issue 2: Bright Data Internal Routing

**Question:** Could removing `customer` param affect Bright Data's internal routing?

**Answer:** No - test proved it works without it. Token is sufficient for routing.

### Issue 3: Breaking Change

**Question:** Will this break existing user code?

**Answer:** Yes, if users are passing `customer_id`. Hence:
- Mark as breaking change in CHANGELOG
- Bump major version (v2 → v3)
- Provide clear migration guide

**Mitigation:**
```python
# Option: Keep parameter but mark deprecated
def __init__(
    self,
    token: Optional[str] = None,
    customer_id: Optional[str] = None,  # Deprecated, ignored
    ...
):
    if customer_id:
        warnings.warn(
            "customer_id is deprecated and no longer needed. "
            "It will be removed in v4.0.0",
            DeprecationWarning
        )
    # Don't store customer_id
```

## Implementation Checklist

### Code Changes
- [ ] Remove `customer_id` parameter from `BrightDataClient.__init__`
- [ ] Remove `self.customer_id` assignment
- [ ] Remove `customer_id` from docstrings
- [ ] Search and remove all `customer_id` references in `src/`
- [ ] Remove `customer` from async unblocker URL params
- [ ] Update `AsyncUnblockerClient` to not require `customer_id`

### Documentation Changes
- [ ] Update README.md examples
- [ ] Remove `BRIGHTDATA_CUSTOMER_ID` from env var docs
- [ ] Update `serp_async_endpoint_improvement.md`
- [ ] Update `critic.md` (remove ISSUE 2, update ISSUE 3)
- [ ] Add migration guide to CHANGELOG.md
- [ ] Update any other docs mentioning customer_id

### Test Changes
- [ ] Remove tests that verify customer_id behavior
- [ ] Update tests that use customer_id parameter
- [ ] Add test verifying async unblocker works without customer param
- [ ] Verify all tests pass after removal

### Final Verification
- [ ] Run: `grep -r "customer_id" src/` → Should be empty
- [ ] Run: `grep -r "CUSTOMER_ID" src/` → Should be empty
- [ ] Run all tests → Should pass
- [ ] Test async SERP without customer param → Should work
- [ ] Update version number (major bump)

## Timeline

- **Removal:** 1-2 hours
- **Testing:** 1 hour
- **Documentation:** 1 hour
- **Total:** 3-4 hours

## Alternative: Deprecation Path

If you want to avoid breaking change immediately:

### Phase 1: Deprecate (v2.1.0)
```python
def __init__(self, token, customer_id=None, ...):
    if customer_id:
        warnings.warn("customer_id is deprecated", DeprecationWarning)
    # Store but don't use
```

### Phase 2: Remove (v3.0.0)
```python
def __init__(self, token, ...):
    # No customer_id parameter
```

This gives users time to update their code.

## Recommendation

**For this SDK (currently v2.1.0):**

Since the SDK is under heavy development and not widely adopted yet:
- **Immediate removal** is acceptable
- Bump to **v2.2.0** with breaking change note
- Clear migration guide in CHANGELOG
- Most users likely haven't deployed yet

**For mature SDK:**
- Use deprecation path (v2.1.0 deprecate, v3.0.0 remove)
