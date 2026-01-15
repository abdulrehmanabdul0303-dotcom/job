"""Add apply kit and job activity tables.

Revision ID: 006
Revises: 005
Create Date: 2024-01-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create apply_kits table
    op.create_table(
        'apply_kits',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('job_id', sa.String(36), nullable=False),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('tailored_bullets_json', sa.Text(), nullable=True),
        sa.Column('qa_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for apply_kits
    op.create_index('ix_apply_kits_user_id', 'apply_kits', ['user_id'])
    op.create_index('ix_apply_kits_job_id', 'apply_kits', ['job_id'])
    
    # Create job_activities table
    op.create_table(
        'job_activities',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('job_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for job_activities
    op.create_index('ix_job_activities_user_id', 'job_activities', ['user_id'])
    op.create_index('ix_job_activities_job_id', 'job_activities', ['job_id'])
    op.create_index('ix_job_activities_status', 'job_activities', ['status'])
    op.create_index('ix_job_activities_created_at', 'job_activities', ['created_at'])


def downgrade() -> None:
    # Drop indexes for job_activities
    op.drop_index('ix_job_activities_created_at', 'job_activities')
    op.drop_index('ix_job_activities_status', 'job_activities')
    op.drop_index('ix_job_activities_job_id', 'job_activities')
    op.drop_index('ix_job_activities_user_id', 'job_activities')
    
    # Drop job_activities table
    op.drop_table('job_activities')
    
    # Drop indexes for apply_kits
    op.drop_index('ix_apply_kits_job_id', 'apply_kits')
    op.drop_index('ix_apply_kits_user_id', 'apply_kits')
    
    # Drop apply_kits table
    op.drop_table('apply_kits')
