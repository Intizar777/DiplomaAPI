"""
Fast Initial Sync script to populate DiplomaAPI database from a SQL dump.
Directly parses COPY statements and performs bulk inserts.
"""
import asyncio
import os
import re
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from app.database import AsyncSessionLocal
from app.models import (
    Product, UnitOfMeasure, Warehouse, Customer, ProductionLine,
    OrderSnapshot, ProductionOutput, InventorySnapshot,
    SensorParameter, Sensor, SensorReading, SaleRecord, QualityResult, QualitySpec
)
import structlog

logger = structlog.get_logger()

DUMP_FILE = "production-dump.sql"

# Mappings for denormalization
products_map: Dict[UUID, Dict[str, Any]] = {}
orders_map: Dict[UUID, Dict[str, Any]] = {}
lines_map: Dict[UUID, Dict[str, Any]] = {}
warehouses_map: Dict[UUID, Dict[str, Any]] = {}
uoms_map: Dict[UUID, str] = {}
sensors_map: Dict[UUID, Dict[str, Any]] = {}
sensor_params_map: Dict[UUID, Dict[str, Any]] = {}
specs_map: Dict[UUID, Dict[str, Any]] = {}

def parse_val(val: str, type_hint: str = "str") -> Any:
    if val == "\\N" or val == "NULL":
        return None
    if type_hint == "uuid":
        return UUID(val)
    if type_hint == "float":
        return float(val)
    if type_hint == "int":
        return int(val)
    if type_hint == "bool":
        return val == "t"
    if type_hint == "datetime":
        return datetime.fromisoformat(val.replace(" ", "T"))
    if type_hint == "date":
        return date.fromisoformat(val)
    return val

async def read_copy_block(f):
    """Generator to read data from a COPY block."""
    for line in f:
        line = line.strip()
        if line == "\\.":
            break
        yield line.split("\t")

async def fast_import():
    if not os.path.exists(DUMP_FILE):
        logger.error("dump_file_not_found", path=DUMP_FILE)
        return

    async with AsyncSessionLocal() as db:
        logger.info("clearing_tables")
        # Order matters for CASCADE, but we truncate all anyway
        await db.execute(text("TRUNCATE TABLE units_of_measure, warehouses, customers, products, production_lines, order_snapshots, production_output, inventory_snapshots, sensor_parameters, sensors, sensor_readings, sale_records, quality_results, quality_specs CASCADE"))
        await db.commit()

        logger.info("parsing_dump", file=DUMP_FILE)
        with open(DUMP_FILE, "r") as f:
            for line in f:
                if not line.startswith("COPY"):
                    continue

                match = re.match(r"COPY public\.(\w+) \((.*)\) FROM stdin;", line)
                if not match:
                    continue

                table_name = match.group(1)
                cols = [c.strip() for c in match.group(2).split(",")]
                
                logger.info("importing_table", table=table_name)
                
                batch = []
                async for row in read_copy_block(f):
                    if len(row) != len(cols):
                        continue
                    data = dict(zip(cols, row))
                    
                    if table_name == "units_of_measure":
                        u_id = UUID(data["id"])
                        uoms_map[u_id] = data["code"]
                        batch.append({
                            "id": u_id,
                            "code": data["code"],
                            "name": data["name"],
                            "created_at": parse_val(data["created_at"], "datetime")
                        })

                    elif table_name == "warehouses":
                        w_id = UUID(data["id"])
                        warehouses_map[w_id] = {"code": data["code"], "name": data["name"]}
                        batch.append({
                            "id": w_id,
                            "code": data["code"],
                            "name": data["name"],
                            "is_active": True,
                            "created_at": parse_val(data["created_at"], "datetime")
                        })

                    elif table_name == "customers":
                        c_id = UUID(data["id"])
                        batch.append({
                            "id": c_id,
                            "name": data["name"],
                            "code": f"CUST-{str(c_id)[:8]}",
                            "region": "Unknown",
                            "is_active": True,
                            "created_at": parse_val(data["created_at"], "datetime")
                        })

                    elif table_name == "products":
                        p_id = UUID(data["id"])
                        uom_id = parse_val(data["unit_of_measure_id"], "uuid")
                        products_map[p_id] = {"name": data["name"], "uom": uoms_map.get(uom_id) if uom_id else None}
                        batch.append({
                            "id": p_id,
                            "code": data["code"],
                            "name": data["name"],
                            "category": parse_val(data["category"]),
                            "brand": parse_val(data["brand"]),
                            "unit_of_measure_id": uom_id,
                            "shelf_life_days": parse_val(data["shelf_life_days"], "int"),
                            "requires_quality_check": parse_val(data["requires_quality_check"], "bool"),
                            "source_system_id": data["source_system_id"],
                            "created_at": parse_val(data["created_at"], "datetime")
                        })

                    elif table_name == "production_lines":
                        l_id = UUID(data["id"])
                        lines_map[l_id] = {"name": data["name"], "code": data["code"]}
                        batch.append({
                            "id": l_id,
                            "name": data["name"],
                            "code": data["code"],
                            "description": parse_val(data["description"]),
                            "division": parse_val(data["division"]),
                            "is_active": parse_val(data["is_active"], "bool"),
                            "created_at": parse_val(data["created_at"], "datetime")
                        })

                    elif table_name == "production_orders":
                        o_id = UUID(data["id"])
                        p_id = UUID(data["product_id"])
                        l_id = parse_val(data["production_line_id"], "uuid")
                        
                        # Ensure product exists
                        if p_id not in products_map:
                            await create_product_placeholder(db, p_id)
                        
                        p_info = products_map.get(p_id, {"name": "Unknown Product"})
                        l_info = lines_map.get(l_id, {"code": "Unknown"}) if l_id else {"code": "Unknown"}
                        
                        orders_map[o_id] = {
                            "product_id": p_id,
                            "product_name": p_info["name"],
                            "line_code": l_info["code"]
                        }
                        
                        created_at = parse_val(data["created_at"], "datetime")
                        batch.append({
                            "id": o_id,
                            "order_id": o_id,
                            "external_order_id": data["external_order_id"],
                            "product_id": p_id,
                            "product_name": p_info["name"],
                            "target_quantity": parse_val(data["target_quantity"], "float"),
                            "actual_quantity": parse_val(data["actual_quantity"], "float"),
                            "unit_of_measure": p_info.get("uom"),
                            "status": data["status"],
                            "production_line": l_info["code"],
                            "planned_start": parse_val(data["planned_start"], "datetime"),
                            "planned_end": parse_val(data["planned_end"], "datetime"),
                            "actual_start": parse_val(data["actual_start"], "datetime"),
                            "actual_end": parse_val(data["actual_end"], "datetime"),
                            "snapshot_date": created_at.date() if created_at else date.today(),
                            "created_at": created_at
                        })

                    elif table_name == "production_output":
                        out_id = UUID(data["id"])
                        o_id = parse_val(data["order_id"], "uuid")
                        o_info = orders_map.get(o_id)
                        
                        p_id = o_info["product_id"] if o_info else None
                        p_name = o_info["product_name"] if o_info else "Unknown"
                        
                        created_at = parse_val(data["created_at"], "datetime")
                        batch.append({
                            "id": out_id,
                            "order_id": o_id,
                            "product_id": p_id,
                            "product_name": p_name,
                            "lot_number": data["lot_number"],
                            "quantity": parse_val(data["quantity"], "float"),
                            "quality_status": parse_val(data["quality_status"]),
                            "production_date": parse_val(data["production_date"], "date"),
                            "shift": parse_val(data["shift"]),
                            "snapshot_date": created_at.date() if created_at else date.today(),
                            "created_at": created_at
                        })

                    elif table_name == "inventory":
                        inv_id = UUID(data["id"])
                        p_id = UUID(data["product_id"])
                        w_id = parse_val(data["warehouse_id"], "uuid")
                        
                        if p_id not in products_map:
                            await create_product_placeholder(db, p_id)
                        if w_id and w_id not in warehouses_map:
                            await create_warehouse_placeholder(db, w_id)

                        p_info = products_map.get(p_id, {"name": "Unknown", "uom": None})
                        w_info = warehouses_map.get(w_id, {"code": "Unknown", "name": "Unknown"}) if w_id else {"code": "Unknown", "name": "Unknown"}
                        
                        batch.append({
                            "id": inv_id,
                            "product_id": p_id,
                            "product_name": p_info["name"],
                            "warehouse_id": w_id,
                            "warehouse_code": w_info["code"],
                            "warehouse_name": w_info["name"],
                            "lot_number": parse_val(data["lot_number"]),
                            "quantity": parse_val(data["quantity"], "float"),
                            "unit_of_measure": p_info["uom"],
                            "last_updated": parse_val(data["last_updated"], "datetime"),
                            "snapshot_date": date.today()
                        })

                    elif table_name == "sensor_parameters":
                        sp_id = UUID(data["id"])
                        sensor_params_map[sp_id] = {"name": data["name"], "unit": data["unit"]}
                        batch.append({
                            "id": sp_id,
                            "name": data["name"],
                            "code": re.sub(r'[^a-z0-9]', '_', data["name"].lower()),
                            "unit": data["unit"],
                            "is_active": True,
                            "created_at": parse_val(data["created_at"], "datetime")
                        })

                    elif table_name == "sensors":
                        s_id = UUID(data["id"])
                        l_id = UUID(data["production_line_id"])
                        sp_id = UUID(data["sensor_parameter_id"])
                        l_info = lines_map.get(l_id, {"name": "Unknown"})
                        sp_info = sensor_params_map.get(sp_id, {"name": "Unknown", "unit": ""})
                        
                        sensors_map[s_id] = {
                            "line_name": l_info["name"],
                            "param_name": sp_info["name"],
                            "param_unit": sp_info["unit"]
                        }
                        batch.append({
                            "id": s_id,
                            "device_id": data["device_id"],
                            "production_line_id": l_id,
                            "line_name": l_info["name"],
                            "sensor_parameter_id": sp_id,
                            "parameter_name": sp_info["name"],
                            "parameter_unit": sp_info["unit"],
                            "is_active": parse_val(data["is_active"], "bool"),
                            "created_at": parse_val(data["created_at"], "datetime")
                        })

                    elif table_name == "sensor_readings":
                        sr_id = UUID(data["id"])
                        created_at = parse_val(data["created_at"], "datetime")
                        batch.append({
                            "id": sr_id,
                            "sensor_id": UUID(data["sensor_id"]),
                            "value": parse_val(data["value"], "float"),
                            "quality": data["quality"],
                            "recorded_at": parse_val(data["recorded_at"], "datetime"),
                            "snapshot_date": created_at
                        })

                    elif table_name == "sales":
                        s_id = UUID(data["id"])
                        p_id = UUID(data["product_id"])
                        if p_id not in products_map:
                            await create_product_placeholder(db, p_id)
                        
                        p_info = products_map.get(p_id, {"name": "Unknown"})
                        created_at = parse_val(data["created_at"], "datetime")
                        batch.append({
                            "id": s_id,
                            "external_id": data["external_id"],
                            "product_id": p_id,
                            "product_name": p_info["name"],
                            "customer_id": parse_val(data["customer_id"], "uuid"),
                            "quantity": parse_val(data["quantity"], "float"),
                            "amount": parse_val(data["amount"], "float"),
                            "cost": parse_val(data["cost"], "float"),
                            "sale_date": parse_val(data["sale_date"], "date"),
                            "region": parse_val(data["region"]),
                            "channel": parse_val(data["channel"]),
                            "snapshot_date": created_at.date() if created_at else date.today()
                        })

                    elif table_name == "quality_specs":
                        qs_id = UUID(data["id"])
                        p_id = UUID(data["product_id"])
                        if p_id not in products_map:
                            await create_product_placeholder(db, p_id)

                        specs_map[qs_id] = {
                            "product_id": p_id,
                            "parameter_name": data["parameter_name"],
                            "lower_limit": parse_val(data["lower_limit"], "float"),
                            "upper_limit": parse_val(data["upper_limit"], "float")
                        }
                        batch.append({
                            "id": qs_id,
                            "product_id": p_id,
                            "parameter_name": data["parameter_name"],
                            "lower_limit": parse_val(data["lower_limit"], "float"),
                            "upper_limit": parse_val(data["upper_limit"], "float"),
                            "is_active": parse_val(data["is_active"], "bool")
                        })

                    elif table_name == "quality_results":
                        qr_id = UUID(data["id"])
                        qs_id = parse_val(data["quality_spec_id"], "uuid")
                        qs_info = specs_map.get(qs_id, {"product_id": None, "parameter_name": "Unknown"}) if qs_id else {"product_id": None, "parameter_name": "Unknown"}
                        p_info = products_map.get(qs_info["product_id"], {"name": "Unknown"}) if qs_info["product_id"] else {"name": "Unknown"}
                        
                        val = parse_val(data["result_value"], "float")
                        in_spec = True
                        if val is not None and qs_id in specs_map:
                            in_spec = (val >= specs_map[qs_id]["lower_limit"]) and (val <= specs_map[qs_id]["upper_limit"])

                        batch.append({
                            "id": qr_id,
                            "lot_number": data["lot_number"],
                            "product_id": qs_info["product_id"],
                            "product_name": p_info["name"],
                            "parameter_name": qs_info["parameter_name"],
                            "result_value": val,
                            "quality_spec_id": qs_id,
                            "in_spec": in_spec,
                            "decision": data["quality_status"],
                            "test_date": parse_val(data["test_date"], "date")
                        })

                    if len(batch) >= 5000:
                        await do_insert(db, table_name, batch)
                        batch = []
                
                if batch:
                    await do_insert(db, table_name, batch)
                    
        logger.info("import_completed")

async def create_product_placeholder(db, p_id: UUID):
    """Creates a placeholder in the products table."""
    placeholder = {
        "id": p_id,
        "code": f"UNKNOWN-{str(p_id)[:8]}",
        "name": f"Unknown Product ({str(p_id)[:8]})",
        "category": "unknown",
        "requires_quality_check": False
    }
    stmt = insert(Product.__table__).values(placeholder).on_conflict_do_nothing()
    await db.execute(stmt)
    await db.commit()
    products_map[p_id] = {"name": placeholder["name"], "uom": None}

async def create_warehouse_placeholder(db, w_id: UUID):
    """Creates a placeholder in the warehouses table."""
    placeholder = {
        "id": w_id,
        "code": f"WH-UNK-{str(w_id)[:8]}",
        "name": f"Unknown Warehouse ({str(w_id)[:8]})",
        "is_active": True
    }
    stmt = insert(Warehouse.__table__).values(placeholder).on_conflict_do_nothing()
    await db.execute(stmt)
    await db.commit()
    warehouses_map[w_id] = {"code": placeholder["code"], "name": placeholder["name"]}

async def do_insert(db, table_name, batch):
    model_map = {
        "units_of_measure": UnitOfMeasure,
        "warehouses": Warehouse,
        "customers": Customer,
        "products": Product,
        "production_lines": ProductionLine,
        "production_orders": OrderSnapshot,
        "production_output": ProductionOutput,
        "inventory": InventorySnapshot,
        "sensor_parameters": SensorParameter,
        "sensors": Sensor,
        "sensor_readings": SensorReading,
        "sales": SaleRecord,
        "quality_specs": QualitySpec,
        "quality_results": QualityResult
    }
    model = model_map.get(table_name)
    if not model:
        return
    
    # Use SQLAlchemy Core for fast insertion with conflict handling
    stmt = insert(model.__table__).values(batch).on_conflict_do_nothing()
    await db.execute(stmt)
    await db.commit()

if __name__ == "__main__":
    asyncio.run(fast_import())
