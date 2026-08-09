import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

class PlanStatus(str, enum.Enum):
    completed = "completed"
    failed = "failed"
    partial = "partial"

class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(String, nullable=False)
    status = Column(Enum(PlanStatus), nullable=False)
    itinerary = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processing_time_seconds = Column(Float, nullable=True)
