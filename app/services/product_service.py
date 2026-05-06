"""
Product business logic service.
"""
from datetime import date
from typing import Optional, List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.services.gateway_client import GatewayClient
import structlog

logger = structlog.get_logger()


class ProductService:
    """Service for Product business logic."""
    
    def __init__(self, db: AsyncSession, gateway: GatewayClient):
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
    
    async def sync_from_gateway(self) -> int:
        """Sync products from Gateway (full upsert)."""
        logger.info("syncing_products_from_gateway")
        
        gateway_data = await self.gateway.get_products()
        products = gateway_data.get("products", [])
        logger.info("products_fetched_from_gateway", total_products=len(products))
        
        records_processed = 0
        
        for product_data in products:
            product_id = product_data.get("id")
            code = product_data.get("code")
            
            # Try to find existing product by code (upsert)
            existing = await self.db.execute(
                select(Product).where(Product.code == code)
            )
            product = existing.scalar_one_or_none()
            
            if product:
                product.name = product_data.get("name", product.name)
                product.category = product_data.get("category", product.category)
                product.brand = product_data.get("brand", product.brand)
                product.unit_of_measure = product_data.get("unitOfMeasure", product.unit_of_measure)
                product.shelf_life_days = product_data.get("shelfLifeDays", product.shelf_life_days)
                product.requires_quality_check = product_data.get("requiresQualityCheck", product.requires_quality_check)
                product.source_system_id = product_data.get("sourceSystemId", product.source_system_id)
            else:
                product = Product(
                    code=code,
                    name=product_data.get("name", ""),
                    category=product_data.get("category"),
                    brand=product_data.get("brand"),
                    unit_of_measure=product_data.get("unitOfMeasure"),
                    shelf_life_days=product_data.get("shelfLifeDays"),
                    requires_quality_check=product_data.get("requiresQualityCheck", False),
                    source_system_id=product_data.get("sourceSystemId"),
                )
                self.db.add(product)
            
            records_processed += 1
            
            if records_processed % 100 == 0:
                await self.db.flush()
                logger.info("products_sync_batch", records_processed=records_processed)
        
        await self.db.commit()
        logger.info("products_sync_completed", records_processed=records_processed)
        return records_processed
