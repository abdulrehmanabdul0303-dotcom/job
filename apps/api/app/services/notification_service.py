"""
Notification service for managing notifications and scheduling.
Includes rate limiting and digest scheduling.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.notification import NotificationSettings, NotificationLog, NotificationType
from app.models.user import User
from app.models.match import JobMatch
from app.models.apply import JobActivity, ActivityStatus
from app.services.email_service import EmailService
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class NotificationSettingsService:
    """Service for managing notification settings."""
    
    @staticmethod
    async def get_or_create_settings(
        db: AsyncSession,
        user_id: str,
    ) -> NotificationSettings:
        """Get or create notification settings for user."""
        result = await db.execute(
            select(NotificationSettings).where(
                NotificationSettings.user_id == user_id
            )
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            settings = NotificationSettings(user_id=user_id)
            db.add(settings)
            await db.flush()
            await db.refresh(settings)
        
        return settings
    
    @staticmethod
    async def update_settings(
        db: AsyncSession,
        user_id: str,
        **kwargs,
    ) -> NotificationSettings:
        """Update notification settings."""
        settings = await NotificationSettingsService.get_or_create_settings(db, user_id)
        
        # Update allowed fields
        allowed_fields = {
            'email_enabled',
            'daily_digest_enabled',
            'high_match_alert_enabled',
            'application_update_enabled',
            'interview_reminder_enabled',
            'offer_notification_enabled',
            'daily_digest_time',
            'high_match_threshold',
        }
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(settings, key, value)
        
        settings.updated_at = datetime.utcnow()
        await db.flush()
        await db.refresh(settings)
        
        return settings


class NotificationLogService:
    """Service for logging notifications."""
    
    @staticmethod
    async def log_notification(
        db: AsyncSession,
        user_id: str,
        notification_type: NotificationType,
        recipient_email: str,
        subject: str,
        body: Optional[str] = None,
        status: str = "pending",
        error_message: Optional[str] = None,
        related_job_id: Optional[str] = None,
        related_match_id: Optional[str] = None,
    ) -> NotificationLog:
        """Log a notification."""
        log = NotificationLog(
            user_id=user_id,
            notification_type=notification_type,
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            status=status,
            error_message=error_message,
            related_job_id=related_job_id,
            related_match_id=related_match_id,
        )
        
        db.add(log)
        await db.flush()
        await db.refresh(log)
        
        return log
    
    @staticmethod
    async def mark_sent(
        db: AsyncSession,
        log_id: str,
    ) -> Optional[NotificationLog]:
        """Mark notification as sent."""
        result = await db.execute(
            select(NotificationLog).where(NotificationLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if log:
            log.status = "sent"
            log.sent_at = datetime.utcnow()
            await db.flush()
            await db.refresh(log)
        
        return log
    
    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        log_id: str,
        error_message: str,
    ) -> Optional[NotificationLog]:
        """Mark notification as failed."""
        result = await db.execute(
            select(NotificationLog).where(NotificationLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if log:
            log.status = "failed"
            log.error_message = error_message
            await db.flush()
            await db.refresh(log)
        
        return log
    
    @staticmethod
    async def get_notification_history(
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
    ) -> List[NotificationLog]:
        """Get user's notification history."""
        result = await db.execute(
            select(NotificationLog)
            .where(NotificationLog.user_id == user_id)
            .order_by(NotificationLog.created_at.desc())
            .limit(limit)
        )
        
        return list(result.scalars().all())


class RateLimiter:
    """Simple rate limiter for notifications."""
    
    # In-memory rate limit tracking (in production, use Redis)
    _limits: Dict[str, List[datetime]] = {}
    
    @staticmethod
    def is_allowed(
        user_id: str,
        notification_type: str,
        max_per_hour: int = 5,
    ) -> bool:
        """
        Check if notification is allowed based on rate limit.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            max_per_hour: Maximum notifications per hour
            
        Returns:
            True if allowed, False if rate limited
        """
        key = f"{user_id}:{notification_type}"
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        # Initialize if not exists
        if key not in RateLimiter._limits:
            RateLimiter._limits[key] = []
        
        # Remove old entries
        RateLimiter._limits[key] = [
            ts for ts in RateLimiter._limits[key]
            if ts > one_hour_ago
        ]
        
        # Check limit
        if len(RateLimiter._limits[key]) >= max_per_hour:
            logger.warning(f"Rate limit exceeded for {key}")
            return False
        
        # Add current timestamp
        RateLimiter._limits[key].append(now)
        return True


class DigestService:
    """Service for generating and sending digest notifications."""
    
    @staticmethod
    async def generate_daily_digest(
        db: AsyncSession,
        user_id: str,
        email_service: EmailService,
    ) -> bool:
        """
        Generate and send daily digest for user.
        
        Args:
            db: Database session
            user_id: User ID
            email_service: Email service instance
            
        Returns:
            True if sent successfully
        """
        try:
            # Get user
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Get settings
            settings = await NotificationSettingsService.get_or_create_settings(db, user_id)
            
            if not settings.email_enabled or not settings.daily_digest_enabled:
                logger.info(f"Daily digest disabled for user {user_id}")
                return False
            
            # Check rate limit (max 1 per hour for digest)
            if not RateLimiter.is_allowed(user_id, "daily_digest", max_per_hour=1):
                logger.warning(f"Daily digest rate limited for user {user_id}")
                return False
            
            # Get new matches from last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            matches_result = await db.execute(
                select(JobMatch)
                .where(
                    and_(
                        JobMatch.user_id == user_id,
                        JobMatch.created_at >= yesterday,
                    )
                )
                .order_by(JobMatch.match_score.desc())
                .limit(10)
            )
            matches = list(matches_result.scalars().all())
            
            # Get application counts
            applied_result = await db.execute(
                select(func.count(JobActivity.id)).where(
                    and_(
                        JobActivity.user_id == user_id,
                        JobActivity.status == ActivityStatus.APPLIED,
                    )
                )
            )
            applications_count = applied_result.scalar() or 0
            
            interview_result = await db.execute(
                select(func.count(JobActivity.id)).where(
                    and_(
                        JobActivity.user_id == user_id,
                        JobActivity.status == ActivityStatus.INTERVIEW,
                    )
                )
            )
            interviews_count = interview_result.scalar() or 0
            
            # Format matches for email
            top_matches = []
            for match in matches[:5]:
                # Get job details
                job_result = await db.execute(
                    select(JobMatch).where(JobMatch.id == match.id)
                )
                job_match = job_result.scalar_one_or_none()
                
                if job_match:
                    top_matches.append({
                        'job_title': f"Job {job_match.job_id}",
                        'company': 'Company',
                        'score': job_match.match_score,
                    })
            
            # Send email
            success = email_service.send_daily_digest(
                to_email=user.email,
                user_name=user.full_name or "User",
                new_matches_count=len(matches),
                top_matches=top_matches,
                applications_count=applications_count,
                interviews_count=interviews_count,
            )
            
            # Log notification
            await NotificationLogService.log_notification(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.DAILY_DIGEST,
                recipient_email=user.email,
                subject=f"JobPilot Daily Digest - {len(matches)} New Matches",
                status="sent" if success else "failed",
            )
            
            await db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating daily digest for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def send_application_update_notification(
        db: AsyncSession,
        user_id: str,
        job_id: str,
        status: ActivityStatus,
        email_service: EmailService,
    ) -> bool:
        """
        Send application update notification.
        
        Args:
            db: Database session
            user_id: User ID
            job_id: Job ID
            status: New status
            email_service: Email service instance
            
        Returns:
            True if sent successfully
        """
        try:
            # Get user
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Get settings
            settings = await NotificationSettingsService.get_or_create_settings(db, user_id)
            
            if not settings.email_enabled or not settings.application_update_enabled:
                logger.info(f"Application update notifications disabled for user {user_id}")
                return False
            
            # Check rate limit (max 20 per hour)
            if not RateLimiter.is_allowed(user_id, "application_update", max_per_hour=20):
                logger.warning(f"Application update rate limited for user {user_id}")
                return False
            
            # Send email
            success = email_service.send_application_update(
                to_email=user.email,
                user_name=user.full_name or "User",
                job_title="Job Title",
                company="Company",
                status=status.value,
            )
            
            # Log notification
            await NotificationLogService.log_notification(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.APPLICATION_UPDATE,
                recipient_email=user.email,
                subject=f"Application Update: {status.value.upper()}",
                status="sent" if success else "failed",
                related_job_id=job_id,
            )
            
            await db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending application update notification: {e}")
            return False
    
    @staticmethod
    async def send_high_match_alert(
        db: AsyncSession,
        user_id: str,
        match_id: str,
        email_service: EmailService,
    ) -> bool:
        """
        Send high match alert for a specific match.
        
        Args:
            db: Database session
            user_id: User ID
            match_id: Match ID
            email_service: Email service instance
            
        Returns:
            True if sent successfully
        """
        try:
            # Get user
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Get settings
            settings = await NotificationSettingsService.get_or_create_settings(db, user_id)
            
            if not settings.email_enabled or not settings.high_match_alert_enabled:
                logger.info(f"High match alert disabled for user {user_id}")
                return False
            
            # Check rate limit (max 10 per hour)
            if not RateLimiter.is_allowed(user_id, "high_match_alert", max_per_hour=10):
                logger.warning(f"High match alert rate limited for user {user_id}")
                return False
            
            # Get match
            match_result = await db.execute(
                select(JobMatch).where(JobMatch.id == match_id)
            )
            match = match_result.scalar_one_or_none()
            
            if not match:
                logger.error(f"Match not found: {match_id}")
                return False
            
            # Check threshold
            threshold = float(settings.high_match_threshold)
            if match.match_score < threshold:
                logger.info(f"Match score {match.match_score} below threshold {threshold}")
                return False
            
            # Send email
            success = email_service.send_high_match_alert(
                to_email=user.email,
                user_name=user.full_name or "User",
                job_title="Job Title",
                company="Company",
                match_score=match.match_score,
                location=None,
            )
            
            # Log notification
            await NotificationLogService.log_notification(
                db=db,
                user_id=user_id,
                notification_type=NotificationType.HIGH_MATCH_ALERT,
                recipient_email=user.email,
                subject=f"🎯 High Match Alert: {match.match_score:.0f}%",
                status="sent" if success else "failed",
                related_match_id=match_id,
            )
            
            await db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending high match alert for match {match_id}: {e}")
            return False
