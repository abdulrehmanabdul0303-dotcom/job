"""
Notification API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.services.notification_service import (
    NotificationSettingsService,
    NotificationLogService,
    DigestService,
)
from app.services.email_service import EmailService
from app.schemas.notification import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    NotificationHistoryResponse,
    SendTestEmailRequest,
    SendTestEmailResponse,
)
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize email service
email_service = EmailService()


# Notification Settings Endpoints
@router.get("/notifications/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's notification settings.
    
    Returns:
        User's notification settings
    """
    try:
        settings = await NotificationSettingsService.get_or_create_settings(
            db=db,
            user_id=current_user.id,
        )
        
        return settings
        
    except Exception as e:
        logger.error(f"Error fetching notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching notification settings"
        )


@router.put("/notifications/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    request: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's notification settings.
    
    Args:
        request: Updated settings
        
    Returns:
        Updated notification settings
    """
    try:
        settings = await NotificationSettingsService.update_settings(
            db=db,
            user_id=current_user.id,
            **request.model_dump(exclude_unset=True),
        )
        
        await db.commit()
        
        return settings
        
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating notification settings"
        )


# Notification History Endpoints
@router.get("/notifications/history", response_model=NotificationHistoryResponse)
async def get_notification_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's notification history.
    
    Args:
        limit: Maximum number of notifications to return
        
    Returns:
        List of notifications
    """
    try:
        notifications = await NotificationLogService.get_notification_history(
            db=db,
            user_id=current_user.id,
            limit=limit,
        )
        
        return NotificationHistoryResponse(
            notifications=notifications,
            total=len(notifications),
        )
        
    except Exception as e:
        logger.error(f"Error fetching notification history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching notification history"
        )


# Test Email Endpoint
@router.post("/notifications/test-email", response_model=SendTestEmailResponse)
async def send_test_email(
    request: SendTestEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a test email to verify email configuration.
    
    Args:
        request: Test email request with recipient
        
    Returns:
        Success status
    """
    try:
        if not email_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email service not configured. Please set SMTP credentials."
            )
        
        # Send test email
        subject = "JobPilot Test Email"
        html_body = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #2196F3; color: white; padding: 20px; border-radius: 4px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Test Email</h1>
                    </div>
                    <p>This is a test email from JobPilot. If you received this, your email configuration is working correctly!</p>
                    <p>You can now enable notifications in your account settings.</p>
                </div>
            </body>
        </html>
        """
        
        success = email_service.send_email(
            to_email=request.email,
            subject=subject,
            html_body=html_body,
        )
        
        if success:
            # Log notification
            await NotificationLogService.log_notification(
                db=db,
                user_id=current_user.id,
                notification_type="test_email",
                recipient_email=request.email,
                subject=subject,
                status="sent",
            )
            
            await db.commit()
            
            return SendTestEmailResponse(
                success=True,
                message="Test email sent successfully",
                email=request.email,
            )
        else:
            return SendTestEmailResponse(
                success=False,
                message="Failed to send test email. Check logs for details.",
                email=request.email,
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending test email"
        )


# Manual Digest Trigger (for testing)
@router.post("/notifications/send-digest")
async def send_digest_now(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger daily digest (for testing).
    
    Returns:
        Success status
    """
    try:
        success = await DigestService.generate_daily_digest(
            db=db,
            user_id=current_user.id,
            email_service=email_service,
        )
        
        if success:
            return {
                "success": True,
                "message": "Daily digest sent successfully",
            }
        else:
            return {
                "success": False,
                "message": "Failed to send daily digest",
            }
        
    except Exception as e:
        logger.error(f"Error sending digest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending digest"
        )
