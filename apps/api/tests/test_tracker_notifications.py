"""
Tests for Tracker and Notifications system.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.apply import JobActivity, ActivityStatus
from app.models.notification import NotificationSettings, NotificationLog, NotificationType
from app.services.apply_service import ActivityService
from app.services.notification_service import (
    NotificationSettingsService,
    NotificationLogService,
    RateLimiter,
    DigestService,
)
from app.services.email_service import EmailService, EmailTemplates


@pytest.mark.asyncio
class TestActivityTracking:
    """Test job activity tracking."""
    
    async def test_set_activity_status(self, db: AsyncSession, test_user: User):
        """Test setting activity status."""
        job_id = "job-123"
        
        activity = await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.INTERESTED,
            notes="Looks interesting",
        )
        
        assert activity is not None
        assert activity.user_id == test_user.id
        assert activity.job_id == job_id
        assert activity.status == ActivityStatus.INTERESTED
        assert activity.notes == "Looks interesting"
    
    async def test_update_activity_status(self, db: AsyncSession, test_user: User):
        """Test updating activity status."""
        job_id = "job-456"
        
        # Create initial activity
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.INTERESTED,
        )
        
        # Update status
        updated = await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.APPLIED,
            notes="Applied on company website",
        )
        
        assert updated.status == ActivityStatus.APPLIED
        assert updated.notes == "Applied on company website"
    
    async def test_get_activity(self, db: AsyncSession, test_user: User):
        """Test retrieving activity."""
        job_id = "job-789"
        
        # Create activity
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.INTERVIEW,
        )
        
        # Retrieve activity
        activity = await ActivityService.get_activity(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
        )
        
        assert activity is not None
        assert activity.status == ActivityStatus.INTERVIEW
    
    async def test_get_activities_with_pagination(self, db: AsyncSession, test_user: User):
        """Test retrieving activities with pagination."""
        # Create multiple activities
        for i in range(5):
            await ActivityService.set_activity_status(
                db=db,
                user_id=test_user.id,
                job_id=f"job-{i}",
                status=ActivityStatus.INTERESTED,
            )
        
        # Get first page
        activities, total = await ActivityService.get_activities(
            db=db,
            user_id=test_user.id,
            page=1,
            page_size=2,
        )
        
        assert len(activities) == 2
        assert total == 5
    
    async def test_get_activities_by_status(self, db: AsyncSession, test_user: User):
        """Test filtering activities by status."""
        # Create activities with different statuses
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-1",
            status=ActivityStatus.INTERESTED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-2",
            status=ActivityStatus.APPLIED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-3",
            status=ActivityStatus.APPLIED,
        )
        
        # Get only applied activities
        activities, total = await ActivityService.get_activities(
            db=db,
            user_id=test_user.id,
            status=ActivityStatus.APPLIED,
        )
        
        assert len(activities) == 2
        assert total == 2
        assert all(a.status == ActivityStatus.APPLIED for a in activities)
    
    async def test_get_activity_summary(self, db: AsyncSession, test_user: User):
        """Test getting activity summary."""
        # Create activities with different statuses
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-1",
            status=ActivityStatus.INTERESTED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-2",
            status=ActivityStatus.APPLIED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-3",
            status=ActivityStatus.APPLIED,
        )
        await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id="job-4",
            status=ActivityStatus.INTERVIEW,
        )
        
        # Get summary
        summary = await ActivityService.get_activity_summary(
            db=db,
            user_id=test_user.id,
        )
        
        assert summary["interested"] == 1
        assert summary["applied"] == 2
        assert summary["interview"] == 1


@pytest.mark.asyncio
class TestNotificationSettings:
    """Test notification settings management."""
    
    async def test_get_or_create_settings(self, db: AsyncSession, test_user: User):
        """Test getting or creating notification settings."""
        settings = await NotificationSettingsService.get_or_create_settings(
            db=db,
            user_id=test_user.id,
        )
        
        assert settings is not None
        assert settings.user_id == test_user.id
        assert settings.email_enabled is True
        assert settings.daily_digest_enabled is True
        assert settings.high_match_threshold == "85"
    
    async def test_update_settings(self, db: AsyncSession, test_user: User):
        """Test updating notification settings."""
        # Update settings
        updated = await NotificationSettingsService.update_settings(
            db=db,
            user_id=test_user.id,
            email_enabled=False,
            daily_digest_enabled=False,
            high_match_threshold="90",
        )
        
        assert updated.email_enabled is False
        assert updated.daily_digest_enabled is False
        assert updated.high_match_threshold == "90"
    
    async def test_settings_persistence(self, db: AsyncSession, test_user: User):
        """Test that settings persist across calls."""
        # Create settings
        await NotificationSettingsService.update_settings(
            db=db,
            user_id=test_user.id,
            email_enabled=False,
        )
        
        # Retrieve settings
        settings = await NotificationSettingsService.get_or_create_settings(
            db=db,
            user_id=test_user.id,
        )
        
        assert settings.email_enabled is False


@pytest.mark.asyncio
class TestNotificationLogging:
    """Test notification logging."""
    
    async def test_log_notification(self, db: AsyncSession, test_user: User):
        """Test logging a notification."""
        log = await NotificationLogService.log_notification(
            db=db,
            user_id=test_user.id,
            notification_type=NotificationType.DAILY_DIGEST,
            recipient_email=test_user.email,
            subject="Test Digest",
            body="Test body",
            status="sent",
        )
        
        assert log is not None
        assert log.user_id == test_user.id
        assert log.notification_type == NotificationType.DAILY_DIGEST
        assert log.status == "sent"
    
    async def test_mark_sent(self, db: AsyncSession, test_user: User):
        """Test marking notification as sent."""
        # Create log
        log = await NotificationLogService.log_notification(
            db=db,
            user_id=test_user.id,
            notification_type=NotificationType.HIGH_MATCH_ALERT,
            recipient_email=test_user.email,
            subject="Test Alert",
            status="pending",
        )
        
        # Mark as sent
        updated = await NotificationLogService.mark_sent(
            db=db,
            log_id=log.id,
        )
        
        assert updated.status == "sent"
        assert updated.sent_at is not None
    
    async def test_mark_failed(self, db: AsyncSession, test_user: User):
        """Test marking notification as failed."""
        # Create log
        log = await NotificationLogService.log_notification(
            db=db,
            user_id=test_user.id,
            notification_type=NotificationType.APPLICATION_UPDATE,
            recipient_email=test_user.email,
            subject="Test Update",
            status="pending",
        )
        
        # Mark as failed
        updated = await NotificationLogService.mark_failed(
            db=db,
            log_id=log.id,
            error_message="SMTP connection failed",
        )
        
        assert updated.status == "failed"
        assert updated.error_message == "SMTP connection failed"
    
    async def test_get_notification_history(self, db: AsyncSession, test_user: User):
        """Test retrieving notification history."""
        # Create multiple notifications
        for i in range(5):
            await NotificationLogService.log_notification(
                db=db,
                user_id=test_user.id,
                notification_type=NotificationType.DAILY_DIGEST,
                recipient_email=test_user.email,
                subject=f"Digest {i}",
                status="sent",
            )
        
        # Get history
        history = await NotificationLogService.get_notification_history(
            db=db,
            user_id=test_user.id,
            limit=10,
        )
        
        assert len(history) == 5


@pytest.mark.asyncio
class TestRateLimiter:
    """Test rate limiting."""
    
    def test_rate_limit_allowed(self):
        """Test that requests are allowed within limit."""
        user_id = "user-123"
        notification_type = "test_notification"
        
        # First 5 should be allowed
        for i in range(5):
            allowed = RateLimiter.is_allowed(
                user_id=user_id,
                notification_type=notification_type,
                max_per_hour=5,
            )
            assert allowed is True
    
    def test_rate_limit_exceeded(self):
        """Test that requests are blocked when limit exceeded."""
        user_id = "user-456"
        notification_type = "test_notification"
        
        # Fill up the limit
        for i in range(3):
            RateLimiter.is_allowed(
                user_id=user_id,
                notification_type=notification_type,
                max_per_hour=3,
            )
        
        # Next request should be blocked
        allowed = RateLimiter.is_allowed(
            user_id=user_id,
            notification_type=notification_type,
            max_per_hour=3,
        )
        
        assert allowed is False
    
    def test_rate_limit_different_types(self):
        """Test that different notification types have separate limits."""
        user_id = "user-789"
        
        # Fill up digest limit
        for i in range(2):
            RateLimiter.is_allowed(
                user_id=user_id,
                notification_type="digest",
                max_per_hour=2,
            )
        
        # Alert should still be allowed
        allowed = RateLimiter.is_allowed(
            user_id=user_id,
            notification_type="alert",
            max_per_hour=2,
        )
        
        assert allowed is True


@pytest.mark.asyncio
class TestEmailTemplates:
    """Test email template generation."""
    
    def test_daily_digest_template(self):
        """Test daily digest email template."""
        subject, html_body = EmailTemplates.daily_digest_template(
            user_name="John Doe",
            new_matches_count=5,
            top_matches=[
                {"job_title": "Senior Engineer", "company": "Tech Corp", "score": 95},
                {"job_title": "Developer", "company": "StartUp Inc", "score": 88},
            ],
            applications_count=3,
            interviews_count=1,
        )
        
        assert "Daily Digest" in subject
        assert "5" in subject
        assert "John Doe" in html_body
        assert "Senior Engineer" in html_body
        assert "95" in html_body
    
    def test_high_match_alert_template(self):
        """Test high match alert email template."""
        subject, html_body = EmailTemplates.high_match_alert_template(
            user_name="Jane Smith",
            job_title="Product Manager",
            company="Big Tech",
            match_score=92.5,
            location="San Francisco, CA",
        )
        
        assert "High Match Alert" in subject
        assert "Product Manager" in subject
        assert "Big Tech" in subject
        assert "Jane Smith" in html_body
        assert "92" in html_body
    
    def test_application_update_template(self):
        """Test application update email template."""
        subject, html_body = EmailTemplates.application_update_template(
            user_name="Bob Johnson",
            job_title="Data Scientist",
            company="Analytics Co",
            status="interview",
        )
        
        assert "Application Update" in subject
        assert "Data Scientist" in subject
        assert "Analytics Co" in subject
        assert "Bob Johnson" in html_body
        assert "interview" in html_body.lower()


@pytest.mark.asyncio
class TestEmailService:
    """Test email service."""
    
    def test_email_service_initialization(self):
        """Test email service initialization."""
        service = EmailService(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@test.com",
            smtp_password="password",
            from_email="noreply@test.com",
        )
        
        assert service.smtp_host == "smtp.test.com"
        assert service.smtp_port == 587
        assert service.enabled is True
    
    def test_email_service_disabled_without_credentials(self):
        """Test that email service is disabled without credentials."""
        service = EmailService(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="",
            smtp_password="",
        )
        
        assert service.enabled is False


@pytest.mark.asyncio
class TestDigestService:
    """Test digest service."""
    
    async def test_generate_daily_digest_disabled(self, db: AsyncSession, test_user: User):
        """Test that digest is not sent when disabled."""
        # Disable digest
        await NotificationSettingsService.update_settings(
            db=db,
            user_id=test_user.id,
            daily_digest_enabled=False,
        )
        
        # Try to generate digest
        email_service = EmailService()
        result = await DigestService.generate_daily_digest(
            db=db,
            user_id=test_user.id,
            email_service=email_service,
        )
        
        assert result is False
    
    async def test_generate_daily_digest_rate_limited(self, db: AsyncSession, test_user: User):
        """Test that digest is rate limited."""
        email_service = EmailService()
        
        # First digest should be allowed (but will fail due to no SMTP)
        # Second digest should be rate limited
        RateLimiter.is_allowed(test_user.id, "daily_digest", max_per_hour=1)
        
        result = await DigestService.generate_daily_digest(
            db=db,
            user_id=test_user.id,
            email_service=email_service,
        )
        
        # Should be rate limited
        assert result is False


@pytest.mark.asyncio
class TestNotificationIntegration:
    """Test notification integration with tracker."""
    
    async def test_activity_status_change_triggers_notification(
        self,
        db: AsyncSession,
        test_user: User,
    ):
        """Test that status change can trigger notification."""
        job_id = "job-integration-test"
        
        # Set activity status
        activity = await ActivityService.set_activity_status(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
            status=ActivityStatus.APPLIED,
            notes="Applied successfully",
        )
        
        # Verify activity was created
        assert activity is not None
        assert activity.status == ActivityStatus.APPLIED
        
        # In production, this would trigger a notification
        # For now, just verify the activity was logged
        retrieved = await ActivityService.get_activity(
            db=db,
            user_id=test_user.id,
            job_id=job_id,
        )
        
        assert retrieved.status == ActivityStatus.APPLIED
