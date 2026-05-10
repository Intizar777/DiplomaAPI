"""
Product business logic service.
"""
from datetime import date
from typing import Optional, List, Dict
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, UnitOfMeasure
from app.services.gateway_client import GatewayClient
from app.utils.logging_utils import track_feature_path, log_data_flow
import structlog

logger = structlog.get_logger()


class ProductService:
    """Service for Product business logic."""

    def __init__(self, db: AsyncSession, gateway: Optional[GatewayClient] = None):
        self.db = db
        self.gateway = gateway
    
    async def get_products(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None
    ) -> List[Product]:
        """Get products with optional filters."""
        query = select(Product).order_by(Product.name)
        
        if category:
            query = query.where(Product.category == category)
        if brand:
            query = query.where(Product.brand == brand)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single product by ID."""
        query = select(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_product_name_map(self) -> Dict[str, str]:
        """Get mapping of product_id -> product_name for enrichment."""
        query = select(Product.id, Product.name)
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}
    
    async def _sync_unit_of_measure(self, unit_data) -> Optional[UUID]:
        """Sync a unit of measure and return its ID."""
        if not unit_data:
            return None

        # Gateway returns unitOfMeasure as a plain string (e.g. "kg", "liters")
        if isinstance(unit_data, str):
            code = unit_data.strip()
            if not code:
                return None
            existing = await self.db.execute(
                select(UnitOfMeasure).where(UnitOfMeasure.code == code)
            )
            unit = existing.scalar_one_or_none()
            if not unit:
                unit = UnitOfMeasure(id=uuid4(), code=code, name=code)
                self.db.add(unit)
                await self.db.flush()
            return unit.id

        # Handle Pydantic models and dictionaries
        if hasattr(unit_data, '__dict__'):  # Pydantic model or dataclass
            unit_id_raw = getattr(unit_data, 'id', None)
            code = getattr(unit_data, 'code', None)
            name = getattr(unit_data, 'name', '')
            source_system_id = getattr(unit_data, 'sourceSystemId', None)
        else:  # Dictionary
            unit_id_raw = unit_data.get("id")
            code = unit_data.get("code")
            name = unit_data.get("name", "")
            source_system_id = unit_data.get("sourceSystemId")

        try:
            unit_id = UUID(unit_id_raw) if isinstance(unit_id_raw, str) else unit_id_raw
        except (ValueError, AttributeError, TypeError):
            logger.warning("invalid_unit_of_measure_id_skipped", raw=unit_id_raw)
            return None

        # Try to find existing by code or id
        if code:
            existing = await self.db.execute(
                select(UnitOfMeasure).where(UnitOfMeasure.code == code)
            )
            unit = existing.scalar_one_or_none()
        else:
            unit = None

        if not unit and unit_id:
            existing = await self.db.execute(
                select(UnitOfMeasure).where(UnitOfMeasure.id == unit_id)
            )
            unit = existing.scalar_one_or_none()

        if unit:
            unit.code = code or unit.code
            unit.name = name or unit.name
            unit.source_system_id = source_system_id or unit.source_system_id
        else:
            unit = UnitOfMeasure(
                id=unit_id,
                code=code or f"unit_{unit_id}",
                name=name or "",
                source_system_id=source_system_id,
            )
            self.db.add(unit)
            await self.db.flush()

        return unit.id

    @track_feature_path(feature_name="products.sync_from_gateway", log_result=True)
    async def sync_from_gateway(self, from_date=None, to_date=None) -> int:
        """Sync products from Gateway (full upsert)."""
        logger.info("syncing_products_from_gateway")

        products_response = await self.gateway.get_products()
        logger.info("products_fetched_from_gateway", total_products=len(products_response.products))

        records_processed = 0

        for product_item in products_response.products:
            product_id = product_item.id
            code = product_item.code

            # Sync UnitOfMeasure if present
            unit_of_measure_id = None
            if product_item.unitOfMeasure:
                unit_of_measure_id = await self._sync_unit_of_measure(product_item.unitOfMeasure.dict())

            # Try to find existing product by code first (unique constraint), then by id
            if code:
                existing = await self.db.execute(
                    select(Product).where(Product.code == code)
                )
                product = existing.scalar_one_or_none()
            else:
                product = None

            # If not found by code, try by id
            if not product and product_id:
                existing = await self.db.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = existing.scalar_one_or_none()

            if product:
                product.code = code or product.code
                product.name = product_item.name or product.name
                product.category = product_item.category or product.category
                product.brand = product_item.brand or product.brand
                product.unit_of_measure_id = unit_of_measure_id
                product.shelf_life_days = product_item.shelfLifeDays or product.shelf_life_days
                product.requires_quality_check = product_item.requiresQualityCheck if product_item.requiresQualityCheck is not None else product.requires_quality_check
                product.source_system_id = str(product_item.id)
            else:
                product = Product(
                    id=product_id,  # Preserve original UUID from Gateway
                    code=code,
                    name=product_item.name or "",
                    category=product_item.category,
                    brand=product_item.brand,
                    unit_of_measure_id=unit_of_measure_id,
                    shelf_life_days=product_item.shelfLifeDays,
                    requires_quality_check=product_item.requiresQualityCheck if product_item.requiresQualityCheck is not None else False,
                    source_system_id=str(product_item.id),
                )
                self.db.add(product)

            records_processed += 1

            if records_processed % 100 == 0:
                await self.db.flush()
                logger.info("products_sync_batch", records_processed=records_processed)

        log_data_flow(
            source="product_service",
            target="database",
            operation="sync_insert",
            records_count=records_processed,
        )
        await self.db.commit()
        logger.info("products_sync_completed", records_processed=records_processed)
        return records_processed

    async def upsert_from_event(self, payload: "ProductEventPayload", event_id: str = None) -> None:
        """Upsert product from RabbitMQ event. Idempotent by event_id or code/id."""
        from app.messaging.schemas import ProductEventPayload
        from uuid import UUID

        # First check by event_id if provided (absolute idempotency)
        if event_id:
            existing = await self.db.execute(
                select(Product).where(Product.event_id == UUID(event_id))
            )
            product = existing.scalar_one_or_none()
            if product:
                logger.info("product_skipped_duplicate_event", event_id=event_id)
                return

        # Search by code first (unique), then by id (from event)
        if payload.code:
            existing = await self.db.execute(
                select(Product).where(Product.code == payload.code)
            )
            product = existing.scalar_one_or_none()
        else:
            product = None

        if not product:
            existing = await self.db.execute(
                select(Product).where(Product.id == payload.id)
            )
            product = existing.scalar_one_or_none()

        if product:
            # Update existing product
            product.code = payload.code or product.code
            product.name = payload.name
            product.category = payload.category or product.category
            if event_id:
                product.event_id = UUID(event_id)
            logger.info("product_updated_from_event", product_id=str(payload.id), code=payload.code)
        else:
            # Insert new product
            product = Product(
                id=payload.id,
                code=payload.code,
                name=payload.name,
                category=payload.category,
                event_id=UUID(event_id) if event_id else None,
            )
            self.db.add(product)
            logger.info("product_inserted_from_event", product_id=str(payload.id), code=payload.code)

        await self.db.commit()
