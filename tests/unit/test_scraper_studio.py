"""Unit tests for Scraper Studio service."""

import inspect

from brightdata import BrightDataClient, ScraperStudioJob, JobStatus, ScraperStudioService
from brightdata.scraper_studio.client import ScraperStudioAPIClient


class TestJobStatus:
    """Test JobStatus dataclass."""

    def test_job_status_from_api_response(self):
        """Test parsing API response into JobStatus."""
        raw = {
            "id": "j_abc123",
            "status": "done",
            "collector": "c_xyz789",
            "inputs": 1,
            "lines": 60,
            "fails": 0,
            "success_rate": 1.0,
            "created": "2026-02-07T00:00:00.000Z",
            "started": "2026-02-07T00:00:01.000Z",
            "finished": "2026-02-07T00:01:12.000Z",
            "job_time": 71459,
            "queue_time": 645,
        }
        status = JobStatus.from_api_response(raw)

        assert status.id == "j_abc123"
        assert status.status == "done"
        assert status.collector == "c_xyz789"
        assert status.inputs == 1
        assert status.lines == 60
        assert status.fails == 0
        assert status.success_rate == 1.0
        assert status.job_time == 71459
        assert status.queue_time == 645

    def test_job_status_handles_mixed_case(self):
        """Test parsing API response with mixed-case field names."""
        raw = {
            "Id": "j_abc123",
            "Status": "done",
            "Collector": "c_xyz789",
            "Inputs": 1,
            "Lines": 60,
            "Fails": 0,
            "Success_rate": 1.0,
            "created": "2026-02-07T00:00:00.000Z",
            "started": "2026-02-07T00:00:01.000Z",
            "finished": "2026-02-07T00:01:12.000Z",
            "Job_time": 71459,
            "Queue_time": 645,
        }
        status = JobStatus.from_api_response(raw)

        assert status.id == "j_abc123"
        assert status.status == "done"
        assert status.collector == "c_xyz789"
        assert status.success_rate == 1.0
        assert status.job_time == 71459
        assert status.queue_time == 645

    def test_job_status_handles_missing_optional_fields(self):
        """Test parsing response with missing optional fields."""
        raw = {
            "id": "j_abc123",
            "status": "queued",
            "collector": "c_xyz789",
        }
        status = JobStatus.from_api_response(raw)

        assert status.id == "j_abc123"
        assert status.status == "queued"
        assert status.started is None
        assert status.finished is None
        assert status.job_time is None
        assert status.queue_time is None

    def test_job_status_direct_construction(self):
        """Test direct construction of JobStatus."""
        status = JobStatus(
            id="j_test",
            status="running",
            collector="c_test",
            inputs=5,
            lines=3,
            fails=2,
            success_rate=0.6,
            created="2026-01-01T00:00:00Z",
        )
        assert status.id == "j_test"
        assert status.inputs == 5
        assert status.success_rate == 0.6


class TestScraperStudioJob:
    """Test ScraperStudioJob model."""

    def test_job_attributes(self):
        """Test ScraperStudioJob has correct attributes."""
        job = ScraperStudioJob.__new__(ScraperStudioJob)
        job.response_id = "resp_abc123"
        job._api_client = None
        job._cached_data = None

        assert job.response_id == "resp_abc123"

    def test_job_repr(self):
        """Test ScraperStudioJob repr."""
        job = ScraperStudioJob.__new__(ScraperStudioJob)
        job.response_id = "resp_abc123"
        job._api_client = None
        job._cached_data = None

        assert "resp_abc123" in repr(job)

    def test_job_has_fetch_method(self):
        """Test ScraperStudioJob has fetch method."""
        assert hasattr(ScraperStudioJob, "fetch")
        assert callable(getattr(ScraperStudioJob, "fetch"))

    def test_job_has_wait_and_fetch_method(self):
        """Test ScraperStudioJob has wait_and_fetch method."""
        assert hasattr(ScraperStudioJob, "wait_and_fetch")
        assert callable(getattr(ScraperStudioJob, "wait_and_fetch"))

    def test_wait_and_fetch_signature(self):
        """Test wait_and_fetch method signature."""
        sig = inspect.signature(ScraperStudioJob.wait_and_fetch)
        assert "timeout" in sig.parameters
        assert "poll_interval" in sig.parameters
        assert sig.parameters["timeout"].default == 300
        assert sig.parameters["poll_interval"].default == 10


class TestScraperStudioAPIClient:
    """Test ScraperStudioAPIClient."""

    def test_client_has_trigger_immediate(self):
        """Test API client has trigger_immediate method."""
        assert hasattr(ScraperStudioAPIClient, "trigger_immediate")
        assert callable(getattr(ScraperStudioAPIClient, "trigger_immediate"))

    def test_client_has_fetch_immediate_result(self):
        """Test API client has fetch_immediate_result method."""
        assert hasattr(ScraperStudioAPIClient, "fetch_immediate_result")
        assert callable(getattr(ScraperStudioAPIClient, "fetch_immediate_result"))

    def test_client_has_get_status(self):
        """Test API client has get_status method."""
        assert hasattr(ScraperStudioAPIClient, "get_status")
        assert callable(getattr(ScraperStudioAPIClient, "get_status"))

    def test_trigger_immediate_signature(self):
        """Test trigger_immediate method signature."""
        sig = inspect.signature(ScraperStudioAPIClient.trigger_immediate)
        assert "collector" in sig.parameters
        assert "input" in sig.parameters

    def test_fetch_immediate_result_signature(self):
        """Test fetch_immediate_result method signature."""
        sig = inspect.signature(ScraperStudioAPIClient.fetch_immediate_result)
        assert "response_id" in sig.parameters

    def test_get_status_signature(self):
        """Test get_status method signature."""
        sig = inspect.signature(ScraperStudioAPIClient.get_status)
        assert "job_id" in sig.parameters


class TestScraperStudioService:
    """Test ScraperStudioService."""

    def test_service_has_run_method(self):
        """Test service has run method."""
        assert hasattr(ScraperStudioService, "run")
        assert callable(getattr(ScraperStudioService, "run"))

    def test_service_has_trigger_method(self):
        """Test service has trigger method."""
        assert hasattr(ScraperStudioService, "trigger")
        assert callable(getattr(ScraperStudioService, "trigger"))

    def test_service_has_status_method(self):
        """Test service has status method."""
        assert hasattr(ScraperStudioService, "status")
        assert callable(getattr(ScraperStudioService, "status"))

    def test_service_has_fetch_method(self):
        """Test service has fetch method."""
        assert hasattr(ScraperStudioService, "fetch")
        assert callable(getattr(ScraperStudioService, "fetch"))

    def test_run_method_signature(self):
        """Test run method signature."""
        sig = inspect.signature(ScraperStudioService.run)
        assert "collector" in sig.parameters
        assert "input" in sig.parameters
        assert "timeout" in sig.parameters
        assert "poll_interval" in sig.parameters
        assert sig.parameters["timeout"].default == 180
        assert sig.parameters["poll_interval"].default == 10

    def test_trigger_method_signature(self):
        """Test trigger method signature."""
        sig = inspect.signature(ScraperStudioService.trigger)
        assert "collector" in sig.parameters
        assert "input" in sig.parameters

    def test_status_method_signature(self):
        """Test status method signature."""
        sig = inspect.signature(ScraperStudioService.status)
        assert "job_id" in sig.parameters

    def test_fetch_method_signature(self):
        """Test fetch method signature."""
        sig = inspect.signature(ScraperStudioService.fetch)
        assert "response_id" in sig.parameters


class TestScraperStudioClientIntegration:
    """Test Scraper Studio integration with BrightDataClient."""

    def test_client_has_scraper_studio_property(self):
        """Test BrightDataClient has scraper_studio property."""
        client = BrightDataClient(token="test_token_123456789")
        assert hasattr(client, "scraper_studio")

    def test_scraper_studio_returns_service_instance(self):
        """Test scraper_studio property returns ScraperStudioService."""
        client = BrightDataClient(token="test_token_123456789")
        service = client.scraper_studio
        assert isinstance(service, ScraperStudioService)

    def test_scraper_studio_lazy_loaded(self):
        """Test scraper_studio property is lazy-loaded (same instance)."""
        client = BrightDataClient(token="test_token_123456789")
        service1 = client.scraper_studio
        service2 = client.scraper_studio
        assert service1 is service2


class TestSyncScraperStudioService:
    """Test sync Scraper Studio service."""

    def test_sync_client_has_scraper_studio_property(self):
        """Test SyncBrightDataClient has scraper_studio property."""
        from brightdata import SyncBrightDataClient

        assert hasattr(SyncBrightDataClient, "scraper_studio")

    def test_sync_service_has_all_methods(self):
        """Test SyncScraperStudioService has run, trigger, status, fetch."""
        from brightdata.sync_client import SyncScraperStudioService

        assert hasattr(SyncScraperStudioService, "run")
        assert hasattr(SyncScraperStudioService, "trigger")
        assert hasattr(SyncScraperStudioService, "status")
        assert hasattr(SyncScraperStudioService, "fetch")


class TestExports:
    """Test public API exports."""

    def test_scraper_studio_job_exported(self):
        """Test ScraperStudioJob is exported from brightdata."""
        from brightdata import ScraperStudioJob

        assert ScraperStudioJob is not None

    def test_job_status_exported(self):
        """Test JobStatus is exported from brightdata."""
        from brightdata import JobStatus

        assert JobStatus is not None

    def test_scraper_studio_service_exported(self):
        """Test ScraperStudioService is exported from brightdata."""
        from brightdata import ScraperStudioService

        assert ScraperStudioService is not None
