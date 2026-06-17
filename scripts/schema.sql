BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 7e28e392b990

CREATE TABLE aggregated_kpi (
    period_from DATE NOT NULL, 
    period_to DATE NOT NULL, 
    production_line VARCHAR(50), 
    total_output DECIMAL(15, 3) NOT NULL, 
    defect_rate DECIMAL(5, 2) NOT NULL, 
    completed_orders INTEGER NOT NULL, 
    total_orders INTEGER NOT NULL, 
    oee_estimate DECIMAL(5, 2), 
    avg_order_completion_time VARCHAR(50), 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT uix_kpi_period_line UNIQUE (period_from, period_to, production_line)
);

CREATE INDEX ix_aggregated_kpi_period_from ON aggregated_kpi (period_from);

CREATE INDEX ix_aggregated_kpi_period_to ON aggregated_kpi (period_to);

CREATE INDEX ix_aggregated_kpi_production_line ON aggregated_kpi (production_line);

CREATE TABLE aggregated_sales (
    period_from DATE NOT NULL, 
    period_to DATE NOT NULL, 
    group_by_type VARCHAR(20) NOT NULL, 
    group_key VARCHAR(100) NOT NULL, 
    total_quantity DECIMAL(15, 3) NOT NULL, 
    total_amount DECIMAL(15, 2) NOT NULL, 
    sales_count INTEGER NOT NULL, 
    avg_order_value DECIMAL(15, 2), 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT uix_sales_period_group UNIQUE (period_from, period_to, group_by_type, group_key)
);

CREATE INDEX idx_sales_group_type ON aggregated_sales (group_by_type);

CREATE INDEX idx_sales_period ON aggregated_sales (period_from, period_to);

CREATE TABLE order_snapshots (
    order_id UUID NOT NULL, 
    external_order_id VARCHAR(100), 
    product_id UUID NOT NULL, 
    product_name VARCHAR(255), 
    target_quantity DECIMAL(15, 3), 
    actual_quantity DECIMAL(15, 3), 
    unit_of_measure VARCHAR(20), 
    status VARCHAR(20) NOT NULL, 
    production_line VARCHAR(50), 
    planned_start TIMESTAMP WITH TIME ZONE, 
    planned_end TIMESTAMP WITH TIME ZONE, 
    actual_start TIMESTAMP WITH TIME ZONE, 
    actual_end TIMESTAMP WITH TIME ZONE, 
    snapshot_date DATE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_order_snapshots_composite ON order_snapshots (snapshot_date, status, production_line);

CREATE INDEX ix_order_snapshots_order_id ON order_snapshots (order_id);

CREATE INDEX ix_order_snapshots_production_line ON order_snapshots (production_line);

CREATE INDEX ix_order_snapshots_snapshot_date ON order_snapshots (snapshot_date);

CREATE INDEX ix_order_snapshots_status ON order_snapshots (status);

CREATE TABLE quality_results (
    lot_number VARCHAR(100) NOT NULL, 
    product_id UUID NOT NULL, 
    product_name VARCHAR(255), 
    parameter_name VARCHAR(50) NOT NULL, 
    result_value DECIMAL(10, 4), 
    lower_limit DECIMAL(10, 4), 
    upper_limit DECIMAL(10, 4), 
    in_spec BOOLEAN NOT NULL, 
    decision VARCHAR(20) NOT NULL, 
    test_date DATE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_quality_date_decision ON quality_results (test_date, decision);

CREATE INDEX idx_quality_product_date ON quality_results (product_id, test_date);

CREATE INDEX ix_quality_results_decision ON quality_results (decision);

CREATE INDEX ix_quality_results_lot_number ON quality_results (lot_number);

CREATE INDEX ix_quality_results_product_id ON quality_results (product_id);

CREATE INDEX ix_quality_results_test_date ON quality_results (test_date);

CREATE TABLE sales_trends (
    trend_date DATE NOT NULL, 
    interval_type VARCHAR(10) NOT NULL, 
    region VARCHAR(100), 
    channel VARCHAR(50), 
    total_amount DECIMAL(15, 2) NOT NULL, 
    total_quantity DECIMAL(15, 3) NOT NULL, 
    order_count INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT uix_trends_date_interval UNIQUE (trend_date, interval_type, region, channel)
);

CREATE INDEX idx_trends_date ON sales_trends (trend_date);

CREATE INDEX idx_trends_interval ON sales_trends (interval_type);

CREATE TABLE sync_logs (
    task_name VARCHAR(100) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    records_processed INTEGER, 
    records_inserted INTEGER, 
    records_updated INTEGER, 
    error_message TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_sync_started ON sync_logs (started_at);

CREATE INDEX idx_sync_task_status ON sync_logs (task_name, status);

CREATE INDEX ix_sync_logs_status ON sync_logs (status);

CREATE INDEX ix_sync_logs_task_name ON sync_logs (task_name);

CREATE TABLE sync_errors (
    sync_log_id UUID NOT NULL, 
    error_type VARCHAR(50) NOT NULL, 
    error_code VARCHAR(100), 
    error_message TEXT NOT NULL, 
    entity_type VARCHAR(50), 
    entity_id VARCHAR(100), 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(sync_log_id) REFERENCES sync_logs (id) ON DELETE CASCADE
);

CREATE INDEX idx_error_sync_log ON sync_errors (sync_log_id);

CREATE INDEX idx_error_type ON sync_errors (error_type);

CREATE INDEX ix_sync_errors_error_type ON sync_errors (error_type);

INSERT INTO alembic_version (version_num) VALUES ('7e28e392b990') RETURNING alembic_version.version_num;

-- Running upgrade 7e28e392b990 -> 1084a7ccef58

CREATE TABLE inventory_snapshots (
    product_id UUID NOT NULL, 
    product_name VARCHAR(255), 
    warehouse_code VARCHAR(50) NOT NULL, 
    lot_number VARCHAR(100), 
    quantity DECIMAL(15, 3), 
    unit_of_measure VARCHAR(20), 
    last_updated TIMESTAMP WITH TIME ZONE, 
    snapshot_date DATE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_inventory_date_warehouse ON inventory_snapshots (snapshot_date, warehouse_code);

CREATE INDEX idx_inventory_product_warehouse ON inventory_snapshots (product_id, warehouse_code);

CREATE INDEX ix_inventory_snapshots_product_id ON inventory_snapshots (product_id);

CREATE INDEX ix_inventory_snapshots_snapshot_date ON inventory_snapshots (snapshot_date);

CREATE INDEX ix_inventory_snapshots_warehouse_code ON inventory_snapshots (warehouse_code);

CREATE TABLE production_output (
    order_id UUID, 
    product_id UUID NOT NULL, 
    product_name VARCHAR(255), 
    lot_number VARCHAR(100) NOT NULL, 
    quantity DECIMAL(15, 3), 
    quality_status VARCHAR(20), 
    production_date DATE NOT NULL, 
    shift VARCHAR(20), 
    snapshot_date DATE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_output_date_shift ON production_output (production_date, shift);

CREATE INDEX idx_output_product_date ON production_output (product_id, production_date);

CREATE INDEX ix_production_output_lot_number ON production_output (lot_number);

CREATE INDEX ix_production_output_order_id ON production_output (order_id);

CREATE INDEX ix_production_output_product_id ON production_output (product_id);

CREATE INDEX ix_production_output_production_date ON production_output (production_date);

CREATE INDEX ix_production_output_shift ON production_output (shift);

CREATE INDEX ix_production_output_snapshot_date ON production_output (snapshot_date);

CREATE TABLE products (
    code VARCHAR(100) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    category VARCHAR(50), 
    brand VARCHAR(255), 
    unit_of_measure VARCHAR(20), 
    shelf_life_days INTEGER, 
    requires_quality_check BOOLEAN, 
    source_system_id VARCHAR(100), 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_products_category_brand ON products (category, brand);

CREATE INDEX ix_products_brand ON products (brand);

CREATE INDEX ix_products_category ON products (category);

CREATE UNIQUE INDEX ix_products_code ON products (code);

CREATE TABLE sale_records (
    external_id VARCHAR(100), 
    product_id UUID NOT NULL, 
    product_name VARCHAR(255), 
    customer_name VARCHAR(255), 
    quantity DECIMAL(15, 3), 
    amount DECIMAL(15, 2), 
    sale_date DATE NOT NULL, 
    region VARCHAR(100), 
    channel VARCHAR(50), 
    snapshot_date DATE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_sale_records_channel_date ON sale_records (channel, sale_date);

CREATE INDEX idx_sale_records_product_date ON sale_records (product_id, sale_date);

CREATE INDEX ix_sale_records_channel ON sale_records (channel);

CREATE INDEX ix_sale_records_external_id ON sale_records (external_id);

CREATE INDEX ix_sale_records_product_id ON sale_records (product_id);

CREATE INDEX ix_sale_records_region ON sale_records (region);

CREATE INDEX ix_sale_records_sale_date ON sale_records (sale_date);

CREATE INDEX ix_sale_records_snapshot_date ON sale_records (snapshot_date);

CREATE TABLE sensor_readings (
    device_id VARCHAR(100) NOT NULL, 
    production_line VARCHAR(50) NOT NULL, 
    parameter_name VARCHAR(50) NOT NULL, 
    value DECIMAL(12, 4), 
    unit VARCHAR(20), 
    quality VARCHAR(20), 
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    snapshot_date TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_sensor_line_date ON sensor_readings (production_line, recorded_at);

CREATE INDEX idx_sensor_line_param ON sensor_readings (production_line, parameter_name);

CREATE INDEX ix_sensor_readings_device_id ON sensor_readings (device_id);

CREATE INDEX ix_sensor_readings_parameter_name ON sensor_readings (parameter_name);

CREATE INDEX ix_sensor_readings_production_line ON sensor_readings (production_line);

CREATE INDEX ix_sensor_readings_quality ON sensor_readings (quality);

CREATE INDEX ix_sensor_readings_recorded_at ON sensor_readings (recorded_at);

CREATE INDEX ix_sensor_readings_snapshot_date ON sensor_readings (snapshot_date);

UPDATE alembic_version SET version_num='1084a7ccef58' WHERE alembic_version.version_num = '7e28e392b990';

-- Running upgrade 1084a7ccef58 -> 1122e8e59f9b

CREATE TABLE departments (
    name VARCHAR(255) NOT NULL, 
    code VARCHAR(100), 
    location_id UUID, 
    parent_id UUID, 
    type VARCHAR(50), 
    is_active BOOLEAN, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_departments_location_type ON departments (location_id, type);

CREATE INDEX ix_departments_code ON departments (code);

CREATE INDEX ix_departments_location_id ON departments (location_id);

CREATE INDEX ix_departments_parent_id ON departments (parent_id);

CREATE INDEX ix_departments_type ON departments (type);

CREATE TABLE employees (
    first_name VARCHAR(100) NOT NULL, 
    last_name VARCHAR(100) NOT NULL, 
    middle_name VARCHAR(100), 
    employee_number VARCHAR(100), 
    position_id UUID, 
    workstation_id UUID, 
    status VARCHAR(50), 
    email VARCHAR(255), 
    phone VARCHAR(50), 
    hire_date DATE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_employees_position_status ON employees (position_id, status);

CREATE INDEX ix_employees_employee_number ON employees (employee_number);

CREATE INDEX ix_employees_position_id ON employees (position_id);

CREATE INDEX ix_employees_status ON employees (status);

CREATE INDEX ix_employees_workstation_id ON employees (workstation_id);

CREATE TABLE locations (
    name VARCHAR(255) NOT NULL, 
    code VARCHAR(100), 
    type VARCHAR(50), 
    address VARCHAR(500), 
    is_active BOOLEAN, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_locations_code ON locations (code);

CREATE INDEX ix_locations_type ON locations (type);

CREATE TABLE positions (
    name VARCHAR(255) NOT NULL, 
    code VARCHAR(100), 
    department_id UUID, 
    level VARCHAR(50), 
    is_active BOOLEAN, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_positions_code ON positions (code);

CREATE INDEX ix_positions_department_id ON positions (department_id);

CREATE TABLE production_lines (
    name VARCHAR(255) NOT NULL, 
    code VARCHAR(100), 
    location_id UUID, 
    description VARCHAR(500), 
    is_active BOOLEAN, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_production_lines_code ON production_lines (code);

CREATE INDEX ix_production_lines_location_id ON production_lines (location_id);

CREATE TABLE workstations (
    name VARCHAR(255) NOT NULL, 
    code VARCHAR(100), 
    location_id UUID, 
    production_line_id UUID, 
    type VARCHAR(50), 
    is_active BOOLEAN, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_workstations_location_line ON workstations (location_id, production_line_id);

CREATE INDEX ix_workstations_code ON workstations (code);

CREATE INDEX ix_workstations_location_id ON workstations (location_id);

CREATE INDEX ix_workstations_production_line_id ON workstations (production_line_id);

CREATE INDEX ix_workstations_type ON workstations (type);

UPDATE alembic_version SET version_num='1122e8e59f9b' WHERE alembic_version.version_num = '1084a7ccef58';

-- Running upgrade 1122e8e59f9b -> 4757d0526d42

ALTER TABLE products ADD COLUMN event_id UUID;

CREATE UNIQUE INDEX ix_products_event_id ON products (event_id) WHERE event_id IS NOT NULL;

ALTER TABLE order_snapshots ADD COLUMN event_id UUID;

CREATE UNIQUE INDEX ix_order_snapshots_event_id ON order_snapshots (event_id) WHERE event_id IS NOT NULL;

ALTER TABLE production_output ADD COLUMN event_id UUID;

CREATE UNIQUE INDEX ix_production_output_event_id ON production_output (event_id) WHERE event_id IS NOT NULL;

ALTER TABLE sale_records ADD COLUMN event_id UUID;

CREATE UNIQUE INDEX ix_sale_records_event_id ON sale_records (event_id) WHERE event_id IS NOT NULL;

ALTER TABLE inventory_snapshots ADD COLUMN event_id UUID;

CREATE UNIQUE INDEX ix_inventory_snapshots_event_id ON inventory_snapshots (event_id) WHERE event_id IS NOT NULL;

ALTER TABLE quality_results ADD COLUMN event_id UUID;

CREATE UNIQUE INDEX ix_quality_results_event_id ON quality_results (event_id) WHERE event_id IS NOT NULL;

UPDATE alembic_version SET version_num='4757d0526d42' WHERE alembic_version.version_num = '1122e8e59f9b';

-- Running upgrade 4757d0526d42 -> 001_ref_tables_3nf

CREATE TABLE units_of_measure (
    id UUID NOT NULL, 
    code VARCHAR(20) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    source_system_id VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_units_of_measure_code UNIQUE (code), 
    CONSTRAINT uq_units_of_measure_source_system_id UNIQUE (source_system_id)
);

CREATE UNIQUE INDEX ix_units_of_measure_code ON units_of_measure (code);

CREATE UNIQUE INDEX ix_units_of_measure_source_system_id ON units_of_measure (source_system_id);

CREATE TABLE warehouses (
    id UUID NOT NULL, 
    name VARCHAR(150) NOT NULL, 
    code VARCHAR(20) NOT NULL, 
    location VARCHAR(200) NOT NULL, 
    capacity DECIMAL(15, 2), 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    source_system_id VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_warehouses_code UNIQUE (code), 
    CONSTRAINT uq_warehouses_source_system_id UNIQUE (source_system_id)
);

CREATE UNIQUE INDEX ix_warehouses_code ON warehouses (code);

CREATE INDEX ix_warehouses_is_active ON warehouses (is_active);

CREATE UNIQUE INDEX ix_warehouses_source_system_id ON warehouses (source_system_id);

CREATE TABLE sensor_parameters (
    id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    code VARCHAR(20) NOT NULL, 
    unit VARCHAR(20) NOT NULL, 
    description VARCHAR(255), 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_sensor_parameters_code UNIQUE (code)
);

CREATE UNIQUE INDEX ix_sensor_parameters_code ON sensor_parameters (code);

CREATE INDEX ix_sensor_parameters_is_active ON sensor_parameters (is_active);

CREATE TABLE sensors (
    id UUID NOT NULL, 
    device_id VARCHAR(50) NOT NULL, 
    production_line_id UUID NOT NULL, 
    sensor_parameter_id UUID NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(sensor_parameter_id) REFERENCES sensor_parameters (id) ON DELETE CASCADE, 
    CONSTRAINT uq_sensors_device_id UNIQUE (device_id)
);

CREATE UNIQUE INDEX ix_sensors_device_id ON sensors (device_id);

CREATE INDEX ix_sensors_production_line_id ON sensors (production_line_id);

CREATE INDEX ix_sensors_sensor_parameter_id ON sensors (sensor_parameter_id);

CREATE INDEX ix_sensors_is_active ON sensors (is_active);

CREATE TABLE customers (
    id UUID NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    code VARCHAR(20) NOT NULL, 
    region VARCHAR(100) NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    source_system_id VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_customers_code UNIQUE (code), 
    CONSTRAINT uq_customers_source_system_id UNIQUE (source_system_id)
);

CREATE UNIQUE INDEX ix_customers_code ON customers (code);

CREATE INDEX ix_customers_region ON customers (region);

CREATE INDEX ix_customers_is_active ON customers (is_active);

CREATE UNIQUE INDEX ix_customers_source_system_id ON customers (source_system_id);

CREATE TABLE quality_specs (
    id UUID NOT NULL, 
    product_id UUID NOT NULL, 
    parameter_name VARCHAR(100) NOT NULL, 
    lower_limit DECIMAL(15, 6) NOT NULL, 
    upper_limit DECIMAL(15, 6) NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_quality_specs_product_param UNIQUE (product_id, parameter_name)
);

CREATE INDEX ix_quality_specs_product_id ON quality_specs (product_id);

CREATE UNIQUE INDEX ix_quality_specs_product_param ON quality_specs (product_id, parameter_name);

CREATE INDEX ix_quality_specs_is_active ON quality_specs (is_active);

UPDATE alembic_version SET version_num='001_ref_tables_3nf' WHERE alembic_version.version_num = '4757d0526d42';

-- Running upgrade 001_ref_tables_3nf -> 002_add_fk_existing

ALTER TABLE products ADD COLUMN unit_of_measure_id UUID;

ALTER TABLE products ADD CONSTRAINT fk_products_unit_of_measure_id FOREIGN KEY(unit_of_measure_id) REFERENCES units_of_measure (id) ON DELETE SET NULL;

CREATE INDEX ix_products_unit_of_measure_id ON products (unit_of_measure_id);

ALTER TABLE inventory_snapshots ADD COLUMN warehouse_id UUID;

ALTER TABLE inventory_snapshots ADD CONSTRAINT fk_inventory_snapshots_warehouse_id FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL;

CREATE INDEX ix_inventory_snapshots_warehouse_id ON inventory_snapshots (warehouse_id);

ALTER TABLE sale_records ADD COLUMN customer_id UUID;

ALTER TABLE sale_records ADD CONSTRAINT fk_sale_records_customer_id FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE SET NULL;

CREATE INDEX ix_sale_records_customer_id ON sale_records (customer_id);

ALTER TABLE quality_results ADD COLUMN quality_spec_id UUID;

ALTER TABLE quality_results ADD CONSTRAINT fk_quality_results_quality_spec_id FOREIGN KEY(quality_spec_id) REFERENCES quality_specs (id) ON DELETE SET NULL;

CREATE INDEX ix_quality_results_quality_spec_id ON quality_results (quality_spec_id);

ALTER TABLE sensor_readings ADD COLUMN sensor_id UUID;

ALTER TABLE sensor_readings ADD CONSTRAINT fk_sensor_readings_sensor_id FOREIGN KEY(sensor_id) REFERENCES sensors (id) ON DELETE CASCADE;

CREATE INDEX ix_sensor_readings_sensor_id ON sensor_readings (sensor_id);

UPDATE alembic_version SET version_num='002_add_fk_existing' WHERE alembic_version.version_num = '001_ref_tables_3nf';

-- Running upgrade 002_add_fk_existing -> 003_remove_denorm_sensors

DROP INDEX IF EXISTS ix_sensor_readings_device_id;

DROP INDEX IF EXISTS ix_sensor_readings_production_line;

DROP INDEX IF EXISTS ix_sensor_readings_parameter_name;

CREATE INDEX ix_sensor_readings_sensor_recorded ON sensor_readings (sensor_id, recorded_at);

CREATE INDEX ix_sensor_readings_recorded_quality ON sensor_readings (recorded_at, quality);

ALTER TABLE sensor_readings DROP COLUMN device_id;

ALTER TABLE sensor_readings DROP COLUMN production_line;

ALTER TABLE sensor_readings DROP COLUMN parameter_name;

ALTER TABLE sensor_readings DROP COLUMN unit;

UPDATE alembic_version SET version_num='003_remove_denorm_sensors' WHERE alembic_version.version_num = '002_add_fk_existing';

-- Running upgrade 003_remove_denorm_sensors -> 004_remove_denorm_warehouse

DROP INDEX IF EXISTS idx_inventory_product_warehouse;

DROP INDEX IF EXISTS idx_inventory_date_warehouse;

CREATE INDEX idx_inventory_product_warehouse ON inventory_snapshots (product_id, warehouse_id);

CREATE INDEX idx_inventory_date_warehouse ON inventory_snapshots (snapshot_date, warehouse_id);

ALTER TABLE inventory_snapshots DROP COLUMN warehouse_code;

UPDATE alembic_version SET version_num='004_remove_denorm_warehouse' WHERE alembic_version.version_num = '003_remove_denorm_sensors';

-- Running upgrade 004_remove_denorm_warehouse -> 005_remove_denorm_quality

ALTER TABLE quality_results DROP COLUMN upper_limit;

ALTER TABLE quality_results DROP COLUMN lower_limit;

UPDATE alembic_version SET version_num='005_remove_denorm_quality' WHERE alembic_version.version_num = '004_remove_denorm_warehouse';

-- Running upgrade 005_remove_denorm_quality -> b23f4a1858c8

ALTER TABLE production_lines ADD COLUMN division VARCHAR(255);

CREATE TABLE batch_inputs (
    id UUID NOT NULL, 
    order_id UUID, 
    product_id UUID, 
    quantity DECIMAL(15, 3) NOT NULL, 
    input_date TIMESTAMP WITH TIME ZONE NOT NULL, 
    event_id VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (event_id)
);

CREATE INDEX ix_batch_inputs_order_id ON batch_inputs (order_id);

CREATE INDEX ix_batch_inputs_product_id ON batch_inputs (product_id);

CREATE INDEX ix_batch_inputs_input_date ON batch_inputs (input_date);

CREATE TABLE downtime_events (
    id UUID NOT NULL, 
    production_line_id UUID, 
    reason VARCHAR(500) NOT NULL, 
    category VARCHAR(50) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ended_at TIMESTAMP WITH TIME ZONE, 
    duration_minutes INTEGER, 
    event_id VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (event_id)
);

CREATE INDEX ix_downtime_events_production_line_id ON downtime_events (production_line_id);

CREATE INDEX ix_downtime_events_category ON downtime_events (category);

CREATE INDEX ix_downtime_events_started_at ON downtime_events (started_at);

CREATE TABLE promo_campaigns (
    id UUID NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    description VARCHAR(1000), 
    channel VARCHAR(50) NOT NULL, 
    product_id UUID, 
    discount_percent DECIMAL(5, 2), 
    start_date DATE NOT NULL, 
    end_date DATE, 
    budget DECIMAL(15, 2), 
    event_id VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (event_id)
);

CREATE INDEX ix_promo_campaigns_channel ON promo_campaigns (channel);

CREATE INDEX ix_promo_campaigns_product_id ON promo_campaigns (product_id);

CREATE INDEX ix_promo_campaigns_start_date ON promo_campaigns (start_date);

UPDATE alembic_version SET version_num='b23f4a1858c8' WHERE alembic_version.version_num = '005_remove_denorm_quality';

-- Running upgrade b23f4a1858c8 -> e42439396426

CREATE TABLE line_capacity_plans (
    id UUID NOT NULL, 
    production_line_id UUID NOT NULL, 
    planned_hours_per_day INTEGER NOT NULL, 
    target_oee_percent DECIMAL(5, 2) DEFAULT '85.00' NOT NULL, 
    period_from DATE NOT NULL, 
    period_to DATE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(production_line_id) REFERENCES production_lines (id) ON DELETE CASCADE
);

CREATE INDEX ix_line_capacity_plans_period_from ON line_capacity_plans (period_from);

CREATE INDEX ix_line_capacity_plans_production_line_id ON line_capacity_plans (production_line_id);

COMMENT ON COLUMN line_capacity_plans.planned_hours_per_day IS 'Плановое рабочее время в часах';

COMMENT ON COLUMN line_capacity_plans.target_oee_percent IS 'Целевое значение OEE в процентах';

UPDATE alembic_version SET version_num='e42439396426' WHERE alembic_version.version_num = 'b23f4a1858c8';

-- Running upgrade e42439396426 -> 373272411dbe

CREATE TABLE cost_bases (
    id UUID NOT NULL, 
    product_id UUID, 
    raw_material_cost DECIMAL(15, 4) NOT NULL, 
    labor_cost_per_hour DECIMAL(10, 2), 
    depreciation_monthly DECIMAL(15, 2), 
    period_from DATE NOT NULL, 
    period_to DATE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_cost_bases_product_id ON cost_bases (product_id);

CREATE INDEX ix_cost_bases_period_from ON cost_bases (period_from);

CREATE INDEX idx_cost_base_product_period ON cost_bases (product_id, period_from);

CREATE INDEX idx_cost_base_period ON cost_bases (period_from, period_to);

CREATE TABLE kpi_configs (
    id UUID NOT NULL, 
    key VARCHAR(100) NOT NULL, 
    value DECIMAL(20, 4) NOT NULL, 
    description VARCHAR(500), 
    updated_by VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (key)
);

CREATE INDEX idx_kpi_config_key ON kpi_configs (key);

UPDATE alembic_version SET version_num='373272411dbe' WHERE alembic_version.version_num = 'e42439396426';

-- Running upgrade 373272411dbe -> 2e566eb26ef2

ALTER TABLE sale_records ADD COLUMN cost DECIMAL(15, 2);

UPDATE alembic_version SET version_num='2e566eb26ef2' WHERE alembic_version.version_num = '373272411dbe';

-- Running upgrade 2e566eb26ef2 -> c993b27cc996

DROP TABLE employees;

DROP TABLE workstations;

DROP TABLE positions;

DROP TABLE departments;

UPDATE alembic_version SET version_num='c993b27cc996' WHERE alembic_version.version_num = '2e566eb26ef2';

-- Running upgrade c993b27cc996 -> f001

ALTER TABLE inventory_snapshots ADD COLUMN warehouse_name VARCHAR(150);

ALTER TABLE inventory_snapshots ADD COLUMN warehouse_code VARCHAR(20);

CREATE INDEX ix_inventory_snapshots_warehouse_code ON inventory_snapshots (warehouse_code);

ALTER TABLE sensors ADD COLUMN line_name VARCHAR(255);

ALTER TABLE sensors ADD COLUMN parameter_name VARCHAR(100);

ALTER TABLE sensors ADD COLUMN parameter_unit VARCHAR(20);

ALTER TABLE aggregated_kpi ADD COLUMN production_line_name VARCHAR(255);

ALTER TABLE production_output ADD COLUMN production_line_id UUID;

CREATE INDEX ix_production_output_production_line_id ON production_output (production_line_id);

ALTER TABLE production_output ADD COLUMN production_line_name VARCHAR(255);

UPDATE alembic_version SET version_num='f001' WHERE alembic_version.version_num = 'c993b27cc996';

-- Running upgrade f001 -> 88817dbdd9e5

ALTER TABLE warehouses DROP COLUMN location;

UPDATE alembic_version SET version_num='88817dbdd9e5' WHERE alembic_version.version_num = 'f001';

-- Running upgrade 88817dbdd9e5 -> 0fae0657ab4f

DROP INDEX idx_cost_base_period;

DROP INDEX idx_cost_base_product_period;

DROP INDEX ix_cost_bases_period_from;

DROP INDEX ix_cost_bases_product_id;

DROP TABLE cost_bases;

UPDATE alembic_version SET version_num='0fae0657ab4f' WHERE alembic_version.version_num = '88817dbdd9e5';

-- Running upgrade 0fae0657ab4f -> d5cefd594a89

DROP INDEX IF EXISTS ix_units_of_measure_source_system_id;

ALTER TABLE units_of_measure DROP COLUMN source_system_id;

DROP INDEX IF EXISTS ix_warehouses_source_system_id;

ALTER TABLE warehouses DROP COLUMN source_system_id;

DROP INDEX IF EXISTS ix_customers_source_system_id;

ALTER TABLE customers DROP COLUMN source_system_id;

UPDATE alembic_version SET version_num='d5cefd594a89' WHERE alembic_version.version_num = '0fae0657ab4f';

-- Running upgrade d5cefd594a89 -> 4a3168777436

ALTER TABLE aggregated_kpi DROP CONSTRAINT uix_kpi_period_line;

DROP INDEX ix_aggregated_kpi_production_line;

ALTER TABLE aggregated_kpi RENAME production_line TO product_line_id;

CREATE INDEX ix_aggregated_kpi_product_line_id ON aggregated_kpi (product_line_id);

ALTER TABLE aggregated_kpi ADD CONSTRAINT uix_kpi_period_line UNIQUE (period_from, period_to, product_line_id);

UPDATE alembic_version SET version_num='4a3168777436' WHERE alembic_version.version_num = 'd5cefd594a89';

-- Running upgrade 4a3168777436 -> 0b0ae77c0985

ALTER TABLE sensor_parameters ALTER COLUMN code TYPE VARCHAR(50);

UPDATE alembic_version SET version_num='0b0ae77c0985' WHERE alembic_version.version_num = '4a3168777436';

-- Running upgrade 0b0ae77c0985 -> d71274f19362

ALTER TABLE sensor_parameters ALTER COLUMN code TYPE VARCHAR(50);

UPDATE alembic_version SET version_num='d71274f19362' WHERE alembic_version.version_num = '0b0ae77c0985';

-- Running upgrade d71274f19362 -> f002

ALTER TABLE aggregated_sales ADD COLUMN group_id VARCHAR(100);

UPDATE alembic_version SET version_num='f002' WHERE alembic_version.version_num = 'd71274f19362';

-- Running upgrade f002 -> f003

CREATE TABLE sensor_anomalies (
    id UUID NOT NULL, 
    reading_id UUID, 
    device_id VARCHAR(50) NOT NULL, 
    production_line_id UUID, 
    parameter_name VARCHAR(100) NOT NULL, 
    value DECIMAL(12, 4), 
    unit VARCHAR(20), 
    quality VARCHAR(20), 
    anomaly_type VARCHAR(50) NOT NULL, 
    severity VARCHAR(20) NOT NULL, 
    reason VARCHAR(500), 
    lower_limit DECIMAL(12, 4), 
    upper_limit DECIMAL(12, 4), 
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    event_id VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    UNIQUE (event_id)
);

CREATE INDEX ix_sensor_anomalies_production_line_id ON sensor_anomalies (production_line_id);

CREATE INDEX ix_sensor_anomalies_severity ON sensor_anomalies (severity);

CREATE INDEX ix_sensor_anomalies_anomaly_type ON sensor_anomalies (anomaly_type);

CREATE INDEX ix_sensor_anomalies_detected_at ON sensor_anomalies (detected_at);

CREATE INDEX ix_sensor_anomalies_reading_id ON sensor_anomalies (reading_id);

CREATE INDEX ix_sensor_anomalies_device_id ON sensor_anomalies (device_id);

CREATE INDEX ix_sensor_anomalies_detected_at_severity ON sensor_anomalies (detected_at, severity);

UPDATE alembic_version SET version_num='f003' WHERE alembic_version.version_num = 'f002';

COMMIT;

