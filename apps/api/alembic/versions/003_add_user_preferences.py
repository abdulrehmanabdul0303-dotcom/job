"""add user preferences table

Revision ID: 003
Revises: 002
Create Date: 2025-01-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_preferences table."""
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, unique=True),
        sa.Column('desired_role', sa.String(255), nullable=True),
        sa.Column('preferred_countries', sa.Text, nullable=True),
        sa.Column('min_salary', sa.Integer, nullable=True),
        sa.Column('max_salary', sa.Integer, nullable=True),
        sa.Column('work_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create index on user_id for faster lookups
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])


def downgrade() -> None:
    """Drop user_preferences table."""
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')
