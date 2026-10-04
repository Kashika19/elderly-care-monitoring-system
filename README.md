# ElderCare Monitoring System

> **Status:** Portfolio prototype using synthetic data

A full-stack monitoring prototype that accepts simulated or serial sensor readings, stores recent observations, raises rule-based alerts, and presents live metrics in a browser dashboard.

This project demonstrates systems integration, API development, data validation, monitoring workflows, requirements traceability, and responsible handling of health-related information. It is an educational prototype, not a medical device, diagnostic system, or substitute for professional care.

## Features

- FastAPI service for heart rate, oxygen saturation, temperature, and fall readings
- SQLite persistence with configurable retention limits
- Threshold and rule-based anomaly alerts
- Live Chart.js dashboard and metric cards
- CSV exports for readings and alerts
- Optional bearer-token protection for sensor ingestion
- Optional Twilio SMS integration with safe simulated fallback
- Arduino serial bridge and software device simulator
- API tests and a requirements traceability matrix

## Technology

- Python and FastAPI
- SQLAlchemy and SQLite
- Pydantic
- JavaScript, Vite, and Chart.js
- Pytest
- Arduino-compatible serial integration

## Architecture

```text
Sensor or simulator
        |
        v
Serial bridge / HTTP client
        |
        v
FastAPI ingestion and alert rules
        |
        +--> SQLite persistence
        |
        +--> CSV reports and optional SMS
        |
        v
Vite dashboard
```

## Run locally

### API

```bash
python -m venv .venv
# Activate the virtual environment for your operating system
pip install -r api/requirements.txt
copy .env.example .env
uvicorn api.main:app --reload
```

The API and interactive documentation are available at `http://127.0.0.1:8000` and `http://127.0.0.1:8000/docs`.

### Dashboard

```bash
cd web-dashboard
npm install
copy .env.example .env
npm run dev
```

### Generate synthetic readings

```bash
python web-dashboard/simulate_device.py --interval 2
```

If an ingestion token is enabled, set the same `INGEST_TOKEN` for the simulator or serial bridge and `VITE_INGEST_TOKEN` for the dashboard demonstration.

## Testing

```bash
pytest api/tests
cd web-dashboard
npm run build
```

## Privacy and safety

- No real patient, resident, carer, or contact information is included.
- The committed repository excludes environment files, credentials, local databases, exports, dependencies, and caches.
- Demonstration readings are synthetic and may include intentionally abnormal values.
- The browser access screen is an explicitly labelled local demonstration, not secure authentication.
- Production use would require clinical validation, secure identity and access management, encryption, audit logging, consent and retention controls, resilient alert delivery, and regulatory review.

## Current limitations

- Alert detection uses transparent thresholds and simple rules rather than a trained machine-learning model.
- The default database is local SQLite.
- Live Server-Sent Events are implemented by the API but are not yet connected to the dashboard.
- SMS delivery is optional and requires separately managed credentials.
- Automated frontend and end-to-end test coverage remains limited.

## Repository structure

```text
api/                    FastAPI service, database models, rules, and tests
bridge/                 Arduino serial-to-HTTP bridge
docs/                   Code manifest and requirements traceability
web-dashboard/          Vite and Chart.js frontend plus simulator
.env.example            Safe configuration template
```

## Portfolio context

The project focuses on the full monitoring workflow: requirements, device ingestion, validation, storage, alerting, reporting, user interface design, testing, and privacy-aware documentation.
