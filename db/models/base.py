from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone
Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))



# base.py / prediction.py / training.py

# # 1
# timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
# # 2
# timestamp = Column(DateTime, default=datetime.now)  # local time
# # 3 (для PostgreSQL с timezone)
# from sqlalchemy import func
# timestamp = Column(DateTime(timezone=True), server_default=func.now())