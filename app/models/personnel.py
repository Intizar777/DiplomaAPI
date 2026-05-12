"""
Personnel reference models (synced from Gateway).
"""
from sqlalchemy import Column, String, Boolean, Index, Date
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class Location(Base, UUIDMixin, TimestampMixin):
    """
    Physical location (plant, warehouse, office).
    """
    __tablename__ = "locations"

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)
    type = Column(String(50), nullable=True, index=True)
    address = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)

    def __repr__(self):
        return f"<Location(code={self.code}, name={self.name})>"


class ProductionLine(Base, UUIDMixin, TimestampMixin):
    """
    Production line within a location.
    """
    __tablename__ = "production_lines"

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)
    location_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    description = Column(String(500), nullable=True)
    division = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)

    def __repr__(self):
        return f"<ProductionLine(code={self.code}, name={self.name})>"


class Department(Base, UUIDMixin, TimestampMixin):
    """
    Department / organizational unit.
    """
    __tablename__ = "departments"

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)
    location_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    parent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    type = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, nullable=True, default=True)

    __table_args__ = (
        Index("idx_departments_location_type", "location_id", "type"),
    )

    def __repr__(self):
        return f"<Department(code={self.code}, name={self.name})>"


class Position(Base, UUIDMixin, TimestampMixin):
    """
    Job position within a department.
    """
    __tablename__ = "positions"

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)
    department_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    level = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)

    def __repr__(self):
        return f"<Position(code={self.code}, name={self.name})>"


class Workstation(Base, UUIDMixin, TimestampMixin):
    """
    Workstation within a location and production line.
    """
    __tablename__ = "workstations"

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)
    location_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    production_line_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    type = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, nullable=True, default=True)

    __table_args__ = (
        Index("idx_workstations_location_line", "location_id", "production_line_id"),
    )

    def __repr__(self):
        return f"<Workstation(code={self.code}, name={self.name})>"


class Employee(Base, UUIDMixin, TimestampMixin):
    """
    Employee record.
    """
    __tablename__ = "employees"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    employee_number = Column(String(100), nullable=True, index=True)
    position_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    workstation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    status = Column(String(50), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    hire_date = Column(Date, nullable=True)

    __table_args__ = (
        Index("idx_employees_position_status", "position_id", "status"),
    )

    def __repr__(self):
        return f"<Employee(number={self.employee_number}, name={self.last_name} {self.first_name})>"
