# Tiny rule-based anomaly heuristic (stateless demo)
# Returns a list of messages (0, 1 or more) when something looks odd.

from typing import List, Optional

def update_and_check(hr: Optional[float], spo2: Optional[float], temp: Optional[float]) -> List[str]:
    out: List[str] = []
    try:
        if hr is not None and (hr < 45 or hr > 150):
            out.append(f"Unusual HR {int(hr)} bpm")
        if spo2 is not None and spo2 < 88:
            out.append(f"Unusual SpO₂ {int(spo2)}%")
        if temp is not None and (temp < 35.0 or temp > 39.5):
            out.append(f"Unusual Temp {temp:.1f}°C")
    except Exception:
        # don't let anomaly checks break ingestion
        pass
    return out
