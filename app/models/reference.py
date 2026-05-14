"""
Reference data models (normalized dictionaries from Gateway).
"""
from sqlalchemy import Column, String, Integer, DECIMAL, Boolean, Index, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProductionLine(Base, UUIDMixin, TimestampMixin):
    """
    Production line reference data.
    Synced from Gateway personnel service.
    """
    __tablename__ = "production_lines"

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)
    location_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    description = Column(String(500), nullable=True)
    division = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)

    def __repr__(self):
        return f"<ProductionLine(code={self.code}, name={self.name})>"


class UnitOfMeasure(Base, UUIDMixin, TimestampMixin):
    """
    Unit of measure reference (kg, liters, pieces, etc).
    Synced from Gateway Production Service. ID must be provided from Gateway.
    """
    __tablename__ = "units_of_measure"

    code = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)

    __table_args__ = (
        Index('idx_unit_of_measure_code', 'code'),
    )

    def __repr__(self):
        return f"<UnitOfMeasure(code={self.code}, name={self.name})>"


class Warehouse(Base, UUIDMixin, TimestampMixin):
    """
    Warehouse reference data.
    Synced from Gateway Production Service. ID must be provided from Gateway.
    """
    __tablename__ = "warehouses"

    name = Column(String(150), nullable=False)
    code = Column(String(20), nullable=False, unique=True, index=True)
    capacity = Column(DECIMAL(15, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        Index('idx_warehouse_code', 'code'),
        Index('idx_warehouse_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Warehouse(code={self.code}, name={self.name})>"


class SensorParameter(Base, UUIDMixin, TimestampMixin):
    """
    Sensor parameter reference (Temperature, Pressure, Flow Rate, Humidity, etc).
    Synced from Gateway Production Service.
    """
    __tablename__ = "sensor_parameters"

    name = Column(String(100), nullable=False)  # на русском: Температура, Давление и т.д.
    code = Column(String(50), nullable=False, unique=True, index=True)
    unit = Column(String(20), nullable=False)  # °C, кПа, л/ч, %
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        Index('idx_sensor_parameter_code', 'code'),
        Index('idx_sensor_parameter_active', 'is_active'),
    )

    def __repr__(self):
        return f"<SensorParameter(code={self.code}, name={self.name}, unit={self.unit})>"


class Sensor(Base, UUIDMixin, TimestampMixin):
    """
    IoT Sensor device reference.
    Synced from Gateway Production Service.
    Denormalized: line_name, parameter_name, parameter_unit for reporting without JOIN.
    """
    __tablename__ = "sensors"

    device_id = Column(String(50), nullable=False, unique=True, index=True)
    production_line_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    line_name = Column(String(255), nullable=True)
    sensor_parameter_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    parameter_name = Column(String(100), nullable=True)
    parameter_unit = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        Index('idx_sensor_device_id', 'device_id'),
        Index('idx_sensor_production_line', 'production_line_id'),
        Index('idx_sensor_parameter', 'sensor_parameter_id'),
        Index('idx_sensor_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Sensor(device_id={self.device_id}, param_id={self.sensor_parameter_id})>"


class Customer(Base, UUIDMixin, TimestampMixin):
    """
    Customer reference for sales.
    Synced from Gateway Production Service. ID must be provided from Gateway.
    """
    __tablename__ = "customers"

    name = Column(String(200), nullable=False)
    code = Column(String(20), nullable=False, unique=True, index=True)
    region = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        Index('idx_customer_code', 'code'),
        Index('idx_customer_region', 'region'),
        Index('idx_customer_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Customer(code={self.code}, name={self.name}, region={self.region})>"


class QualitySpec(Base, UUIDMixin, TimestampMixin):
    """
    Quality specification for products (separated from test results for 3NF).
    Synced from Gateway Production Service.
    """
    __tablename__ = "quality_specs"

    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    parameter_name = Column(String(100), nullable=False)
    lower_limit = Column(DECIMAL(15, 6), nullable=False)
    upper_limit = Column(DECIMAL(15, 6), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        Index('idx_quality_spec_product', 'product_id'),
        Index('idx_quality_spec_product_param', 'product_id', 'parameter_name'),
        Index('idx_quality_spec_active', 'is_active'),
    )

    def __repr__(self):
        return f"<QualitySpec(product_id={self.product_id}, param={self.parameter_name})>"


class LineCapacityPlan(Base, UUIDMixin, TimestampMixin):
    """
    Production line capacity plan (planed hours and target OEE).
    Used for calculating OEE metrics.
    """
    __tablename__ = "line_capacity_plans"

    production_line_id = Column(UUID(as_uuid=True), ForeignKey("production_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    planned_hours_per_day = Column(Integer, nullable=False)
    target_oee_percent = Column(DECIMAL(5, 2), nullable=False, default=85)
    period_from = Column(Date, nullable=False, index=True)
    period_to = Column(Date, nullable=True)

    __table_args__ = (
        Index('idx_line_capacity_plan_line_period', 'production_line_id', 'period_from'),
    )

    def __repr__(self):
        return f"<LineCapacityPlan(line={self.production_line_id}, {self.period_from}-{self.period_to})>"


class KPIConfig(Base, UUIDMixin, TimestampMixin):
    """
    KPI configuration for admin-settable targets and parameters.
    Used for EBITDA targets, market volume, and other configurable metrics.
    """
    __tablename__ = "kpi_configs"

    key = Column(String(100), nullable=False, unique=True, index=True)  # e.g. "market_total_volume_tonnes"
    value = Column(DECIMAL(20, 4), nullable=False)
    description = Column(String(500), nullable=True)
    updated_by = Column(String(255), nullable=True)

    __table_args__ = (
        Index('idx_kpi_config_key', 'key'),
    )

    def __repr__(self):
        return f"<KPIConfig(key={self.key}, value={self.value})>"
