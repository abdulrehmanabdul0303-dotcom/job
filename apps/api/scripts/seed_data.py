"""
Seed data script for JobPilot AI.
Creates test users, jobs, and validates cookie auth flow.
"""
import argparse
import json
import random
import string
from dataclasses import dataclass
from typing import Dict, List

import requests


def randid(n: int = 6) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


@dataclass
class SeedUser:
    full_name: str
    email: str
    password: str


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.s = requests.Session()  # keeps cookies automatically

    def post(self, path: str, payload: Dict) -> requests.Response:
        url = f"{self.base_url}{path}"
        res = self.s.post(url, json=payload, timeout=30)
        return res

    def get(self, path: str) -> requests.Response:
        url = f"{self.base_url}{path}"
        res = self.s.get(url, timeout=30)
        return res


def must(res: requests.Response, ok_codes=(200, 201), label="request"):
    if res.status_code not in ok_codes:
        raise RuntimeError(
            f"{label} failed: {res.status_code}\n"
            f"URL: {res.url}\n"
            f"BODY: {res.text[:1000]}"
        )


def seed_users(api: ApiClient, email_prefix: str, count: int) -> List[SeedUser]:
    users: List[SeedUser] = []
    for i in range(count):
        email = f"{email_prefix}{i+1}-{randid()}@jobpilot.ai"
        user = SeedUser(
            full_name=f"Seed User {i+1}",
            email=email,
            password="Str0ng!Passw0rd_123",
        )

        # register (matches your UserCreate schema)
        res = api.post("/auth/register", {
            "email": user.email, 
            "password": user.password,
            "full_name": user.full_name
        })
        if res.status_code in (200, 201):
            print(f"  ✅ Registered: {user.email}")
        elif res.status_code == 400 and "already" in res.text.lower():
            print(f"  ⚠️ Already exists: {user.email}")
        else:
            print(f"  ❌ Register failed ({res.status_code}): {res.text[:200]}")
            continue

        # login (critical for cookie)
        res2 = api.post("/auth/login", {"email": user.email, "password": user.password})
        if res2.status_code != 200:
            print(f"  ❌ Login failed ({res2.status_code}): {res2.text[:200]}")
            continue

        # Check Set-Cookie header
        if "set-cookie" in res2.headers:
            print(f"  ✅ Cookie set on login")
        else:
            print(f"  ⚠️ No Set-Cookie header on login")

        # /me must work
        res3 = api.get("/auth/me")
        if res3.status_code == 200:
            print(f"  ✅ /me works with cookie")
        else:
            print(f"  ❌ /me failed ({res3.status_code}): {res3.text[:200]}")

        users.append(user)
    return users


def seed_jobs(api: ApiClient, count: int) -> List[Dict]:
    """
    Try to create jobs if the endpoint exists.
    Your API may have different job creation endpoints.
    """
    titles = [
        "Junior Python Developer",
        "Backend Engineer (FastAPI)",
        "Frontend Engineer (Next.js)",
        "Data Analyst",
        "ML Engineer (NLP)",
        "DevOps Engineer",
        "Full Stack Developer",
        "Senior Software Engineer",
    ]
    companies = ["Acme", "ByteWorks", "CloudNine", "DataForge", "NexaTech", "OrbitLabs"]
    locations = ["Remote", "Islamabad", "Lahore", "Karachi", "New York", "San Francisco"]

    created: List[Dict] = []
    for i in range(count):
        title = random.choice(titles)
        company = random.choice(companies)
        payload = {
            "title": title,
            "company": company,
            "location": random.choice(locations),
            "employment_type": random.choice(["full-time", "internship", "contract"]),
            "description": f"{title} role at {company}. Must know APIs, SQL, testing.",
            "skills": random.sample(["python", "fastapi", "sql", "postgres", "docker", "nextjs", "typescript", "pytest"], k=4),
            "source": "seed",
            "url": f"https://example.com/jobs/{company.lower()}-{randid()}",
        }

        # Try common patterns
        res = api.post("/jobs", payload)
        if res.status_code in (200, 201):
            try:
                created.append(res.json())
                print(f"  ✅ Created job: {title} at {company}")
            except Exception:
                created.append({"raw": res.text})
        else:
            # Job creation may not be available via API
            if i == 0:
                print(f"  ⚠️ Job creation endpoint not available ({res.status_code})")
            break

    return created


def run_smoke(api: ApiClient):
    """Run basic health checks."""
    res = api.get("/health")
    if res.status_code == 200:
        print("✅ /health OK")
    else:
        print(f"⚠️ /health returned {res.status_code}")


def main():
    ap = argparse.ArgumentParser(description="Seed JobPilot AI with test data")
    ap.add_argument("--base-url", default="http://localhost:8000/api/v1")
    ap.add_argument("--users", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--email-prefix", default="seed")
    args = ap.parse_args()

    print("=== JOBPILOT SEED SCRIPT ===")
    print(f"Base URL: {args.base_url}")
    print("")

    api = ApiClient(args.base_url)
    
    print("[SMOKE] Health check...")
    run_smoke(api)
    print("")

    print(f"[SEED] Creating {args.users} users + validating cookie auth via /me ...")
    users = seed_users(api, args.email_prefix, args.users)
    print(f"[SEED] Users created: {len(users)}")
    print("")

    print(f"[SEED] Creating {args.jobs} jobs (if endpoint exists) ...")
    jobs = seed_jobs(api, args.jobs)
    print(f"[SEED] Jobs attempted/created: {len(jobs)}")
    print("")

    # Write artifact
    out = {
        "base_url": args.base_url,
        "users": [{"email": u.email, "password": u.password, "full_name": u.full_name} for u in users],
        "jobs": jobs[:10],
    }
    with open("seed_artifacts.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print("[SEED] Done. Wrote seed_artifacts.json")


if __name__ == "__main__":
    main()
