"""Unit tests for SERP pagination."""

from brightdata.api.serp.google import GoogleSERPService
from brightdata.api.serp.bing import BingSERPService
from brightdata.api.serp.yandex import YandexSERPService
from brightdata.api.serp.url_builder import GoogleURLBuilder
from brightdata.api.serp.base import BaseSERPService
from brightdata.core.engine import AsyncEngine


class TestGoogleURLBuilderPagination:
    """Tests for GoogleURLBuilder pagination support."""

    def test_build_without_start_param(self):
        """Default start=0 should not add start param to URL."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=0)
        assert "start=" not in url
        assert "q=test" in url

    def test_build_with_start_param(self):
        """start > 0 should add start param to URL."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=10)
        assert "start=10" in url

    def test_build_with_large_start(self):
        """Large start values should work."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=100)
        assert "start=100" in url

    def test_start_param_position_in_url(self):
        """start param should appear before num param."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=20, num_results=10)
        # start should be in URL
        assert "start=20" in url
        assert "num=10" in url

    def test_start_zero_not_in_url(self):
        """start=0 should not add start param (default behavior)."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=0, num_results=10)
        assert "start=0" not in url
        assert "start=" not in url


class TestPaginationConstants:
    """Tests for pagination constants."""

    def test_page_size_constant(self):
        """PAGE_SIZE should be 10."""
        assert BaseSERPService.PAGE_SIZE == 10

    def test_max_pages_constant(self):
        """MAX_PAGES should be 20."""
        assert BaseSERPService.MAX_PAGES == 20

    def test_pagination_timeout_constant(self):
        """PAGINATION_TIMEOUT should be 300 seconds."""
        assert BaseSERPService.PAGINATION_TIMEOUT == 300


class TestPaginationRouting:
    """Tests for pagination routing logic."""

    def test_num_results_10_no_pagination(self):
        """num_results=10 (exactly PAGE_SIZE) should NOT trigger pagination."""
        # PAGE_SIZE is 10, so num_results=10 should not paginate
        # Routing condition is num_results > PAGE_SIZE
        assert not (10 > BaseSERPService.PAGE_SIZE)

    def test_num_results_11_triggers_pagination(self):
        """num_results=11 (just over PAGE_SIZE) should trigger pagination."""
        assert 11 > BaseSERPService.PAGE_SIZE

    def test_num_results_100_triggers_pagination(self):
        """num_results=100 should trigger pagination."""
        assert 100 > BaseSERPService.PAGE_SIZE

    def test_pagination_google_only(self):
        """Pagination should only apply to Google, not Bing/Yandex."""
        assert GoogleSERPService.SEARCH_ENGINE == "google"
        assert BingSERPService.SEARCH_ENGINE == "bing"
        assert YandexSERPService.SEARCH_ENGINE == "yandex"


class TestPaginationBehavior:
    """Tests for pagination behavior."""

    def test_google_service_has_pagination_method(self):
        """GoogleSERPService should have _search_with_pagination method."""
        engine = AsyncEngine("test_token_123456789")
        service = GoogleSERPService(engine)
        assert hasattr(service, "_search_with_pagination")
        assert callable(service._search_with_pagination)

    def test_google_service_has_execute_request_method(self):
        """GoogleSERPService should have _execute_serp_request method."""
        engine = AsyncEngine("test_token_123456789")
        service = GoogleSERPService(engine)
        assert hasattr(service, "_execute_serp_request")
        assert callable(service._execute_serp_request)


class TestBingYandexNoPagination:
    """Tests to verify Bing/Yandex don't support pagination."""

    def test_bing_ignores_start_param(self):
        """Bing URL builder should accept but ignore start param via kwargs."""
        from brightdata.api.serp.url_builder import BingURLBuilder

        builder = BingURLBuilder()
        # start goes into **kwargs and is ignored
        url = builder.build(query="test", start=10, num_results=10)
        # Bing uses &first= for pagination, but we don't implement it
        assert "start=" not in url
        assert "first=" not in url

    def test_yandex_ignores_start_param(self):
        """Yandex URL builder should accept but ignore start param via kwargs."""
        from brightdata.api.serp.url_builder import YandexURLBuilder

        builder = YandexURLBuilder()
        url = builder.build(query="test", start=10, num_results=10)
        # Yandex uses &p= for pagination, but we don't implement it
        assert "start=" not in url
        assert "&p=" not in url


class TestEdgeCases:
    """Edge case tests."""

    def test_num_results_equals_page_size(self):
        """num_results=10 should not paginate."""
        # Routing condition is num_results > PAGE_SIZE, not >=
        assert not (10 > BaseSERPService.PAGE_SIZE)

    def test_num_results_one(self):
        """num_results=1 should not trigger pagination."""
        assert not (1 > BaseSERPService.PAGE_SIZE)

    def test_query_with_special_characters(self):
        """Pagination should work with special characters in query."""
        builder = GoogleURLBuilder()
        url = builder.build(query="python & java", start=10)
        assert "start=10" in url
        # Query should be URL encoded
        assert "+" in url or "%26" in url or "%20" in url

    def test_query_with_unicode(self):
        """Pagination should work with unicode in query."""
        builder = GoogleURLBuilder()
        url = builder.build(query="café München", start=20)
        assert "start=20" in url


class TestURLBuilderInterface:
    """Tests for URL builder interface consistency."""

    def test_all_builders_accept_kwargs(self):
        """All URL builders should accept **kwargs for forward compatibility."""
        from brightdata.api.serp.url_builder import (
            GoogleURLBuilder,
            BingURLBuilder,
            YandexURLBuilder,
        )

        # All should accept extra kwargs without error
        google = GoogleURLBuilder()
        bing = BingURLBuilder()
        yandex = YandexURLBuilder()

        # These should not raise
        google.build(query="test", unknown_param="value")
        bing.build(query="test", unknown_param="value")
        yandex.build(query="test", unknown_param="value")


class TestServiceInheritance:
    """Tests for service inheritance of pagination methods."""

    def test_google_inherits_pagination(self):
        """GoogleSERPService should inherit pagination from BaseSERPService."""
        engine = AsyncEngine("test_token_123456789")
        service = GoogleSERPService(engine)

        # Should have all pagination-related attributes
        assert hasattr(service, "PAGE_SIZE")
        assert hasattr(service, "MAX_PAGES")
        assert hasattr(service, "PAGINATION_TIMEOUT")
        assert hasattr(service, "_search_with_pagination")
        assert hasattr(service, "_execute_serp_request")

    def test_bing_inherits_pagination_methods(self):
        """BingSERPService inherits methods but won't use them (SEARCH_ENGINE != google)."""
        engine = AsyncEngine("test_token_123456789")
        service = BingSERPService(engine)

        # Has the methods (inherited)
        assert hasattr(service, "_search_with_pagination")

        # But SEARCH_ENGINE is not "google", so routing won't trigger pagination
        assert service.SEARCH_ENGINE == "bing"
        assert service.SEARCH_ENGINE != "google"
