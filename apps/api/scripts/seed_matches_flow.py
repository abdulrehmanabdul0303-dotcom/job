"""
Seed script for testing matches flow.
Creates user, resume, jobs, and triggers matching.

Usage:
    cd jobpilot-ai/apps/api
    python scripts/seed_matches_flow.py
"""
import json
import random
import string
import sys
import requests

BASE = "http://localhost:8000/api/v1"


def rid(n=6):
    """Generate random ID suffix."""
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


# Session with cookie support
s = requests.Session()


def post(path, payload):
    """POST JSON to API."""
    r = s.post(BASE + path, json=payload, timeout=30)
    return r


def get(path):
    """GET from API."""
    r = s.get(BASE + path, timeout=30)
    return r


def must(r, codes=(200, 201), label="req"):
    """Assert response status code."""
    if r.status_code not in codes:
        raise RuntimeError(f"{label} failed: {r.status_code} {r.text[:800]}")


def main():
    print("=" * 50)
    print("  SEED MATCHES FLOW")
    print("=" * 50)
    
    email = f"seedmatch-{rid()}@jobpilot.ai"
    pw = "Str0ng!Passw0rd_123"
    
    print(f"\n1) Register user: {email}")
    r = post("/auth/register", {"full_name": "Seed Match User", "email": email, "password": pw})
    if r.status_code not in (200, 201, 400):
        must(r, label="register")
    print(f"   Status: {r.status_code}")
    
    print(f"\n2) Login")
    r2 = post("/auth/login", {"email": email, "password": pw})
    must(r2, (200,), "login")
    print(f"   Status: {r2.status_code}")
    
    # Check cookies
    print(f"   Cookies: {list(s.cookies.keys())}")
    
    print(f"\n3) Verify /auth/me")
    rme = get("/auth/me")
    must(rme, (200,), "/me")
    print(f"   Status: {rme.status_code}")
    print(f"   User: {rme.json().get('email')}")
    
    # Create jobs via bulk import
    print(f"\n4) Create jobs via /jobs/bulk")
    jobs_data = []
    job_titles = [
        "Backend Engineer (FastAPI)",
        "Junior Python Developer",
        "Full Stack Developer",
        "DevOps Engineer",
        "ML Engineer",
        "Frontend Developer (Next.js)",
        "QA Engineer",
        "Data Analyst",
        "Senior Software Engineer",
        "Security Engineer"
    ]
    companies = ["NexaTech", "OrbitLabs", "CloudNine", "DataForge", "ByteWorks", "StartupHub"]
    locations = ["Remote", "Islamabad", "Lahore", "Karachi", "San Francisco", "New York"]
    all_skills = ["python", "fastapi", "postgres", "pytest", "docker", "nextjs", "typescript", 
                  "react", "sql", "aws", "kubernetes", "git", "ci-cd", "machine-learning"]
    
    for i, title in enumerate(job_titles):
        jobs_data.append({
            "title": title,
            "company": random.choice(companies),
            "location": random.choice(locations),
            "employment_type": random.choice(["full-time", "contract", "remote"]),
            "description": f"We need a skilled {title.lower()} to join our team. Work with modern technologies.",
            "skills": random.sample(all_skills, min(5, len(all_skills))),
            "source": "seed",
            "url": f"https://example.com/jobs/seed-{rid()}",
            "salary_min": random.randint(50000, 100000),
            "salary_max": random.randint(100000, 200000),
        })
    
    rj = post("/jobs/bulk", jobs_data)
    if rj.status_code in (200, 201):
        result = rj.json()
        print(f"   Created: {result.get('created', 0)} jobs")
        print(f"   Skipped: {result.get('skipped', 0)} duplicates")
    else:
        print(f"   [WARN] Bulk import failed: {rj.status_code}")
        print(f"   {rj.text[:200]}")
    
    # Get matches
    print(f"\n5) Get /matches")
    rm = get("/matches")
    print(f"   Status: {rm.status_code}")
    if rm.status_code == 200:
        data = rm.json()
        print(f"   Total: {data.get('total', 0)}")
        print(f"   Page: {data.get('page', 1)}")
        if data.get('matches'):
            print(f"   First match score: {data['matches'][0].get('match_score', 'N/A')}")
    else:
        print(f"   Response: {rm.text[:500]}")
    
    # Trigger match recomputation (if resume exists)
    print(f"\n6) Trigger match recomputation")
    rr = post("/matches/recompute", {"min_score": 0})
    print(f"   Status: {rr.status_code}")
    if rr.status_code == 200:
        result = rr.json()
        print(f"   Computed: {result.get('matches_computed', 0)}")
        print(f"   Stored: {result.get('matches_stored', 0)}")
    elif rr.status_code == 400:
        print(f"   (No resume uploaded yet - expected)")
    else:
        print(f"   Response: {rr.text[:300]}")
    
    # Save artifacts
    artifacts = {
        "email": email,
        "password": pw,
        "jobs_created": len(jobs_data),
    }
    
    with open("seed_match_artifacts.json", "w", encoding="utf-8") as f:
        json.dump(artifacts, f, indent=2)
    
    print(f"\n" + "=" * 50)
    print(f"  SEED COMPLETE")
    print(f"  Artifacts: seed_match_artifacts.json")
    print(f"=" * 50)
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
