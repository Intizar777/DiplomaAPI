"""add analytics tables and division to production_lines

Revision ID: b23f4a1858c8
Revises: 005_remove_denorm_quality
Create Date: 2026-05-12 06:39:33.908413+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b23f4a1858c8'
down_revision = '005_remove_denorm_quality'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add division column to production_lines
    op.add_column('production_lines', sa.Column('division', sa.String(255), nullable=True))

    # Create batch_inputs table
    op.create_table(
        'batch_inputs',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quantity', sa.DECIMAL(precision=15, scale=3), nullable=False),
        sa.Column('input_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
    )
    op.create_index('ix_batch_inputs_order_id', 'batch_inputs', ['order_id'])
    op.create_index('ix_batch_inputs_product_id', 'batch_inputs', ['product_id'])
    op.create_index('ix_batch_inputs_input_date', 'batch_inputs', ['input_date'])

    # Create downtime_events table
    op.create_table(
        'downtime_events',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('production_line_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.String(500), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer, nullable=True),
        sa.Column('event_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
    )
    op.create_index('ix_downtime_events_production_line_id', 'downtime_events', ['production_line_id'])
    op.create_index('ix_downtime_events_category', 'downtime_events', ['category'])
    op.create_index('ix_downtime_events_started_at', 'downtime_events', ['started_at'])

    # Create promo_campaigns table
    op.create_table(
        'promo_campaigns',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('product_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('discount_percent', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('budget', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('event_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
    )
    op.create_index('ix_promo_campaigns_channel', 'promo_campaigns', ['channel'])
    op.create_index('ix_promo_campaigns_product_id', 'promo_campaigns', ['product_id'])
    op.create_index('ix_promo_campaigns_start_date', 'promo_campaigns', ['start_date'])


def downgrade() -> None:
    # Drop promo_campaigns table
    op.drop_index('ix_promo_campaigns_start_date', 'promo_campaigns')
    op.drop_index('ix_promo_campaigns_product_id', 'promo_campaigns')
    op.drop_index('ix_promo_campaigns_channel', 'promo_campaigns')
    op.drop_table('promo_campaigns')

    # Drop downtime_events table
    op.drop_index('ix_downtime_events_started_at', 'downtime_events')
    op.drop_index('ix_downtime_events_category', 'downtime_events')
    op.drop_index('ix_downtime_events_production_line_id', 'downtime_events')
    op.drop_table('downtime_events')

    # Drop batch_inputs table
    op.drop_index('ix_batch_inputs_input_date', 'batch_inputs')
    op.drop_index('ix_batch_inputs_product_id', 'batch_inputs')
    op.drop_index('ix_batch_inputs_order_id', 'batch_inputs')
    op.drop_table('batch_inputs')

    # Remove division column from production_lines
    op.drop_column('production_lines', 'division')
