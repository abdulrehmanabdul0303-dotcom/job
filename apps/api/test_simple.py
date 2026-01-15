#!/usr/bin/env python
"""Simple endpoint check"""
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

try:
    print("Testing health endpoint...")
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"Health: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"Error: {e}")
