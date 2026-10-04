# Code Manifest – ElderCare Monitoring System

## Overview
This document provides a mapping of the project structure, explaining the purpose of each main file and folder.

## Project Structure
- **api/** → Backend FastAPI application
  - `main.py` → Main API entry point
  - `models.py` → Database ORM models
  - `database.py` → Database connection and session
  - `schemas.py` → Pydantic schemas for data validation
  - `anomaly.py` → Anomaly detection logic
  - `requirements.txt` → Python dependencies

- **bridge/** → Arduino/Serial bridge scripts
  - `serial_bridge.py` → Reads sensor data from Arduino and sends to API

- **web-dashboard/** → Frontend (vanilla JavaScript and Vite)
  - `src/main.js` → Dashboard behaviour, charting, simulation, and routing
  - `src/style.css` → Global CSS styles
  - `public/` → Static files

- **docs/** → Documentation
  - `CODE_MANIFEST.md` → Code overview
  - `traceability.md` → Requirements traceability

- **api/tests/** → Automated tests for backend API

## Environment
- `.env` → Local environment variables (excluded from the repository)
- `.env.example` → Example env file for setup

## Database
- `eldercare.db` → Local SQLite database file (excluded from the repository)
