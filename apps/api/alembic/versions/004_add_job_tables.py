"""add job tables

Revision ID: 004
Revises: 003
Create Date: 2025-01-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create job_sources and job_postings tables."""
    
    # Create job_sources table
    op.create_table(
        'job_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('fetch_frequency_hours', sa.Integer, nullable=False, server_default='24'),
        sa.Column('last_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_fetch_status', sa.String(50), nullable=True),
        sa.Column('last_fetch_error', sa.Text, nullable=True),
        sa.Column('jobs_fetched_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create job_postings table
    op.create_table(
        'job_postings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('requirements', sa.Text, nullable=True),
        sa.Column('salary_min', sa.Integer, nullable=True),
        sa.Column('salary_max', sa.Integer, nullable=True),
        sa.Column('salary_currency', sa.String(10), nullable=True),
        sa.Column('work_type', sa.String(50), nullable=True),
        sa.Column('application_url', sa.String(500), nullable=False),
        sa.Column('url_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('posted_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_data', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_job_postings_source_id', 'job_postings', ['source_id'])
    op.create_index('ix_job_postings_title', 'job_postings', ['title'])
    op.create_index('ix_job_postings_company', 'job_postings', ['company'])
    op.create_index('ix_job_postings_url_hash', 'job_postings', ['url_hash'])
    op.create_index('ix_job_postings_created_at', 'job_postings', ['created_at'])


def downgrade() -> None:
    """Drop job tables."""
    op.drop_index('ix_job_postings_created_at', table_name='job_postings')
    op.drop_index('ix_job_postings_url_hash', table_name='job_postings')
    op.drop_index('ix_job_postings_company', table_name='job_postings')
    op.drop_index('ix_job_postings_title', table_name='job_postings')
    op.drop_index('ix_job_postings_source_id', table_name='job_postings')
    op.drop_table('job_postings')
    op.drop_table('job_sources')
