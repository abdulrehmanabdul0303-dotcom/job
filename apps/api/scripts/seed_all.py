"""
Comprehensive seed script for JobPilot AI.
Seeds users, jobs, and tests job matching functionality.
"""
import argparse
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests


@dataclass
class SeedUser:
    full_name: str
    email: str
    password: str
    profile: Optional[Dict] = None


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.s = requests.Session()

    def post(self, path: str, payload) -> requests.Response:
        url = f"{self.base_url}{path}"
        res = self.s.post(url, json=payload, timeout=30)
        return res

    def get(self, path: str) -> requests.Response:
        url = f"{self.base_url}{path}"
        res = self.s.get(url, timeout=30)
        return res


def load_sample_file(filename: str) -> List[Dict]:
    """Load sample data from JSON file."""
    # Try multiple paths
    paths = [
        Path(__file__).parent.parent.parent.parent / "samples" / filename,
        Path("samples") / filename,
        Path("../../samples") / filename,
    ]
    
    for path in paths:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    
    print(f"⚠️ Could not find {filename}")
    return []


def seed_users(api: ApiClient, users_data: List[Dict]) -> List[SeedUser]:
    """Seed users from sample data."""
    users: List[SeedUser] = []
    
    for user_data in users_data:
        user = SeedUser(
            full_name=user_data.get("full_name", "Test User"),
            email=user_data.get("email"),
            password=user_data.get("password", "Str0ng!Passw0rd_123"),
            profile=user_data.get("profile")
        )
        
        # Register
        res = api.post("/auth/register", {
            "email": user.email,
            "password": user.password,
            "full_name": user.full_name
        })
        
        if res.status_code in (200, 201):
            print(f"  ✅ Registered: {user.email}")
        elif res.status_code == 400 and "already" in res.text.lower():
            print(f"  ⚠️ Already exists: {user.email}")
            # Login to get session
            api.post("/auth/login", {"email": user.email, "password": user.password})
        else:
            print(f"  ❌ Register failed ({res.status_code}): {res.text[:200]}")
            continue
        
        # Verify /me works
        res_me = api.get("/auth/me")
        if res_me.status_code == 200:
            print(f"  ✅ Cookie auth verified for {user.email}")
        else:
            print(f"  ⚠️ /me failed for {user.email}")
        
        users.append(user)
    
    return users


def seed_jobs(api: ApiClient, jobs_data: List[Dict]) -> Dict:
    """Seed jobs using bulk import endpoint."""
    if not jobs_data:
        print("  ⚠️ No jobs data to seed")
        return {"created": 0, "skipped": 0}
    
    # Use bulk import endpoint
    res = api.post("/jobs/bulk", jobs_data)
    
    if res.status_code in (200, 201):
        result = res.json()
        print(f"  ✅ Bulk import: {result.get('created', 0)} created, {result.get('skipped', 0)} skipped")
        return result
    else:
        print(f"  ❌ Bulk import failed ({res.status_code}): {res.text[:200]}")
        
        # Fall back to individual creation
        print("  📝 Falling back to individual job creation...")
        created = 0
        for job in jobs_data:
            res = api.post("/jobs", job)
            if res.status_code in (200, 201):
                created += 1
        print(f"  ✅ Created {created} jobs individually")
        return {"created": created, "skipped": 0}


def test_job_matching(api: ApiClient, user_email: str) -> None:
    """Test job matching functionality."""
    print(f"\n[MATCHING] Testing job matching for {user_email}...")
    
    # Get jobs
    res = api.get("/jobs?page_size=5")
    if res.status_code == 200:
        data = res.json()
        jobs = data.get("jobs", [])
        print(f"  ✅ Found {len(jobs)} jobs")
        for job in jobs[:3]:
            print(f"     - {job.get('title')} at {job.get('company')}")
    else:
        print(f"  ❌ Failed to get jobs ({res.status_code})")
    
    # Try matches endpoint if it exists
    res = api.get("/matches")
    if res.status_code == 200:
        data = res.json()
        matches = data.get("matches", data) if isinstance(data, dict) else data
        print(f"  ✅ Found {len(matches) if isinstance(matches, list) else 'some'} matches")
    elif res.status_code == 404:
        print(f"  ⚠️ Matches endpoint not found (may need resume first)")
    else:
        print(f"  ⚠️ Matches returned {res.status_code}")


def run_health_check(api: ApiClient) -> bool:
    """Run health check."""
    res = api.get("/health")
    if res.status_code == 200:
        print("✅ Health check passed")
        return True
    else:
        print(f"❌ Health check failed ({res.status_code})")
        return False


def main():
    ap = argparse.ArgumentParser(description="Seed JobPilot AI with sample data")
    ap.add_argument("--base-url", default="http://localhost:8000/api/v1")
    ap.add_argument("--users-file", default="sample_users.json")
    ap.add_argument("--jobs-file", default="sample_jobs.json")
    ap.add_argument("--skip-users", action="store_true", help="Skip user seeding")
    ap.add_argument("--skip-jobs", action="store_true", help="Skip job seeding")
    ap.add_argument("--test-matching", action="store_true", help="Test job matching")
    args = ap.parse_args()

    print("=" * 50)
    print("JOBPILOT AI - COMPREHENSIVE SEED")
    print("=" * 50)
    print(f"Base URL: {args.base_url}")
    print("")

    api = ApiClient(args.base_url)
    
    # Health check
    if not run_health_check(api):
        print("⚠️ API may not be running. Continuing anyway...")
    print("")

    # Seed users
    users = []
    if not args.skip_users:
        print("[USERS] Loading sample users...")
        users_data = load_sample_file(args.users_file)
        if users_data:
            print(f"[USERS] Seeding {len(users_data)} users...")
            users = seed_users(api, users_data)
            print(f"[USERS] Seeded {len(users)} users")
        else:
            print("[USERS] No users file found, creating default user...")
            users = seed_users(api, [{
                "full_name": "Test User",
                "email": "test@jobpilot.ai",
                "password": "Str0ng!Passw0rd_123"
            }])
    print("")

    # Seed jobs
    if not args.skip_jobs:
        print("[JOBS] Loading sample jobs...")
        jobs_data = load_sample_file(args.jobs_file)
        if jobs_data:
            print(f"[JOBS] Seeding {len(jobs_data)} jobs...")
            # Need to be logged in to create jobs
            if users:
                api.post("/auth/login", {
                    "email": users[0].email,
                    "password": users[0].password
                })
            result = seed_jobs(api, jobs_data)
            print(f"[JOBS] Done: {result}")
        else:
            print("[JOBS] No jobs file found")
    print("")

    # Test matching
    if args.test_matching and users:
        test_job_matching(api, users[0].email)
    print("")

    # Summary
    print("=" * 50)
    print("SEED COMPLETE")
    print("=" * 50)
    print(f"Users: {len(users)}")
    print(f"Jobs: Check /api/v1/jobs for count")
    print("")
    print("Test credentials:")
    if users:
        print(f"  Email: {users[0].email}")
        print(f"  Password: {users[0].password}")


if __name__ == "__main__":
    main()
