from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime, timezone
import enum

class TrainingStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class Training(Base):
    __tablename__ = "trainings"
    
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, nullable=False)
    status = Column(Enum(TrainingStatus), default=TrainingStatus.PENDING)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Foreign Keys
    base_id = Column(Integer, ForeignKey("bases.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    base = relationship("BaseEntity", back_populates="trainings")
    user = relationship("User", back_populates="trainings")