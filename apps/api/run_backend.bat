#!/bin/bash
cd d:\idea\jobpilot-ai\apps\api
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
