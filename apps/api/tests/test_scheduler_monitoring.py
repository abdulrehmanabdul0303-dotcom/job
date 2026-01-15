"""
Tests for background job scheduler monitoring.

Tests monitoring, health checks, and metrics for scheduled jobs.
"""
import pytest
from datetime import datetime, timedelta
from app.services.scheduler_monitor import (
    SchedulerMonitor,
    JobExecution,
    JobStatus,
    get_monitor,
)


class TestJobExecution:
    """Test JobExecution dataclass."""
    
    def test_job_execution_creation(self):
        """Test creating a job execution."""
        execution = JobExecution(
            job_id="test_job",
            job_name="Test Job",
            started_at=datetime.utcnow(),
        )
        
        assert execution.job_id == "test_job"
        assert execution.job_name == "Test Job"
        assert execution.status == JobStatus.RUNNING
        assert execution.completed_at is None
        assert execution.duration_seconds is None
    
    def test_job_execution_complete_success(self):
        """Test completing a job execution successfully."""
        execution = JobExecution(
            job_id="test_job",
            job_name="Test Job",
            started_at=datetime.utcnow(),
        )
        
        metrics = {"items_processed": 100}
        execution.complete(JobStatus.SUCCESS, metrics=metrics)
        
        assert execution.status == JobStatus.SUCCESS
        assert execution.completed_at is not None
        assert execution.duration_seconds is not None
        assert execution.duration_seconds >= 0
        assert execution.error_message is None
        assert execution.metrics == metrics
    
    def test_job_execution_complete_failure(self):
        """Test completing a job execution with failure."""
        execution = JobExecution(
            job_id="test_job",
            job_name="Test Job",
            started_at=datetime.utcnow(),
        )
        
        error_msg = "Database connection failed"
        execution.complete(JobStatus.FAILED, error_message=error_msg)
        
        assert execution.status == JobStatus.FAILED
        assert execution.completed_at is not None
        assert execution.duration_seconds is not None
        assert execution.error_message == error_msg


class TestSchedulerMonitor:
    """Test SchedulerMonitor class."""
    
    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor instance for each test."""
        return SchedulerMonitor()
    
    def test_register_job(self, monitor):
        """Test registering a job for monitoring."""
        monitor.register_job(
            job_id="test_job",
            job_name="Test Job",
            expected_interval_minutes=60,
            max_duration_minutes=30,
        )
        
        assert "test_job" in monitor._job_configs
        config = monitor._job_configs["test_job"]
        assert config["job_name"] == "Test Job"
        assert config["expected_interval_minutes"] == 60
        assert config["max_duration_minutes"] == 30
        assert "registered_at" in config
    
    def test_start_execution(self, monitor):
        """Test starting a job execution."""
        execution = monitor.start_execution("test_job", "Test Job")
        
        assert execution.job_id == "test_job"
        assert execution.job_name == "Test Job"
        assert execution.status == JobStatus.RUNNING
        assert "test_job" in monitor._executions
        assert len(monitor._executions["test_job"]) == 1
    
    def test_complete_execution(self, monitor):
        """Test completing a job execution."""
        execution = monitor.start_execution("test_job", "Test Job")
        
        metrics = {"items_processed": 50}
        monitor.complete_execution(
            execution,
            JobStatus.SUCCESS,
            metrics=metrics
        )
        
        assert execution.status == JobStatus.SUCCESS
        assert execution.completed_at is not None
        assert execution.metrics == metrics
        assert monitor._last_execution["test_job"] == execution
    
    def test_execution_history_trimming(self, monitor):
        """Test that execution history is trimmed to max_history."""
        monitor._max_history = 5
        
        # Create 10 executions
        for i in range(10):
            execution = monitor.start_execution("test_job", "Test Job")
            monitor.complete_execution(execution, JobStatus.SUCCESS)
        
        # Should only keep last 5
        assert len(monitor._executions["test_job"]) == 5
    
    def test_get_job_status_never_run(self, monitor):
        """Test getting status of a job that has never run."""
        monitor.register_job(
            job_id="test_job",
            job_name="Test Job",
            expected_interval_minutes=60,
        )
        
        status = monitor.get_job_status("test_job")
        
        assert status["job_id"] == "test_job"
        assert status["job_name"] == "Test Job"
        assert status["status"] == JobStatus.NEVER_RUN
        assert status["last_execution"] is None
        assert status["statistics"]["total_executions"] == 0
        assert status["health"]["is_healthy"] is False
    
    def test_get_job_status_with_executions(self, monitor):
        """Test getting status of a job with execution history."""
        monitor.register_job(
            job_id="test_job",
            job_name="Test Job",
            expected_interval_minutes=60,
        )
        
        # Run job 3 times: 2 success, 1 failure
        for i in range(2):
            execution = monitor.start_execution("test_job", "Test Job")
            monitor.complete_execution(execution, JobStatus.SUCCESS)
        
        execution = monitor.start_execution("test_job", "Test Job")
        monitor.complete_execution(execution, JobStatus.FAILED, error_message="Test error")
        
        status = monitor.get_job_status("test_job")
        
        assert status["statistics"]["total_executions"] == 3
        assert status["statistics"]["successful_executions"] == 2
        assert status["statistics"]["failed_executions"] == 1
        assert status["statistics"]["success_rate"] == pytest.approx(2/3)
        assert status["statistics"]["average_duration_seconds"] is not None
    
    def test_get_job_status_overdue(self, monitor):
        """Test detecting overdue jobs."""
        monitor.register_job(
            job_id="test_job",
            job_name="Test Job",
            expected_interval_minutes=60,
        )
        
        # Create an execution that completed 2 hours ago
        execution = monitor.start_execution("test_job", "Test Job")
        execution.started_at = datetime.utcnow() - timedelta(hours=2, minutes=5)
        execution.completed_at = datetime.utcnow() - timedelta(hours=2)
        execution.status = JobStatus.SUCCESS
        execution.duration_seconds = 300  # 5 minutes
        monitor._last_execution["test_job"] = execution
        
        status = monitor.get_job_status("test_job")
        
        assert status["health"]["is_overdue"] is True
        assert status["health"]["overdue_by_minutes"] is not None
        assert status["health"]["overdue_by_minutes"] > 0
        assert status["health"]["is_healthy"] is False
    
    def test_get_job_status_stuck(self, monitor):
        """Test detecting stuck jobs."""
        monitor.register_job(
            job_id="test_job",
            job_name="Test Job",
            max_duration_minutes=30,
        )
        
        # Create a running execution that started 1 hour ago
        execution = monitor.start_execution("test_job", "Test Job")
        execution.started_at = datetime.utcnow() - timedelta(hours=1)
        monitor._last_execution["test_job"] = execution
        
        status = monitor.get_job_status("test_job")
        
        assert status["health"]["is_stuck"] is True
        assert status["health"]["is_healthy"] is False
    
    def test_get_all_jobs_status(self, monitor):
        """Test getting status of all jobs."""
        # Register and run multiple jobs
        for i in range(3):
            job_id = f"job_{i}"
            monitor.register_job(job_id, f"Job {i}")
            execution = monitor.start_execution(job_id, f"Job {i}")
            monitor.complete_execution(execution, JobStatus.SUCCESS)
        
        all_status = monitor.get_all_jobs_status()
        
        assert len(all_status) == 3
        assert all([s["job_id"].startswith("job_") for s in all_status])
    
    def test_get_health_summary_all_healthy(self, monitor):
        """Test health summary when all jobs are healthy."""
        # Register and run jobs successfully
        for i in range(3):
            job_id = f"job_{i}"
            monitor.register_job(job_id, f"Job {i}", expected_interval_minutes=60)
            execution = monitor.start_execution(job_id, f"Job {i}")
            monitor.complete_execution(execution, JobStatus.SUCCESS)
        
        summary = monitor.get_health_summary()
        
        assert summary["is_healthy"] is True
        assert summary["total_jobs"] == 3
        assert summary["healthy_jobs"] == 3
        assert summary["unhealthy_jobs"] == 0
        assert summary["failed_jobs"] == 0
    
    def test_get_health_summary_with_failures(self, monitor):
        """Test health summary with failed jobs."""
        # Job 1: Success
        monitor.register_job("job_1", "Job 1")
        execution = monitor.start_execution("job_1", "Job 1")
        monitor.complete_execution(execution, JobStatus.SUCCESS)
        
        # Job 2: Failed
        monitor.register_job("job_2", "Job 2")
        execution = monitor.start_execution("job_2", "Job 2")
        monitor.complete_execution(execution, JobStatus.FAILED, error_message="Error")
        
        summary = monitor.get_health_summary()
        
        assert summary["is_healthy"] is False
        assert summary["total_jobs"] == 2
        assert summary["healthy_jobs"] == 1
        assert summary["unhealthy_jobs"] == 1
        assert summary["failed_jobs"] == 1
    
    def test_get_recent_failures(self, monitor):
        """Test getting recent job failures."""
        # Create multiple jobs with some failures
        for i in range(5):
            job_id = f"job_{i}"
            monitor.register_job(job_id, f"Job {i}")
            
            # Alternate success and failure
            execution = monitor.start_execution(job_id, f"Job {i}")
            if i % 2 == 0:
                monitor.complete_execution(execution, JobStatus.SUCCESS)
            else:
                monitor.complete_execution(
                    execution,
                    JobStatus.FAILED,
                    error_message=f"Error {i}"
                )
        
        failures = monitor.get_recent_failures(limit=10)
        
        # Should have 2 failures (jobs 1 and 3)
        assert len(failures) == 2
        assert all(f["error_message"] is not None for f in failures)
    
    def test_get_recent_failures_limit(self, monitor):
        """Test that recent failures respects limit."""
        # Create 10 failed jobs
        for i in range(10):
            job_id = f"job_{i}"
            execution = monitor.start_execution(job_id, f"Job {i}")
            monitor.complete_execution(
                execution,
                JobStatus.FAILED,
                error_message=f"Error {i}"
            )
        
        failures = monitor.get_recent_failures(limit=5)
        
        assert len(failures) == 5


class TestMonitorSingleton:
    """Test global monitor instance."""
    
    def test_get_monitor_returns_same_instance(self):
        """Test that get_monitor returns the same instance."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        
        assert monitor1 is monitor2
    
    def test_monitor_persists_state(self):
        """Test that monitor state persists across get_monitor calls."""
        monitor1 = get_monitor()
        monitor1.register_job("test_job", "Test Job")
        
        monitor2 = get_monitor()
        assert "test_job" in monitor2._job_configs


class TestJobStatusEnum:
    """Test JobStatus enum."""
    
    def test_job_status_values(self):
        """Test JobStatus enum values."""
        assert JobStatus.SUCCESS == "success"
        assert JobStatus.FAILED == "failed"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.NEVER_RUN == "never_run"
