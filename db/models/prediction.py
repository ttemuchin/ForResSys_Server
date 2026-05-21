from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime, timezone

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    input_file = Column(String, nullable=False)
    model = Column(String, nullable=False)
    results_path = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Foreign Keys
    base_id = Column(Integer, ForeignKey("bases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    base = relationship("BaseEntity", back_populates="predictions")
    user = relationship("User", back_populates="predictions")