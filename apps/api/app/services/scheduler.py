"""
Job scheduler using APScheduler.
Schedules periodic job fetching from all active sources.
Schedules daily batch matching for all users.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.job_service import JobService
from app.services.match_service import MatchComputationService
from app.services.scheduler_monitor import get_monitor, JobStatus
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()

# Get monitor instance
monitor = get_monitor()


async def fetch_all_sources():
    """
    Background task to fetch jobs from all active sources.
    Runs periodically based on each source's fetch_frequency_hours.
    """
    job_id = "fetch_all_sources"
    execution = monitor.start_execution(job_id, "Fetch jobs from all active sources")
    
    logger.info("Starting scheduled job fetch for all active sources")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all active sources
            sources = await JobService.get_sources(db, active_only=True)
            
            logger.info(f"Found {len(sources)} active sources")
            
            if not sources:
                logger.info("No active sources to fetch from")
                monitor.complete_execution(
                    execution,
                    JobStatus.SUCCESS,
                    metrics={"sources_processed": 0, "jobs_fetched": 0}
                )
                return
            
            total_jobs_fetched = 0
            sources_processed = 0
            
            for source in sources:
                try:
                    logger.info(f"Fetching jobs from source: {source.name}")
                    stats = await JobService.fetch_and_store_jobs(db, source.id)
                    await db.commit()
                    
                    total_jobs_fetched += stats['jobs_new']
                    sources_processed += 1
                    
                    logger.info(
                        f"Fetched {stats['jobs_new']} new jobs from {source.name}"
                    )
                except Exception as e:
                    logger.error(f"Error fetching from source {source.name}: {e}")
                    await db.rollback()
                    continue
            
            logger.info("Completed scheduled job fetch")
            
            monitor.complete_execution(
                execution,
                JobStatus.SUCCESS,
                metrics={
                    "sources_processed": sources_processed,
                    "jobs_fetched": total_jobs_fetched,
                    "total_sources": len(sources)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in scheduled job fetch: {e}")
            await db.rollback()
            monitor.complete_execution(
                execution,
                JobStatus.FAILED,
                error_message=str(e)
            )


async def batch_compute_matches():
    """
    Background task to compute matches for all users.
    Runs daily to ensure all users have up-to-date matches.
    """
    job_id = "batch_compute_matches"
    execution = monitor.start_execution(job_id, "Daily batch match computation")
    
    logger.info("Starting daily batch match computation")
    
    async with AsyncSessionLocal() as db:
        try:
            stats = await MatchComputationService.compute_matches_for_all_users(
                db=db,
                min_score=30,  # Default threshold
            )
            
            logger.info(
                f"Daily batch matching complete: {stats['users_processed']} users, "
                f"{stats['total_matches']} matches created"
            )
            
            if stats['errors']:
                logger.warning(f"Batch matching had {len(stats['errors'])} errors")
            
            # Determine status based on errors
            status = JobStatus.SUCCESS if not stats['errors'] else JobStatus.FAILED
            error_message = f"{len(stats['errors'])} errors occurred" if stats['errors'] else None
            
            monitor.complete_execution(
                execution,
                status,
                error_message=error_message,
                metrics={
                    "users_processed": stats['users_processed'],
                    "total_matches": stats['total_matches'],
                    "errors_count": len(stats['errors'])
                }
            )
                
        except Exception as e:
            logger.error(f"Error in daily batch matching: {e}")
            monitor.complete_execution(
                execution,
                JobStatus.FAILED,
                error_message=str(e)
            )


def start_scheduler():
    """Start the job scheduler."""
    if not scheduler.running:
        # Register jobs with monitor
        monitor.register_job(
            job_id="fetch_all_sources",
            job_name="Fetch jobs from all active sources",
            expected_interval_minutes=60,  # Every hour
            max_duration_minutes=30,  # Should complete within 30 minutes
        )
        
        monitor.register_job(
            job_id="batch_compute_matches",
            job_name="Daily batch match computation",
            expected_interval_minutes=1440,  # Daily (24 hours)
            max_duration_minutes=120,  # Should complete within 2 hours
        )
        
        # Schedule job fetching every hour
        scheduler.add_job(
            fetch_all_sources,
            trigger=IntervalTrigger(hours=1),
            id='fetch_all_sources',
            name='Fetch jobs from all active sources',
            replace_existing=True,
        )
        
        # Schedule daily batch matching at 3 AM
        scheduler.add_job(
            batch_compute_matches,
            trigger=CronTrigger(hour=3, minute=0),
            id='batch_compute_matches',
            name='Daily batch match computation for all users',
            replace_existing=True,
        )
        
        scheduler.start()
        logger.info("Job scheduler started - fetching jobs every hour, batch matching daily at 3 AM")
        logger.info("Scheduler monitoring enabled with health checks")


def stop_scheduler():
    """Stop the job scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Job scheduler stopped")
