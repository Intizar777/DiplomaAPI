"""
Sync status API schemas.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SyncTaskStatus(BaseModel):
    """Single sync task status."""
    task_name: str
    status: str  # pending, running, completed, failed
    last_run: Optional[datetime]
    last_success: Optional[datetime]
    records_processed: int
    records_inserted: int
    records_updated: int
    error_message: Optional[str]


class SyncStatusResponse(BaseModel):
    """Sync status response."""
    tasks: List[SyncTaskStatus]
    overall_status: str = Field(description="Overall sync status")
    last_sync: Optional[datetime]
    
    class Config:
        from_attributes = True


class SyncTriggerResponse(BaseModel):
    """Sync trigger response."""
    message: str
    triggered_tasks: List[str]
    
    class Config:
        from_attributes = True
