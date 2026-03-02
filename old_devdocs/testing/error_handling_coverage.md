# Error Handling Test Coverage Analysis

## Current Coverage (`probe_tests/test_09_error_handling.py`)

### ✅ What's Currently Tested

#### 1. Authentication Errors
- Invalid token handling
- Token validation on client creation
- `test_connection_sync()` with invalid token

#### 2. Validation Errors
- URL validation (empty, malformed, wrong protocol, XSS attempts)
- Zone name validation
- Input parameter validation

#### 3. Exception Hierarchy
- All custom exceptions inherit from `BrightDataError`
- Exception instantiation and attributes
- `APIError.status_code` attribute

#### 4. Async Error Handling
- Errors in async operations
- Batch operations with invalid URLs
- ValidationError propagation in async context

#### 5. Zone Configuration
- Zone name validation
- Non-existent zone handling

---

## ❌ What's NOT Tested (Gaps)

### Critical Gaps

#### 1. **Network Errors**
```python
# NOT TESTED:
- Connection refused (server down)
- DNS resolution failures
- SSL/TLS certificate errors
- Connection timeouts
- Socket errors
- Network unreachable
```

**Why important:** Real-world network issues are common

**Example test:**
```python
async def test_network_errors():
    """Test network-level error handling."""
    client = BrightDataClient()

    # Test connection refused
    # Modify engine to use fake unreachable endpoint

    # Test DNS failure
    # Use invalid domain

    # Test timeout
    # Use extremely slow endpoint
```

#### 2. **HTTP Status Code Errors**
```python
# NOT TESTED:
- 429 (Rate Limit)
- 500 (Internal Server Error)
- 502 (Bad Gateway)
- 503 (Service Unavailable)
- 504 (Gateway Timeout)
- 401/403 (Auth errors from API)
```

**Why important:** API can return various error codes

**Example test:**
```python
def test_http_error_codes():
    """Test various HTTP error responses."""

    # Mock HTTP responses
    test_cases = [
        (429, "Rate limit", RateLimitError),
        (500, "Server error", APIError),
        (502, "Bad gateway", APIError),
        (503, "Service unavailable", APIError),
    ]

    for status_code, message, expected_exception in test_cases:
        # Mock response, verify exception
        pass
```

#### 3. **Timeout Scenarios**
```python
# NOT TESTED:
- Poll timeout (job takes too long)
- Fetch timeout (download takes too long)
- Trigger timeout
- Status check timeout
- Different timeout configurations
```

**Why important:** We just fixed ChatGPT batch timeout issue - need tests!

**Example test:**
```python
async def test_timeout_scenarios():
    """Test various timeout scenarios."""

    # Test poll timeout
    result = await client.scrape.amazon.products_async(
        urls=["https://amazon.com/..."],
        poll_timeout=1  # Very short
    )
    assert result.error contains "timeout"

    # Test fetch timeout with large batch
    # (This would have caught the ChatGPT bug!)

    # Test custom timeout override
```

#### 4. **Malformed API Responses**
```python
# NOT TESTED:
- Invalid JSON
- Missing required fields
- Unexpected data structure
- Empty responses
- Null values in critical fields
```

**Why important:** API can return corrupted/unexpected data

**Example test:**
```python
def test_malformed_responses():
    """Test handling of malformed API responses."""

    # Mock invalid JSON response
    # Mock response missing required fields
    # Mock response with wrong data types
```

#### 5. **Retry Mechanisms**
```python
# NOT TESTED:
- Retry on transient errors
- Exponential backoff
- Max retry limit
- Retry success after failures
```

**Why important:** Transient errors should be retried

#### 6. **Context Manager Errors**
```python
# NOT TESTED:
- Error inside `async with client:` block
- Cleanup on error
- Multiple errors in context
- Context manager not used (should fail)
```

**Why important:** We require `async with` pattern

**Example test:**
```python
async def test_context_manager_errors():
    """Test error handling with context manager."""

    # Test error inside context
    try:
        async with client:
            raise RuntimeError("Simulated error")
    except RuntimeError:
        # Verify cleanup happened
        pass

    # Test without context manager
    try:
        result = await client.scrape.amazon.products_async(...)
    except RuntimeError as e:
        assert "context manager" in str(e)
```

#### 7. **Concurrent Error Handling**
```python
# NOT TESTED:
- Errors in concurrent operations
- Partial failures in batch
- Connector errors (we had these!)
- Rate limiting with concurrency
```

**Why important:** We just added concurrency tests but not error scenarios

**Example test:**
```python
async def test_concurrent_errors():
    """Test error handling with concurrent operations."""

    async with client:
        # Mix valid and invalid URLs
        tasks = [
            client.scrape.amazon.products_async(valid_url),
            client.scrape.amazon.products_async("invalid"),
            client.scrape.amazon.products_async(valid_url),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify: 2 successes, 1 failure
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]
```

#### 8. **Rate Limiting**
```python
# NOT TESTED:
- Rate limit error detection
- Rate limit retry logic
- Rate limit headers parsing
- Backoff strategy
```

**Example test:**
```python
async def test_rate_limiting():
    """Test rate limit handling."""

    # Make many requests rapidly
    # Verify rate limiting kicks in
    # Verify retry with backoff
```

#### 9. **Dataset-Specific Errors**
```python
# NOT TESTED:
- Invalid dataset ID
- Dataset not accessible
- Invalid payload for dataset
- Snapshot not found
- Snapshot expired
```

**Example test:**
```python
async def test_dataset_errors():
    """Test dataset-specific error handling."""

    # Test with invalid dataset ID
    scraper.DATASET_ID = "invalid_id_12345"

    # Test with invalid payload

    # Test fetching non-existent snapshot
```

#### 10. **Scraper-Specific Errors**
```python
# NOT TESTED:
- Amazon: Invalid ASIN
- LinkedIn: Profile not found
- ChatGPT: Prompt too long
- Instagram: Private profile
- Facebook: Page access denied
```

**Example test:**
```python
async def test_scraper_specific_errors():
    """Test scraper-specific error scenarios."""

    # Amazon: Invalid ASIN
    result = await client.scrape.amazon.products_async(
        asins=["INVALID123"]
    )

    # LinkedIn: Non-existent profile
    result = await client.scrape.linkedin.profile_async(
        url="https://linkedin.com/in/doesnotexist99999"
    )
```

#### 11. **Empty/Null Response Handling**
```python
# NOT TESTED:
- API returns empty array
- API returns null
- API returns success but no data
- Polling succeeds but fetch returns empty
```

**Example test:**
```python
def test_empty_responses():
    """Test handling of empty/null responses."""

    # Mock API returning empty array
    # Verify SDK handles gracefully

    # Mock API returning null
    # Verify no crash
```

#### 12. **Character Encoding Errors**
```python
# NOT TESTED:
- Invalid UTF-8 in response
- Unicode handling
- Special characters in URLs
- Emoji in prompts
```

#### 13. **Large Payload Errors**
```python
# NOT TESTED:
- Request too large
- Response too large
- Memory errors with huge datasets
```

#### 14. **Error Recovery**
```python
# NOT TESTED:
- Recovery from transient errors
- Partial success handling
- Fallback mechanisms
- Graceful degradation
```

---

## 📊 Coverage Summary

| Category | Current Tests | Missing Tests | Priority |
|----------|--------------|---------------|----------|
| Authentication | ✅ Basic | ❌ Token refresh, expired tokens | Medium |
| Validation | ✅ URL, Zone | ❌ Payload, parameters | Medium |
| Network | ❌ None | ❌ All network errors | **High** |
| HTTP Errors | ❌ None | ❌ 429, 500, 502, 503 | **High** |
| Timeouts | ❌ None | ❌ Poll, fetch, trigger | **Critical** |
| Malformed Data | ❌ None | ❌ Invalid JSON, missing fields | High |
| Retry Logic | ❌ None | ❌ Retry mechanisms | Medium |
| Context Manager | ❌ None | ❌ Error cleanup | High |
| Concurrency | ❌ None | ❌ Concurrent errors | **High** |
| Rate Limiting | ❌ None | ❌ Rate limit handling | High |
| Dataset Errors | ❌ None | ❌ Invalid datasets | Medium |
| Scraper Errors | ❌ None | ❌ Platform-specific | Medium |
| Empty Responses | ❌ None | ❌ Null/empty handling | Medium |
| Recovery | ❌ None | ❌ Error recovery | Low |

**Overall Coverage: ~15%** (5 categories / ~30 total categories)

---

## 🎯 Recommended Extensions

### Priority 1: Critical (Implement First)

#### Test 6: Timeout Handling
```python
def test_6_timeout_scenarios():
    """Test 6: Timeout error handling."""
    print_test("6. Timeout Scenarios")

    async def async_test():
        client = BrightDataClient()
        async with client:
            # Test 6a: Poll timeout
            print("  Testing poll timeout...")
            result = await client.scrape.amazon.products_async(
                urls=["https://amazon.com/dp/B08N5WRWNW"],
                poll_timeout=1  # Very short - should timeout
            )
            assert not result.success
            assert "timeout" in result.error.lower()

            # Test 6b: Verify normal timeout works
            result = await client.scrape.amazon.products_async(
                urls=["https://amazon.com/dp/B08N5WRWNW"],
                poll_timeout=300  # Normal
            )
            # Should work or fail for different reason

    return asyncio.run(async_test())
```

#### Test 7: Network Errors
```python
def test_7_network_errors():
    """Test 7: Network error handling."""
    print_test("7. Network Errors")

    async def async_test():
        client = BrightDataClient()

        # Test 7a: Connection to invalid host
        # (Requires mocking or test server)

        # Test 7b: DNS failure
        # Use definitely non-existent domain

        # Test 7c: Connection timeout
        # Use blackhole IP address

    return asyncio.run(async_test())
```

#### Test 8: Concurrent Error Scenarios
```python
def test_8_concurrent_errors():
    """Test 8: Error handling with concurrent operations."""
    print_test("8. Concurrent Error Scenarios")

    async def async_test():
        client = BrightDataClient()
        async with client:
            # Mix of valid and invalid operations
            valid_url = "https://amazon.com/dp/B08N5WRWNW"
            invalid_url = "not-a-url"

            tasks = [
                client.scrape.amazon.products_async(urls=[valid_url]),
                client.scrape.amazon.products_async(urls=[invalid_url]),
                client.scrape.amazon.products_async(urls=[valid_url]),
                client.scrape.amazon.products_async(urls=[invalid_url]),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify: Some success, some fail, no crashes
            successes = [r for r in results if not isinstance(r, Exception)]
            failures = [r for r in results if isinstance(r, Exception)]

            print(f"  Successes: {len(successes)}")
            print(f"  Failures: {len(failures)}")

            # Verify no connector errors
            connector_errors = [
                f for f in failures
                if isinstance(f, Exception) and "connector" in str(f).lower()
            ]
            assert len(connector_errors) == 0

    return asyncio.run(async_test())
```

### Priority 2: High Importance

#### Test 9: HTTP Error Codes
```python
def test_9_http_error_codes():
    """Test 9: HTTP error code handling."""
    # Requires mocking HTTP responses
    # Test 429, 500, 502, 503, 504
```

#### Test 10: Malformed API Responses
```python
def test_10_malformed_responses():
    """Test 10: Malformed API response handling."""
    # Mock invalid JSON, missing fields, wrong types
```

#### Test 11: Context Manager Error Handling
```python
def test_11_context_manager_errors():
    """Test 11: Error handling with context managers."""
    # Test errors inside and outside context
```

### Priority 3: Medium Importance

#### Test 12: Rate Limiting
```python
def test_12_rate_limiting():
    """Test 12: Rate limit error handling."""
    # Test rapid requests, verify rate limiting
```

#### Test 13: Dataset Errors
```python
def test_13_dataset_errors():
    """Test 13: Dataset-specific errors."""
    # Invalid dataset IDs, missing snapshots, etc.
```

#### Test 14: Empty Response Handling
```python
def test_14_empty_responses():
    """Test 14: Empty/null response handling."""
    # API returns empty, null, or no data
```

---

## 🚀 How to Extend

### Step 1: Choose a Category

Pick one of the missing test categories from the priority list.

### Step 2: Create Test Function

Follow the existing pattern:

```python
def test_N_category_name():
    """Test N: Description."""
    print_test("N. Category Name")

    try:
        # Test setup

        # Test execution

        # Assertions

        all_passed = True  # or calculate based on sub-tests
        return print_result(all_passed, "Description")

    except Exception as e:
        print_result(False, f"Exception: {e}")
        traceback.print_exc()
        return False
```

### Step 3: Add to Test Suite

```python
def main():
    tests = [
        test_1_invalid_token_handling,
        test_2_url_validation,
        test_3_exception_hierarchy,
        test_4_async_error_handling,
        test_5_zone_errors,
        test_6_timeout_scenarios,  # ← NEW
        test_7_network_errors,      # ← NEW
        # ... add more
    ]
```

### Step 4: Use Mocking for External Dependencies

For tests that require specific API responses:

```python
from unittest.mock import patch, AsyncMock

def test_http_500_error():
    """Test 500 error handling."""

    with patch('brightdata.core.engine.AsyncEngine._make_request') as mock:
        # Configure mock to return 500 error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock.return_value.__aenter__.return_value = mock_response

        # Test SDK handles it correctly
        client = BrightDataClient()
        # ...
```

### Step 5: Document Expected Behavior

Each test should document what behavior is expected:

```python
def test_rate_limiting():
    """Test rate limiting.

    Expected behavior:
    - SDK should detect 429 status code
    - Should wait before retrying
    - Should eventually succeed or fail gracefully
    - Should not make more requests than rate limit
    """
```

---

## 📝 Test Template

```python
def test_N_test_name():
    """Test N: Brief description.

    This test verifies:
    - Specific behavior 1
    - Specific behavior 2
    - Edge case handling

    Expected outcomes:
    - What should happen on success
    - What should happen on failure
    """
    print_test("N. Test Name")

    async def async_test():
        try:
            # Skip if preconditions not met
            if not some_precondition:
                print("  ⚠️  SKIPPED: Reason")
                return None

            client = BrightDataClient()
            async with client:

                # Test case 1
                print("  Test case 1: Description...")
                # ... test code ...
                test1_passed = True  # or False
                print(f"    Result: {test1_passed}")

                # Test case 2
                print("  Test case 2: Description...")
                # ... test code ...
                test2_passed = True  # or False
                print(f"    Result: {test2_passed}")

                all_passed = test1_passed and test2_passed
                return all_passed

        except Exception as e:
            print(f"  Unexpected error: {e}")
            traceback.print_exc()
            return False

    # Run async test
    try:
        result = asyncio.run(async_test())
        if result is not None:
            return print_result(result, "Test description")
        return None  # Skipped
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False
```

---

## 🎓 Best Practices

### 1. Test Real Scenarios
```python
# ✅ Good: Test actual error scenario
result = await scraper.scrape_async("invalid-url")
assert not result.success

# ❌ Bad: Test contrived scenario
raise ValidationError("test")  # Not realistic
```

### 2. Test Both Sync and Async
```python
# Test async version
async def test_async():
    result = await client.scrape.amazon.products_async(...)

# Test sync version
def test_sync():
    result = client.scrape.amazon.products(...)
```

### 3. Test Error Messages
```python
# Verify error messages are helpful
result = await scraper.scrape_async("invalid")
assert "invalid" in result.error.lower()
assert "url" in result.error.lower()
# User should understand what went wrong
```

### 4. Test Error Recovery
```python
# After error, SDK should still work
result1 = await scraper.scrape_async("invalid")  # Fails
result2 = await scraper.scrape_async(valid_url)  # Should work
assert result2.success  # SDK recovered
```

### 5. Use Subtests for Multiple Cases
```python
test_cases = [
    ("", "empty string"),
    ("invalid", "no protocol"),
    ("ftp://example.com", "wrong protocol"),
]

for url, description in test_cases:
    print(f"  Testing {description}...")
    # Test each case
```

---

## 📈 Coverage Goal

**Target: 80% coverage of error scenarios**

Current: ~15%
Next milestone: 40% (add Priority 1 tests)
Final goal: 80% (all priority 1 & 2 tests)

---

## 🔍 How to Find Missing Coverage

1. **Look at issue tracker**: What errors do users report?
2. **Check logs**: What errors happen in production?
3. **Review exceptions.py**: Are all exceptions tested?
4. **Read API docs**: What errors can the API return?
5. **Think about edge cases**: What could go wrong?

---

## Summary

**Current state:**
- Basic coverage of validation and auth errors
- Missing most real-world error scenarios
- No timeout, network, or concurrent error tests

**Highest priority additions:**
1. Timeout scenarios (poll timeout, fetch timeout) - **CRITICAL**
2. Network errors (connection refused, DNS, timeouts)
3. Concurrent error handling (partial failures, connector errors)
4. HTTP error codes (429, 500, 502, 503)
5. Context manager error handling

**How to extend:**
1. Pick a category from priority list
2. Write test following the template
3. Add to test suite
4. Use mocking for external dependencies
5. Document expected behavior

The test file has a good foundation but needs significant expansion to cover real-world error scenarios, especially given the issues we've discovered (ChatGPT timeout, connector errors, etc.).
