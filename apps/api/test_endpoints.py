"""
Comprehensive API endpoint testing script.
Tests all major endpoints with detailed output.
"""
import requests
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10

# Test results
class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"✓ {test_name}")
    
    def add_fail(self, test_name: str, reason: str):
        self.total += 1
        self.failed += 1
        self.errors.append(f"{test_name}: {reason}")
        print(f"✗ {test_name}")
        print(f"  Reason: {reason}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        if self.total > 0:
            pass_rate = (self.passed / self.total) * 100
            print(f"Pass Rate: {pass_rate:.1f}%")
        print("="*60)
        
        if self.failed > 0:
            print("\nFailed Tests:")
            for error in self.errors:
                print(f"  • {error}")
        
        return self.failed == 0


results = TestResults()
access_token = None
refresh_token = None


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    expected_status: int = 200
) -> Optional[Dict]:
    """Make HTTP request and return JSON response."""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    headers["Content-Type"] = "application/json"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=TIMEOUT)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == expected_status:
            try:
                return response.json()
            except:
                return {"status": "ok"}
        else:
            raise Exception(f"Expected {expected_status}, got {response.status_code}: {response.text}")
    
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")


def test_health_checks():
    """Test health check endpoints."""
    print("\n1. HEALTH CHECK TESTS")
    print("-" * 60)
    
    try:
        make_request("GET", "/health", expected_status=200)
        results.add_pass("Health Check")
    except Exception as e:
        results.add_fail("Health Check", str(e))
    
    try:
        make_request("GET", "/health/detailed", expected_status=200)
        results.add_pass("Detailed Health Check")
    except Exception as e:
        results.add_fail("Detailed Health Check", str(e))


def test_authentication():
    """Test authentication endpoints."""
    global access_token, refresh_token
    
    print("\n2. AUTHENTICATION TESTS")
    print("-" * 60)
    
    # Register new user
    register_data = {
        "email": f"test.user.{datetime.now().timestamp()}@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = make_request("POST", "/auth/register", register_data, expected_status=201)
        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token")
        results.add_pass("Register User")
    except Exception as e:
        results.add_fail("Register User", str(e))
        return
    
    # Login with existing user
    login_data = {
        "email": "john.doe@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = make_request("POST", "/auth/login", login_data, expected_status=200)
        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token")
        results.add_pass("Login User")
    except Exception as e:
        results.add_fail("Login User", str(e))


def test_user_profile():
    """Test user profile endpoints."""
    if not access_token:
        print("\n3. USER PROFILE TESTS")
        print("-" * 60)
        print("⊘ Skipped (no access token)")
        return
    
    print("\n3. USER PROFILE TESTS")
    print("-" * 60)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        make_request("GET", "/auth/me", headers=headers, expected_status=200)
        results.add_pass("Get Current User")
    except Exception as e:
        results.add_fail("Get Current User", str(e))


def test_token_refresh():
    """Test token refresh endpoint."""
    if not refresh_token:
        print("\n4. TOKEN REFRESH TESTS")
        print("-" * 60)
        print("⊘ Skipped (no refresh token)")
        return
    
    print("\n4. TOKEN REFRESH TESTS")
    print("-" * 60)
    
    refresh_data = {"refresh_token": refresh_token}
    
    try:
        response = make_request("POST", "/auth/refresh", refresh_data, expected_status=200)
        results.add_pass("Refresh Token")
    except Exception as e:
        results.add_fail("Refresh Token", str(e))


def test_resumes():
    """Test resume endpoints."""
    if not access_token:
        print("\n5. RESUME TESTS")
        print("-" * 60)
        print("⊘ Skipped (no access token)")
        return
    
    print("\n5. RESUME TESTS")
    print("-" * 60)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        make_request("GET", "/resume", headers=headers, expected_status=200)
        results.add_pass("Get User Resumes")
    except Exception as e:
        results.add_fail("Get User Resumes", str(e))


def test_preferences():
    """Test user preferences endpoints."""
    if not access_token:
        print("\n6. USER PREFERENCES TESTS")
        print("-" * 60)
        print("⊘ Skipped (no access token)")
        return
    
    print("\n6. USER PREFERENCES TESTS")
    print("-" * 60)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get preferences
    try:
        make_request("GET", "/preferences", headers=headers, expected_status=200)
        results.add_pass("Get User Preferences")
    except Exception as e:
        results.add_fail("Get User Preferences", str(e))
    
    # Update preferences
    prefs_data = {
        "job_titles": ["Senior Engineer", "Tech Lead"],
        "locations": ["San Francisco", "Remote"],
        "work_types": ["full-time"],
        "min_salary": 150000,
        "max_salary": 250000,
        "currency": "USD",
        "remote_preference": "hybrid",
        "auto_apply_enabled": True,
        "auto_apply_threshold": 75
    }
    
    try:
        make_request("PUT", "/preferences", prefs_data, headers=headers, expected_status=200)
        results.add_pass("Update Preferences")
    except Exception as e:
        results.add_fail("Update Preferences", str(e))


def test_jobs():
    """Test jobs endpoints."""
    print("\n7. JOBS TESTS")
    print("-" * 60)
    
    # Get all jobs
    try:
        response = make_request("GET", "/jobs", expected_status=200)
        total_jobs = response.get("total", 0)
        results.add_pass(f"Get All Jobs (Total: {total_jobs})")
    except Exception as e:
        results.add_fail("Get All Jobs", str(e))
    
    # Get jobs with filters
    try:
        make_request("GET", "/jobs?title=Engineer&page=1&page_size=10", expected_status=200)
        results.add_pass("Get Jobs with Filters")
    except Exception as e:
        results.add_fail("Get Jobs with Filters", str(e))
    
    # Get job sources
    try:
        response = make_request("GET", "/jobs/sources", expected_status=200)
        total_sources = len(response.get("sources", []))
        results.add_pass(f"Get Job Sources (Total: {total_sources})")
    except Exception as e:
        results.add_fail("Get Job Sources", str(e))


def test_job_matches():
    """Test job matches endpoints."""
    if not access_token:
        print("\n8. JOB MATCHES TESTS")
        print("-" * 60)
        print("⊘ Skipped (no access token)")
        return
    
    print("\n8. JOB MATCHES TESTS")
    print("-" * 60)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get matches
    try:
        response = make_request("GET", "/matches", headers=headers, expected_status=200)
        total_matches = response.get("total", 0)
        results.add_pass(f"Get Job Matches (Total: {total_matches})")
    except Exception as e:
        results.add_fail("Get Job Matches", str(e))
    
    # Get matches with filters
    try:
        make_request("GET", "/matches?status=unreviewed&page=1&page_size=10", headers=headers, expected_status=200)
        results.add_pass("Get Matches with Filters")
    except Exception as e:
        results.add_fail("Get Matches with Filters", str(e))


def test_apply_kits():
    """Test apply kit endpoints."""
    if not access_token:
        print("\n9. APPLY KIT TESTS")
        print("-" * 60)
        print("⊘ Skipped (no access token)")
        return
    
    print("\n9. APPLY KIT TESTS")
    print("-" * 60)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get apply kits
    try:
        response = make_request("GET", "/apply/kits", headers=headers, expected_status=200)
        total_kits = len(response.get("kits", []))
        results.add_pass(f"Get Apply Kits (Total: {total_kits})")
    except Exception as e:
        results.add_fail("Get Apply Kits", str(e))
    
    # Create apply kit
    kit_data = {
        "name": "Test Apply Kit",
        "description": "Test kit for API testing",
        "cover_letter_template": "Dear Hiring Manager,\n\nI am interested in this position...",
        "is_default": False
    }
    
    try:
        make_request("POST", "/apply/kits", kit_data, headers=headers, expected_status=201)
        results.add_pass("Create Apply Kit")
    except Exception as e:
        results.add_fail("Create Apply Kit", str(e))


def test_notifications():
    """Test notification endpoints."""
    if not access_token:
        print("\n10. NOTIFICATIONS TESTS")
        print("-" * 60)
        print("⊘ Skipped (no access token)")
        return
    
    print("\n10. NOTIFICATIONS TESTS")
    print("-" * 60)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get notification settings
    try:
        make_request("GET", "/notifications/settings", headers=headers, expected_status=200)
        results.add_pass("Get Notification Settings")
    except Exception as e:
        results.add_fail("Get Notification Settings", str(e))
    
    # Update notification settings
    notif_data = {
        "email_on_match": True,
        "email_on_application": True,
        "email_on_response": True,
        "email_digest_frequency": "daily",
        "push_notifications_enabled": True,
        "sms_notifications_enabled": False
    }
    
    try:
        make_request("PUT", "/notifications/settings", notif_data, headers=headers, expected_status=200)
        results.add_pass("Update Notification Settings")
    except Exception as e:
        results.add_fail("Update Notification Settings", str(e))
    
    # Get notification logs
    try:
        response = make_request("GET", "/notifications/logs", headers=headers, expected_status=200)
        total_logs = response.get("total", 0)
        results.add_pass(f"Get Notification Logs (Total: {total_logs})")
    except Exception as e:
        results.add_fail("Get Notification Logs", str(e))


def main():
    """Run all tests."""
    print("="*60)
    print("JobPilot AI - API Endpoint Testing")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Run all test suites
    test_health_checks()
    test_authentication()
    test_user_profile()
    test_token_refresh()
    test_resumes()
    test_preferences()
    test_jobs()
    test_job_matches()
    test_apply_kits()
    test_notifications()
    
    # Print summary
    success = results.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
