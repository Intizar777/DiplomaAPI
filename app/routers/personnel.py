"""
Personnel API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import GatewayClient, PersonnelService
from app.schemas import (
    LocationResponse,
    DepartmentResponse,
    PositionResponse,
    EmployeeResponse,
    PersonnelSummaryResponse,
)

router = APIRouter(prefix="/api/v1/personnel", tags=["Personnel"])


async def get_services(db: AsyncSession = Depends(get_db)):
    """Dependency to get personnel services."""
    gateway = GatewayClient()
    service = PersonnelService(db, gateway)
    return service


@router.get("/locations", response_model=List[LocationResponse])
async def get_locations(
    type: Optional[str] = Query(None, description="Filter by location type"),
    service: PersonnelService = Depends(get_services)
):
    """
    Get personnel locations with optional type filter.
    """
    return await service.get_locations(type)


@router.get("/departments", response_model=List[DepartmentResponse])
async def get_departments(
    type: Optional[str] = Query(None, description="Filter by department type"),
    service: PersonnelService = Depends(get_services)
):
    """
    Get departments with optional type filter.
    """
    return await service.get_departments(type)


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    service: PersonnelService = Depends(get_services)
):
    """
    Get positions with optional department filter.
    """
    return await service.get_positions(department_id)


@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees(
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    status: Optional[str] = Query(None, description="Filter by employee status"),
    service: PersonnelService = Depends(get_services)
):
    """
    Get employees with optional filters.
    """
    return await service.get_employees(department_id, status)


@router.get("/summary", response_model=PersonnelSummaryResponse)
async def get_summary(
    service: PersonnelService = Depends(get_services)
):
    """
    Get summary counts for all personnel entities.
    """
    counts = await service.get_summary()
    return PersonnelSummaryResponse(**counts)
