"""
Background Job Monitoring

Provides monitoring, health checks, and metrics for scheduled background jobs.

Features:
- Job execution tracking
- Failure detection and alerting
- Health check endpoint
- Job execution metrics
- Last run timestamps
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    NEVER_RUN = "never_run"


@dataclass
class JobExecution:
    """Record of a job execution."""
    job_id: str
    job_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.RUNNING
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, status: JobStatus, error_message: Optional[str] = None, metrics: Optional[Dict[str, Any]] = None):
        """Mark execution as complete."""
        self.completed_at = datetime.utcnow()
        self.status = status
        self.error_message = error_message
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        if metrics:
            self.metrics = metrics


class SchedulerMonitor:
    """
    Monitor for background job scheduler.
    
    Tracks job executions, failures, and provides health checks.
    """
    
    def __init__(self):
        """Initialize scheduler monitor."""
        self._executions: Dict[str, List[JobExecution]] = {}
        self._last_execution: Dict[str, JobExecution] = {}
        self._job_configs: Dict[str, Dict[str, Any]] = {}
        self._max_history = 100  # Keep last 100 executions per job
    
    def register_job(
        self,
        job_id: str,
        job_name: str,
        expected_interval_minutes: Optional[int] = None,
        max_duration_minutes: Optional[int] = None,
    ):
        """
        Register a job for monitoring.
        
        Args:
            job_id: Unique job identifier
            job_name: Human-readable job name
            expected_interval_minutes: Expected time between executions
            max_duration_minutes: Maximum expected duration
        """
        self._job_configs[job_id] = {
            "job_name": job_name,
            "expected_interval_minutes": expected_interval_minutes,
            "max_duration_minutes": max_duration_minutes,
            "registered_at": datetime.utcnow(),
        }
        
        if job_id not in self._executions:
            self._executions[job_id] = []
        
        logger.info(f"Registered job for monitoring: {job_name} (ID: {job_id})")
    
    def start_execution(self, job_id: str, job_name: str) -> JobExecution:
        """
        Record the start of a job execution.
        
        Args:
            job_id: Job identifier
            job_name: Job name
            
        Returns:
            JobExecution instance
        """
        execution = JobExecution(
            job_id=job_id,
            job_name=job_name,
            started_at=datetime.utcnow(),
        )
        
        if job_id not in self._executions:
            self._executions[job_id] = []
        
        self._executions[job_id].append(execution)
        
        # Trim history
        if len(self._executions[job_id]) > self._max_history:
            self._executions[job_id] = self._executions[job_id][-self._max_history:]
        
        logger.info(f"Job execution started: {job_name} (ID: {job_id})")
        
        return execution
    
    def complete_execution(
        self,
        execution: JobExecution,
        status: JobStatus,
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ):
        """
        Record the completion of a job execution.
        
        Args:
            execution: JobExecution instance
            status: Execution status
            error_message: Error message if failed
            metrics: Execution metrics
        """
        execution.complete(status, error_message, metrics)
        self._last_execution[execution.job_id] = execution
        
        if status == JobStatus.SUCCESS:
            logger.info(
                f"Job execution completed: {execution.job_name} "
                f"(duration: {execution.duration_seconds:.2f}s)"
            )
        else:
            logger.error(
                f"Job execution failed: {execution.job_name} "
                f"(error: {error_message})"
            )
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of a specific job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dictionary
        """
        config = self._job_configs.get(job_id, {})
        last_execution = self._last_execution.get(job_id)
        executions = self._executions.get(job_id, [])
        
        # Calculate statistics
        total_executions = len(executions)
        successful_executions = sum(1 for e in executions if e.status == JobStatus.SUCCESS)
        failed_executions = sum(1 for e in executions if e.status == JobStatus.FAILED)
        
        # Calculate average duration
        completed_executions = [e for e in executions if e.duration_seconds is not None]
        avg_duration = (
            sum(e.duration_seconds for e in completed_executions) / len(completed_executions)
            if completed_executions else None
        )
        
        # Check if job is overdue
        is_overdue = False
        overdue_by_minutes = None
        if last_execution and last_execution.completed_at and config.get("expected_interval_minutes"):
            expected_next = last_execution.completed_at + timedelta(
                minutes=config["expected_interval_minutes"]
            )
            if datetime.utcnow() > expected_next:
                is_overdue = True
                overdue_by_minutes = (datetime.utcnow() - expected_next).total_seconds() / 60
        
        # Check if currently running too long
        is_stuck = False
        if last_execution and last_execution.status == JobStatus.RUNNING:
            if config.get("max_duration_minutes"):
                max_duration = timedelta(minutes=config["max_duration_minutes"])
                if datetime.utcnow() - last_execution.started_at > max_duration:
                    is_stuck = True
        
        # Determine overall health
        current_status = last_execution.status if last_execution else JobStatus.NEVER_RUN
        is_healthy = not (
            is_overdue or 
            is_stuck or 
            current_status == JobStatus.FAILED or
            current_status == JobStatus.NEVER_RUN
        )
        
        return {
            "job_id": job_id,
            "job_name": config.get("job_name", "Unknown"),
            "status": current_status,
            "last_execution": {
                "started_at": last_execution.started_at.isoformat() if last_execution else None,
                "completed_at": last_execution.completed_at.isoformat() if last_execution and last_execution.completed_at else None,
                "duration_seconds": last_execution.duration_seconds if last_execution else None,
                "error_message": last_execution.error_message if last_execution else None,
                "metrics": last_execution.metrics if last_execution else {},
            } if last_execution else None,
            "statistics": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
                "average_duration_seconds": avg_duration,
            },
            "health": {
                "is_healthy": is_healthy,
                "is_overdue": is_overdue,
                "overdue_by_minutes": overdue_by_minutes,
                "is_stuck": is_stuck,
            },
            "config": config,
        }
    
    def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all registered jobs.
        
        Returns:
            List of job status dictionaries
        """
        return [
            self.get_job_status(job_id)
            for job_id in self._job_configs.keys()
        ]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall health summary of all jobs.
        
        Returns:
            Health summary dictionary
        """
        all_jobs = self.get_all_jobs_status()
        
        total_jobs = len(all_jobs)
        healthy_jobs = sum(1 for job in all_jobs if job["health"]["is_healthy"])
        overdue_jobs = sum(1 for job in all_jobs if job["health"]["is_overdue"])
        stuck_jobs = sum(1 for job in all_jobs if job["health"]["is_stuck"])
        failed_jobs = sum(1 for job in all_jobs if job["status"] == JobStatus.FAILED)
        never_run_jobs = sum(1 for job in all_jobs if job["status"] == JobStatus.NEVER_RUN)
        
        is_healthy = healthy_jobs == total_jobs
        
        return {
            "is_healthy": is_healthy,
            "total_jobs": total_jobs,
            "healthy_jobs": healthy_jobs,
            "unhealthy_jobs": total_jobs - healthy_jobs,
            "overdue_jobs": overdue_jobs,
            "stuck_jobs": stuck_jobs,
            "failed_jobs": failed_jobs,
            "never_run_jobs": never_run_jobs,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_recent_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent job failures.
        
        Args:
            limit: Maximum number of failures to return
            
        Returns:
            List of recent failures
        """
        failures = []
        
        for job_id, executions in self._executions.items():
            for execution in reversed(executions):
                if execution.status == JobStatus.FAILED:
                    failures.append({
                        "job_id": job_id,
                        "job_name": execution.job_name,
                        "started_at": execution.started_at.isoformat(),
                        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                        "error_message": execution.error_message,
                        "duration_seconds": execution.duration_seconds,
                    })
                    
                    if len(failures) >= limit:
                        break
            
            if len(failures) >= limit:
                break
        
        return failures


# Global monitor instance
monitor = SchedulerMonitor()


def get_monitor() -> SchedulerMonitor:
    """Get the global scheduler monitor instance."""
    return monitor

