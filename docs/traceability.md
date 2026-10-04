# Requirements Traceability Matrix – ElderCare Monitoring System

| Requirement ID | Requirement Description                                  | Implemented In         | Verified By            |
|----------------|----------------------------------------------------------|------------------------|------------------------|
| R1             | System must ingest sensor data (HR, SpO2, Temp, Fall)    | `api/main.py`, `bridge/serial_bridge.py` | API Tests, Simulation |
| R2             | Data must be stored in a database                        | `api/database.py`, `api/models.py` | Database queries |
| R3             | Alerts must be raised if thresholds are exceeded         | `api/anomaly.py`, `api/main.py` | Unit tests, Alerts UI |
| R4             | User dashboard must show live data & alerts              | `web-dashboard/src/main.js` | Manual testing in browser |
| R5             | Data export as CSV for readings and alerts               | `api/main.py` | Tested via Swagger UI |
| R6             | Authentication for ingestion (token-based)               | `main.py`, `.env` | API test with token |
| R7             | Frontend should provide clearly labelled demonstration access | `web-dashboard/src/main.js` | Manual testing |
| R8             | Rule-based anomaly checks should flag abnormal readings  | `api/anomaly.py` | Unit tests |
