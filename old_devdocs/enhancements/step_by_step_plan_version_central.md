# Version Centralization Plan

## Goal

Centralize version management so that `pyproject.toml` is the **single source of truth**. All other files read from it dynamically.

---

## Current State (Problem)

Version `2.1.0` is hardcoded in **5 places**:

| File | Line | Current Code |
|------|------|--------------|
| `pyproject.toml` | 10 | `version = "2.1.0"` |
| `src/brightdata/__init__.py` | 3 | `__version__ = "2.1.0"` |
| `src/brightdata/_version.py` | 3 | `__version__ = "2.1.0"` |
| `src/brightdata/core/engine.py` | 95 | `"User-Agent": "brightdata-sdk/2.1.0"` |
| `src/brightdata/cli/main.py` | 16 | `@click.version_option(version="2.1.0")` |

**Problem**: When bumping version, you must update 5 files. Easy to miss one.

---

## Target State (Solution)

| File | Role |
|------|------|
| `pyproject.toml` | **Single source of truth** - only place to update |
| `src/brightdata/__init__.py` | Reads version via `importlib.metadata` |
| `src/brightdata/_version.py` | **Deleted** (no longer needed) |
| `src/brightdata/core/engine.py` | Imports `__version__` from package |
| `src/brightdata/cli/main.py` | Imports `__version__` from package |

---

## Step-by-Step Implementation

### Step 1: Update `__init__.py`

**File**: `src/brightdata/__init__.py`

**Change from**:
```python
__version__ = "2.1.0"
```

**Change to**:
```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("brightdata-sdk")
except PackageNotFoundError:
    # Package not installed (development mode without pip install -e)
    __version__ = "0.0.0.dev"
```

**Why try/except?**
- `importlib.metadata.version()` only works when package is installed
- During development without `pip install -e .`, it would fail
- Fallback to `"0.0.0.dev"` prevents crashes

---

### Step 2: Delete `_version.py`

**File**: `src/brightdata/_version.py`

**Action**: Delete this file entirely.

**Why?**
- It's redundant with `__init__.py`
- No other file should import from `_version.py` directly

**Check first**: Ensure nothing imports from `_version.py`:
```bash
grep -r "from.*_version" src/
grep -r "import.*_version" src/
```

---

### Step 3: Update `engine.py`

**File**: `src/brightdata/core/engine.py`

**Find** (around line 95):
```python
"User-Agent": "brightdata-sdk/2.1.0",
```

**Replace with**:
```python
"User-Agent": f"brightdata-sdk/{__version__}",
```

**Add import at top of file**:
```python
from brightdata import __version__
```

---

### Step 4: Update `cli/main.py`

**File**: `src/brightdata/cli/main.py`

**Find** (around line 16):
```python
@click.version_option(version="2.1.0", prog_name="brightdata")
```

**Replace with**:
```python
@click.version_option(version=__version__, prog_name="brightdata")
```

**Add import at top of file**:
```python
from brightdata import __version__
```

---

### Step 5: Verify `setup.py` (No changes needed)

**File**: `setup.py`

`setup.py` already reads version dynamically:
```python
def read_version():
    version_file = os.path.join("src", "brightdata", "__init__.py")
    # ... reads __version__ from file
```

**Note**: This pattern reads the literal string from the file, not the runtime value.

**Option A** (Simple): Keep as-is. It parses the file and finds `__version__ = version("brightdata-sdk")` which won't work.

**Option B** (Better): Update `setup.py` to also use `importlib.metadata`:
```python
from importlib.metadata import version
setup(
    version=version("brightdata-sdk"),
    ...
)
```

**Option C** (Best): Since you use `pyproject.toml`, you may not need `setup.py` at all. Modern Python packaging uses `pyproject.toml` exclusively.

**Recommendation**: Check if `setup.py` is still needed. If using `build` or `pip install .`, `pyproject.toml` is sufficient.

---

### Step 6: Update `pyproject.toml` (No changes needed)

**File**: `pyproject.toml`

Already correct:
```toml
[project]
name = "brightdata-sdk"
version = "2.1.0"
```

This is now the **only place** to update when bumping versions.

---

## Verification Checklist

After implementation, verify:

### 1. Package version is accessible
```python
import brightdata
print(brightdata.__version__)  # Should print "2.1.0"
```

### 2. CLI shows correct version
```bash
brightdata --version
# Should print: brightdata, version 2.1.0
```

### 3. User-Agent header is correct
```python
from brightdata import BrightDataClient
client = BrightDataClient(token="test")
# Check engine headers include "brightdata-sdk/2.1.0"
```

### 4. All tests pass
```bash
pytest tests/
```

### 5. No remaining hardcoded versions
```bash
grep -r "2\.1\.0" src/
# Should only find comments or non-version strings
```

---

## Version Bump Process (After Implementation)

**Before** (5 files):
1. Edit `pyproject.toml`
2. Edit `src/brightdata/__init__.py`
3. Edit `src/brightdata/_version.py`
4. Edit `src/brightdata/core/engine.py`
5. Edit `src/brightdata/cli/main.py`

**After** (1 file):
1. Edit `pyproject.toml` → Done!

---

## Rollback Plan

If issues arise:
1. Revert `__init__.py` to hardcoded `__version__ = "2.1.0"`
2. Restore `_version.py`
3. Revert `engine.py` and `cli/main.py` to hardcoded values

---

## Files Changed Summary

| File | Action |
|------|--------|
| `src/brightdata/__init__.py` | Modify - use `importlib.metadata` |
| `src/brightdata/_version.py` | Delete |
| `src/brightdata/core/engine.py` | Modify - import and use `__version__` |
| `src/brightdata/cli/main.py` | Modify - import and use `__version__` |
| `pyproject.toml` | No change (already source of truth) |
| `setup.py` | Review if still needed |
