"""Add resume tables

Revision ID: 002
Revises: 001
Create Date: 2026-01-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create resumes table
    op.create_table(
        'resumes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', sa.Text(), nullable=True),  # JSON as TEXT for SQLite
        sa.Column('is_parsed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_user_id'), 'resumes', ['user_id'], unique=False)
    
    # Create resume_scorecards table
    op.create_table(
        'resume_scorecards',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('resume_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('ats_score', sa.Integer(), nullable=False),
        sa.Column('contact_score', sa.Integer(), nullable=False),
        sa.Column('sections_score', sa.Integer(), nullable=False),
        sa.Column('keywords_score', sa.Integer(), nullable=False),
        sa.Column('formatting_score', sa.Integer(), nullable=False),
        sa.Column('impact_score', sa.Integer(), nullable=False),
        sa.Column('missing_keywords', sa.Text(), nullable=True),  # JSON as TEXT
        sa.Column('formatting_issues', sa.Text(), nullable=True),  # JSON as TEXT
        sa.Column('suggestions', sa.Text(), nullable=True),  # JSON as TEXT
        sa.Column('strengths', sa.Text(), nullable=True),  # JSON as TEXT
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_scorecards_resume_id'), 'resume_scorecards', ['resume_id'], unique=True)
    op.create_index(op.f('ix_resume_scorecards_user_id'), 'resume_scorecards', ['user_id'], unique=False)
    
    # Create resume_share_links table
    op.create_table(
        'resume_share_links',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('resume_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('share_token', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('view_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_share_links_resume_id'), 'resume_share_links', ['resume_id'], unique=False)
    op.create_index(op.f('ix_resume_share_links_share_token'), 'resume_share_links', ['share_token'], unique=True)
    op.create_index(op.f('ix_resume_share_links_user_id'), 'resume_share_links', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_share_links_user_id'), table_name='resume_share_links')
    op.drop_index(op.f('ix_resume_share_links_share_token'), table_name='resume_share_links')
    op.drop_index(op.f('ix_resume_share_links_resume_id'), table_name='resume_share_links')
    op.drop_table('resume_share_links')
    
    op.drop_index(op.f('ix_resume_scorecards_user_id'), table_name='resume_scorecards')
    op.drop_index(op.f('ix_resume_scorecards_resume_id'), table_name='resume_scorecards')
    op.drop_table('resume_scorecards')
    
    op.drop_index(op.f('ix_resumes_user_id'), table_name='resumes')
    op.drop_table('resumes')
