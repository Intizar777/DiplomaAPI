"""
Shared reference data sync utilities.

Eliminates duplicate upsert logic across sync_references_task,
SalesService._sync_customer(), and InventoryService._sync_warehouse().
"""
from uuid import UUID
from typing import Optional, Dict

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Customer, Warehouse, UnitOfMeasure, SensorParameter, Product, QualitySpec, ProductionLine

logger = structlog.get_logger()


async def get_product_name_map(db: AsyncSession) -> Dict[UUID, str]:
    """Get mapping of product_id -> product_name for enrichment."""
    result = await db.execute(select(Product.id, Product.name))
    return {row[0]: row[1] for row in result.all()}


async def upsert_customer(db: AsyncSession, customer_data: dict) -> Optional[UUID]:
    """Upsert a customer from Gateway data. Returns customer_id."""
    customer_id_raw = customer_data.get("id")
    try:
        customer_id = UUID(customer_id_raw) if isinstance(customer_id_raw, str) else customer_id_raw
    except (ValueError, AttributeError, TypeError):
        logger.warning("invalid_customer_id_skipped", raw=customer_id_raw)
        return None

    code = customer_data.get("code") or str(customer_id)[:8]

    if code:
        existing = await db.execute(select(Customer).where(Customer.code == code))
        customer = existing.scalar_one_or_none()
    else:
        customer = None

    if not customer and customer_id:
        existing = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = existing.scalar_one_or_none()

    if customer:
        customer.name = customer_data.get("name", customer.name)
        customer.region = customer_data.get("region", customer.region)
        customer.is_active = customer_data.get("isActive", customer.is_active)
    else:
        customer = Customer(
            id=customer_id,
            code=code,
            name=customer_data.get("name", ""),
            region=customer_data.get("region", "Unknown"),
            is_active=customer_data.get("isActive", True),
        )
        db.add(customer)

    return customer.id


async def upsert_warehouse(db: AsyncSession, warehouse_data: dict) -> Optional[UUID]:
    """Upsert a warehouse from Gateway data. Returns warehouse_id."""
    warehouse_id_raw = warehouse_data.get("id")
    try:
        warehouse_id = UUID(warehouse_id_raw) if isinstance(warehouse_id_raw, str) else warehouse_id_raw
    except (ValueError, AttributeError, TypeError):
        logger.warning("invalid_warehouse_id_skipped", raw=warehouse_id_raw)
        return None

    code = warehouse_data.get("code")

    if code:
        existing = await db.execute(select(Warehouse).where(Warehouse.code == code))
        warehouse = existing.scalar_one_or_none()
    else:
        warehouse = None

    if not warehouse and warehouse_id:
        existing = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
        warehouse = existing.scalar_one_or_none()

    if warehouse:
        warehouse.code = code or warehouse.code
        warehouse.name = warehouse_data.get("name", warehouse.name)
        warehouse.capacity = warehouse_data.get("capacity", warehouse.capacity)
        warehouse.is_active = warehouse_data.get("isActive", warehouse.is_active)
    else:
        warehouse = Warehouse(
            id=warehouse_id,
            code=code or f"warehouse_{warehouse_id}",
            name=warehouse_data.get("name", ""),
            capacity=warehouse_data.get("capacity", 0),
            is_active=warehouse_data.get("isActive", True),
        )
        db.add(warehouse)

    return warehouse.id


async def upsert_unit_of_measure(db: AsyncSession, unit_data: dict) -> Optional[UUID]:
    """Upsert a unit of measure from Gateway data. Returns unit_id."""
    unit_id_raw = unit_data.get("id")
    try:
        unit_id = UUID(unit_id_raw) if isinstance(unit_id_raw, str) else unit_id_raw
    except (ValueError, AttributeError, TypeError):
        logger.warning("invalid_unit_of_measure_id_skipped", raw=unit_id_raw)
        return None

    code = unit_data.get("code")
    name = unit_data.get("name", "")

    if code:
        existing = await db.execute(select(UnitOfMeasure).where(UnitOfMeasure.code == code))
        unit = existing.scalar_one_or_none()
    else:
        unit = None

    if not unit and unit_id:
        existing = await db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == unit_id))
        unit = existing.scalar_one_or_none()

    if unit:
        unit.code = code or unit.code
        unit.name = name or unit.name
    else:
        unit = UnitOfMeasure(
            id=unit_id,
            code=code or f"unit_{unit_id}",
            name=name or "",
        )
        db.add(unit)

    return unit.id


async def upsert_sensor_parameter(db: AsyncSession, param_data: dict) -> Optional[UUID]:
    """Upsert a sensor parameter from Gateway data. Returns parameter_id."""
    param_id_raw = param_data.get("id")
    try:
        param_id = UUID(param_id_raw) if isinstance(param_id_raw, str) else param_id_raw
    except (ValueError, AttributeError, TypeError):
        logger.warning("invalid_sensor_parameter_id_skipped", raw=param_id_raw)
        return None

    code = param_data.get("code")
    name = param_data.get("name", "")
    unit = param_data.get("unit", "")
    description = param_data.get("description")
    is_active = param_data.get("isActive", True)

    if code:
        existing = await db.execute(select(SensorParameter).where(SensorParameter.code == code))
        param = existing.scalar_one_or_none()
    else:
        param = None

    if not param and param_id:
        existing = await db.execute(select(SensorParameter).where(SensorParameter.id == param_id))
        param = existing.scalar_one_or_none()

    if param:
        param.code = code or param.code
        param.name = name or param.name
        param.unit = unit or param.unit
        param.description = description or param.description
        param.is_active = is_active
    else:
        param = SensorParameter(
            id=param_id,
            code=code or f"param_{param_id}",
            name=name or "",
            unit=unit or "",
            description=description,
            is_active=is_active,
        )
        db.add(param)

    return param.id


async def upsert_quality_spec(db: AsyncSession, spec_data: dict) -> Optional[UUID]:
    """Upsert a quality spec from Gateway data. Returns spec_id."""
    spec_id_raw = spec_data.get("id")
    try:
        spec_id = UUID(spec_id_raw) if isinstance(spec_id_raw, str) else spec_id_raw
    except (ValueError, AttributeError, TypeError):
        logger.warning("invalid_quality_spec_id_skipped", raw=spec_id_raw)
        return None

    product_id_raw = spec_data.get("productId")
    try:
        product_id = UUID(product_id_raw) if isinstance(product_id_raw, str) else product_id_raw
    except (ValueError, AttributeError, TypeError):
        logger.warning("invalid_product_id_in_quality_spec_skipped", spec_id=spec_id_raw)
        return None

    parameter_name = spec_data.get("parameterName", "")
    lower_limit = spec_data.get("lowerLimit")
    upper_limit = spec_data.get("upperLimit")
    is_active = spec_data.get("isActive", True)

    # Find existing spec by product_id + parameter_name (natural key)
    if parameter_name:
        existing = await db.execute(
            select(QualitySpec).where(
                (QualitySpec.product_id == product_id) &
                (QualitySpec.parameter_name == parameter_name)
            )
        )
        spec = existing.scalar_one_or_none()
    else:
        spec = None

    # Fall back to UUID lookup
    if not spec and spec_id:
        existing = await db.execute(select(QualitySpec).where(QualitySpec.id == spec_id))
        spec = existing.scalar_one_or_none()

    if spec:
        spec.parameter_name = parameter_name or spec.parameter_name
        spec.lower_limit = lower_limit if lower_limit is not None else spec.lower_limit
        spec.upper_limit = upper_limit if upper_limit is not None else spec.upper_limit
        spec.is_active = is_active
    else:
        spec = QualitySpec(
            id=spec_id,
            product_id=product_id,
            parameter_name=parameter_name,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            is_active=is_active,
        )
        db.add(spec)

    return spec.id



async def upsert_production_line(db: AsyncSession, line_data: dict) -> Optional[UUID]:
    """Upsert a production line from Gateway data. Returns line_id."""
    line_id_raw = line_data.get("id")
    try:
        line_id = UUID(line_id_raw) if isinstance(line_id_raw, str) else line_id_raw
    except (ValueError, AttributeError, TypeError):
        logger.warning("invalid_production_line_id_skipped", raw=line_id_raw)
        return None

    code = line_data.get("code")
    name = line_data.get("name", "")
    division = line_data.get("division")
    is_active = line_data.get("isActive", True)

    if code:
        existing = await db.execute(select(ProductionLine).where(ProductionLine.code == code))
        line = existing.scalar_one_or_none()
    else:
        line = None

    if not line and line_id:
        existing = await db.execute(select(ProductionLine).where(ProductionLine.id == line_id))
        line = existing.scalar_one_or_none()

    if line:
        line.code = code or line.code
        line.name = name or line.name
        line.division = division or line.division
        line.is_active = is_active
    else:
        line = ProductionLine(
            id=line_id,
            code=code or f"line_{line_id}",
            name=name or "",
            division=division,
            is_active=is_active,
        )
        db.add(line)

    return line.id
