# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - TBD

### Added
- Initial release of the refactored Bright Data Python SDK
- Async-first architecture with sync wrappers
- Registry pattern for extensible scrapers
- Rich result objects (ScrapeResult, CrawlResult)
- Comprehensive type hints
- Modular architecture with clear separation of concerns

### Changed
- Complete rewrite from v1.x
- Minimum Python version: 3.9+

### Breaking Changes
- `bdclient` → `BrightData` (class rename)
- Returns `ScrapeResult` objects instead of raw dict/str
- Async methods require `await`

