"""
Cost base service for managing product costs and KPI configurations.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CostBase, KPIConfig
import structlog

logger = structlog.get_logger()


class CostBaseService:
    """Service for cost base management and KPI configuration."""

    async def create_or_update_cost_base(
        self,
        db: AsyncSession,
        product_id: Optional[str],
        raw_material_cost: Decimal,
        labor_cost_per_hour: Optional[Decimal],
        depreciation_monthly: Optional[Decimal],
        period_from: date,
        period_to: Optional[date],
    ) -> dict:
        """Create or update cost base for a product and period."""
        logger.info(
            "create_cost_base",
            product_id=product_id,
            raw_material_cost=raw_material_cost,
            period_from=period_from,
            period_to=period_to,
        )

        cost_base = CostBase(
            product_id=UUID(product_id) if product_id else None,
            raw_material_cost=raw_material_cost,
            labor_cost_per_hour=labor_cost_per_hour,
            depreciation_monthly=depreciation_monthly,
            period_from=period_from,
            period_to=period_to,
        )
        db.add(cost_base)
        await db.commit()
        await db.refresh(cost_base)

        logger.info("cost_base_created", cost_base_id=str(cost_base.id))
        return {
            "id": str(cost_base.id),
            "product_id": str(cost_base.product_id) if cost_base.product_id else None,
            "raw_material_cost": cost_base.raw_material_cost,
            "labor_cost_per_hour": cost_base.labor_cost_per_hour,
            "depreciation_monthly": cost_base.depreciation_monthly,
            "period_from": cost_base.period_from.isoformat(),
            "period_to": cost_base.period_to.isoformat() if cost_base.period_to else None,
            "created_at": cost_base.created_at.isoformat(),
            "updated_at": cost_base.updated_at.isoformat(),
        }

    async def get_cost_base(
        self,
        db: AsyncSession,
        product_id: Optional[str],
        as_of_date: date,
    ) -> Optional[CostBase]:
        """Get latest active cost base for a product as of a given date."""
        query = select(CostBase).where(
            and_(
                CostBase.period_from <= as_of_date,
            )
        )

        if product_id:
            query = query.where(CostBase.product_id == UUID(product_id))
        else:
            query = query.where(CostBase.product_id.is_(None))

        # Add period_to condition: either NULL or >= as_of_date
        query = query.where(
            (CostBase.period_to.is_(None)) | (CostBase.period_to >= as_of_date)
        )

        query = query.order_by(CostBase.period_from.desc()).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_cost_bases(
        self,
        db: AsyncSession,
        product_id: Optional[str],
        offset: int = 0,
        limit: int = 100,
    ) -> dict:
        """Get all cost bases for a product, paginated."""
        query = select(CostBase)

        if product_id:
            query = query.where(CostBase.product_id == UUID(product_id))
        else:
            query = query.where(CostBase.product_id.is_(None))

        query = query.order_by(CostBase.period_from.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        cost_bases = result.scalars().all()

        return {
            "total": len(cost_bases),
            "offset": offset,
            "limit": limit,
            "items": [
                {
                    "id": str(cb.id),
                    "product_id": str(cb.product_id) if cb.product_id else None,
                    "raw_material_cost": cb.raw_material_cost,
                    "labor_cost_per_hour": cb.labor_cost_per_hour,
                    "depreciation_monthly": cb.depreciation_monthly,
                    "period_from": cb.period_from.isoformat(),
                    "period_to": cb.period_to.isoformat() if cb.period_to else None,
                    "created_at": cb.created_at.isoformat(),
                    "updated_at": cb.updated_at.isoformat(),
                }
                for cb in cost_bases
            ],
        }

    async def set_kpi_config(
        self,
        db: AsyncSession,
        key: str,
        value: Decimal,
        description: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> dict:
        """Set or update a KPI configuration value."""
        logger.info("set_kpi_config", key=key, value=value)

        # Try to find existing config
        query = select(KPIConfig).where(KPIConfig.key == key)
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if config:
            config.value = value
            config.description = description or config.description
            config.updated_by = updated_by
            config.updated_at = datetime.now()
        else:
            config = KPIConfig(
                key=key,
                value=value,
                description=description,
                updated_by=updated_by,
            )
            db.add(config)

        await db.commit()
        await db.refresh(config)

        logger.info("kpi_config_set", key=key, value=value)
        return {
            "id": str(config.id),
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "updated_by": config.updated_by,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
        }

    async def get_kpi_config(
        self,
        db: AsyncSession,
        key: str,
    ) -> Optional[Decimal]:
        """Get a KPI configuration value, returns None if not found."""
        query = select(KPIConfig).where(KPIConfig.key == key)
        result = await db.execute(query)
        config = result.scalar_one_or_none()
        return config.value if config else None

    async def get_all_kpi_configs(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 100,
    ) -> dict:
        """Get all KPI configurations, paginated."""
        query = select(KPIConfig).order_by(KPIConfig.key).offset(offset).limit(limit)
        result = await db.execute(query)
        configs = result.scalars().all()

        return {
            "total": len(configs),
            "offset": offset,
            "limit": limit,
            "items": [
                {
                    "id": str(c.id),
                    "key": c.key,
                    "value": c.value,
                    "description": c.description,
                    "updated_by": c.updated_by,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                }
                for c in configs
            ],
        }
