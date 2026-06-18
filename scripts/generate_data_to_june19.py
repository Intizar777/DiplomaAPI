"""
Generate data for all date-based tables up to June 19 inclusive.
Uses batch inserts for performance.
"""
import asyncio
import random
import uuid
import logging
from datetime import date, datetime, timedelta, timezone

logging.basicConfig(level=logging.WARNING)

from app.database import AsyncSessionLocal
from sqlalchemy import text
from sqlalchemy.engine import Engine

# Silence SQLAlchemy logging
for name in ["sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.dialects"]:
    logging.getLogger(name).setLevel(logging.WARNING)

random.seed(42)

PRODUCTION_LINES = [
    ("4d1b5527-2315-0129-4000-409c8f901120", "TAM_LINE_A", "Линия А - Рафинация маслосемян (Тамань)"),
    ("1aebc8ae-4374-f95a-8ec9-b80f1375d3c6", "TAM_LINE_B", "Линия Б - Упаковка масел (Тамань)"),
    ("596c3638-89d3-1d32-8529-8207984638e7", "EKB_LINE_A", "Линия А - Производство майонеза (ЕЖК)"),
    ("a25e7bc7-221e-1376-0bc0-f30299a83ff1", "EKB_LINE_B", "Линия Б - Кетчуп и горчица (ЕЖК)"),
    ("49a5ba6f-3838-3d85-6310-cf1ec432864d", "HOH_LINE_A", "Линия А - Производство маргарина (Хохольский)"),
    ("9330f683-f62b-5e4a-7877-6d2f13d19384", "HOH_LINE_B", "Линия Б - Мыловарение (Хохольский)"),
    ("3d57ea5f-fcd5-3a77-24cb-7996f830f190", "ALM_LINE_A", "Линия А - Основное производство (Алматы)"),
    ("a0a65c5f-bb95-e4a8-e1be-3b6dff660b2d", "NOG_LINE_A", "Линия А - Производство майонеза (Ногинск)"),
]

FINISHED_PRODUCTS = [
    ("b8dc0162-3e21-4839-91e4-39ec49c17785", "FP-001", "Масло подсолнечное Слобода рафин. 1л ПЭТ"),
    ("8a162761-6d2e-481f-8f34-1211131e5331", "FP-002", "Масло подсолнечное Слобода рафин. 5л ПЭТ"),
    ("ed40c866-e295-4d26-8b16-4cac014cf12e", "FP-003", "Масло подсолнечное Слобода нерафин. 0.5л ст."),
    ("92cee10f-badd-43cc-85e3-8d2a4096523e", "FP-004", "Масло Altero Golden 1л ПЭТ"),
    ("348d95de-d10c-40a7-9382-f0de6dfdf1de", "FP-005", "Масло Altero с добавлением лимона 0.25л"),
    ("bb11cfb3-b6f3-4aa7-a2c7-79f361facb2d", "FP-006", "Масло подсолнечное Солнечная Линия 1л ПЭТ"),
    ("afbd2523-e9be-487a-821c-9649fa36e352", "FP-007", "Масло подсолнечное Солнечная Линия 5л ПЭТ"),
    ("968c41a9-1fb0-4ad4-9835-e3e9a08d45db", "FP-008", "Масло подсолнечное Слобода 3л ПЭТ"),
    ("e773a5c4-a6fb-4dbe-af69-faa320f1dae0", "FP-009", "Масло подсолнечное Солнечная Линия 1л ПЭТ"),
    ("3d0ad376-80c8-4def-a067-7b5ce4190573", "FP-010", "Маргарин Слобода 72% 400г брикет"),
    ("3df0b82b-afed-40a3-87f2-11c80c2a072c", "FP-011", "Маргарин Слобода 80% 200г"),
    ("444f14e2-2f7d-4c3e-af94-1f9e2405bd2b", "FP-012", "Спред «Мягкое масло» 65% 400г ванночка"),
    ("2001a072-bca0-4e3d-805e-73b205284297", "FP-013", "Майонез Слобода Провансаль 67% 400г"),
    ("b3bf537d-803c-48dc-bf5a-e353dc43f1ef", "FP-014", "Майонез Слобода 67% 1кг дойпак"),
    ("b21cf5a3-2897-4752-8227-00ce49bc76ea", "FP-015", "Майонез Слобода Провансаль 67% 800г"),
    ("9e918070-f73f-4f2e-8e25-10aeff57752a", "FP-016", "Майонез Слобода Лёгкий 40% 400г"),
    ("08c0e28f-3a45-4a88-9b16-dd4029c59718", "FP-017", "Майонез Слобода Провансаль 67% 200г туба"),
    ("e9f64892-d8c9-4a9c-bdce-c1e153abfa62", "FP-018", "Майонез Altero Premium 67% 200г стекло"),
    ("ae6bd5b7-7844-419a-b146-0cb1c13d39ac", "FP-019", "Майонез EFKO Food Провансаль 67% 5кг (HoReCa)"),
    ("c550af75-d173-425f-93a7-3e14f68c8d08", "FP-020", "Масло сливочное аналог 82.5% 180г EFKO Food"),
    ("56c13507-91a3-48b3-bcbf-af9a1550f02e", "FP-021", "Соус Слобода Томатный 350г"),
    ("4c38bae6-5810-4884-9a75-aa091bc31109", "FP-022", "Соус Слобода Горчица 200г"),
    ("efa332de-2c02-4899-9308-0fcee5ec13d1", "FP-023", "Кетчуп Слобода Шашлычный 350г"),
    ("5b8c6021-28bc-4c8e-9b9f-29915f84d3e8", "FP-024", "Кетчуп Слобода Томатный 350г"),
    ("dd271d3c-483f-4660-889a-66e4894b58ee", "FP-025", "Масло кукурузное Слобода 1л ПЭТ"),
    ("6dee41f1-f5ee-438b-8a1d-b6bde77a8b53", "FP-026", "Масло льняное Алтайское 0.5л ст."),
    ("5456c5f4-fc4c-44f2-8435-40db48733702", "FP-027", "Кетчуп Слобода Томатный 1кг дойпак"),
    ("22e66e9b-e191-4790-b447-6f01e4982ea6", "FP-028", "Майонез EFKO Food Классик 67% 10кг ведро"),
]

RAW_MATERIALS = [
    ("483f2a10-5f63-4d9e-b1cc-8f553184e7f0", "RM-001", "Подсолнечник масличный"),
    ("dc814e09-e107-4711-9c79-fd49f24cec99", "RM-002", "Соевые бобы"),
    ("6f832144-9455-4b6f-9459-0eb02b88d477", "RM-003", "Рапс"),
    ("6223a0c8-c130-4b60-8f88-859ad9af8184", "RM-004", "Пальмовое масло сырое"),
    ("8d11b4dd-fa99-4c00-a2cc-f956de17d67a", "RM-005", "Масло пальмоядровое сырое"),
    ("09a3d8a6-88c8-4d04-99d0-0acbc018df79", "RM-006", "Молоко цельное сырое"),
    ("6e722b8e-993f-4ed1-a8fa-b10adfa0cf10", "RM-007", "Яйца куриные пищевые"),
    ("19979c23-2586-48d1-aa3d-d5f83d01cfc0", "RM-008", "Сахар-песок"),
    ("a337a0fb-c9a6-48a4-b3c9-11ad2284b120", "RM-009", "Соль поваренная пищевая"),
    ("569b4801-6128-4117-8947-5a2eaf46276a", "RM-010", "Уксус столовый 9%"),
]

REGIONS = [
    "Алматы", "Белгородская область", "Воронежская область", "ДФО",
    "Краснодарский край", "Московская область", "Новосибирская область",
    "ПФО", "Ростовская область", "Свердловская область", "СЗФО", "СФО",
    "Татарстан", "УФО", "ЦФО", "Экспорт (Азия)", "Экспорт (Африка)",
    "Экспорт (Ближний Восток)", "Экспорт (СНГ)", "ЮФО",
]
CHANNELS = ["export", "horeca", "retail", "wholesale"]
SHIFTS = ["Утренняя", "Дневная", "Ночная"]

SENSORS = [
    ("68d284ea-29d4-4c82-be74-36cb7e434855", "ALM_LINE_A-ВЛАЖ"),
    ("ce21b29b-2969-450b-9d29-435fc0636d85", "ALM_LINE_A-РАСХ"),
    ("8ad0f8c0-aa5f-4af4-8ec8-f361f42513f4", "EKB_LINE_A-ТЕМП"),
    ("0a19701a-e189-4eb4-97cb-a2378b281022", "EKB_LINE_A-ВЛАЖ"),
    ("5e9097c2-0254-40cd-82cd-7deaf5366ac4", "HOH_LINE_A-ТЕМП"),
    ("6b5a7b5f-1701-4f35-8bc4-d5f84c186bc9", "HOH_LINE_A-ДАВЛ"),
    ("20517ee4-7622-4f9d-bc5c-7f9cde9e69a6", "NOG_LINE_A-ТЕМП"),
    ("cb11a035-adf3-4550-ba92-a4e4a9ab3bae", "NOG_LINE_A-T01-ТЕМП"),
]

QUALITY_SPECS_SAMPLE = [
    ("b8dc0162-3e21-4839-91e4-39ec49c17785", "Кислотное число", "0.000000", "0.600000"),
    ("b8dc0162-3e21-4839-91e4-39ec49c17785", "Перекисное число", "0.000000", "5.000000"),
    ("b8dc0162-3e21-4839-91e4-39ec49c17785", "Содержание жира", "60.000000", "85.000000"),
    ("b8dc0162-3e21-4839-91e4-39ec49c17785", "Влажность", "0.000000", "0.150000"),
    ("c550af75-d173-425f-93a7-3e14f68c8d08", "Кислотное число", "0.000000", "0.600000"),
    ("c550af75-d173-425f-93a7-3e14f68c8d08", "Перекисное число", "0.000000", "5.000000"),
    ("c550af75-d173-425f-93a7-3e14f68c8d08", "Содержание жира", "60.000000", "85.000000"),
    ("c550af75-d173-425f-93a7-3e14f68c8d08", "Влажность", "0.000000", "0.150000"),
    ("2001a072-bca0-4e3d-805e-73b205284297", "Кислотное число", "0.000000", "0.600000"),
    ("2001a072-bca0-4e3d-805e-73b205284297", "Перекисное число", "0.000000", "5.000000"),
    ("2001a072-bca0-4e3d-805e-73b205284297", "Содержание жира", "60.000000", "85.000000"),
    ("2001a072-bca0-4e3d-805e-73b205284297", "Влажность", "0.000000", "0.150000"),
    ("56c13507-91a3-48b3-bcbf-af9a1550f02e", "Кислотное число", "0.000000", "0.400000"),
    ("56c13507-91a3-48b3-bcbf-af9a1550f02e", "Перекисное число", "0.000000", "2.000000"),
    ("56c13507-91a3-48b3-bcbf-af9a1550f02e", "Влажность", "0.000000", "0.100000"),
    ("4c38bae6-5810-4884-9a75-aa091bc31109", "Кислотное число", "0.000000", "0.400000"),
    ("4c38bae6-5810-4884-9a75-aa091bc31109", "Перекисное число", "0.000000", "2.000000"),
    ("4c38bae6-5810-4884-9a75-aa091bc31109", "Влажность", "0.000000", "0.100000"),
]

WAREHOUSES = [
    ("bba9b083-f819-44db-9dd0-46cd548b0d18", "Склад сырья № 1", "WH-RAW-01"),
    ("05de42f5-af9e-40e5-b82c-61d6598d499c", "Склад готовой продукции № 1", "WH-FP-01"),
    ("9dcc6a29-4a5f-4ae0-8fd5-44b8c5bc8d07", "Склад готовой продукции № 2", "WH-FP-02"),
    ("271b8cb5-a27f-41f7-a978-5c31ec14e48a", "Склад готовой продукции № 3", "WH-FP-03"),
    ("06937a75-9cc8-4304-873d-42c3c3c374b2", "Склад готовой продукции № 4", "WH-FP-04"),
    ("718aed21-341d-4231-aaae-7bca545656d8", "Склад полуфабрикатов", "WH-SF-01"),
    ("b5e50785-5b48-4f10-8d1d-d9ec464096db", "Экспортный склад", "WH-EXP-01"),
]

CUSTOMERS_DATA = [
    ("0ca9399c-15b0-4d5c-875b-3877e2c4cee2", "CUST-0ca9399c", "ООО «Ашан Ритейл Россия»"),
    ("9d7b33ab-13b4-45ff-8f71-6f3ac54f00bc", "CUST-9d7b33ab", "X5 Retail Group (Пятёрочка)"),
    ("ec87110e-4e58-41c3-bf0d-8e1c80b7df39", "CUST-ec87110e", "Efko China Distribution (Китай)"),
    ("3ca38131-dea4-413c-a988-0c0a72b8d8c1", "CUST-3ca38131", "ООО «Тандер» (Магнит)"),
    ("ac6e5ee5-112b-46e2-bb22-3863f3d9fc43", "CUST-ac6e5ee5", "X5 Retail Group (Перекрёсток)"),
    ("30f0a1f5-3d5a-4ff1-a67b-466563af87de", "CUST-30f0a1f5", "ООО «Лента»"),
    ("0256f641-5809-41bb-8db7-1a5e63f3c411", "CUST-0256f641", "ООО «О'КЕЙ»"),
    ("fc3ba518-2134-40dd-83e5-c5aa824d64ed", "CUST-fc3ba518", "АО «Дикси Юг»"),
    ("8092458c-eb82-4786-9afa-bc467dd68129", "CUST-8092458c", "ООО «Метро Кэш энд Керри»"),
    ("04080bff-5323-4ec4-80ae-1718aca7797b", "CUST-04080bff", "ООО «ВкусВилл»"),
    ("d0a2a66a-e709-4e21-9bab-720c782f377c", "CUST-d0a2a66a", "АО «Торговый Дом Перекрёсток»"),
    ("2b097d00-02b9-41a9-a2b5-dd6e3250604f", "CUST-2b097d00", "ООО «Агроторг»"),
    ("6e871e8c-0c82-493a-88bf-6207be4d750c", "CUST-6e871e8c", "ООО «Чижик» (X5)"),
    ("ff51cad8-ef3c-4486-ad1c-2fe1eb023838", "CUST-ff51cad8", "Efko Food Ltd (Египет)"),
    ("3b75c317-9e33-49dd-bfba-af69e89c915f", "CUST-3b75c317", "Al-Bakri Trading (Саудовская Аравия)"),
    ("86873592-2406-4602-9e74-ea34df4706b0", "CUST-86873592", "АО «Белагропродторг» (Беларусь)"),
    ("16a30e1e-b41d-4672-9faa-a621b67fc2ac", "CUST-16a30e1e", "ТОО «КазОйл» (Казахстан)"),
    ("e90eec3c-1e7c-49cf-8fd7-0874fd98adf6", "CUST-e90eec3c", "ООО «УзМасло» (Узбекистан)"),
    ("9ddf9584-bcdb-4413-a360-6c8c50fd428e", "CUST-9ddf9584", "ООО «Фудмарт Сервис» (HoReCa)"),
    ("4820fd34-604f-4527-96ea-e090787ccd29", "CUST-4820fd34", "ООО «Vkusno i tochka»"),
]


def uid() -> str:
    return str(uuid.uuid4())


def make_dt(d: date, h: int = 0, m: int = 0, s: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, h, m, s, tzinfo=timezone.utc)


async def batch_insert(session, sql: str, rows: list[dict], batch_size: int = 500):
    """Insert rows in batches using executemany."""
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        await session.execute(text(sql), batch)
    return len(rows)


async def gen_sale_records(target_date: date) -> list[dict]:
    day_of_week = target_date.weekday()
    count = random.randint(25, 35) if day_of_week < 5 else random.randint(15, 25)
    rows = []
    for i in range(count):
        product = random.choice(FINISHED_PRODUCTS)
        customer = random.choice(CUSTOMERS_DATA)
        qty = round(random.uniform(100, 2000), 3)
        unit_price = round(random.uniform(150, 800), 2)
        amount = round(qty * unit_price, 2)
        cost = round(amount * random.uniform(0.65, 0.85), 2)
        rows.append({
            "id": uid(), "external_id": f"SALE-{target_date.strftime('%Y%m%d')}-{i+1:04d}",
            "product_id": product[0], "product_name": product[2],
            "customer_id": customer[0], "customer_name": customer[2],
            "quantity": qty, "amount": amount, "cost": cost,
            "sale_date": target_date, "region": random.choice(REGIONS),
            "channel": random.choice(CHANNELS), "snapshot_date": target_date + timedelta(days=1),
            "event_id": None,
        })
    return rows


async def gen_order_snapshots(target_date: date, session) -> list[dict]:
    result = await session.execute(text("""
        SELECT DISTINCT order_id, product_id, product_name, target_quantity, unit_of_measure, production_line
        FROM order_snapshots
    """))
    templates = result.fetchall()
    if not templates:
        return []
    rows = []
    for tpl in templates:
        order_id, product_id, product_name, target_qty, uom, prod_line = tpl
        r = random.random()
        status = "completed" if r < 0.6 else "planned" if r < 0.8 else "in_progress" if r < 0.95 else "cancelled"
        ps = make_dt(target_date, 6, 0, 0)
        pe = make_dt(target_date, 22, 0, 0)
        as_ = ae = aq = None
        if status == "completed":
            as_ = ps + timedelta(minutes=random.randint(10, 90))
            ae = pe - timedelta(minutes=random.randint(10, 120))
            aq = round(float(target_qty) * random.uniform(0.97, 1.03), 3)
        elif status == "in_progress":
            as_ = ps + timedelta(minutes=random.randint(10, 60))
        rows.append({
            "id": uid(), "order_id": order_id,
            "external_order_id": f"ORD-{target_date.strftime('%Y%m%d')}-{random.randint(100, 999)}",
            "product_id": product_id, "product_name": product_name,
            "target_quantity": target_qty, "actual_quantity": aq,
            "unit_of_measure": uom, "status": status, "production_line": prod_line,
            "planned_start": ps, "planned_end": pe,
            "actual_start": as_, "actual_end": ae,
            "snapshot_date": target_date, "event_id": None,
        })
    return rows


async def gen_quality_results(target_date: date) -> list[dict]:
    count = random.randint(50, 80)
    rows = []
    for _ in range(count):
        product = random.choice(FINISHED_PRODUCTS)
        specs = [s for s in QUALITY_SPECS_SAMPLE if s[0] == product[0]]
        spec = random.choice(specs) if specs else random.choice(QUALITY_SPECS_SAMPLE)
        result_value = round(random.uniform(float(spec[2]) * 0.3, float(spec[3]) * 0.9), 4)
        in_spec = result_value <= float(spec[3])
        rows.append({
            "id": uid(), "lot_number": f"LOT-{target_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            "product_id": product[0], "product_name": product[2],
            "parameter_name": spec[1], "result_value": result_value,
            "quality_spec_id": None, "in_spec": in_spec,
            "decision": "approved" if in_spec else random.choice(["rejected", "rework"]),
            "test_date": target_date, "event_id": uid(),
        })
    return rows


async def gen_production_output(target_date: date) -> list[dict]:
    count = random.randint(14, 23)
    rows = []
    for _ in range(count):
        product = random.choice(FINISHED_PRODUCTS)
        line = random.choice(PRODUCTION_LINES)
        rows.append({
            "id": uid(), "order_id": uid(),
            "product_id": product[0], "product_name": product[2],
            "production_line_id": line[0], "production_line_name": line[2],
            "lot_number": f"LOT-{target_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            "quantity": round(random.uniform(200, 800), 3),
            "quality_status": "approved" if random.random() > 0.05 else "rejected",
            "production_date": target_date, "shift": random.choice(SHIFTS),
            "snapshot_date": target_date, "event_id": None,
        })
    return rows


async def gen_inventory_snapshots(target_date: date, session) -> list[dict]:
    result = await session.execute(text("""
        SELECT DISTINCT product_id, product_name, warehouse_id, warehouse_name, warehouse_code, unit_of_measure, lot_number
        FROM inventory_snapshots
    """))
    existing = result.fetchall()
    rows = []
    for item in existing:
        rows.append({
            "id": uid(), "product_id": item[0], "product_name": item[1],
            "warehouse_id": item[2], "warehouse_name": item[3], "warehouse_code": item[4],
            "lot_number": item[6], "quantity": round(random.uniform(500, 50000), 3),
            "unit_of_measure": item[5],
            "last_updated": make_dt(target_date, random.randint(0, 23), random.randint(0, 59), random.randint(0, 59)),
            "snapshot_date": target_date, "event_id": None,
        })
    return rows


async def gen_sensor_readings(target_date: date) -> list[dict]:
    rows = []
    for sensor_id, _ in SENSORS:
        for h in range(24):
            for _ in range(random.randint(1, 2)):
                dt = make_dt(target_date, h, random.randint(0, 59), random.randint(0, 59))
                rows.append({
                    "id": uid(), "sensor_id": sensor_id,
                    "value": round(random.uniform(10, 100), 4),
                    "quality": "good" if random.random() > 0.03 else "warning",
                    "recorded_at": dt,
                    "snapshot_date": dt + timedelta(days=1, hours=random.randint(1, 5)),
                })
    return rows


async def gen_batch_inputs(target_date: date) -> list[dict]:
    count = random.randint(8, 16)
    rows = []
    for _ in range(count):
        rm = random.choice(RAW_MATERIALS)
        input_dt = make_dt(target_date, random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
        rows.append({
            "id": uid(), "order_id": uid(), "product_id": rm[0],
            "quantity": round(random.uniform(500, 5000), 3),
            "input_date": input_dt, "event_id": f"EVT-INPUT-{uid()[:8].upper()}",
        })
    return rows


async def gen_sales_trends(target_date: date) -> list[dict]:
    rows = []
    for region in random.sample(REGIONS, k=random.randint(8, 15)):
        for channel in random.sample(CHANNELS, k=random.randint(1, 3)):
            rows.append({
                "id": uid(), "trend_date": target_date, "interval_type": "day",
                "region": region, "channel": channel,
                "total_amount": round(random.uniform(50000, 500000), 2),
                "total_quantity": round(random.uniform(100, 2000), 3),
                "order_count": random.randint(1, 8),
            })
    return rows


async def gen_aggregated_kpi(target_date: date) -> list[dict]:
    period_from = target_date - timedelta(days=30)
    rows = []
    for line_id, line_code, line_name in PRODUCTION_LINES:
        output = round(random.uniform(5000, 15000), 3)
        defect = round(random.uniform(0.005, 0.03), 2)
        completed = random.randint(15, 35)
        total = completed + random.randint(0, 5)
        rows.append({
            "id": uid(), "period_from": period_from, "period_to": target_date,
            "product_line_id": line_id, "production_line_name": line_name,
            "total_output": output, "defect_rate": defect,
            "completed_orders": completed, "total_orders": total,
            "oee_estimate": round(random.uniform(65, 90), 2),
            "avg_order_completion_time": "10 hours 15 minutes",
        })
    total_output = sum(r["total_output"] for r in rows)
    total_completed = sum(r["completed_orders"] for r in rows)
    total_orders = sum(r["total_orders"] for r in rows)
    avg_defect = round(sum(r["defect_rate"] for r in rows) / len(rows), 2)
    avg_oee = round(sum(r["oee_estimate"] for r in rows) / len(rows), 2)
    rows.append({
        "id": uid(), "period_from": period_from, "period_to": target_date,
        "product_line_id": None, "production_line_name": "Все линии",
        "total_output": round(total_output, 3), "defect_rate": avg_defect,
        "completed_orders": total_completed, "total_orders": total_orders,
        "oee_estimate": avg_oee, "avg_order_completion_time": "10 hours 45 minutes",
    })
    return rows


async def gen_sync_logs(target_date: date) -> list[dict]:
    tasks = ["kpi", "kpi_per_line", "aggregate_sales_trends", "sync_orders", "sync_sales", "sync_quality"]
    rows = []
    for hour in range(0, 24, 4):
        started = make_dt(target_date, hour, random.randint(0, 10), random.randint(0, 59))
        duration = timedelta(seconds=random.randint(5, 300))
        records = random.randint(100, 5000)
        rows.append({
            "id": uid(), "task_name": random.choice(tasks), "status": "completed",
            "started_at": started, "completed_at": started + duration,
            "records_processed": records,
            "records_inserted": int(records * random.uniform(0.7, 1.0)),
            "records_updated": int(records * random.uniform(0, 0.3)),
            "error_message": None,
        })
    return rows


# SQL templates
SQL_SALE_RECORDS = """
    INSERT INTO sale_records (id, external_id, product_id, product_name, customer_id, customer_name,
        quantity, amount, cost, sale_date, region, channel, snapshot_date, event_id, created_at, updated_at)
    VALUES (:id, :external_id, :product_id, :product_name, :customer_id, :customer_name,
        :quantity, :amount, :cost, :sale_date, :region, :channel, :snapshot_date, :event_id, NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
"""

SQL_ORDER_SNAPSHOTS = """
    INSERT INTO order_snapshots (id, order_id, external_order_id, product_id, product_name,
        target_quantity, actual_quantity, unit_of_measure, status, production_line,
        planned_start, planned_end, actual_start, actual_end, snapshot_date, event_id, created_at, updated_at)
    VALUES (:id, :order_id, :external_order_id, :product_id, :product_name,
        :target_quantity, :actual_quantity, :unit_of_measure, :status, :production_line,
        :planned_start, :planned_end, :actual_start, :actual_end, :snapshot_date, :event_id, NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
"""

SQL_QUALITY_RESULTS = """
    INSERT INTO quality_results (id, lot_number, product_id, product_name, parameter_name,
        result_value, quality_spec_id, in_spec, decision, test_date, event_id, created_at, updated_at)
    VALUES (:id, :lot_number, :product_id, :product_name, :parameter_name,
        :result_value, :quality_spec_id, :in_spec, :decision, :test_date, :event_id, NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
"""

SQL_PRODUCTION_OUTPUT = """
    INSERT INTO production_output (id, order_id, product_id, product_name,
        production_line_id, production_line_name, lot_number, quantity, quality_status,
        production_date, shift, snapshot_date, event_id, created_at, updated_at)
    VALUES (:id, :order_id, :product_id, :product_name,
        :production_line_id, :production_line_name, :lot_number, :quantity, :quality_status,
        :production_date, :shift, :snapshot_date, :event_id, NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
"""

SQL_INVENTORY_SNAPSHOTS = """
    INSERT INTO inventory_snapshots (id, product_id, product_name, warehouse_id, warehouse_name,
        warehouse_code, lot_number, quantity, unit_of_measure, last_updated, snapshot_date, event_id, created_at, updated_at)
    VALUES (:id, :product_id, :product_name, :warehouse_id, :warehouse_name,
        :warehouse_code, :lot_number, :quantity, :unit_of_measure, :last_updated, :snapshot_date, :event_id, NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
"""

SQL_SENSOR_READINGS = """
    INSERT INTO sensor_readings (id, sensor_id, value, quality, recorded_at, snapshot_date, created_at, updated_at)
    VALUES (:id, :sensor_id, :value, :quality, :recorded_at, :snapshot_date, NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
"""

SQL_BATCH_INPUTS = """
    INSERT INTO batch_inputs (id, order_id, product_id, quantity, input_date, event_id, created_at, updated_at)
    VALUES (:id, :order_id, :product_id, :quantity, :input_date, :event_id, NOW(), NOW())
    ON CONFLICT (event_id) DO NOTHING
"""

SQL_SALES_TRENDS = """
    INSERT INTO sales_trends (id, trend_date, interval_type, region, channel,
        total_amount, total_quantity, order_count, created_at, updated_at)
    VALUES (:id, :trend_date, :interval_type, :region, :channel,
        :total_amount, :total_quantity, :order_count, NOW(), NOW())
    ON CONFLICT (trend_date, interval_type, region, channel) DO UPDATE SET
        total_amount = EXCLUDED.total_amount,
        total_quantity = EXCLUDED.total_quantity,
        order_count = EXCLUDED.order_count,
        updated_at = NOW()
"""

SQL_AGGREGATED_KPI = """
    INSERT INTO aggregated_kpi (id, period_from, period_to, product_line_id, production_line_name,
        total_output, defect_rate, completed_orders, total_orders, oee_estimate, avg_order_completion_time,
        created_at, updated_at)
    VALUES (:id, :period_from, :period_to, :product_line_id, :production_line_name,
        :total_output, :defect_rate, :completed_orders, :total_orders, :oee_estimate, :avg_order_completion_time,
        NOW(), NOW())
    ON CONFLICT (period_from, period_to, product_line_id) DO UPDATE SET
        total_output = EXCLUDED.total_output,
        defect_rate = EXCLUDED.defect_rate,
        completed_orders = EXCLUDED.completed_orders,
        total_orders = EXCLUDED.total_orders,
        oee_estimate = EXCLUDED.oee_estimate,
        avg_order_completion_time = EXCLUDED.avg_order_completion_time,
        updated_at = NOW()
"""

SQL_SYNC_LOGS = """
    INSERT INTO sync_logs (id, task_name, status, started_at, completed_at,
        records_processed, records_inserted, records_updated, error_message, created_at, updated_at)
    VALUES (:id, :task_name, :status, :started_at, :completed_at,
        :records_processed, :records_inserted, :records_updated, :error_message, NOW(), NOW())
    ON CONFLICT (id) DO NOTHING
"""


async def main():
    async with AsyncSessionLocal() as session:
        june15 = date(2026, 6, 15)
        june16 = date(2026, 6, 16)
        june17 = date(2026, 6, 17)
        june18 = date(2026, 6, 18)
        june19 = date(2026, 6, 19)

        # sale_records: June 15-19
        print("sale_records...")
        for d in [june15, june16, june17, june18, june19]:
            rows = await gen_sale_records(d)
            n = await batch_insert(session, SQL_SALE_RECORDS, rows)
            print(f"  {d}: {n}")

        # order_snapshots: June 16-19
        print("order_snapshots...")
        for d in [june16, june17, june18, june19]:
            rows = await gen_order_snapshots(d, session)
            n = await batch_insert(session, SQL_ORDER_SNAPSHOTS, rows)
            print(f"  {d}: {n}")

        # quality_results: June 16-19
        print("quality_results...")
        for d in [june16, june17, june18, june19]:
            rows = await gen_quality_results(d)
            n = await batch_insert(session, SQL_QUALITY_RESULTS, rows)
            print(f"  {d}: {n}")

        # production_output: June 16-19
        print("production_output...")
        for d in [june16, june17, june18, june19]:
            rows = await gen_production_output(d)
            n = await batch_insert(session, SQL_PRODUCTION_OUTPUT, rows)
            print(f"  {d}: {n}")

        # inventory_snapshots: June 17-19
        print("inventory_snapshots...")
        for d in [june17, june18, june19]:
            rows = await gen_inventory_snapshots(d, session)
            n = await batch_insert(session, SQL_INVENTORY_SNAPSHOTS, rows)
            print(f"  {d}: {n}")

        # sensor_readings: June 15-19
        print("sensor_readings...")
        for d in [june15, june16, june17, june18, june19]:
            rows = await gen_sensor_readings(d)
            n = await batch_insert(session, SQL_SENSOR_READINGS, rows)
            print(f"  {d}: {n}")

        # batch_inputs: June 15-19
        print("batch_inputs...")
        for d in [june15, june16, june17, june18, june19]:
            rows = await gen_batch_inputs(d)
            n = await batch_insert(session, SQL_BATCH_INPUTS, rows)
            print(f"  {d}: {n}")

        # sales_trends: June 15-19
        print("sales_trends...")
        for d in [june15, june16, june17, june18, june19]:
            rows = await gen_sales_trends(d)
            n = await batch_insert(session, SQL_SALES_TRENDS, rows)
            print(f"  {d}: {n}")

        # aggregated_kpi: period_to = June 19
        print("aggregated_kpi...")
        rows = await gen_aggregated_kpi(june19)
        n = await batch_insert(session, SQL_AGGREGATED_KPI, rows)
        print(f"  {june19}: {n}")

        # sync_logs: June 18-19
        print("sync_logs...")
        for d in [june18, june19]:
            rows = await gen_sync_logs(d)
            n = await batch_insert(session, SQL_SYNC_LOGS, rows)
            print(f"  {d}: {n}")

        await session.commit()
        print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
