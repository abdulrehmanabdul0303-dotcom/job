"""Add job matches table.

Revision ID: 005
Revises: 004
Create Date: 2024-01-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create job_matches table
    op.create_table(
        'job_matches',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('job_id', sa.String(36), nullable=False),
        sa.Column('resume_id', sa.String(36), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=False),
        sa.Column('score_breakdown', sa.Text(), nullable=True),
        sa.Column('why_json', sa.Text(), nullable=True),
        sa.Column('missing_skills_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index('ix_job_matches_user_id', 'job_matches', ['user_id'])
    op.create_index('ix_job_matches_job_id', 'job_matches', ['job_id'])
    op.create_index('ix_job_matches_created_at', 'job_matches', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_job_matches_created_at', 'job_matches')
    op.drop_index('ix_job_matches_job_id', 'job_matches')
    op.drop_index('ix_job_matches_user_id', 'job_matches')
    
    # Drop table
    op.drop_table('job_matches')
