"""Remove denormalized limit columns from quality_results

Revision ID: 005_remove_denormalized_quality_limits
Revises: 004_remove_denormalized_warehouse_code
Create Date: 2026-05-08 12:20:00.000000+00:00

After introducing quality_spec_id FK, remove denormalized lower_limit and upper_limit.
Quality specification limits are now stored in the quality_specs table and accessed
through the quality_spec_id foreign key relationship.
"""
from alembic import op
import sqlalchemy as sa


revision = '005_remove_denormalized_quality_limits'
down_revision = '004_remove_denormalized_warehouse_code'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop limit columns from quality_results
    op.drop_column('quality_results', 'upper_limit')
    op.drop_column('quality_results', 'lower_limit')


def downgrade() -> None:
    # Restore limit columns (nullable, since we can't know original values)
    op.add_column(
        'quality_results',
        sa.Column('lower_limit', sa.DECIMAL(precision=10, scale=4), nullable=True)
    )
    op.add_column(
        'quality_results',
        sa.Column('upper_limit', sa.DECIMAL(precision=10, scale=4), nullable=True)
    )
