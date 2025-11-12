# Bright Data Python SDK

Modern async-first Python SDK for Bright Data APIs.

## Installation

```bash
pip install brightdata-sdk
```

## Quick Start

```python
from brightdata import BrightData

# Initialize client
client = BrightData(api_token="your_token")

# Scrape a URL
result = client.scrape("https://example.com")
print(result.data)
```

## Features

- ✅ Async-first architecture with sync wrappers
- ✅ Registry pattern for extensible scrapers
- ✅ Rich result objects with timing and metadata
- ✅ Comprehensive type hints
- ✅ Modular architecture

## Documentation

See [docs/](docs/) for complete documentation.

## License

MIT License - see [LICENSE](LICENSE) file for details.

