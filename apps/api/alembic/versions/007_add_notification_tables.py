"""Add notification tables.

Revision ID: 007
Revises: 006
Create Date: 2024-01-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_settings table
    op.create_table(
        'notification_settings',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('daily_digest_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('high_match_alert_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('application_update_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('interview_reminder_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('offer_notification_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('daily_digest_time', sa.String(5), nullable=False, server_default='09:00'),
        sa.Column('high_match_threshold', sa.String(3), nullable=False, server_default='85'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    
    # Create index for notification_settings
    op.create_index('ix_notification_settings_user_id', 'notification_settings', ['user_id'])
    
    # Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('related_job_id', sa.String(36), nullable=True),
        sa.Column('related_match_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for notification_logs
    op.create_index('ix_notification_logs_user_id', 'notification_logs', ['user_id'])
    op.create_index('ix_notification_logs_notification_type', 'notification_logs', ['notification_type'])
    op.create_index('ix_notification_logs_related_job_id', 'notification_logs', ['related_job_id'])
    op.create_index('ix_notification_logs_created_at', 'notification_logs', ['created_at'])


def downgrade() -> None:
    # Drop indexes for notification_logs
    op.drop_index('ix_notification_logs_created_at', 'notification_logs')
    op.drop_index('ix_notification_logs_related_job_id', 'notification_logs')
    op.drop_index('ix_notification_logs_notification_type', 'notification_logs')
    op.drop_index('ix_notification_logs_user_id', 'notification_logs')
    
    # Drop notification_logs table
    op.drop_table('notification_logs')
    
    # Drop index for notification_settings
    op.drop_index('ix_notification_settings_user_id', 'notification_settings')
    
    # Drop notification_settings table
    op.drop_table('notification_settings')
