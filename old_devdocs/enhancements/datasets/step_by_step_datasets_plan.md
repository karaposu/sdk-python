# Datasets API Implementation Plan

## Overview

Add a new `client.datasets` namespace to the SDK for interacting with Bright Data's pre-collected datasets.

**Scope (4 methods):**
1. `client.datasets.list()` - List all available datasets
2. `client.datasets.{domain}.get_metadata()` - Get field schema for a dataset
3. `client.datasets.{domain}.filter()` - Trigger filter, returns snapshot_id
4. `client.datasets.{domain}.download()` - Poll + download snapshot data

---

## API Design

### Usage Pattern

```python
async with BrightDataClient() as client:
    # 1. List all available datasets
    datasets = await client.datasets.list()
    # Returns: [{"id": "gd_l1viktl72bvl7bjuj0", "name": "LinkedIn Profiles", "size": 620000000}, ...]

    # 2. Access a specific dataset and get metadata
    metadata = await client.datasets.linkedin_profiles.get_metadata()
    # Returns field names, types, descriptions

    # 3. Filter the dataset (returns snapshot_id immediately, no polling)
    snapshot_id = await client.datasets.linkedin_profiles.filter(
        filter={
            "name": "industry",
            "operator": "=",
            "value": "Technology"
        },
        records_limit=100
    )
    # snapshot_id is just a string: "snap_xxx"

    # 4. Download data separately (handles polling internally)
    data = await client.datasets.linkedin_profiles.download(snapshot_id)
    # Returns: [{"name": "John", "industry": "Technology", ...}, ...]
```

### Why This Pattern?

**Mirrors scraper pattern:**
```python
# Scrapers
client.scraper.linkedin.profiles(urls=[...])

# Datasets
client.datasets.linkedin_profiles.filter(filter={...})
```

**Domain-specific access:**
- `client.datasets.linkedin_profiles` - LinkedIn people profiles
- `client.datasets.linkedin_companies` - LinkedIn companies
- `client.datasets.amazon_products` - Amazon products
- `client.datasets.crunchbase_companies` - Crunchbase companies

Each domain object knows its dataset ID and provides `.filter()` method.

### Filter Fields are Per-Dataset

Each dataset has its own schema with different filterable fields:

| Dataset | Example Fields |
|---------|----------------|
| LinkedIn Profiles | `name`, `industry`, `followers`, `position`, `city`, `country_code`, `connections` |
| LinkedIn Companies | `name`, `company_size`, `headquarters`, `industry`, `founded`, `employees_in_linkedin` |
| Amazon Products | `title`, `price`, `rating`, `category`, `seller`, `reviews_count` |
| Crunchbase Companies | `name`, `funding`, `founded_on`, `num_employees`, `categories` |

**This is why `get_metadata()` matters** - users should call it first to discover what fields they can filter by:

```python
# Discover available fields before filtering
metadata = await client.datasets.linkedin_profiles.get_metadata()
print(metadata.fields.keys())
# ['name', 'industry', 'followers', 'position', 'city', ...]

# Now filter using valid fields
snapshot_id = await client.datasets.linkedin_profiles.filter(
    filter={"name": "followers", "operator": ">", "value": 10000}
)
```

---

## Step 1: Create Module Structure ✅ DONE

**Location:** `src/brightdata/datasets/`

```
src/brightdata/datasets/
├── __init__.py              # Exports all classes
├── client.py                # DatasetsClient with list() + properties
├── base.py                  # BaseDataset (shared logic)
├── models.py                # DatasetInfo, SnapshotStatus, etc.
├── linkedin/
│   ├── __init__.py
│   ├── people_profiles.py   # LinkedInPeopleProfiles
│   └── company_profiles.py  # LinkedInCompanyProfiles
├── amazon/
│   ├── __init__.py
│   └── products.py          # AmazonProducts
└── crunchbase/
    ├── __init__.py
    └── companies.py         # CrunchbaseCompanies
```

**Reasoning:** Mirrors scraper structure (`scrapers/linkedin/`, `scrapers/amazon/`). Each dataset has its own file with dataset-specific documentation and fields.

---

## Step 2: Define Models ✅ DONE

**File:** `src/brightdata/datasets/models.py`

```python
@dataclass
class DatasetInfo:
    """Returned by list()"""
    id: str
    name: str
    size: int  # record count

@dataclass
class DatasetField:
    """Field metadata"""
    type: str  # "text", "number", "url", "array", "object", "boolean"
    active: bool = True
    required: bool = False
    description: Optional[str] = None

@dataclass
class DatasetMetadata:
    """Returned by get_metadata()"""
    id: str
    fields: Dict[str, DatasetField]

@dataclass
class SnapshotStatus:
    """Returned when checking snapshot status"""
    id: str
    status: Literal["scheduled", "building", "ready", "failed"]
    dataset_id: Optional[str] = None
    dataset_size: Optional[int] = None  # records in snapshot
    file_size: Optional[int] = None     # bytes
    cost: Optional[float] = None
    error: Optional[str] = None
```

---

## Step 3: Implement BaseDataset Class ✅ DONE

**File:** `src/brightdata/datasets/base.py`

```python
class BaseDataset:
    """Base class for all dataset types."""

    DATASET_ID: str = ""  # Override in subclasses
    NAME: str = ""        # Override in subclasses

    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._metadata: Optional[DatasetMetadata] = None

    async def get_metadata(self) -> DatasetMetadata:
        """GET /datasets/{dataset_id}/metadata"""
        ...

    async def filter(
        self,
        filter: Dict[str, Any],
        records_limit: Optional[int] = None,
    ) -> str:
        """POST /datasets/filter - returns snapshot_id"""
        ...

    async def get_status(self, snapshot_id: str) -> SnapshotStatus:
        """GET /datasets/snapshots/{id} - check status"""
        ...

    async def download(
        self,
        snapshot_id: str,
        format: Literal["json", "jsonl", "csv"] = "jsonl",
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> List[Dict[str, Any]]:
        """GET /datasets/snapshots/{id}/download - polls + returns data"""
        ...
```

**Reasoning:**
- `filter()` returns immediately with snapshot_id (like `trigger_collection()`)
- `get_status()` lets users check progress manually if needed
- `download()` handles polling + download in one call
- Separation allows users to trigger many filters, then download later
- Large datasets may take hours - users control when to wait

---

## Step 4: Implement Dataset Classes ✅ DONE

Each dataset inherits from `BaseDataset` and sets its own `DATASET_ID`:

**File:** `src/brightdata/datasets/linkedin/people_profiles.py` ✅ COMPLETE (42 fields with metadata)
```python
class LinkedInPeopleProfiles(BaseDataset):
    DATASET_ID = "gd_l1viktl72bvl7bjuj0"
    NAME = "linkedin_people_profiles"
    # 620M+ profiles, 42 fields with type, description, fill_rate
    FIELDS: Dict[str, Dict[str, Any]] = {
        "id": {"type": "text", "description": "...", "fill_rate": 100.00},
        "name": {"type": "text", "description": "Profile name", "fill_rate": 97.54},
        # ... 42 total fields
    }

    @classmethod
    def get_field_names(cls) -> list: ...
    @classmethod
    def get_high_fill_rate_fields(cls, min_rate: float = 50.0) -> list: ...
```

**File:** `src/brightdata/datasets/linkedin/company_profiles.py` ✅ COMPLETE (36 fields with metadata)
```python
class LinkedInCompanyProfiles(BaseDataset):
    DATASET_ID = "gd_l1vikfnt1wgvvqz95w"
    NAME = "linkedin_company_profiles"
    # 58.5M+ companies, 36 fields with type, description
    FIELDS: Dict[str, Dict[str, Any]] = {
        "id": {"type": "text", "description": "..."},
        "name": {"type": "text", "description": "Company name"},
        # ... 36 total fields
    }

    @classmethod
    def get_field_names(cls) -> list: ...
    @classmethod
    def get_text_fields(cls) -> list: ...
```

**File:** `src/brightdata/datasets/amazon/products.py` ✅ COMPLETE (85 fields with metadata)
```python
class AmazonProducts(BaseDataset):
    DATASET_ID = "gd_l7q7dkf244hwjntr0"
    NAME = "amazon_products"
    # 85 fields with type, description
    FIELDS: Dict[str, Dict[str, Any]] = {
        "title": {"type": "text", "description": "Product title/name"},
        "asin": {"type": "text", "description": "Amazon Standard Identification Number"},
        # ... 85 total fields
    }

    @classmethod
    def get_field_names(cls) -> list: ...
    @classmethod
    def get_fields_by_type(cls, field_type: str) -> list: ...
    @classmethod
    def get_pricing_fields(cls) -> list: ...
```

**File:** `src/brightdata/datasets/crunchbase/companies.py` ✅ COMPLETE (98 fields with metadata)
```python
class CrunchbaseCompanies(BaseDataset):
    DATASET_ID = "gd_l1vijqt9jfj7olije"
    NAME = "crunchbase_companies"
    # 2.3M+ companies, 98 fields with type, description, fill_rate
    FIELDS: Dict[str, Dict[str, Any]] = {
        "name": {"type": "text", "description": "...", "fill_rate": 100.00},
        "cb_rank": {"type": "number", "description": "...", "fill_rate": 97.02},
        # ... 98 total fields
    }

    @classmethod
    def get_field_names(cls) -> list: ...
    @classmethod
    def get_high_fill_rate_fields(cls, min_rate: float = 50.0) -> list: ...
    @classmethod
    def get_fields_by_type(cls, field_type: str) -> list: ...
```

---

## Step 5: Implement DatasetsClient ✅ DONE

**File:** `src/brightdata/datasets/client.py`

```python
class DatasetsClient:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._linkedin_profiles: Optional[LinkedInPeopleProfiles] = None
        self._linkedin_companies: Optional[LinkedInCompanyProfiles] = None
        self._amazon_products: Optional[AmazonProducts] = None
        self._crunchbase_companies: Optional[CrunchbaseCompanies] = None

    async def list(self) -> List[DatasetInfo]:
        """GET /datasets/list"""
        ...

    @property
    def linkedin_profiles(self) -> LinkedInPeopleProfiles:
        if self._linkedin_profiles is None:
            self._linkedin_profiles = LinkedInPeopleProfiles(self._engine)
        return self._linkedin_profiles

    @property
    def linkedin_companies(self) -> LinkedInCompanyProfiles:
        ...

    @property
    def amazon_products(self) -> AmazonProducts:
        ...

    @property
    def crunchbase_companies(self) -> CrunchbaseCompanies:
        ...
```

**Reasoning:**
- Properties provide IDE autocomplete: `client.datasets.linkedin_profiles`
- Lazy initialization of dataset objects

---

## Step 6: Integrate with BrightDataClient ✅ DONE

**File:** `src/brightdata/client.py`

```python
from brightdata.datasets import DatasetsClient

class BrightDataClient:
    def __init__(self, ...):
        ...
        self._datasets_client: Optional[DatasetsClient] = None

    @property
    def datasets(self) -> DatasetsClient:
        if self._datasets_client is None:
            self._datasets_client = DatasetsClient(self.engine)
        return self._datasets_client
```

---

## Step 7: Error Handling

| HTTP Code | Error | SDK Exception |
|-----------|-------|---------------|
| 400 | Invalid filter syntax | `ValidationError` |
| 401 | Bad API key | `AuthenticationError` |
| 402 | Insufficient funds | `InsufficientFundsError` |
| 404 | Dataset not found | `NotFoundError` |
| 422 | Filter matched 0 records | `NoMatchError` (new) |
| 429 | Too many jobs | `RateLimitError` |

---

## Step 8: Testing

- [ ] Unit tests for models
- [ ] Unit tests for filter/download logic
- [ ] Integration tests with real API
- [ ] Notebook demonstration

---

## Example Usage (Final API)

```python
from brightdata import BrightDataClient

async with BrightDataClient() as client:
    # List all datasets
    all_datasets = await client.datasets.list()
    print(f"Available: {len(all_datasets)} datasets")

    # Get LinkedIn profiles metadata
    metadata = await client.datasets.linkedin_profiles.get_metadata()
    print(f"Fields: {list(metadata.fields.keys())}")

    # Filter for tech industry profiles with 10k+ followers
    snapshot_id = await client.datasets.linkedin_profiles.filter(
        filter={
            "operator": "and",
            "filters": [
                {"name": "industry", "operator": "=", "value": "Technology"},
                {"name": "followers", "operator": ">", "value": 10000}
            ]
        },
        records_limit=100
    )
    print(f"Snapshot created: {snapshot_id}")

    # Optionally check status manually
    status = await client.datasets.linkedin_profiles.get_status(snapshot_id)
    print(f"Status: {status.status}")

    # Download data (polls until ready, then returns data)
    data = await client.datasets.linkedin_profiles.download(snapshot_id)
    print(f"Found {len(data)} profiles")
    for profile in data[:5]:
        print(f"  - {profile['name']}: {profile['position']}")
```

---

## Success Criteria

- [x] `client.datasets.list()` returns available datasets
- [x] `client.datasets.linkedin_profiles.get_metadata()` returns field schema
- [x] `client.datasets.linkedin_profiles.filter(...)` returns snapshot_id
- [x] `client.datasets.linkedin_profiles.get_status(id)` returns snapshot status
- [x] `client.datasets.linkedin_profiles.download(id)` polls and returns data
- [ ] Errors map to SDK exceptions
- [ ] Notebook demonstrates workflow
