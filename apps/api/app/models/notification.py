"""
Notification database models.
Includes NotificationSettings and NotificationLog for email management.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func
import uuid
from enum import Enum
from app.core.database import Base


class NotificationType(str, Enum):
    """Notification type enum."""
    DAILY_DIGEST = "daily_digest"
    HIGH_MATCH_ALERT = "high_match_alert"
    APPLICATION_UPDATE = "application_update"
    INTERVIEW_REMINDER = "interview_reminder"
    OFFER_NOTIFICATION = "offer_notification"


class NotificationSettings(Base):
    """User notification preferences."""
    
    __tablename__ = "notification_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    
    # Email preferences
    email_enabled = Column(Boolean, default=True, nullable=False)
    daily_digest_enabled = Column(Boolean, default=True, nullable=False)
    high_match_alert_enabled = Column(Boolean, default=True, nullable=False)
    application_update_enabled = Column(Boolean, default=True, nullable=False)
    interview_reminder_enabled = Column(Boolean, default=True, nullable=False)
    offer_notification_enabled = Column(Boolean, default=True, nullable=False)
    
    # Digest settings
    daily_digest_time = Column(String(5), default="09:00", nullable=False)  # HH:MM format
    high_match_threshold = Column(String(3), default="85", nullable=False)  # Percentage
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationSettings user={self.user_id}>"


class NotificationLog(Base):
    """Log of sent notifications."""
    
    __tablename__ = "notification_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(
        SQLEnum(NotificationType),
        nullable=False,
        index=True
    )
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    
    # Content
    body = Column(Text, nullable=True)
    
    # Status
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    
    # Related data
    related_job_id = Column(String(36), nullable=True, index=True)
    related_match_id = Column(String(36), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<NotificationLog user={self.user_id} type={self.notification_type}>"
