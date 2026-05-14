#!/usr/bin/env python3
"""
Manual sync job runner - запуск задач синхронизации вручную.

Usage:
    python run_sync_job.py kpi
    python run_sync_job.py sales
    python run_sync_job.py all
    python run_sync_job.py all --auto-truncate  # Автоматический truncate при ошибке
    python run_sync_job.py list

KPI Sync Modes:
    - Initial sync (первый раз): Загружает KPI по месяцам с 2024-01 до сегодня (~30 запросов)
    - Incremental sync (регулярно): Загружает последние 30 дней + текущая неделя (1 запрос, upsert)
    
    Подробнее: KPI_SYNC_EXPLAINED.md
"""
import asyncio
import sys
from datetime import date, timedelta
import structlog

from app.cron.jobs import (
    sync_kpi_task, sync_kpi_per_line_task, sync_sales_task, sync_orders_task,
    sync_quality_task, sync_products_task, sync_output_task, sync_sensors_task,
    sync_inventory_task, sync_references_task, sync_batch_inputs_task,
    sync_downtime_events_task, sync_promo_campaigns_task, aggregate_sales_trends_task,
    sync_quality_specs_task, cleanup_old_data_task, truncate_all_data_task,
    initial_sync_kpi_task, initial_sync_kpi_per_line_task, initial_sync_sales_task,
    initial_sync_orders_task, initial_sync_quality_task, initial_sync_output_task,
    initial_sync_sensors_task, initial_sync_inventory_task, initial_sync_task,
    initial_sync_batch_inputs_task, initial_sync_downtime_events_task, initial_sync_promo_campaigns_task
)

logger = structlog.get_logger()

JOBS = {
    "initial_sync": ("🚀 ПОЛНАЯ СИНХРОНИЗАЦИЯ (все данные 2024-01→сегодня)", initial_sync_task),
    "references": ("Справочные таблицы", sync_references_task),
    "products": ("Продукты", sync_products_task),
    "quality_specs": ("Спецификации качества", sync_quality_specs_task),
    "kpi": ("KPI производства (incremental: 30 дней+неделя)", sync_kpi_task),
    "kpi_per_line": ("KPI по линиям (incremental: 30 дней+неделя)", sync_kpi_per_line_task),
    "initial_sync_kpi": ("KPI производства (полная: 2024-01→сегодня)", initial_sync_kpi_task),
    "initial_sync_kpi_per_line": ("KPI по линиям (полная: 2024-01→сегодня)", initial_sync_kpi_per_line_task),
    "sales": ("Продажи (incremental: 30 дней)", sync_sales_task),
    "initial_sync_sales": ("Продажи (полная: 2024-01→сегодня)", initial_sync_sales_task),
    "orders": ("Заказы (incremental: 30 дней)", sync_orders_task),
    "initial_sync_orders": ("Заказы (полная: 2024-01→сегодня)", initial_sync_orders_task),
    "quality": ("Качество (incremental: 30 дней)", sync_quality_task),
    "initial_sync_quality": ("Качество (полная: 2024-01→сегодня)", initial_sync_quality_task),
    "output": ("Выпуск продукции (incremental: 1 день)", sync_output_task),
    "initial_sync_output": ("Выпуск продукции (полная: 2024-01→сегодня)", initial_sync_output_task),
    "sensors": ("Датчики (incremental: 30 дней)", sync_sensors_task),
    "initial_sync_sensors": ("Датчики (полная: 2024-01→сегодня)", initial_sync_sensors_task),
    "inventory": ("Инвентарь", sync_inventory_task),
    "initial_sync_inventory": ("Инвентарь (полная: 2024-01→сегодня)", initial_sync_inventory_task),
    "batch_inputs": ("Входные партии (incremental: 7 дней, limit 100)", sync_batch_inputs_task),
    "initial_sync_batch_inputs": ("Входные партии (полная, limit 100)", initial_sync_batch_inputs_task),
    "downtime_events": ("События простоя (incremental: 7 дней, limit 100)", sync_downtime_events_task),
    "initial_sync_downtime_events": ("События простоя (полная, limit 100)", initial_sync_downtime_events_task),
    "promo_campaigns": ("Промо-кампании (incremental: ±30 дней, limit 100)", sync_promo_campaigns_task),
    "initial_sync_promo_campaigns": ("Промо-кампании (полная, limit 100)", initial_sync_promo_campaigns_task),
    "aggregate_sales_trends": ("Агрегация трендов продаж", aggregate_sales_trends_task),
    "cleanup": ("Очистка старых данных", cleanup_old_data_task),
    "truncate": ("⚠️  TRUNCATE ВСЕ ДАННЫЕ (опасно!)", truncate_all_data_task),
}


async def run_job(job_name: str, auto_truncate_on_error: bool = False) -> bool:
    """Run a single job."""
    if job_name not in JOBS:
        print(f"❌ Неизвестная задача: {job_name}")
        return False
    
    desc, job_func = JOBS[job_name]
    
    # Confirm dangerous operations
    if job_name == "truncate":
        print("\n" + "=" * 60)
        print("⚠️  ВНИМАНИЕ: Это удалит ВСЕ данные из всех таблиц!")
        print("=" * 60)
        confirm = input("Введите 'yes' для подтверждения: ").strip().lower()
        if confirm != "yes":
            print("❌ Отменено")
            return False
    
    print(f"\n▶️  Запуск: {desc} ({job_name})")
    
    try:
        await job_func()
        print(f"✅ Завершено: {job_name}")
        return True
    except Exception as e:
        print(f"❌ Ошибка в {job_name}: {e}")
        logger.error("manual_job_failed", job=job_name, error=str(e))
        
        # Auto-truncate on error if enabled
        if auto_truncate_on_error and job_name not in ("truncate", "initial_sync"):
            print(f"\n⚠️  Автоматический truncate из-за ошибки...")
            try:
                await truncate_all_data_task()
                print("✅ Данные очищены. Повторите синхронизацию.")
            except Exception as truncate_error:
                print(f"❌ Ошибка при truncate: {truncate_error}")
        
        return False


async def run_all_jobs(auto_truncate_on_error: bool = False) -> int:
    """Run all jobs in order."""
    print("=" * 60)
    print("Запуск всех задач синхронизации")
    if auto_truncate_on_error:
        print("⚠️  Режим: автоматический truncate при ошибке")
    print("=" * 60)
    
    # Order matters: references first, then products, then transactional data
    order = [
        "references", "products", "quality_specs",
        "initial_sync_kpi", "initial_sync_kpi_per_line", "initial_sync_sales", 
        "initial_sync_orders", "initial_sync_quality", "initial_sync_output", 
        "initial_sync_sensors", "initial_sync_inventory",
        "batch_inputs", "downtime_events", "promo_campaigns",
        "aggregate_sales_trends"
    ]
    
    results = {}
    for job_name in order:
        results[job_name] = await run_job(job_name, auto_truncate_on_error)
        if not results[job_name] and auto_truncate_on_error:
            print(f"\n⚠️  Остановка цепочки из-за ошибки в {job_name}")
            break
    
    # Summary
    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)
    
    success = sum(1 for v in results.values() if v)
    total = len(results)
    
    for job_name, success_flag in results.items():
        status = "✅" if success_flag else "❌"
        desc = JOBS[job_name][0]
        print(f"{status} {desc}")
    
    print(f"\nВсего: {success}/{total} успешно")
    return 0 if success == total else 1


def list_jobs():
    """List all available jobs."""
    print("Доступные задачи синхронизации:\n")
    for job_name, (desc, _) in sorted(JOBS.items()):
        print(f"  {job_name:<20} - {desc}")
    print(f"\nВсего: {len(JOBS)} задач")


async def main():
    if len(sys.argv) < 2:
        print("Использование: python run_sync_job.py <задача|all|list> [--auto-truncate]\n")
        list_jobs()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    auto_truncate = "--auto-truncate" in sys.argv
    
    if auto_truncate and command not in ("all", "initial_sync"):
        print("⚠️  --auto-truncate работает только с 'all' или 'initial_sync'")
        auto_truncate = False
    
    if command == "list":
        list_jobs()
        sys.exit(0)
    elif command == "all":
        sys.exit(await run_all_jobs(auto_truncate))
    elif command == "initial_sync":
        success = await run_job(command, auto_truncate_on_error=auto_truncate)
        sys.exit(0 if success else 1)
    else:
        success = await run_job(command, auto_truncate_on_error=auto_truncate)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
