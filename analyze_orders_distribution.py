#!/usr/bin/env python3
"""
Deep analysis of orders data distribution.
"""
import asyncio
import httpx
from collections import Counter
from datetime import date, timedelta
import statistics


async def analyze_distribution():
    """Analyze orders data distribution in detail."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Deep analysis of orders data distribution")
        print("=" * 60)
        
        # Get all orders (multiple pages)
        all_orders = []
        page = 1
        total_pages = 1
        
        while page <= total_pages:
            params = {"page": page, "limit": 500}
            response = await client.get(f"{base_url}/api/v1/orders/list", params=params)
            
            if response.status_code != 200:
                print(f"Error fetching page {page}: {response.status_code}")
                break
                
            data = response.json()
            all_orders.extend(data['orders'])
            
            if page == 1:
                total_pages = data['pages']
                print(f"Total orders in database: {data['total']}")
                print(f"Total pages to fetch: {total_pages}")
            
            page += 1
            if page > 10:  # Limit to first 10 pages for speed
                print(f"Limited analysis to first {len(all_orders)} orders")
                break
        
        if not all_orders:
            print("No orders found")
            return
        
        print(f"\nAnalyzing {len(all_orders)} orders...")
        
        # 1. Date distribution
        print("\n1. DATE DISTRIBUTION:")
        dates = [order['snapshot_date'] for order in all_orders]
        date_counts = Counter(dates)
        
        print(f"   Unique dates: {len(date_counts)}")
        print(f"   Date range: {min(dates)} to {max(dates)}")
        
        # Convert to date objects for analysis
        date_objs = [date.fromisoformat(d) for d in dates]
        if len(date_objs) > 1:
            date_diffs = [(date_objs[i+1] - date_objs[i]).days for i in range(len(date_objs)-1)]
            print(f"   Average days between orders: {statistics.mean(date_diffs):.2f}")
        
        # Show top dates
        print(f"   Top 5 dates by order count:")
        for d, count in date_counts.most_common(5):
            print(f"     {d}: {count} orders ({count/len(all_orders)*100:.1f}%)")
        
        # 2. Status distribution
        print("\n2. STATUS DISTRIBUTION:")
        statuses = [order['status'] for order in all_orders]
        status_counts = Counter(statuses)
        
        print(f"   Unique statuses: {len(status_counts)}")
        for status, count in status_counts.most_common():
            percentage = count/len(all_orders)*100
            print(f"     {status}: {count} orders ({percentage:.1f}%)")
        
        # 3. Production line distribution
        print("\n3. PRODUCTION LINE DISTRIBUTION:")
        lines = [order['production_line'] for order in all_orders if order['production_line']]
        line_counts = Counter(lines)
        
        print(f"   Orders with line specified: {len(lines)}/{len(all_orders)} ({len(lines)/len(all_orders)*100:.1f}%)")
        print(f"   Unique production lines: {len(line_counts)}")
        
        if line_counts:
            # Calculate Gini coefficient for inequality
            line_values = list(line_counts.values())
            line_values.sort()
            n = len(line_values)
            cumulative = sum(line_values)
            
            if n > 1 and cumulative > 0:
                gini_sum = sum((2*i - n - 1) * line_values[i] for i in range(n))
                gini = gini_sum / (n * cumulative)
                print(f"   Gini coefficient (inequality): {gini:.3f} (0=perfect equality, 1=perfect inequality)")
            
            print(f"   Top 10 production lines:")
            for line, count in line_counts.most_common(10):
                percentage = count/len(lines)*100
                print(f"     {line[:8]}...: {count} orders ({percentage:.1f}%)")
        
        # 4. Product distribution
        print("\n4. PRODUCT DISTRIBUTION:")
        products = [order['product_id'] for order in all_orders if order['product_id']]
        product_counts = Counter(products)
        
        print(f"   Unique products: {len(product_counts)}")
        
        if product_counts:
            product_values = list(product_counts.values())
            print(f"   Min orders per product: {min(product_values)}")
            print(f"   Max orders per product: {max(product_values)}")
            print(f"   Mean orders per product: {statistics.mean(product_values):.1f}")
            print(f"   Std dev: {statistics.stdev(product_values) if len(product_values) > 1 else 0:.1f}")
            
            print(f"   Top 10 products:")
            for product, count in product_counts.most_common(10):
                percentage = count/len(products)*100
                print(f"     {product[:8]}...: {count} orders ({percentage:.1f}%)")
        
        # 5. Quantity analysis
        print("\n5. QUANTITY ANALYSIS:")
        target_qty = [float(order['target_quantity']) for order in all_orders 
                     if order['target_quantity'] is not None]
        actual_qty = [float(order['actual_quantity']) for order in all_orders 
                     if order['actual_quantity'] is not None]
        
        print(f"   Target quantity:")
        if target_qty:
            print(f"     Count: {len(target_qty)}")
            print(f"     Min: {min(target_qty):.2f}")
            print(f"     Max: {max(target_qty):.2f}")
            print(f"     Mean: {statistics.mean(target_qty):.2f}")
            print(f"     Median: {statistics.median(target_qty):.2f}")
            if len(target_qty) > 1:
                print(f"     Std dev: {statistics.stdev(target_qty):.2f}")
        
        print(f"   Actual quantity:")
        if actual_qty:
            print(f"     Count: {len(actual_qty)}")
            print(f"     Min: {min(actual_qty):.2f}")
            print(f"     Max: {max(actual_qty):.2f}")
            print(f"     Mean: {statistics.mean(actual_qty):.2f}")
            print(f"     Median: {statistics.median(actual_qty):.2f}")
            if len(actual_qty) > 1:
                print(f"     Std dev: {statistics.stdev(actual_qty):.2f}")
        
        # 6. Time-based analysis
        print("\n6. TIME-BASED ANALYSIS:")
        planned_starts = [order['planned_start'] for order in all_orders if order['planned_start']]
        planned_ends = [order['planned_end'] for order in all_orders if order['planned_end']]
        actual_starts = [order['actual_start'] for order in all_orders if order['actual_start']]
        actual_ends = [order['actual_end'] for order in all_orders if order['actual_end']]
        
        print(f"   Planned start dates: {len(planned_starts)}/{len(all_orders)} ({len(planned_starts)/len(all_orders)*100:.1f}%)")
        print(f"   Planned end dates: {len(planned_ends)}/{len(all_orders)} ({len(planned_ends)/len(all_orders)*100:.1f}%)")
        print(f"   Actual start dates: {len(actual_starts)}/{len(all_orders)} ({len(actual_starts)/len(all_orders)*100:.1f}%)")
        print(f"   Actual end dates: {len(actual_ends)}/{len(all_orders)} ({len(actual_ends)/len(all_orders)*100:.1f}%)")
        
        print("\n" + "=" * 60)
        print("Analysis complete.")


if __name__ == "__main__":
    asyncio.run(analyze_distribution())