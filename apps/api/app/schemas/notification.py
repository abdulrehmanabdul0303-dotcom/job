"""
Notification Pydantic schemas.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NotificationTypeEnum(str, Enum):
    """Notification type enum for schemas."""
    DAILY_DIGEST = "daily_digest"
    HIGH_MATCH_ALERT = "high_match_alert"
    APPLICATION_UPDATE = "application_update"
    INTERVIEW_REMINDER = "interview_reminder"
    OFFER_NOTIFICATION = "offer_notification"


# Notification Settings Schemas
class NotificationSettingsBase(BaseModel):
    """Base schema for notification settings."""
    email_enabled: bool = Field(True, description="Enable email notifications")
    daily_digest_enabled: bool = Field(True, description="Enable daily digest")
    high_match_alert_enabled: bool = Field(True, description="Enable high match alerts")
    application_update_enabled: bool = Field(True, description="Enable application updates")
    interview_reminder_enabled: bool = Field(True, description="Enable interview reminders")
    offer_notification_enabled: bool = Field(True, description="Enable offer notifications")
    daily_digest_time: str = Field("09:00", description="Daily digest time (HH:MM)")
    high_match_threshold: str = Field("85", description="High match threshold (0-100)")


class NotificationSettingsUpdate(BaseModel):
    """Schema for updating notification settings."""
    email_enabled: Optional[bool] = None
    daily_digest_enabled: Optional[bool] = None
    high_match_alert_enabled: Optional[bool] = None
    application_update_enabled: Optional[bool] = None
    interview_reminder_enabled: Optional[bool] = None
    offer_notification_enabled: Optional[bool] = None
    daily_digest_time: Optional[str] = None
    high_match_threshold: Optional[str] = None


class NotificationSettingsResponse(NotificationSettingsBase):
    """Schema for notification settings response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Notification Log Schemas
class NotificationLogResponse(BaseModel):
    """Schema for notification log response."""
    id: str
    user_id: str
    notification_type: NotificationTypeEnum
    recipient_email: str
    subject: str
    body: Optional[str] = None
    sent_at: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None
    related_job_id: Optional[str] = None
    related_match_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationHistoryResponse(BaseModel):
    """Response for notification history."""
    notifications: List[NotificationLogResponse]
    total: int


# Test Email Schema
class SendTestEmailRequest(BaseModel):
    """Request to send test email."""
    email: EmailStr = Field(..., description="Email address to send test to")


class SendTestEmailResponse(BaseModel):
    """Response after sending test email."""
    success: bool
    message: str
    email: str
