"""add_line_capacity_plans_for_oee

Revision ID: e42439396426
Revises: b23f4a1858c8
Create Date: 2026-05-12 07:06:14.270892+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e42439396426'
down_revision = 'b23f4a1858c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'line_capacity_plans',
        sa.Column('id', sa.UUID, primary_key=True),
        sa.Column('production_line_id', sa.UUID, nullable=False, index=True),
        sa.Column('planned_hours_per_day', sa.Integer, nullable=False, comment='Плановое рабочее время в часах'),
        sa.Column('target_oee_percent', sa.DECIMAL(5, 2), nullable=False, server_default='85.00', comment='Целевое значение OEE в процентах'),
        sa.Column('period_from', sa.Date, nullable=False, index=True),
        sa.Column('period_to', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['production_line_id'], ['production_lines.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('line_capacity_plans')
