# simulate_device.py
import time, random, argparse, requests, os
from datetime import datetime

def rand(a, b, dp=1):
    return round(random.uniform(a, b), dp)

def make_reading(device_id, tick):
    """Mostly normal values, with occasional anomalies."""
    # baseline normal
    hr  = rand(70, 90, 0)
    sp  = rand(96, 99, 0)
    tmp = rand(36.4, 37.2, 1)
    fall = False

    # every ~7th reading, inject a random anomaly
    if tick % 7 == 0:
        which = random.choice(["high_hr", "low_spo2", "fever", "fall"])
        if which == "high_hr":
            hr = rand(130, 160, 0)
        elif which == "low_spo2":
            sp = rand(85, 91, 0)
        elif which == "fever":
            tmp = rand(38.3, 39.5, 1)
        elif which == "fall":
            fall = True

    return {
        "device_id": device_id,
        "heart_rate": hr,
        "spo2": sp,
        "temperature": tmp,
        "fall_detected": fall
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.getenv("ELDERCARE_API", "http://127.0.0.1:8000"),
                    help="Base URL of the API (default: http://127.0.0.1:8000)")
    ap.add_argument("--device", default="nano33ble-001", help="Device ID")
    ap.add_argument("--interval", type=float, default=2.0, help="Seconds between readings")
    args = ap.parse_args()

    ingest_url = f"{args.url.rstrip('/')}/ingest"
    token = os.getenv("INGEST_TOKEN", "").strip()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    print(f"[sim] posting to {ingest_url} every {args.interval}s — Ctrl+C to stop")

    tick = 1
    try:
        while True:
            reading = make_reading(args.device, tick)
            r = requests.post(ingest_url, json=reading, headers=headers, timeout=5)
            ok = "OK" if r.status_code == 200 else f"ERR {r.status_code}"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {ok}  {reading}")
            tick += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[sim] stopped.")

if __name__ == "__main__":
    main()
