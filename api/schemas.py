from pydantic import BaseModel
from typing import Optional

class ReadingIn(BaseModel):
    device_id: str = "nano33ble-001"
    heart_rate: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    fall_detected: bool = False
