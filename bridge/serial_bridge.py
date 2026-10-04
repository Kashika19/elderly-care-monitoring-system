import argparse, json, sys, time, os
import requests, serial
from serial.tools import list_ports
from dotenv import load_dotenv

load_dotenv()

ARDUINO_VIDS = {0x2341, 0x2A03}  # Arduino
INGEST_TOKEN = os.getenv("INGEST_TOKEN", "").strip()

def find_port(preferred=None):
    if preferred:
        return preferred
    for p in list_ports.comports():
        name = (p.description or "") + " " + (p.manufacturer or "")
        if ("Nano 33 BLE" in name) or (p.vid in ARDUINO_VIDS if p.vid else False):
            return p.device
    for p in list_ports.comports():
        if p.device.upper().startswith("COM") or "ttyACM" in p.device:
            return p.device
    return None

def open_serial(port, baud, attempts=5):
    last = None
    for _ in range(attempts):
        try:
            ser = serial.Serial(port, baudrate=baud, timeout=2, write_timeout=2)
            ser.reset_input_buffer(); ser.reset_output_buffer()
            ser.dtr = True; ser.rts = True; time.sleep(0.2)
            ser.dtr = False; ser.rts = False; time.sleep(0.3)
            return ser
        except Exception as e:
            last = e; time.sleep(0.8)
    raise last

def main():
    ap = argparse.ArgumentParser(description="Arduino JSON → Eldercare API")
    ap.add_argument("--port")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--url", default="http://127.0.0.1:8000/ingest")
    ap.add_argument("--device-id")
    ap.add_argument("--echo", action="store_true")
    args = ap.parse_args()

    port = find_port(args.port)
    if not port:
        print("[bridge] ERROR: no serial port found."); sys.exit(1)

    print(f"[bridge] Opening {port} @ {args.baud}")
    ser = open_serial(port, args.baud)
    print(f"[bridge] Posting to {args.url}")

    headers = {}
    if INGEST_TOKEN:
        headers["Authorization"] = f"Bearer {INGEST_TOKEN}"

    try:
        while True:
            raw = ser.readline()
            if not raw:
                if args.echo: print("[bridge] waiting for serial data...")
                continue
            line = raw.decode("utf-8", errors="ignore").strip()
            if args.echo: print(f"[bridge] <- {line}")
            if not line: continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            if args.device_id:
                data["device_id"] = args.device_id

            try:
                r = requests.post(args.url, json=data, headers=headers, timeout=5)
                if r.status_code != 200:
                    print(f"[bridge] POST {r.status_code}: {r.text[:200]}")
                else:
                    j = r.json()
                    print(f"[bridge] ok id={j.get('id')} hr={j.get('heart_rate')} "
                          f"spo2={j.get('spo2')} temp={j.get('temperature')} "
                          f"fall={j.get('fall_detected')}")
            except requests.RequestException as e:
                print(f"[bridge] POST error: {e}"); time.sleep(1)
    except KeyboardInterrupt:
        print("\n[bridge] Stopped.")
    finally:
        try: ser.close()
        except: pass

if __name__ == "__main__":
    main()
