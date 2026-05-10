"""
Personnel business logic service.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Location, ProductionLine, Department, Position, Workstation, Employee
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class PersonnelService:
    """Service for Personnel business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway

    async def get_locations(self, type: Optional[str] = None) -> List[Location]:
        """Get locations with optional type filter."""
        query = select(Location).order_by(Location.name)
        if type:
            query = query.where(Location.type == type)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_departments(self, type: Optional[str] = None) -> List[Department]:
        """Get departments with optional type filter."""
        query = select(Department).order_by(Department.name)
        if type:
            query = query.where(Department.type == type)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_positions(self, department_id: Optional[str] = None) -> List[Position]:
        """Get positions with optional department filter."""
        query = select(Position).order_by(Position.name)
        if department_id:
            query = query.where(Position.department_id == department_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_employees(
        self,
        department_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Employee]:
        """Get employees with optional filters."""
        query = select(Employee).order_by(Employee.last_name, Employee.first_name)

        if department_id:
            # Filter by department through position
            subquery = select(Position.id).where(Position.department_id == department_id).subquery()
            query = query.where(Employee.position_id.in_(subquery))

        if status:
            query = query.where(Employee.status == status)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_summary(self) -> Dict[str, int]:
        """Get counts for all personnel entities."""
        counts = {}
        for model, key in [
            (Location, "locations"),
            (ProductionLine, "production_lines"),
            (Department, "departments"),
            (Position, "positions"),
            (Workstation, "workstations"),
            (Employee, "employees"),
        ]:
            result = await self.db.execute(select(func.count()).select_from(model))
            counts[key] = result.scalar() or 0
        return counts

    @track_feature_path(feature_name="personnel.sync_from_gateway", log_result=True)
    async def sync_from_gateway(self, from_date=None, to_date=None) -> int:
        """Sync all personnel entities from Gateway (full upsert)."""
        if not self.gateway:
            raise ValueError("Gateway client is required for sync")

        total_records = 0

        # 1. Locations (no deps)
        total_records += await self._sync_locations()

        # 2. Production Lines (deps: Location)
        total_records += await self._sync_production_lines()

        # 3. Departments (deps: Location; self-referencing parent_id — two-pass)
        total_records += await self._sync_departments()

        # 4. Positions (deps: Department)
        total_records += await self._sync_positions()

        # 5. Workstations (deps: Location, ProductionLine)
        total_records += await self._sync_workstations()

        # 6. Employees (deps: Position, Workstation)
        total_records += await self._sync_employees()

        log_data_flow(
            source="personnel_service",
            target="database",
            operation="sync_insert",
            records_count=total_records,
        )
        logger.info("personnel_sync_completed", total_records=total_records)
        return total_records

    async def _sync_locations(self) -> int:
        """Sync locations from Gateway."""
        logger.info("syncing_locations_from_gateway")
        locations_response = await self.gateway.get_personnel_locations()
        items = [item.dict() for item in locations_response.locations]
        logger.info("locations_fetched_from_gateway", total=len(items))
        return await self._upsert_entities(Location, items, self._apply_location_fields)

    async def _sync_production_lines(self) -> int:
        """Sync production lines from Gateway."""
        from app.services.gateway_client import GatewayError
        logger.info("syncing_production_lines_from_gateway")
        try:
            production_lines_response = await self.gateway.get_personnel_production_lines()
        except GatewayError as e:
            if "404" in str(e):
                logger.warning(
                    "personnel_production_lines_endpoint_not_found",
                    detail=str(e)[:200],
                )
                return 0
            raise
        items = [item.dict() for item in production_lines_response.productionLines]
        logger.info("production_lines_fetched_from_gateway", total=len(items))
        return await self._upsert_entities(ProductionLine, items, self._apply_production_line_fields)

    async def _sync_departments(self) -> int:
        """Sync departments from Gateway (two-pass for self-referencing parent_id)."""
        logger.info("syncing_departments_from_gateway")
        departments_response = await self.gateway.get_personnel_departments()
        items = [item.dict() for item in departments_response.departments]
        logger.info("departments_fetched_from_gateway", total=len(items))

        # First pass: upsert all without parent_id
        records_processed = await self._upsert_entities(
            Department, items, self._apply_department_fields, skip_parent=True
        )

        # Second pass: update parent_id
        for item in items:
            raw_id = item.get("id")
            try:
                dept_id = UUID(raw_id) if isinstance(raw_id, str) else raw_id
            except (ValueError, AttributeError):
                continue

            raw_parent = item.get("parentId")
            if raw_parent:
                try:
                    parent_id = UUID(raw_parent) if isinstance(raw_parent, str) else raw_parent
                except (ValueError, AttributeError):
                    continue

                existing = await self.db.execute(
                    select(Department).where(Department.id == dept_id)
                )
                dept = existing.scalar_one_or_none()
                if dept:
                    dept.parent_id = parent_id

        await self.db.commit()
        return records_processed

    async def _sync_positions(self) -> int:
        """Sync positions from Gateway."""
        logger.info("syncing_positions_from_gateway")
        positions_response = await self.gateway.get_personnel_positions()
        items = [item.dict() for item in positions_response.positions]
        logger.info("positions_fetched_from_gateway", total=len(items))
        return await self._upsert_entities(Position, items, self._apply_position_fields)

    async def _sync_workstations(self) -> int:
        """Sync workstations from Gateway."""
        logger.info("syncing_workstations_from_gateway")
        workstations_response = await self.gateway.get_personnel_workstations()
        items = [item.dict() for item in workstations_response.workstations]
        logger.info("workstations_fetched_from_gateway", total=len(items))
        return await self._upsert_entities(Workstation, items, self._apply_workstation_fields)

    async def _sync_employees(self) -> int:
        """Sync employees from Gateway."""
        logger.info("syncing_employees_from_gateway")
        employees_response = await self.gateway.get_personnel_employees()
        items = [item.dict() for item in employees_response.employees]
        logger.info("employees_fetched_from_gateway", total=len(items))
        return await self._upsert_entities(Employee, items, self._apply_employee_fields)

    async def _upsert_entities(
        self,
        model_class,
        items: List[Dict[str, Any]],
        apply_fields_fn,
        skip_parent: bool = False
    ) -> int:
        """Generic upsert helper: select by id, update if found, insert if not."""
        records_processed = 0

        for item in items:
            raw_id = item.get("id")
            try:
                entity_id = UUID(raw_id) if isinstance(raw_id, str) else raw_id
            except (ValueError, AttributeError):
                logger.warning(f"invalid_{model_class.__tablename__}_id_skipped", raw=raw_id)
                continue

            existing = await self.db.execute(
                select(model_class).where(model_class.id == entity_id)
            )
            entity = existing.scalar_one_or_none()

            if entity:
                apply_fields_fn(entity, item, skip_parent=skip_parent)
            else:
                entity = model_class(id=entity_id)
                apply_fields_fn(entity, item, skip_parent=skip_parent)
                self.db.add(entity)

            records_processed += 1

            if records_processed % 100 == 0:
                await self.db.flush()
                logger.info(f"{model_class.__tablename__}_sync_batch", records_processed=records_processed)

        await self.db.commit()
        logger.info(f"{model_class.__tablename__}_sync_completed", records_processed=records_processed)
        return records_processed

    def _apply_location_fields(self, location: Location, data: Dict[str, Any], **kwargs) -> None:
        location.name = data.get("name", location.name or "")
        location.code = data.get("code", location.code)
        location.type = data.get("type", location.type)
        location.address = data.get("address", location.address)
        location.is_active = data.get("isActive", location.is_active)

    def _apply_production_line_fields(self, line: ProductionLine, data: Dict[str, Any], **kwargs) -> None:
        line.name = data.get("name", line.name or "")
        line.code = data.get("code", line.code)
        raw_loc = data.get("locationId")
        if raw_loc:
            try:
                line.location_id = UUID(raw_loc) if isinstance(raw_loc, str) else raw_loc
            except (ValueError, AttributeError):
                pass
        line.description = data.get("description", line.description)
        line.is_active = data.get("isActive", line.is_active)

    def _apply_department_fields(self, dept: Department, data: Dict[str, Any], skip_parent: bool = False, **kwargs) -> None:
        dept.name = data.get("name", dept.name or "")
        dept.code = data.get("code", dept.code)
        raw_loc = data.get("locationId")
        if raw_loc:
            try:
                dept.location_id = UUID(raw_loc) if isinstance(raw_loc, str) else raw_loc
            except (ValueError, AttributeError):
                pass
        if not skip_parent:
            raw_parent = data.get("parentId")
            if raw_parent:
                try:
                    dept.parent_id = UUID(raw_parent) if isinstance(raw_parent, str) else raw_parent
                except (ValueError, AttributeError):
                    pass
            else:
                dept.parent_id = None
        dept.type = data.get("type", dept.type)
        dept.is_active = data.get("isActive", dept.is_active)

    def _apply_position_fields(self, position: Position, data: Dict[str, Any], **kwargs) -> None:
        position.name = data.get("name") or data.get("title") or position.name or ""
        position.code = data.get("code", position.code)
        raw_dept = data.get("departmentId")
        if raw_dept:
            try:
                position.department_id = UUID(raw_dept) if isinstance(raw_dept, str) else raw_dept
            except (ValueError, AttributeError):
                pass
        position.level = data.get("level", position.level)
        position.is_active = data.get("isActive", position.is_active)

    def _apply_workstation_fields(self, ws: Workstation, data: Dict[str, Any], **kwargs) -> None:
        ws.name = data.get("name", ws.name or "")
        ws.code = data.get("code", ws.code)
        raw_loc = data.get("locationId")
        if raw_loc:
            try:
                ws.location_id = UUID(raw_loc) if isinstance(raw_loc, str) else raw_loc
            except (ValueError, AttributeError):
                pass
        raw_line = data.get("productionLineId")
        if raw_line:
            try:
                ws.production_line_id = UUID(raw_line) if isinstance(raw_line, str) else raw_line
            except (ValueError, AttributeError):
                pass
        ws.type = data.get("type", ws.type)
        ws.is_active = data.get("isActive", ws.is_active)

    def _apply_employee_fields(self, emp: Employee, data: Dict[str, Any], **kwargs) -> None:
        # Handle both old format (firstName/lastName) and new format (fullName)
        if "fullName" in data:
            full_name = data.get("fullName", "").strip()
            parts = full_name.split()
            if len(parts) >= 2:
                emp.last_name = parts[0]
                emp.first_name = parts[1]
                emp.middle_name = " ".join(parts[2:]) if len(parts) > 2 else None
            elif len(parts) == 1:
                emp.first_name = parts[0]
                emp.last_name = ""
            else:
                emp.first_name = emp.first_name or ""
                emp.last_name = emp.last_name or ""
        else:
            emp.first_name = data.get("firstName", emp.first_name or "")
            emp.last_name = data.get("lastName", emp.last_name or "")
            emp.middle_name = data.get("middleName", emp.middle_name)

        emp.employee_number = data.get("employeeNumber", emp.employee_number)
        raw_pos = data.get("positionId")
        if raw_pos:
            try:
                emp.position_id = UUID(raw_pos) if isinstance(raw_pos, str) else raw_pos
            except (ValueError, AttributeError):
                pass
        raw_ws = data.get("workstationId")
        if raw_ws:
            try:
                emp.workstation_id = UUID(raw_ws) if isinstance(raw_ws, str) else raw_ws
            except (ValueError, AttributeError):
                pass
        emp.status = data.get("status", emp.status)
        emp.email = data.get("email", emp.email)
        emp.phone = data.get("phone", emp.phone)
        raw_date = data.get("hireDate")
        if raw_date:
            from datetime import date as dt_date
            if isinstance(raw_date, str):
                try:
                    emp.hire_date = dt_date.fromisoformat(raw_date)
                except ValueError:
                    pass
            elif isinstance(raw_date, dt_date):
                emp.hire_date = raw_date
