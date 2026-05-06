"""
Base model and common enums.
"""
import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SyncStatus(str, enum.Enum):
    """Synchronization task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderStatus(str, enum.Enum):
    """Production order status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QualityDecision(str, enum.Enum):
    """Quality control decision."""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class UUIDMixin:
    """Mixin for UUID primary key."""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
