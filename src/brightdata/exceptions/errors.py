"""Exception hierarchy for Bright Data SDK."""

from __future__ import annotations

from typing import Any

# Bound how much of a response body an exception retains. Error pages from
# proxies (trust_env=True is on) or CDNs can be hundreds of KB, and exceptions
# are routinely captured by loggers and error trackers.
RAW_LIMIT = 4096


def _truncate(raw: Any) -> Any:
    """Bound a retained response body, marking it when shortened."""
    if isinstance(raw, str) and len(raw) > RAW_LIMIT:
        return f"{raw[:RAW_LIMIT]}…[truncated {len(raw) - RAW_LIMIT} bytes]"
    return raw


class BrightDataError(Exception):
    """
    Base exception for all Bright Data errors.

    Carries structured context alongside the human message so callers can react
    programmatically instead of parsing the message string.

    Attributes:
        message: Short human-readable description.
        status_code: HTTP status, when the failure came from a response.
        url: URL of the failing request, when known.
        method: HTTP method of the failing request, when known.
        retry_after: Seconds parsed from a Retry-After header, when present.
        retryable: Whether repeating the operation is safe and worthwhile.
                   Defaults to False — only a raiser with enough knowledge
                   (currently the engine, for 5xx) may set it True.
        raw: Response body, truncated to RAW_LIMIT.
    """

    def __init__(
        self,
        message: str,
        *args,
        status_code: int | None = None,
        url: str | None = None,
        method: str | None = None,
        retry_after: float | None = None,
        retryable: bool = False,
        raw: Any = None,
        **kwargs,
    ):
        super().__init__(message, *args)
        self.message = message
        self.status_code = status_code
        self.url = url
        self.method = method
        self.retry_after = retry_after
        self.retryable = retryable
        self.raw = _truncate(raw)


class ValidationError(BrightDataError):
    """Input validation failed."""

    pass


class AuthenticationError(BrightDataError):
    """Authentication or authorization failed."""

    pass


class APIError(BrightDataError):
    """API request failed."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_text: str | None = None,
        *args,
        **kwargs,
    ):
        # status_code stays the second positional parameter for backwards
        # compatibility (APIError("msg", 429) is legal); drop any duplicate
        # keyword before forwarding it to the base.
        kwargs.pop("status_code", None)
        super().__init__(message, *args, status_code=status_code, **kwargs)
        self.response_text = response_text


class RateLimitError(APIError):
    """
    HTTP 429 — request rate or quota exceeded.

    Never marked retryable: on the Bright Data API a 429 response itself
    consumes quota, so retrying extends the lockout rather than waiting it out.
    Use `retry_after` to decide how long to pause.
    """

    pass


class DataNotReadyError(BrightDataError):
    """Data is not ready yet (HTTP 202). Should retry."""

    pass


class ZoneError(BrightDataError):
    """Zone operation failed."""

    pass


class NetworkError(BrightDataError):
    """Network connectivity issue."""

    pass


class SSLError(BrightDataError):
    """
    SSL certificate verification error.

    Common on macOS where Python doesn't have access to system certificates.
    """

    pass
