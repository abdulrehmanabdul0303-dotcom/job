#!/usr/bin/env python
"""End-to-end test for JobPilot AI system."""
import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("[OK] Health check passed")
    return response.json()

def test_register():
    """Test user registration."""
    print("\n=== Testing User Registration ===")
    import time
    unique_id = int(time.time())
    user_data = {
        "email": f"e2etest{unique_id}@example.com",
        "password": "TestPass123!@",
        "full_name": "E2E Test User"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201
    print("[OK] Registration passed")
    return user_data

def test_login(user_data):
    """Test user login."""
    print("\n=== Testing User Login ===")
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    # Create a session to maintain cookies
    session = requests.Session()
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    body = response.json()
    print(f"Response: {body}")
    assert response.status_code == 200
    print(f"Cookies received: {session.cookies}")
    print("[OK] Login passed")
    return session

def test_auth_me(session):
    """Test /auth/me endpoint."""
    print("\n=== Testing /auth/me Endpoint ===")
    response = session.get(f"{BASE_URL}/auth/me")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("[OK] /auth/me passed")
    return response.json()

def main():
    try:
        print("Starting E2E Tests...")
        
        # Test health
        health = test_health()
        
        # Register user
        user_data = test_register()
        
        # Login
        session = test_login(user_data)
        
        # Test authenticated endpoint
        user = test_auth_me(session)
        
        print("\n" + "="*50)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("="*50)
        print("\nSystem is working correctly:")
        print(f"- Health: {health['status']}")
        print(f"- User registered: {user_data['email']}")
        print(f"- User authenticated: {user.get('email')}")
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
