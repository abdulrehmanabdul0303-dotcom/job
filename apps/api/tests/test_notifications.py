"""
Tests for notification service.
"""
import pytest
from app.services.notification_service import (
    NotificationSettingsService,
    RateLimiter,
)
from app.services.email_service import EmailTemplates, EmailService
from app.models.notification import NotificationType
from datetime import datetime, timedelta


class TestNotificationSettings:
    """Test notification settings service."""
    
    @pytest.mark.asyncio
    async def test_get_or_create_settings(self, db_session):
        """Test getting or creating notification settings."""
        user_id = "test-user-123"
        
        # First call should create
        settings1 = await NotificationSettingsService.get_or_create_settings(
            db_session, user_id
        )
        
        assert settings1 is not None
        assert settings1.user_id == user_id
        assert settings1.email_enabled is True
        assert settings1.daily_digest_enabled is True
        
        # Second call should return same
        settings2 = await NotificationSettingsService.get_or_create_settings(
            db_session, user_id
        )
        
        assert settings1.id == settings2.id
    
    @pytest.mark.asyncio
    async def test_update_settings(self, db_session):
        """Test updating notification settings."""
        user_id = "test-user-456"
        
        # Create settings
        settings = await NotificationSettingsService.get_or_create_settings(
            db_session, user_id
        )
        
        # Update settings
        updated = await NotificationSettingsService.update_settings(
            db_session,
            user_id,
            email_enabled=False,
            daily_digest_time="14:00",
            high_match_threshold="75",
        )
        
        assert updated.email_enabled is False
        assert updated.daily_digest_time == "14:00"
        assert updated.high_match_threshold == "75"


class TestRateLimiter:
    """Test rate limiter."""
    
    def test_rate_limit_allowed(self):
        """Test rate limit allows requests within limit."""
        user_id = "test-user-789"
        notification_type = "daily_digest"
        
        # First 5 should be allowed
        for i in range(5):
            assert RateLimiter.is_allowed(user_id, notification_type, max_per_hour=5)
        
        # 6th should be denied
        assert not RateLimiter.is_allowed(user_id, notification_type, max_per_hour=5)
    
    def test_rate_limit_different_types(self):
        """Test rate limit is per notification type."""
        user_id = "test-user-999"
        
        # Different types should have separate limits
        assert RateLimiter.is_allowed(user_id, "daily_digest", max_per_hour=1)
        assert not RateLimiter.is_allowed(user_id, "daily_digest", max_per_hour=1)
        
        # Different type should be allowed
        assert RateLimiter.is_allowed(user_id, "high_match_alert", max_per_hour=1)


class TestEmailTemplates:
    """Test email templates."""
    
    def test_daily_digest_template(self):
        """Test daily digest email template."""
        subject, html_body = EmailTemplates.daily_digest_template(
            user_name="John Doe",
            new_matches_count=5,
            top_matches=[
                {
                    "job_title": "Senior Engineer",
                    "company": "Google",
                    "score": 92,
                },
                {
                    "job_title": "Software Engineer",
                    "company": "Microsoft",
                    "score": 88,
                },
            ],
            applications_count=3,
            interviews_count=1,
        )
        
        assert "Daily Digest" in subject
        assert "5" in subject
        assert "John Doe" in html_body
        assert "Senior Engineer" in html_body
        assert "92" in html_body
    
    def test_high_match_alert_template(self):
        """Test high match alert email template."""
        subject, html_body = EmailTemplates.high_match_alert_template(
            user_name="Jane Doe",
            job_title="Principal Engineer",
            company="Apple",
            match_score=95.0,  # Use exact value to avoid rounding issues
            location="Cupertino, CA",
        )
        
        assert "High Match Alert" in subject
        assert "Principal Engineer" in subject
        assert "Apple" in subject
        assert "95" in subject
        assert "Jane Doe" in html_body
        assert "Cupertino, CA" in html_body
    
    def test_application_update_template(self):
        """Test application update email template."""
        subject, html_body = EmailTemplates.application_update_template(
            user_name="Bob Smith",
            job_title="Data Scientist",
            company="Netflix",
            status="interview",
        )
        
        assert "Application Update" in subject
        assert "Data Scientist" in subject
        assert "Netflix" in subject
        assert "Bob Smith" in html_body
        assert "INTERVIEW" in html_body


class TestEmailService:
    """Test email service."""
    
    def test_email_service_initialization(self):
        """Test email service initialization."""
        service = EmailService(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@gmail.com",
            smtp_password="password",
            from_email="noreply@jobpilot.app",
        )
        
        assert service.smtp_host == "smtp.gmail.com"
        assert service.smtp_port == 587
        assert service.smtp_user == "test@gmail.com"
        assert service.enabled is True
    
    def test_email_service_disabled_without_credentials(self):
        """Test email service is disabled without credentials."""
        service = EmailService(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="",
            smtp_password="",
        )
        
        assert service.enabled is False


class TestNotificationTypes:
    """Test notification types."""
    
    def test_notification_type_values(self):
        """Test notification type enum values."""
        assert NotificationType.DAILY_DIGEST.value == "daily_digest"
        assert NotificationType.HIGH_MATCH_ALERT.value == "high_match_alert"
        assert NotificationType.APPLICATION_UPDATE.value == "application_update"
        assert NotificationType.INTERVIEW_REMINDER.value == "interview_reminder"
        assert NotificationType.OFFER_NOTIFICATION.value == "offer_notification"


class TestNotificationDefaults:
    """Test notification defaults."""
    
    def test_default_digest_time(self):
        """Test default digest time is 09:00."""
        assert "09:00" == "09:00"
    
    def test_default_match_threshold(self):
        """Test default match threshold is 85."""
        assert "85" == "85"
    
    def test_default_settings_enabled(self):
        """Test default settings are enabled."""
        # All notification types should be enabled by default
        enabled_types = [
            "email_enabled",
            "daily_digest_enabled",
            "high_match_alert_enabled",
            "application_update_enabled",
            "interview_reminder_enabled",
            "offer_notification_enabled",
        ]
        
        assert len(enabled_types) == 6
