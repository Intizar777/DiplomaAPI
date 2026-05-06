"""
Synchronization logging models.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, SyncStatus


class SyncLog(Base, UUIDMixin, TimestampMixin):
    """
    Log of synchronization task executions.
    """
    __tablename__ = "sync_logs"
    
    # Task info
    task_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # SyncStatus value
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    
    # Error info
    error_message = Column(Text, nullable=True)
    
    # Relationships
    errors = relationship("SyncError", back_populates="sync_log", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_sync_task_status', 'task_name', 'status'),
        Index('idx_sync_started', 'started_at'),
    )
    
    def __repr__(self):
        return f"<SyncLog({self.task_name}, {self.status}, {self.started_at})>"


class SyncError(Base, UUIDMixin, TimestampMixin):
    """
    Detailed error records from synchronization.
    """
    __tablename__ = "sync_errors"
    
    # Reference to sync log
    sync_log_id = Column(UUID(as_uuid=True), ForeignKey('sync_logs.id', ondelete='CASCADE'), nullable=False)
    
    # Error details
    error_type = Column(String(50), nullable=False, index=True)  # 'API_ERROR', 'VALIDATION_ERROR', 'DB_ERROR'
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=False)
    
    # Entity reference
    entity_type = Column(String(50), nullable=True)  # 'order', 'sale', 'kpi'
    entity_id = Column(String(100), nullable=True)
    
    # Relationships
    sync_log = relationship("SyncLog", back_populates="errors")
    
    # Indexes
    __table_args__ = (
        Index('idx_error_sync_log', 'sync_log_id'),
        Index('idx_error_type', 'error_type'),
    )
    
    def __repr__(self):
        return f"<SyncError({self.error_type}, {self.entity_type}={self.entity_id})>"
