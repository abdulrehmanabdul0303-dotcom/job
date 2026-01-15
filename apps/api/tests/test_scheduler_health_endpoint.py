"""
Tests for scheduler health check endpoint.

Tests the /api/v1/scheduler/health endpoint.
"""
import pytest
from httpx import AsyncClient
from app.services.scheduler_monitor import get_monitor, JobStatus


@pytest.mark.asyncio
class TestSchedulerHealthEndpoint:
    """Test scheduler health check endpoint."""
    
    async def test_scheduler_health_endpoint_exists(self, client: AsyncClient):
        """Test that scheduler health endpoint exists."""
        response = await client.get("/api/v1/scheduler/health")
        
        assert response.status_code == 200
    
    async def test_scheduler_health_response_structure(self, client: AsyncClient):
        """Test scheduler health response structure."""
        response = await client.get("/api/v1/scheduler/health")
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "summary" in data
        assert "jobs" in data
        assert "recent_failures" in data
        
        assert data["service"] == "jobpilot-scheduler"
    
    async def test_scheduler_health_summary_structure(self, client: AsyncClient):
        """Test scheduler health summary structure."""
        response = await client.get("/api/v1/scheduler/health")
        data = response.json()
        
        summary = data["summary"]
        assert "is_healthy" in summary
        assert "total_jobs" in summary
        assert "healthy_jobs" in summary
        assert "unhealthy_jobs" in summary
        assert "overdue_jobs" in summary
        assert "stuck_jobs" in summary
        assert "failed_jobs" in summary
        assert "never_run_jobs" in summary
        assert "timestamp" in summary
    
    async def test_scheduler_health_jobs_structure(self, client: AsyncClient):
        """Test scheduler health jobs structure."""
        # Register a test job
        monitor = get_monitor()
        monitor.register_job("test_job", "Test Job", expected_interval_minutes=60)
        
        response = await client.get("/api/v1/scheduler/health")
        data = response.json()
        
        jobs = data["jobs"]
        assert isinstance(jobs, list)
        
        if len(jobs) > 0:
            job = jobs[0]
            assert "job_id" in job
            assert "job_name" in job
            assert "status" in job
            assert "last_execution" in job
            assert "statistics" in job
            assert "health" in job
            assert "config" in job
    
    async def test_scheduler_health_with_successful_job(self, client: AsyncClient):
        """Test scheduler health with a successful job execution."""
        monitor = get_monitor()
        
        # Clear any existing state
        monitor._executions.clear()
        monitor._last_execution.clear()
        monitor._job_configs.clear()
        
        # Register and run a job successfully
        monitor.register_job("test_success", "Test Success Job")
        execution = monitor.start_execution("test_success", "Test Success Job")
        monitor.complete_execution(execution, JobStatus.SUCCESS, metrics={"items": 100})
        
        response = await client.get("/api/v1/scheduler/health")
        data = response.json()
        
        # Find our test job
        test_job = next((j for j in data["jobs"] if j["job_id"] == "test_success"), None)
        assert test_job is not None
        assert test_job["status"] == JobStatus.SUCCESS
        assert test_job["statistics"]["successful_executions"] == 1
        assert test_job["statistics"]["failed_executions"] == 0
    
    async def test_scheduler_health_with_failed_job(self, client: AsyncClient):
        """Test scheduler health with a failed job execution."""
        monitor = get_monitor()
        
        # Clear any existing state
        monitor._executions.clear()
        monitor._last_execution.clear()
        monitor._job_configs.clear()
        
        # Register and run a job with failure
        monitor.register_job("test_failure", "Test Failure Job")
        execution = monitor.start_execution("test_failure", "Test Failure Job")
        monitor.complete_execution(
            execution,
            JobStatus.FAILED,
            error_message="Test error"
        )
        
        response = await client.get("/api/v1/scheduler/health")
        data = response.json()
        
        # Find our test job
        test_job = next((j for j in data["jobs"] if j["job_id"] == "test_failure"), None)
        assert test_job is not None
        assert test_job["status"] == JobStatus.FAILED
        assert test_job["health"]["is_healthy"] is False
        
        # Should appear in recent failures
        failures = data["recent_failures"]
        test_failure = next((f for f in failures if f["job_id"] == "test_failure"), None)
        assert test_failure is not None
        assert test_failure["error_message"] == "Test error"
    
    async def test_scheduler_health_status_healthy(self, client: AsyncClient):
        """Test that status is 'healthy' when all jobs are healthy."""
        monitor = get_monitor()
        
        # Clear any existing state
        monitor._executions.clear()
        monitor._last_execution.clear()
        monitor._job_configs.clear()
        
        # Register and run jobs successfully
        for i in range(3):
            job_id = f"healthy_job_{i}"
            monitor.register_job(job_id, f"Healthy Job {i}")
            execution = monitor.start_execution(job_id, f"Healthy Job {i}")
            monitor.complete_execution(execution, JobStatus.SUCCESS)
        
        response = await client.get("/api/v1/scheduler/health")
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["summary"]["is_healthy"] is True
    
    async def test_scheduler_health_status_unhealthy(self, client: AsyncClient):
        """Test that status is 'unhealthy' when any job is unhealthy."""
        monitor = get_monitor()
        
        # Clear any existing state
        monitor._executions.clear()
        monitor._last_execution.clear()
        monitor._job_configs.clear()
        
        # One successful job
        monitor.register_job("healthy_job", "Healthy Job")
        execution = monitor.start_execution("healthy_job", "Healthy Job")
        monitor.complete_execution(execution, JobStatus.SUCCESS)
        
        # One failed job
        monitor.register_job("unhealthy_job", "Unhealthy Job")
        execution = monitor.start_execution("unhealthy_job", "Unhealthy Job")
        monitor.complete_execution(execution, JobStatus.FAILED, error_message="Error")
        
        response = await client.get("/api/v1/scheduler/health")
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["summary"]["is_healthy"] is False
        assert data["summary"]["failed_jobs"] >= 1
    
    async def test_scheduler_health_recent_failures_limit(self, client: AsyncClient):
        """Test that recent failures are limited to 5."""
        monitor = get_monitor()
        
        # Clear any existing state
        monitor._executions.clear()
        monitor._last_execution.clear()
        monitor._job_configs.clear()
        
        # Create 10 failed jobs
        for i in range(10):
            job_id = f"failed_job_{i}"
            execution = monitor.start_execution(job_id, f"Failed Job {i}")
            monitor.complete_execution(
                execution,
                JobStatus.FAILED,
                error_message=f"Error {i}"
            )
        
        response = await client.get("/api/v1/scheduler/health")
        data = response.json()
        
        failures = data["recent_failures"]
        assert len(failures) <= 5
