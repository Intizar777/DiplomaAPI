#!/usr/bin/env python
"""
Seed script: Generate 50+ quality defect records distributed evenly across the dataset period.

Usage:
    python scripts/seed_quality_defects.py

This script:
1. Queries existing products and quality specs from the database
2. Determines the date range from ProductionOutput records
3. Generates 50+ defective lots with out-of-spec QualityResult records
4. Creates corresponding ProductionOutput records
5. Inserts all data into the database
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4
import random

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.models.product import Product
from app.models.reference import QualitySpec
from app.models.quality import QualityResult
from app.models.output import ProductionOutput


async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with AsyncSession(engine) as session:
        print("=" * 70)
        print("QUALITY DEFECT DATA SEEDING")
        print("=" * 70)
        
        # Step 1: Fetch existing products and specs
        print("\n[1] Analyzing existing data structure...")
        
        products_result = await session.execute(select(Product))
        products = products_result.scalars().all()
        print(f"    Found {len(products)} products")
        
        specs_result = await session.execute(select(QualitySpec).where(QualitySpec.is_active == True))
        specs = specs_result.scalars().all()
        print(f"    Found {len(specs)} active quality specs")
        
        if not products or not specs:
            print("    ERROR: No products or specs found. Aborting.")
            await engine.dispose()
            return
        
        # Step 2: Determine date range
        print("\n[2] Determining date range...")
        
        date_query = select(
            func.min(ProductionOutput.production_date),
            func.max(ProductionOutput.production_date)
        )
        date_result = await session.execute(date_query)
        min_date, max_date = date_result.one()
        
        if not min_date or not max_date:
            print("    ERROR: No production dates found. Aborting.")
            await engine.dispose()
            return
        
        total_days = (max_date - min_date).days
        print(f"    Date range: {min_date} to {max_date} ({total_days} days)")
        
        # Step 3: Generate defect data
        print("\n[3] Generating 50+ defect records...")
        
        num_defects = 55
        quality_results = []
        production_outputs = []
        lot_numbers_created = set()
        
        # Distribute evenly across date range
        for i in range(num_defects):
            # Calculate date: spread evenly across the range
            days_offset = int((i / num_defects) * total_days)
            test_date = min_date + timedelta(days=days_offset)
            
            # Random product and spec
            product = random.choice(products)
            spec = random.choice(specs)
            
            # Generate out-of-spec value
            lower = spec.lower_limit or Decimal("0")
            upper = spec.upper_limit or Decimal("100")
            
            # 50% above upper, 50% below lower
            if random.random() < 0.5:
                result_value = upper + Decimal(str(random.uniform(1, 10)))
            else:
                result_value = lower - Decimal(str(random.uniform(0.1, 5)))
            
            result_value = result_value.quantize(Decimal("0.0001"))
            
            # Create lot number
            lot_number = f"DEFECT-{i+1:03d}-{uuid4().hex[:8].upper()}"
            
            # Create QualityResult
            qr = QualityResult(
                id=uuid4(),
                lot_number=lot_number,
                product_id=product.id,
                product_name=product.name,
                parameter_name=spec.parameter_name,
                result_value=result_value,
                quality_spec_id=spec.id,
                in_spec=False,
                decision="fail",
                test_date=test_date,
            )
            quality_results.append(qr)
            lot_numbers_created.add(lot_number)
            
            # Create ProductionOutput if not exists
            po = ProductionOutput(
                id=uuid4(),
                product_id=product.id,
                product_name=product.name,
                lot_number=lot_number,
                production_date=test_date,
                shift=random.choice(["Shift 1", "Shift 2", "Shift 3"]),
                snapshot_date=date.today(),
            )
            production_outputs.append(po)
        
        print(f"    Generated {len(quality_results)} QualityResult records")
        print(f"    Generated {len(production_outputs)} ProductionOutput records")
        
        # Step 4: Insert data
        print("\n[4] Inserting data into database...")
        
        session.add_all(quality_results)
        session.add_all(production_outputs)
        await session.commit()
        
        print(f"    ✓ Inserted {len(quality_results)} QualityResult records")
        print(f"    ✓ Inserted {len(production_outputs)} ProductionOutput records")
        
        # Step 5: Verify
        print("\n[5] Verifying inserted data...")
        
        verify_query = select(func.count(QualityResult.id)).where(QualityResult.in_spec == False)
        verify_result = await session.execute(verify_query)
        defect_count = verify_result.scalar()
        
        print(f"    Total out-of-spec records in DB: {defect_count}")
        
        # Sample data
        sample_query = select(QualityResult).where(QualityResult.in_spec == False).limit(3)
        sample_result = await session.execute(sample_query)
        samples = sample_result.scalars().all()
        
        print("\n    Sample defect records:")
        for qr in samples:
            print(f"      - Lot: {qr.lot_number}, Param: {qr.parameter_name}, Value: {qr.result_value}, Date: {qr.test_date}")
        
        print("\n" + "=" * 70)
        print("✓ SEEDING COMPLETE")
        print("=" * 70)
        print("\nYou can now test the endpoint:")
        print("  curl http://localhost:8000/api/v1/dashboards/qe/batch-analysis")
        print("\nOr visit: http://localhost:8000/docs")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
