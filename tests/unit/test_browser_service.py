"""Unit tests for BrowserService and client.browser integration."""

import os
import pytest
from unittest.mock import patch

from brightdata import BrightDataClient, BrowserService
from brightdata.exceptions import ValidationError


class TestBrowserServiceURL:
    """Test BrowserService URL construction."""

    def test_get_connect_url_basic(self):
        """Test basic URL with default host and port."""
        service = BrowserService(username="brd-customer-abc", password="mypass")
        url = service.get_connect_url()
        assert url == "wss://brd-customer-abc:mypass@brd.superproxy.io:9222"

    def test_get_connect_url_custom_host_port(self):
        """Test URL with custom host and port."""
        service = BrowserService(
            username="brd-customer-abc",
            password="mypass",
            host="custom.host",
            port=1234,
        )
        url = service.get_connect_url()
        assert url == "wss://brd-customer-abc:mypass@custom.host:1234"

    def test_get_connect_url_with_country(self):
        """Test country code is appended to username."""
        service = BrowserService(username="brd-customer-abc", password="mypass")
        url = service.get_connect_url(country="us")
        assert url == "wss://brd-customer-abc-country-us:mypass@brd.superproxy.io:9222"

    def test_get_connect_url_country_none(self):
        """Test no country suffix when country is None."""
        service = BrowserService(username="brd-customer-abc", password="mypass")
        url = service.get_connect_url(country=None)
        assert "-country-" not in url

    def test_get_connect_url_country_empty_string(self):
        """Test no country suffix when country is empty string."""
        service = BrowserService(username="brd-customer-abc", password="mypass")
        url = service.get_connect_url(country="")
        assert "-country-" not in url

    def test_get_connect_url_realistic_credentials(self):
        """Test with realistic Bright Data credentials."""
        service = BrowserService(
            username="brd-customer-hl_67e5ed38-zone-scraping_browser1",
            password="7a9t2k84jhl8",
        )
        url = service.get_connect_url()
        assert url == (
            "wss://brd-customer-hl_67e5ed38-zone-scraping_browser1"
            ":7a9t2k84jhl8@brd.superproxy.io:9222"
        )

    def test_get_connect_url_realistic_with_country(self):
        """Test realistic credentials with country targeting."""
        service = BrowserService(
            username="brd-customer-hl_67e5ed38-zone-scraping_browser1",
            password="7a9t2k84jhl8",
        )
        url = service.get_connect_url(country="gb")
        assert "-zone-scraping_browser1-country-gb:" in url


class TestClientBrowserProperty:
    """Test BrightDataClient.browser property integration."""

    def test_browser_raises_without_credentials(self):
        """Test ValidationError when no credentials provided."""
        with patch.dict(os.environ, {}, clear=True):
            # Need to also clear BRIGHTDATA_API_TOKEN so we pass token explicitly
            client = BrightDataClient(token="test_token_123456789")
            with pytest.raises(ValidationError) as exc_info:
                _ = client.browser

            assert "Browser API credentials not provided" in str(exc_info.value)
            assert "BRIGHTDATA_BROWSERAPI_USERNAME" in str(exc_info.value)

    def test_browser_from_constructor_params(self):
        """Test browser service created from constructor params."""
        client = BrightDataClient(
            token="test_token_123456789",
            browser_username="brd-customer-abc",
            browser_password="mypass",
        )
        url = client.browser.get_connect_url()
        assert url == "wss://brd-customer-abc:mypass@brd.superproxy.io:9222"

    def test_browser_from_env_vars(self):
        """Test browser service reads from environment variables."""
        env = {
            "BRIGHTDATA_BROWSERAPI_USERNAME": "brd-customer-env",
            "BRIGHTDATA_BROWSERAPI_PASSWORD": "envpass",
        }
        with patch.dict(os.environ, env):
            client = BrightDataClient(token="test_token_123456789")
            url = client.browser.get_connect_url()
            assert url == "wss://brd-customer-env:envpass@brd.superproxy.io:9222"

    def test_browser_params_override_env(self):
        """Test explicit params take precedence over env vars."""
        env = {
            "BRIGHTDATA_BROWSERAPI_USERNAME": "brd-customer-env",
            "BRIGHTDATA_BROWSERAPI_PASSWORD": "envpass",
        }
        with patch.dict(os.environ, env):
            client = BrightDataClient(
                token="test_token_123456789",
                browser_username="brd-customer-explicit",
                browser_password="explicitpass",
            )
            url = client.browser.get_connect_url()
            assert "brd-customer-explicit" in url
            assert "explicitpass" in url
            assert "brd-customer-env" not in url

    def test_browser_lazy_creation(self):
        """Test BrowserService is not created until .browser is accessed."""
        client = BrightDataClient(
            token="test_token_123456789",
            browser_username="brd-customer-abc",
            browser_password="mypass",
        )
        assert client._browser_service is None
        _ = client.browser
        assert client._browser_service is not None

    def test_browser_is_cached(self):
        """Test browser property returns same instance on repeated access."""
        client = BrightDataClient(
            token="test_token_123456789",
            browser_username="brd-customer-abc",
            browser_password="mypass",
        )
        service1 = client.browser
        service2 = client.browser
        assert service1 is service2

    def test_browser_custom_host_port(self):
        """Test custom host and port passed through client."""
        client = BrightDataClient(
            token="test_token_123456789",
            browser_username="brd-customer-abc",
            browser_password="mypass",
            browser_host="custom.proxy.io",
            browser_port=8888,
        )
        url = client.browser.get_connect_url()
        assert url == "wss://brd-customer-abc:mypass@custom.proxy.io:8888"

    def test_browser_raises_with_only_username(self):
        """Test ValidationError when only username is provided (no password)."""
        with patch.dict(os.environ, {}, clear=True):
            client = BrightDataClient(
                token="test_token_123456789",
                browser_username="brd-customer-abc",
            )
            with pytest.raises(ValidationError):
                _ = client.browser

    def test_browser_raises_with_only_password(self):
        """Test ValidationError when only password is provided (no username)."""
        with patch.dict(os.environ, {}, clear=True):
            client = BrightDataClient(
                token="test_token_123456789",
                browser_password="mypass",
            )
            with pytest.raises(ValidationError):
                _ = client.browser


class TestSyncClientBrowserProperty:
    """Test SyncBrightDataClient.browser property."""

    def test_sync_client_browser_property(self):
        """Test SyncBrightDataClient.browser returns BrowserService."""
        from brightdata import SyncBrightDataClient

        client = SyncBrightDataClient(
            token="test_token_123456789",
            browser_username="brd-customer-abc",
            browser_password="mypass",
        )
        service = client.browser
        assert isinstance(service, BrowserService)
        url = service.get_connect_url()
        assert url == "wss://brd-customer-abc:mypass@brd.superproxy.io:9222"
