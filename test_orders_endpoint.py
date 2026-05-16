#!/usr/bin/env python3
"""
Test script for /api/v1/orders/list endpoint.
Checks date filtering and data distribution.
"""
import asyncio
import httpx
import json
from datetime import date, timedelta
from collections import Counter
import statistics
from typing import Dict, List, Any


async def test_orders_endpoint():
    """Test the orders list endpoint with various date filters."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Testing /api/v1/orders/list endpoint...")
        print("=" * 60)
        
        # Test 1: Default parameters (last 30 days)
        print("\n1. Testing with default parameters (last 30 days):")
        response = await client.get(f"{base_url}/api/v1/orders/list")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total orders: {data['total']}")
            print(f"   Pages: {data['pages']}")
            print(f"   Orders on page: {len(data['orders'])}")
            
            # Analyze status distribution
            status_counts = Counter(order['status'] for order in data['orders'])
            print(f"   Status distribution: {dict(status_counts)}")
            
            # Analyze date distribution
            dates = [order['snapshot_date'] for order in data['orders']]
            date_counts = Counter(dates)
            print(f"   Unique snapshot dates: {len(date_counts)}")
            
            if date_counts:
                print(f"   Most common date: {max(date_counts.items(), key=lambda x: x[1])}")
                print(f"   Date distribution: {dict(date_counts)}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # Test 2: Specific date range
        print("\n2. Testing with specific date range (last 7 days):")
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        params = {
            "from": start_date.isoformat(),
            "to": end_date.isoformat()
        }
        
        response = await client.get(f"{base_url}/api/v1/orders/list", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"   Date range: {start_date} to {end_date}")
            print(f"   Total orders: {data['total']}")
            
            # Check if dates are within range
            dates_in_range = [order['snapshot_date'] for order in data['orders']]
            min_date = min(dates_in_range) if dates_in_range else None
            max_date = max(dates_in_range) if dates_in_range else None
            print(f"   Min date in results: {min_date}")
            print(f"   Max date in results: {max_date}")
            
            # Check if filtering works
            if dates_in_range:
                all_in_range = all(start_date <= date.fromisoformat(d) <= end_date for d in dates_in_range)
                print(f"   All dates in range: {all_in_range}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # Test 3: Filter by status
        print("\n3. Testing with status filter (completed):")
        params = {
            "status": "completed"
        }
        
        response = await client.get(f"{base_url}/api/v1/orders/list", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"   Total completed orders: {data['total']}")
            
            # Verify all orders have status "completed"
            all_completed = all(order['status'] == 'completed' for order in data['orders'])
            print(f"   All orders are completed: {all_completed}")
            
            if data['orders']:
                statuses = set(order['status'] for order in data['orders'])
                print(f"   Unique statuses in results: {statuses}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # Test 4: Empty date range (should return empty or default)
        print("\n4. Testing with very old date range (should return empty):")
        old_start = date(2020, 1, 1)
        old_end = date(2020, 1, 31)
        
        params = {
            "from": old_start.isoformat(),
            "to": old_end.isoformat()
        }
        
        response = await client.get(f"{base_url}/api/v1/orders/list", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"   Date range: {old_start} to {old_end}")
            print(f"   Total orders: {data['total']}")
            print(f"   Orders returned: {len(data['orders'])}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
        
        # Test 5: Analyze data distribution
        print("\n5. Analyzing data distribution:")
        response = await client.get(f"{base_url}/api/v1/orders/list", params={"limit": 500})
        if response.status_code == 200:
            data = response.json()
            
            if data['orders']:
                # Analyze by production line
                lines = [order['production_line'] for order in data['orders'] if order['production_line']]
                line_counts = Counter(lines)
                print(f"   Unique production lines: {len(line_counts)}")
                if line_counts:
                    print(f"   Top 5 production lines: {line_counts.most_common(5)}")
                
                # Analyze by product
                products = [order['product_id'] for order in data['orders'] if order['product_id']]
                product_counts = Counter(products)
                print(f"   Unique products: {len(product_counts)}")
                if product_counts:
                    print(f"   Top 5 products: {product_counts.most_common(5)}")
                
                # Analyze quantity distribution
                target_quantities = [float(order['target_quantity']) for order in data['orders'] 
                                   if order['target_quantity'] is not None]
                actual_quantities = [float(order['actual_quantity']) for order in data['orders'] 
                                    if order['actual_quantity'] is not None]
                
                if target_quantities:
                    print(f"   Target quantity stats: count={len(target_quantities)}, "
                          f"min={min(target_quantities):.2f}, max={max(target_quantities):.2f}, "
                          f"mean={statistics.mean(target_quantities):.2f}")
                
                if actual_quantities:
                    print(f"   Actual quantity stats: count={len(actual_quantities)}, "
                          f"min={min(actual_quantities):.2f}, max={max(actual_quantities):.2f}, "
                          f"mean={statistics.mean(actual_quantities):.2f}")
                
                # Check data completeness
                total_orders = len(data['orders'])
                has_target_qty = sum(1 for o in data['orders'] if o['target_quantity'] is not None)
                has_actual_qty = sum(1 for o in data['orders'] if o['actual_quantity'] is not None)
                has_product_name = sum(1 for o in data['orders'] if o['product_name'] is not None)
                
                print(f"   Data completeness:")
                print(f"     - Has target quantity: {has_target_qty}/{total_orders} ({has_target_qty/total_orders*100:.1f}%)")
                print(f"     - Has actual quantity: {has_actual_qty}/{total_orders} ({has_actual_qty/total_orders*100:.1f}%)")
                print(f"     - Has product name: {has_product_name}/{total_orders} ({has_product_name/total_orders*100:.1f}%)")
        
        print("\n" + "=" * 60)
        print("Testing complete.")


if __name__ == "__main__":
    asyncio.run(test_orders_endpoint())