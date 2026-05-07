"""
Event handlers — import all modules to trigger @register decorators.
"""
from app.messaging.handlers import (
    product_handler,
    order_handler,
    output_handler,
    sale_handler,
    inventory_handler,
    quality_handler,
)

__all__ = [
    "product_handler",
    "order_handler",
    "output_handler",
    "sale_handler",
    "inventory_handler",
    "quality_handler",
]
