"""
Email service for sending notifications.
Uses SMTP for email delivery with rate limiting and templates.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class EmailTemplates:
    """Email templates for notifications."""
    
    @staticmethod
    def daily_digest_template(
        user_name: str,
        new_matches_count: int,
        top_matches: List[Dict[str, Any]],
        applications_count: int,
        interviews_count: int,
    ) -> tuple[str, str]:
        """
        Generate daily digest email.
        
        Returns:
            Tuple of (subject, html_body)
        """
        subject = f"JobPilot Daily Digest - {new_matches_count} New Matches"
        
        # Build matches HTML
        matches_html = ""
        for match in top_matches[:5]:  # Top 5 matches
            matches_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">
                    <strong>{match.get('job_title', 'Job')}</strong><br>
                    <span style="color: #666;">{match.get('company', 'Company')}</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">
                    <span style="background-color: #4CAF50; color: white; padding: 4px 8px; border-radius: 4px;">
                        {match.get('score', 0):.0f}%
                    </span>
                </td>
            </tr>
            """
        
        html_body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2196F3; color: white; padding: 20px; border-radius: 4px; margin-bottom: 20px; }}
                    .section {{ margin-bottom: 20px; }}
                    .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2196F3; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                    .stat-box {{ flex: 1; background-color: #f5f5f5; padding: 15px; border-radius: 4px; text-align: center; }}
                    .stat-number {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
                    .stat-label {{ color: #666; font-size: 12px; margin-top: 5px; }}
                    .button {{ background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; }}
                    .footer {{ color: #999; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>JobPilot Daily Digest</h1>
                        <p>Your daily job opportunities summary</p>
                    </div>
                    
                    <div class="section">
                        <div class="stats">
                            <div class="stat-box">
                                <div class="stat-number">{new_matches_count}</div>
                                <div class="stat-label">New Matches</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number">{applications_count}</div>
                                <div class="stat-label">Applications</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number">{interviews_count}</div>
                                <div class="stat-label">Interviews</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Top Matches</div>
                        <table>
                            <thead>
                                <tr style="background-color: #f5f5f5;">
                                    <th style="padding: 12px; text-align: left;">Job</th>
                                    <th style="padding: 12px; text-align: center;">Match Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {matches_html}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="section">
                        <a href="https://jobpilot.app/dashboard/matches" class="button">View All Matches</a>
                    </div>
                    
                    <div class="footer">
                        <p>Hi {user_name},</p>
                        <p>This is your daily digest from JobPilot. You can customize your notification preferences in your account settings.</p>
                        <p>© 2024 JobPilot. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return subject, html_body
    
    @staticmethod
    def high_match_alert_template(
        user_name: str,
        job_title: str,
        company: str,
        match_score: float,
        location: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Generate high match alert email.
        
        Returns:
            Tuple of (subject, html_body)
        """
        subject = f"🎯 High Match Alert: {job_title} at {company} ({match_score:.0f}%)"
        
        html_body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 4px; margin-bottom: 20px; }}
                    .job-card {{ background-color: #f9f9f9; padding: 20px; border-left: 4px solid #4CAF50; margin-bottom: 20px; }}
                    .job-title {{ font-size: 20px; font-weight: bold; margin-bottom: 5px; }}
                    .job-company {{ color: #666; font-size: 16px; margin-bottom: 10px; }}
                    .match-score {{ font-size: 32px; font-weight: bold; color: #4CAF50; }}
                    .score-label {{ color: #666; font-size: 14px; }}
                    .button {{ background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 15px; }}
                    .footer {{ color: #999; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎯 High Match Alert!</h1>
                        <p>We found an excellent job match for you</p>
                    </div>
                    
                    <div class="job-card">
                        <div class="job-title">{job_title}</div>
                        <div class="job-company">{company}</div>
                        {f'<div style="color: #999; font-size: 14px; margin-bottom: 15px;">{location}</div>' if location else ''}
                        
                        <div style="margin-top: 15px;">
                            <div class="score-label">Match Score</div>
                            <div class="match-score">{match_score:.0f}%</div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <p>This job matches your profile and preferences very well. We recommend reviewing it and applying if interested.</p>
                    </div>
                    
                    <div>
                        <a href="https://jobpilot.app/dashboard/jobs" class="button">View Job Details</a>
                    </div>
                    
                    <div class="footer">
                        <p>Hi {user_name},</p>
                        <p>This is an automated alert from JobPilot. You can adjust your alert threshold in your notification settings.</p>
                        <p>© 2024 JobPilot. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return subject, html_body
    
    @staticmethod
    def application_update_template(
        user_name: str,
        job_title: str,
        company: str,
        status: str,
    ) -> tuple[str, str]:
        """
        Generate application update email.
        
        Returns:
            Tuple of (subject, html_body)
        """
        status_emoji = {
            "applied": "✅",
            "interview": "📞",
            "offer": "🎉",
            "accepted": "🎊",
            "rejected": "❌",
        }.get(status, "📝")
        
        subject = f"{status_emoji} Application Update: {job_title} at {company}"
        
        html_body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2196F3; color: white; padding: 20px; border-radius: 4px; margin-bottom: 20px; }}
                    .update-card {{ background-color: #f9f9f9; padding: 20px; border-radius: 4px; margin-bottom: 20px; }}
                    .status-badge {{ display: inline-block; background-color: #2196F3; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
                    .footer {{ color: #999; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Application Update</h1>
                        <p>Your application status has been updated</p>
                    </div>
                    
                    <div class="update-card">
                        <p><strong>Job:</strong> {job_title}</p>
                        <p><strong>Company:</strong> {company}</p>
                        <p style="margin-top: 15px;">
                            <strong>Status:</strong> <span class="status-badge">{status.upper()}</span>
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>Hi {user_name},</p>
                        <p>This is an automated notification from JobPilot.</p>
                        <p>© 2024 JobPilot. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return subject, html_body


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(
        self,
        smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port: int = int(os.getenv("SMTP_PORT", "587")),
        smtp_user: str = os.getenv("SMTP_USER", ""),
        smtp_password: str = os.getenv("SMTP_PASSWORD", ""),
        from_email: str = os.getenv("FROM_EMAIL", "noreply@jobpilot.app"),
    ):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.enabled = bool(smtp_user and smtp_password)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured (SMTP credentials missing)")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            # Attach text and HTML parts
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_daily_digest(
        self,
        to_email: str,
        user_name: str,
        new_matches_count: int,
        top_matches: List[Dict[str, Any]],
        applications_count: int,
        interviews_count: int,
    ) -> bool:
        """Send daily digest email."""
        subject, html_body = EmailTemplates.daily_digest_template(
            user_name=user_name,
            new_matches_count=new_matches_count,
            top_matches=top_matches,
            applications_count=applications_count,
            interviews_count=interviews_count,
        )
        
        return self.send_email(to_email, subject, html_body)
    
    def send_high_match_alert(
        self,
        to_email: str,
        user_name: str,
        job_title: str,
        company: str,
        match_score: float,
        location: Optional[str] = None,
    ) -> bool:
        """Send high match alert email."""
        subject, html_body = EmailTemplates.high_match_alert_template(
            user_name=user_name,
            job_title=job_title,
            company=company,
            match_score=match_score,
            location=location,
        )
        
        return self.send_email(to_email, subject, html_body)
    
    def send_application_update(
        self,
        to_email: str,
        user_name: str,
        job_title: str,
        company: str,
        status: str,
    ) -> bool:
        """Send application update email."""
        subject, html_body = EmailTemplates.application_update_template(
            user_name=user_name,
            job_title=job_title,
            company=company,
            status=status,
        )
        
        return self.send_email(to_email, subject, html_body)
