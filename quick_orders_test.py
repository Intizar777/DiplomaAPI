#!/usr/bin/env python3
"""
Quick test of orders endpoint with key checks.
"""
import asyncio
import httpx
from datetime import date, timedelta


async def quick_test():
    """Quick test of key functionality."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("Quick test of /api/v1/orders/list")
        print("=" * 50)
        
        # Test 1: Verify date filtering works
        print("\n1. Testing date filtering:")
        
        # Recent dates
        end_date = date.today()
        start_date = end_date - timedelta(days=3)
        
        params = {"from": start_date.isoformat(), "to": end_date.isoformat(), "limit": 20}
        response = await client.get(f"{base_url}/api/v1/orders/list", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Date range: {start_date} to {end_date}")
            print(f"   Orders found: {data['total']}")
            
            if data['orders']:
                dates = [order['snapshot_date'] for order in data['orders']]
                unique_dates = set(dates)
                print(f"   Unique dates in results: {len(unique_dates)}")
                print(f"   Date range in results: {min(dates)} to {max(dates)}")
        
        # Test 2: Verify status filtering
        print("\n2. Testing status filtering:")
        
        for status in ["completed", "in_progress", "planned"]:
            params = {"status": status, "limit": 10}
            response = await client.get(f"{base_url}/api/v1/orders/list", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['orders']:
                    actual_statuses = set(order['status'] for order in data['orders'])
                    print(f"   Status '{status}': {data['total']} total, {len(data['orders'])} on page")
                    print(f"   Actual statuses: {actual_statuses}")
        
        # Test 3: Check data quality metrics
        print("\n3. Checking data quality (sample of 50 orders):")
        
        params = {"limit": 50}
        response = await client.get(f"{base_url}/api/v1/orders/list", params=params)
        
        if response.status_code == 200:
            data = response.json()
            orders = data['orders']
            
            if orders:
                # Calculate completeness
                total = len(orders)
                has_target = sum(1 for o in orders if o['target_quantity'] is not None)
                has_actual = sum(1 for o in orders if o['actual_quantity'] is not None)
                has_product = sum(1 for o in orders if o['product_name'] is not None)
                has_line = sum(1 for o in orders if o['production_line'] is not None)
                
                print(f"   Sample size: {total} orders")
                print(f"   Has target quantity: {has_target}/{total} ({has_target/total*100:.1f}%)")
                print(f"   Has actual quantity: {has_actual}/{total} ({has_actual/total*100:.1f}%)")
                print(f"   Has product name: {has_product}/{total} ({has_product/total*100:.1f}%)")
                print(f"   Has production line: {has_line}/{total} ({has_line/total*100:.1f}%)")
                
                # Check date distribution
                dates = [o['snapshot_date'] for o in orders]
                unique_dates = set(dates)
                print(f"   Unique dates in sample: {len(unique_dates)}")
                if unique_dates:
                    print(f"   Dates: {sorted(unique_dates)}")
        
        print("\n" + "=" * 50)
        print("Quick test complete.")


if __name__ == "__main__":
    asyncio.run(quick_test())