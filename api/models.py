from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime, func
from .database import Base

class Reading(Base):
    __tablename__ = "readings"
    id           = Column(Integer, primary_key=True, index=True)
    device_id    = Column(String, index=True)
    heart_rate   = Column(Float, nullable=True)
    spo2         = Column(Float, nullable=True)
    temperature  = Column(Float, nullable=True)
    fall_detected = Column(Boolean, default=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"
    id         = Column(Integer, primary_key=True, index=True)
    device_id  = Column(String, index=True)
    type       = Column(String)   # 'fall' | 'heart_rate' | 'spo2' | 'temperature' | 'anomaly'
    severity   = Column(String)   # 'info' | 'warn' | 'critical'
    message    = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
