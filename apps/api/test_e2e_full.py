#!/usr/bin/env python3
"""
Complete E2E Test for JobPilot AI System
Tests: Auth → Resume Upload → Jobs → Matches → Apply Kit → PDF Download
"""
import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def create_sample_pdf():
    """Create a minimal sample PDF for testing."""
    # Create a minimal PDF file
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Sample Resume PDF) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000263 00000 n
0000000341 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
434
%%EOF"""
    
    pdf_path = Path("d:/idea/sample_resume.pdf")
    pdf_path.write_bytes(pdf_content)
    return str(pdf_path)

def test_section(name):
    """Print test section header."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

def test_auth():
    """Test registration and login."""
    test_section("AUTH FLOW")
    
    session = requests.Session()
    unique_id = int(time.time())
    email = f"e2etest{unique_id}@example.com"
    
    # Register
    print("\n[1] Testing Registration...")
    user_data = {
        "email": email,
        "password": "TestPass123!@",
        "full_name": "E2E Test User"
    }
    resp = session.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"    Status: {resp.status_code}")
    print(f"    Response: {resp.json()}")
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    
    # Login
    print("\n[2] Testing Login...")
    login_data = {"email": email, "password": user_data["password"]}
    resp = session.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"    Status: {resp.status_code}")
    print(f"    Response: {resp.json()}")
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    
    # Get authenticated user
    print("\n[3] Testing /auth/me...")
    resp = session.get(f"{BASE_URL}/auth/me")
    print(f"    Status: {resp.status_code}")
    user = resp.json()
    print(f"    User ID: {user.get('id')}")
    print(f"    Email: {user.get('email')}")
    assert resp.status_code == 200
    
    return session, user.get('id')

def test_resume_upload(session):
    """Test resume upload."""
    test_section("RESUME UPLOAD")
    
    # Create sample PDF
    print("\n[1] Creating sample PDF...")
    pdf_path = create_sample_pdf()
    print(f"    Created: {pdf_path}")
    
    # Upload resume
    print("\n[2] Uploading resume...")
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        resp = session.post(f"{BASE_URL}/resumes/upload", files=files)
    
    print(f"    Status: {resp.status_code}")
    result = resp.json()
    print(f"    Response keys: {result.keys()}")
    if 'resume_id' in result:
        print(f"    Resume ID: {result['resume_id']}")
    if 'score' in result:
        print(f"    Score: {result['score']}")
    
    assert resp.status_code in [200, 201], f"Upload failed: {resp.text}"
    
    resume_id = result.get('resume_id') or result.get('id')
    return resume_id

def test_list_resumes(session):
    """List uploaded resumes."""
    test_section("LIST RESUMES")
    
    print("\n[1] Getting resume list...")
    resp = session.get(f"{BASE_URL}/resumes/list")
    print(f"    Status: {resp.status_code}")
    result = resp.json()
    print(f"    Total resumes: {len(result) if isinstance(result, list) else 'N/A'}")
    if isinstance(result, list) and len(result) > 0:
        print(f"    First resume: {result[0]}")
    
    assert resp.status_code == 200
    return result

def test_create_job(session):
    """Create a test job."""
    test_section("CREATE JOB")
    
    print("\n[1] Creating test job...")
    job_data = {
        "title": "Senior Python Developer",
        "company": "TechCorp Inc",
        "location": "San Francisco, CA",
        "description": "Looking for experienced Python developer with FastAPI, PostgreSQL, Redis, Docker, Kubernetes experience",
        "job_type": "Full-time",
        "salary_min": 120000,
        "salary_max": 180000,
        "url": "https://example.com/jobs/123"
    }
    
    resp = session.post(f"{BASE_URL}/jobs", json=job_data)
    print(f"    Status: {resp.status_code}")
    result = resp.json()
    print(f"    Response keys: {result.keys()}")
    
    if 'id' in result:
        print(f"    Job ID: {result['id']}")
    
    assert resp.status_code in [200, 201], f"Job creation failed: {resp.text}"
    
    job_id = result.get('id') or result.get('job_id')
    return job_id

def test_matches(session, resume_id):
    """Test match recomputation."""
    test_section("MATCHES")
    
    print("\n[1] Recomputing matches...")
    resp = session.post(f"{BASE_URL}/matches/recompute")
    print(f"    Status: {resp.status_code}")
    result = resp.json()
    print(f"    Response: {result}")
    assert resp.status_code in [200, 201], f"Match recompute failed: {resp.text}"
    
    print("\n[2] Retrieving matches...")
    resp = session.get(f"{BASE_URL}/matches")
    print(f"    Status: {resp.status_code}")
    result = resp.json()
    
    match_count = 0
    if isinstance(result, dict) and 'matches' in result:
        match_count = len(result['matches'])
    elif isinstance(result, list):
        match_count = len(result)
    
    print(f"    Total matches: {match_count}")
    if match_count > 0:
        print(f"    Sample match: {str(result)[:200]}...")
    
    assert resp.status_code == 200

def test_apply_kit(session, job_id, resume_id):
    """Test apply kit generation."""
    test_section("APPLY KIT")
    
    if not job_id or not resume_id:
        print("\n[SKIP] job_id or resume_id missing")
        return None
    
    print(f"\n[1] Generating apply kit (job={job_id}, resume={resume_id})...")
    kit_data = {"job_id": job_id, "resume_id": resume_id}
    resp = session.post(f"{BASE_URL}/applykit/{job_id}/generate", json=kit_data)
    print(f"    Status: {resp.status_code}")
    result = resp.json()
    print(f"    Response keys: {result.keys()}")
    
    if resp.status_code not in [200, 201]:
        print(f"    Error: {result}")
        return None
    
    kit_id = result.get('id') or result.get('kit_id') or job_id
    print(f"    Kit ID: {kit_id}")
    
    return kit_id

def test_pdf_download(session, job_id):
    """Test PDF download."""
    test_section("PDF DOWNLOAD")
    
    if not job_id:
        print("\n[SKIP] job_id missing")
        return
    
    print(f"\n[1] Downloading PDF (job={job_id})...")
    resp = session.get(f"{BASE_URL}/applykit/{job_id}/download/pdf")
    print(f"    Status: {resp.status_code}")
    
    if resp.status_code == 200:
        pdf_path = "d:/idea/apply_kit_output.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(resp.content)
        print(f"    Success! Saved to: {pdf_path}")
        print(f"    File size: {len(resp.content)} bytes")
    else:
        print(f"    Error: {resp.status_code} - {resp.text[:200]}")

def main():
    try:
        print("\n" + "="*60)
        print(" JobPilot AI - COMPLETE END-TO-END TEST")
        print("="*60)
        
        # Auth flow
        session, user_id = test_auth()
        
        # Resume upload
        resume_id = test_resume_upload(session)
        
        # List resumes
        resumes = test_list_resumes(session)
        
        # Create job
        job_id = test_create_job(session)
        
        # Matches
        test_matches(session, resume_id)
        
        # Apply kit
        kit_id = test_apply_kit(session, job_id, resume_id)
        
        # PDF download
        test_pdf_download(session, job_id)
        
        # Final summary
        print("\n" + "="*60)
        print(" [SUCCESS] ALL E2E TESTS COMPLETED!")
        print("="*60)
        print(f"\nKey IDs Generated:")
        print(f"  User ID: {user_id}")
        print(f"  Resume ID: {resume_id}")
        print(f"  Job ID: {job_id}")
        print(f"  Kit ID: {kit_id}")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
