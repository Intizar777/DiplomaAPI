-- SQL script to merge data from 'stage' schema to 'public' schema for DiplomaAPI
-- Handles denormalization on the fly.
-- This script is optimized to run as individual commands to avoid server crashes.

-- 1. Units of Measure
INSERT INTO public.units_of_measure (id, code, name, created_at, updated_at)
SELECT id, code, name, created_at, created_at
FROM stage.units_of_measure
ON CONFLICT (id) DO NOTHING;

-- 2. Warehouses
INSERT INTO public.warehouses (id, code, name, is_active, created_at, updated_at)
SELECT id, code, name, true, created_at, created_at
FROM stage.warehouses
ON CONFLICT (id) DO NOTHING;

-- 3. Products
INSERT INTO public.products (id, code, name, category, brand, unit_of_measure_id, shelf_life_days, requires_quality_check, source_system_id, created_at, updated_at)
SELECT id, code, name, category, brand, unit_of_measure_id, shelf_life_days, requires_quality_check, source_system_id, created_at, updated_at
FROM stage.products
ON CONFLICT (id) DO NOTHING;

-- 4. Customers
INSERT INTO public.customers (id, code, name, region, is_active, created_at, updated_at)
SELECT id, 'CUST-' || substr(id::text, 1, 8), name, 'Unknown', true, created_at, created_at
FROM stage.customers
ON CONFLICT (id) DO NOTHING;

-- 5. Production Lines
INSERT INTO public.production_lines (id, name, code, description, division, is_active, created_at, updated_at)
SELECT id, name, code, description, division, is_active, created_at, updated_at
FROM stage.production_lines
ON CONFLICT (id) DO NOTHING;

-- 6. Order Snapshots (Denormalized)
INSERT INTO public.order_snapshots (
    id, order_id, external_order_id, product_id, product_name, 
    target_quantity, actual_quantity, unit_of_measure, 
    status, production_line, 
    planned_start, planned_end, actual_start, actual_end, 
    snapshot_date, created_at, updated_at
)
SELECT 
    o.id, o.id, o.external_order_id, o.product_id, p.name,
    o.target_quantity, o.actual_quantity, u.code,
    o.status, l.code,
    o.planned_start, o.planned_end, o.actual_start, o.actual_end,
    COALESCE(o.created_at::date, CURRENT_DATE), o.created_at, o.updated_at
FROM stage.production_orders o
LEFT JOIN stage.products p ON o.product_id = p.id
LEFT JOIN stage.units_of_measure u ON p.unit_of_measure_id = u.id
LEFT JOIN stage.production_lines l ON o.production_line_id = l.id
ON CONFLICT (id) DO NOTHING;

-- 7. Production Output (Denormalized)
INSERT INTO public.production_output (
    id, order_id, product_id, product_name, 
    production_line_id, production_line_name,
    lot_number, quantity, quality_status, 
    production_date, shift, snapshot_date, created_at, updated_at
)
SELECT 
    out.id, out.order_id, o.product_id, p.name,
    o.production_line_id, l.name,
    out.lot_number, out.quantity, out.quality_status,
    out.production_date, 
    CASE 
        WHEN out.shift IN ('Morning', 'morning', 'Day', 'day') THEN 'Утренняя'
        WHEN out.shift IN ('Evening', 'evening', 'Afternoon', 'afternoon') THEN 'Вечерняя'
        WHEN out.shift IN ('Night', 'night') THEN 'Ночная'
        ELSE out.shift
    END,
    COALESCE(out.created_at::date, CURRENT_DATE), out.created_at, out.created_at
FROM stage.production_output out
LEFT JOIN stage.production_orders o ON out.order_id = o.id
LEFT JOIN stage.products p ON o.product_id = p.id
LEFT JOIN stage.production_lines l ON o.production_line_id = l.id
ON CONFLICT (id) DO NOTHING;

-- 8. Inventory Snapshots (Denormalized)
INSERT INTO public.inventory_snapshots (
    id, product_id, product_name, 
    warehouse_id, warehouse_code, warehouse_name,
    lot_number, quantity, unit_of_measure, 
    last_updated, snapshot_date, created_at, updated_at
)
SELECT 
    i.id, i.product_id, p.name,
    i.warehouse_id, w.code, w.name,
    i.lot_number, i.quantity, u.code,
    i.last_updated, CURRENT_DATE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM stage.inventory i
LEFT JOIN stage.products p ON i.product_id = p.id
LEFT JOIN stage.units_of_measure u ON p.unit_of_measure_id = u.id
LEFT JOIN stage.warehouses w ON i.warehouse_id = w.id
ON CONFLICT (id) DO NOTHING;

-- 9. Sensor Parameters
INSERT INTO public.sensor_parameters (id, name, code, unit, is_active, created_at, updated_at)
SELECT id, name, lower(regexp_replace(name, '[^a-zA-Z0-9]', '_', 'g')), unit, true, created_at, created_at
FROM stage.sensor_parameters
ON CONFLICT (id) DO NOTHING;

-- 10. Sensors (Denormalized)
INSERT INTO public.sensors (
    id, device_id, production_line_id, line_name,
    sensor_parameter_id, parameter_name, parameter_unit,
    is_active, created_at, updated_at
)
SELECT 
    s.id, s.device_id, s.production_line_id, l.name,
    s.sensor_parameter_id, sp.name, sp.unit,
    s.is_active, s.created_at, s.updated_at
FROM stage.sensors s
LEFT JOIN stage.production_lines l ON s.production_line_id = l.id
LEFT JOIN stage.sensor_parameters sp ON s.sensor_parameter_id = sp.id
ON CONFLICT (id) DO NOTHING;

-- 11. Sensor Readings
INSERT INTO public.sensor_readings (id, sensor_id, value, quality, recorded_at, snapshot_date, created_at, updated_at)
SELECT id, sensor_id, value, quality, recorded_at, created_at, created_at, created_at
FROM stage.sensor_readings
ON CONFLICT (id) DO NOTHING;

-- 12. Sale Records (Denormalized)
INSERT INTO public.sale_records (
    id, external_id, product_id, product_name,
    customer_id, customer_name,
    quantity, amount, cost, sale_date,
    region, channel, snapshot_date, created_at, updated_at
)
SELECT 
    s.id, s.external_id, s.product_id, p.name,
    s.customer_id, c.name,
    s.quantity, s.amount, s.cost, s.sale_date,
    s.region, s.channel, COALESCE(s.created_at::date, CURRENT_DATE), s.created_at, s.created_at
FROM stage.sales s
LEFT JOIN stage.products p ON s.product_id = p.id
LEFT JOIN stage.customers c ON s.customer_id = c.id
ON CONFLICT (id) DO NOTHING;

-- 13. Quality Specs
INSERT INTO public.quality_specs (id, product_id, parameter_name, lower_limit, upper_limit, is_active, created_at, updated_at)
SELECT id, product_id, parameter_name, lower_limit, upper_limit, is_active, created_at, updated_at
FROM stage.quality_specs
ON CONFLICT (id) DO NOTHING;

-- 14. Quality Results (Denormalized)
INSERT INTO public.quality_results (
    id, lot_number, product_id, product_name,
    parameter_name, result_value, quality_spec_id,
    in_spec, decision, test_date, created_at, updated_at
)
SELECT 
    qr.id, qr.lot_number, qs.product_id, p.name,
    qs.parameter_name, qr.result_value, qr.quality_spec_id,
    (qr.result_value >= qs.lower_limit AND qr.result_value <= qs.upper_limit),
    qr.quality_status, qr.test_date, qr.created_at, qr.created_at
FROM stage.quality_results qr
LEFT JOIN stage.quality_specs qs ON qr.quality_spec_id = qs.id
LEFT JOIN stage.products p ON qs.product_id = p.id
ON CONFLICT (id) DO NOTHING;
