"""
Personnel API schemas.
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LocationResponse(BaseModel):
    """Location response schema."""
    id: UUID
    name: str
    code: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class ProductionLineResponse(BaseModel):
    """Production line response schema."""
    id: UUID
    name: str
    code: Optional[str] = None
    location_id: Optional[UUID] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class DepartmentResponse(BaseModel):
    """Department response schema."""
    id: UUID
    name: str
    code: Optional[str] = None
    location_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    """Position response schema."""
    id: UUID
    name: str
    code: Optional[str] = None
    department_id: Optional[UUID] = None
    level: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class WorkstationResponse(BaseModel):
    """Workstation response schema."""
    id: UUID
    name: str
    code: Optional[str] = None
    location_id: Optional[UUID] = None
    production_line_id: Optional[UUID] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class EmployeeResponse(BaseModel):
    """Employee response schema."""
    id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    employee_number: Optional[str] = None
    position_id: Optional[UUID] = None
    workstation_id: Optional[UUID] = None
    status: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    hire_date: Optional[date] = None

    class Config:
        from_attributes = True


class PersonnelSummaryResponse(BaseModel):
    """Summary counts for all personnel entities."""
    locations: int = Field(description="Total locations count")
    production_lines: int = Field(description="Total production lines count")
    departments: int = Field(description="Total departments count")
    positions: int = Field(description="Total positions count")
    workstations: int = Field(description="Total workstations count")
    employees: int = Field(description="Total employees count")
