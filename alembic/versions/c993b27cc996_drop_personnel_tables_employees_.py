"""drop personnel tables (employees, departments, positions, workstations, locations)

Revision ID: c993b27cc996
Revises: 2e566eb26ef2
Create Date: 2026-05-12 08:44:23.586009+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c993b27cc996'
down_revision = '2e566eb26ef2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop employee-related tables (not part of API responsibilities)
    # Keep production_lines and locations tables (locations is referenced by production_lines)
    op.drop_table('employees')
    op.drop_table('workstations')
    op.drop_table('positions')
    op.drop_table('departments')


def downgrade() -> None:
    # Restore tables (in reverse order of creation, excluding locations which we keep)
    op.create_table(
        'departments',
        sa.Column('id', sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(100), nullable=True),
        sa.Column('location_id', sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column('parent_id', sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_departments_code', 'departments', ['code'])
    op.create_index('idx_departments_location_id', 'departments', ['location_id'])
    op.create_index('idx_departments_parent_id', 'departments', ['parent_id'])
    op.create_index('idx_departments_type', 'departments', ['type'])
    op.create_index('idx_departments_location_type', 'departments', ['location_id', 'type'])

    op.create_table(
        'positions',
        sa.Column('id', sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(100), nullable=True),
        sa.Column('department_id', sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column('level', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_positions_code', 'positions', ['code'])
    op.create_index('idx_positions_department_id', 'positions', ['department_id'])
    op.create_index('idx_positions_level', 'positions', ['level'])

    op.create_table(
        'workstations',
        sa.Column('id', sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(100), nullable=True),
        sa.Column('location_id', sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column('production_line_id', sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workstations_code', 'workstations', ['code'])
    op.create_index('idx_workstations_location_id', 'workstations', ['location_id'])
    op.create_index('idx_workstations_production_line_id', 'workstations', ['production_line_id'])
    op.create_index('idx_workstations_type', 'workstations', ['type'])
    op.create_index('idx_workstations_location_line', 'workstations', ['location_id', 'production_line_id'])

    op.create_table(
        'employees',
        sa.Column('id', sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100), nullable=True),
        sa.Column('employee_number', sa.String(100), nullable=True),
        sa.Column('position_id', sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column('workstation_id', sa.dialects.postgresql.UUID(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_employees_employee_number', 'employees', ['employee_number'])
    op.create_index('idx_employees_position_id', 'employees', ['position_id'])
    op.create_index('idx_employees_workstation_id', 'employees', ['workstation_id'])
    op.create_index('idx_employees_status', 'employees', ['status'])
    op.create_index('idx_employees_position_status', 'employees', ['position_id', 'status'])
