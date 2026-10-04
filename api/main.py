from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from statistics import mean
from typing import Dict, Any, List
import asyncio, datetime, json, os, io, csv

from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Reading, Alert
from .schemas import ReadingIn
from .anomaly import update_and_check

# ---------- Config ----------
load_dotenv()

API_TITLE    = os.getenv("API_TITLE", "ElderCare Monitoring API")
API_VERSION  = os.getenv("API_VERSION", "0.3.0")
INGEST_TOKEN = os.getenv("INGEST_TOKEN", "").strip()

HR_WARN   = float(os.getenv("HR_WARN",   "120"))
SPO2_CRIT = float(os.getenv("SPO2_CRIT", "92"))
TEMP_WARN = float(os.getenv("TEMP_WARN", "38.2"))

MAX_READINGS = int(os.getenv("MAX_READINGS", "2000"))
MAX_ALERTS   = int(os.getenv("MAX_ALERTS",   "500"))

app = FastAPI(title=API_TITLE, version=API_VERSION)

# Allow Vite dev server on any localhost port
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d{4}",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables on startup
@app.on_event("startup")
def _create_tables():
    Base.metadata.create_all(bind=engine)

# ---------- SSE state ----------
latest_data: Dict[str, Any] = {}
alerts_mem: List[str] = []
subscribers: List[asyncio.Queue] = []

# ---------- Helpers ----------
def require_token(req: Request):
    """Simple bearer token guard for /ingest."""
    if not INGEST_TOKEN:
        return
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != INGEST_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

def trim_tables(db: Session):
    """Keep only the most recent N rows (SQLite-friendly)."""
    last = db.query(Reading).order_by(Reading.id.desc()).first()
    if last and last.id > MAX_READINGS:
        db.query(Reading).filter(Reading.id < (last.id - MAX_READINGS)).delete()
    lasta = db.query(Alert).order_by(Alert.id.desc()).first()
    if lasta and lasta.id > MAX_ALERTS:
        db.query(Alert).filter(Alert.id < (lasta.id - MAX_ALERTS)).delete()
    db.commit()

def sms_notify(msg: str):
    """Optional SMS via Twilio; if not configured, just print."""
    sid = os.getenv("TWILIO_ACCT_SID")
    tok = os.getenv("TWILIO_AUTH_TOKEN")
    _from = os.getenv("TWILIO_FROM")
    to = os.getenv("ALERT_SMS_TO")
    if not (sid and tok and _from and to):
        print(f"[SMS simulated] {msg}")
        return
    try:
        from twilio.rest import Client
        Client(sid, tok).messages.create(body=msg, from_=_from, to=to)
    except Exception as e:
        print("[SMS error]", e)

# ---------- Routes ----------
@app.get("/health")
def health():
    return {"ok": True, "time": datetime.datetime.now().isoformat()}

@app.post("/ingest")
async def ingest(payload: ReadingIn, request: Request, db: Session = Depends(get_db)):
    require_token(request)

    # persist
    r = Reading(**payload.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    trim_tables(db)

    # live packet
    ts = datetime.datetime.now().isoformat()
    data = {
        "id": r.id,
        "device_id": r.device_id,
        "heart_rate": r.heart_rate,
        "spo2": r.spo2,
        "temperature": r.temperature,
        "fall_detected": r.fall_detected,
        "timestamp": ts,
        "created_at": r.created_at.isoformat() if r.created_at else ts,
    }
    global latest_data
    latest_data = data

    # rule thresholds
    def add_alert(msg: str, type_: str, severity: str):
        db.add(Alert(device_id=r.device_id, type=type_, severity=severity, message=msg))
        alerts_mem.append(f"[{ts}] {msg}")

    if r.heart_rate is not None and r.heart_rate >= HR_WARN:
        add_alert(f"⚠️ High HR {int(r.heart_rate)} bpm", "heart_rate", "warn")

    if r.spo2 is not None and r.spo2 < SPO2_CRIT:
        m = f"🚨 CRITICAL Low SpO₂ {int(r.spo2)}%"
        add_alert(m, "spo2", "critical")
        sms_notify(m)

    if r.temperature is not None and r.temperature >= TEMP_WARN:
        add_alert(f"⚠️ High Temp {r.temperature:.1f}°C", "temperature", "warn")

    if r.fall_detected:
        m = "🚨 Fall detected!"
        add_alert(m, "fall", "critical")
        sms_notify(m)

    # Additional rule-based anomaly checks
    for m in update_and_check(r.heart_rate, r.spo2, r.temperature):
        add_alert(f"Anomaly: {m}", "anomaly", "warn")

    db.commit()

    # push to SSE subscribers
    for q in list(subscribers):
        try:
            await q.put(data)
        except Exception:
            pass

    return data

@app.get("/events")
async def events(request: Request):
    async def gen():
        q: asyncio.Queue = asyncio.Queue()
        subscribers.append(q)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield "data: {}\n\n"   # keepalive
                else:
                    yield f"data: {json.dumps(data)}\n\n"
        finally:
            subscribers.remove(q)
    return StreamingResponse(gen(), media_type="text/event-stream")

@app.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    rows = db.query(Alert).order_by(Alert.id.desc()).limit(100).all()
    return [
        {
            "id": alert.id,
            "device_id": alert.device_id,
            "type": alert.type,
            "severity": alert.severity,
            "message": alert.message,
            "created_at": alert.created_at.isoformat() if alert.created_at else "",
        }
        for alert in rows
    ]

@app.delete("/alerts")
def clear_alerts(db: Session = Depends(get_db)):
    alerts_mem.clear()
    db.query(Alert).delete()
    db.commit()
    return {"status": "cleared"}

@app.get("/export/readings.csv")
def export_readings_csv(n: int = 500, db: Session = Depends(get_db)):
    rows = db.query(Reading).order_by(Reading.id.desc()).limit(n).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id","device_id","heart_rate","spo2","temperature","fall_detected","created_at"])
    for r in reversed(rows):   # chronological
        w.writerow([
            r.id, r.device_id, r.heart_rate, r.spo2, r.temperature,
            1 if r.fall_detected else 0,
            r.created_at.isoformat() if r.created_at else ""
        ])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=readings.csv"})

@app.get("/export/alerts.csv")
def export_alerts_csv(n: int = 500, db: Session = Depends(get_db)):
    rows = db.query(Alert).order_by(Alert.id.desc()).limit(n).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id","device_id","type","severity","message","created_at"])
    for a in reversed(rows):
        w.writerow([
            a.id, a.device_id, a.type, a.severity, a.message,
            a.created_at.isoformat() if a.created_at else ""
        ])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=alerts.csv"})

@app.get("/stats")
def stats(n: int = 200, db: Session = Depends(get_db)):
    q = db.query(Reading).order_by(Reading.id.desc()).limit(n).all()
    def col(get):
        vals = [get(r) for r in q if get(r) is not None]
        return None if not vals else {
            "min": min(vals), "max": max(vals), "avg": round(mean(vals), 2), "count": len(vals)
        }
    return {
        "window": len(q),
        "heart_rate": col(lambda r: r.heart_rate),
        "spo2": col(lambda r: r.spo2),
        "temperature": col(lambda r: r.temperature),
        "falls_in_window": sum(1 for r in q if r.fall_detected),
    }

@app.get("/version")
def version():
    return {"title": API_TITLE, "version": API_VERSION}
