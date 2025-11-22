# app/models.py
from typing import Optional
from sqlmodel import SQLModel, Field
import datetime

class Reading(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, nullable=False)
    device_id: str
    flow_rate_lpm: float     # liters per minute
    total_liters: float = 0.0
    reading_seconds: Optional[float] = None

    # optional metadata to help ML predictions
    family_size: Optional[int] = None
    appliances: Optional[int] = None
    usage_hours: Optional[float] = None
    primary_appliance: Optional[str] = None
    water_saving_device: Optional[bool] = None
