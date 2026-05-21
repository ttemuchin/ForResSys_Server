from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class BaseEntity(Base, TimestampMixin):
    __tablename__ = "bases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    N = Column(Integer, nullable=False)
    nY = Column(Integer, nullable=False)
    error = Column(JSON, nullable=False)  # [0.001, 0.005]
    nX = Column(Integer, nullable=False)
    dimension = Column(JSON, nullable=False)  # [400, 60]
    trainedModels = Column(JSON, default=[])  # ["CNN", "SVR"]
    user_path = Column(String, nullable=False) # base_path
    static_path = Column(String, nullable=False) # content_path было раньше
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="bases")
    predictions = relationship("Prediction", back_populates="base")
    trainings = relationship("Training", back_populates="base")