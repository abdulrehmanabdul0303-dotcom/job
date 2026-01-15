"""
Seed database with sample data for testing.
Run this after initializing the database.
"""
import asyncio
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal
from app.models.user import User, Session, AuditLog
from app.models.resume import Resume, ResumeScorecard
from app.models.preferences import UserPreferences
from app.models.job import JobSource, JobPosting
from app.models.match import JobMatch
from app.models.apply import ApplyKit, JobActivity, ActivityStatus
from app.models.notification import NotificationSettings, NotificationLog
from app.services.auth import get_password_hash
import uuid
import json


async def seed_database():
    """Seed database with sample data."""
    async with AsyncSessionLocal() as db:
        try:
            print("Seeding database with sample data...")
            
            # 1. Create sample users
            print("\n1. Creating sample users...")
            user1 = User(
                id=str(uuid.uuid4()),
                email="john.doe@example.com",
                hashed_password=get_password_hash("TestPass123!"),
                full_name="John Doe",
                is_active=True,
                is_verified=True
            )
            user2 = User(
                id=str(uuid.uuid4()),
                email="jane.smith@example.com",
                hashed_password=get_password_hash("TestPass456!"),
                full_name="Jane Smith",
                is_active=True,
                is_verified=True
            )
            user3 = User(
                id=str(uuid.uuid4()),
                email="bob.wilson@example.com",
                hashed_password=get_password_hash("TestPass789!"),
                full_name="Bob Wilson",
                is_active=True,
                is_verified=False
            )
            
            db.add_all([user1, user2, user3])
            await db.flush()
            print(f"   ✓ Created 3 users")
            
            # 2. Create sessions (refresh tokens)
            print("\n2. Creating sample sessions...")
            session1 = Session(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                refresh_token="refresh_token_user1_" + str(uuid.uuid4()),
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            session2 = Session(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                refresh_token="refresh_token_user2_" + str(uuid.uuid4()),
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            
            db.add_all([session1, session2])
            await db.flush()
            print(f"   ✓ Created 2 sessions")
            
            # 3. Create audit logs
            print("\n3. Creating sample audit logs...")
            audit1 = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                action="register",
                resource_type="user",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0"
            )
            audit2 = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                action="login",
                resource_type="user",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0"
            )
            
            db.add_all([audit1, audit2])
            await db.flush()
            print(f"   ✓ Created 2 audit logs")
            
            # 4. Create resumes
            print("\n4. Creating sample resumes...")
            resume1 = Resume(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                filename="john_doe_resume.pdf",
                file_path="/uploads/resumes/john_doe_resume.pdf",
                file_size=245000,
                mime_type="application/pdf",
                is_primary=True,
                parsed_content=json.dumps({
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1-555-0100",
                    "summary": "Senior Software Engineer with 8 years of experience",
                    "skills": ["Python", "JavaScript", "React", "FastAPI", "PostgreSQL"],
                    "experience": [
                        {
                            "company": "Tech Corp",
                            "position": "Senior Engineer",
                            "duration": "2020-Present"
                        }
                    ]
                })
            )
            resume2 = Resume(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                filename="jane_smith_resume.pdf",
                file_path="/uploads/resumes/jane_smith_resume.pdf",
                file_size=198000,
                mime_type="application/pdf",
                is_primary=True,
                parsed_content=json.dumps({
                    "name": "Jane Smith",
                    "email": "jane.smith@example.com",
                    "phone": "+1-555-0101",
                    "summary": "Full Stack Developer with 5 years of experience",
                    "skills": ["JavaScript", "React", "Node.js", "MongoDB", "AWS"],
                    "experience": [
                        {
                            "company": "StartUp Inc",
                            "position": "Full Stack Developer",
                            "duration": "2019-Present"
                        }
                    ]
                })
            )
            
            db.add_all([resume1, resume2])
            await db.flush()
            print(f"   ✓ Created 2 resumes")
            
            # 5. Create resume scorecards
            print("\n5. Creating sample resume scorecards...")
            scorecard1 = ResumeScorecard(
                id=str(uuid.uuid4()),
                resume_id=resume1.id,
                overall_score=92,
                skills_score=95,
                experience_score=90,
                education_score=88,
                formatting_score=92,
                feedback=json.dumps({
                    "strengths": ["Strong technical skills", "Clear experience progression"],
                    "improvements": ["Add more quantifiable achievements"]
                })
            )
            
            db.add(scorecard1)
            await db.flush()
            print(f"   ✓ Created 1 resume scorecard")
            
            # 6. Create user preferences
            print("\n6. Creating sample user preferences...")
            prefs1 = UserPreferences(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                job_titles=json.dumps(["Senior Software Engineer", "Tech Lead", "Engineering Manager"]),
                locations=json.dumps(["San Francisco", "New York", "Remote"]),
                work_types=json.dumps(["full-time", "contract"]),
                min_salary=150000,
                max_salary=250000,
                currency="USD",
                industries=json.dumps(["Technology", "Finance", "Healthcare"]),
                company_sizes=json.dumps(["startup", "mid-size", "enterprise"]),
                remote_preference="hybrid",
                experience_level="senior",
                skills_required=json.dumps(["Python", "JavaScript", "React", "FastAPI"]),
                skills_nice_to_have=json.dumps(["Kubernetes", "AWS", "Machine Learning"]),
                auto_apply_enabled=True,
                auto_apply_threshold=75
            )
            prefs2 = UserPreferences(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                job_titles=json.dumps(["Full Stack Developer", "Frontend Engineer"]),
                locations=json.dumps(["Austin", "Denver", "Remote"]),
                work_types=json.dumps(["full-time"]),
                min_salary=100000,
                max_salary=180000,
                currency="USD",
                industries=json.dumps(["Technology", "E-commerce"]),
                company_sizes=json.dumps(["startup", "mid-size"]),
                remote_preference="remote",
                experience_level="mid",
                skills_required=json.dumps(["JavaScript", "React", "Node.js"]),
                skills_nice_to_have=json.dumps(["TypeScript", "GraphQL", "Docker"]),
                auto_apply_enabled=False,
                auto_apply_threshold=80
            )
            
            db.add_all([prefs1, prefs2])
            await db.flush()
            print(f"   ✓ Created 2 user preferences")
            
            # 7. Create job sources
            print("\n7. Creating sample job sources...")
            source1 = JobSource(
                id=str(uuid.uuid4()),
                name="LinkedIn Jobs",
                source_type="api",
                url="https://api.linkedin.com/jobs",
                is_active=True,
                fetch_frequency_hours=24,
                last_fetch_status="success",
                jobs_fetched_count=150
            )
            source2 = JobSource(
                id=str(uuid.uuid4()),
                name="HackerNews Jobs",
                source_type="rss",
                url="https://news.ycombinator.com/rss",
                is_active=True,
                fetch_frequency_hours=12,
                last_fetch_status="success",
                jobs_fetched_count=45
            )
            source3 = JobSource(
                id=str(uuid.uuid4()),
                name="GitHub Jobs",
                source_type="api",
                url="https://api.github.com/jobs",
                is_active=False,
                fetch_frequency_hours=24,
                last_fetch_status="failed",
                last_fetch_error="API endpoint deprecated"
            )
            
            db.add_all([source1, source2, source3])
            await db.flush()
            print(f"   ✓ Created 3 job sources")
            
            # 8. Create job postings
            print("\n8. Creating sample job postings...")
            import hashlib
            
            jobs_data = [
                {
                    "title": "Senior Python Engineer",
                    "company": "Google",
                    "location": "San Francisco, CA",
                    "description": "We are looking for a Senior Python Engineer to join our team...",
                    "requirements": "5+ years Python, FastAPI, PostgreSQL",
                    "salary_min": 180000,
                    "salary_max": 250000,
                    "work_type": "full-time",
                    "application_url": "https://google.com/careers/job1"
                },
                {
                    "title": "React Frontend Developer",
                    "company": "Airbnb",
                    "location": "San Francisco, CA",
                    "description": "Join our frontend team building amazing user experiences...",
                    "requirements": "3+ years React, TypeScript, CSS",
                    "salary_min": 140000,
                    "salary_max": 200000,
                    "work_type": "full-time",
                    "application_url": "https://airbnb.com/careers/job2"
                },
                {
                    "title": "Full Stack Engineer",
                    "company": "Stripe",
                    "location": "Remote",
                    "description": "Build payment infrastructure with us...",
                    "requirements": "4+ years full stack, Node.js, React",
                    "salary_min": 160000,
                    "salary_max": 230000,
                    "work_type": "full-time",
                    "application_url": "https://stripe.com/careers/job3"
                },
                {
                    "title": "DevOps Engineer",
                    "company": "Netflix",
                    "location": "Los Gatos, CA",
                    "description": "Help us scale our infrastructure...",
                    "requirements": "5+ years DevOps, Kubernetes, AWS",
                    "salary_min": 170000,
                    "salary_max": 240000,
                    "work_type": "full-time",
                    "application_url": "https://netflix.com/careers/job4"
                },
                {
                    "title": "Machine Learning Engineer",
                    "company": "OpenAI",
                    "location": "San Francisco, CA",
                    "description": "Work on cutting-edge AI models...",
                    "requirements": "3+ years ML, Python, PyTorch",
                    "salary_min": 200000,
                    "salary_max": 300000,
                    "work_type": "full-time",
                    "application_url": "https://openai.com/careers/job5"
                }
            ]
            
            job_postings = []
            for idx, job_data in enumerate(jobs_data):
                url_hash = hashlib.sha256(job_data["application_url"].encode()).hexdigest()
                job = JobPosting(
                    id=str(uuid.uuid4()),
                    source_id=source1.id if idx < 3 else source2.id,
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    description=job_data["description"],
                    requirements=job_data["requirements"],
                    salary_min=job_data["salary_min"],
                    salary_max=job_data["salary_max"],
                    salary_currency="USD",
                    work_type=job_data["work_type"],
                    application_url=job_data["application_url"],
                    url_hash=url_hash,
                    is_active=True,
                    posted_date=datetime.utcnow() - timedelta(days=idx),
                    raw_data=json.dumps(job_data)
                )
                job_postings.append(job)
            
            db.add_all(job_postings)
            await db.flush()
            print(f"   ✓ Created {len(job_postings)} job postings")
            
            # 9. Create job matches
            print("\n9. Creating sample job matches...")
            match1 = JobMatch(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                job_id=job_postings[0].id,
                match_score=92,
                match_reasons=json.dumps([
                    "Skills match: Python, FastAPI",
                    "Experience level: Senior",
                    "Location: Remote available"
                ]),
                is_applied=False,
                is_rejected=False
            )
            match2 = JobMatch(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                job_id=job_postings[1].id,
                match_score=88,
                match_reasons=json.dumps([
                    "Skills match: React, TypeScript",
                    "Experience level: Mid",
                    "Salary range matches"
                ]),
                is_applied=True,
                is_rejected=False
            )
            
            db.add_all([match1, match2])
            await db.flush()
            print(f"   ✓ Created 2 job matches")
            
            # 10. Create apply kits
            print("\n10. Creating sample apply kits...")
            kit1 = ApplyKit(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                name="Tech Lead Application",
                description="Custom application for tech lead positions",
                cover_letter_template="Dear Hiring Manager,\n\nI am interested in the Tech Lead position...",
                resume_id=resume1.id,
                is_default=True,
                is_active=True
            )
            kit2 = ApplyKit(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                name="Frontend Developer Application",
                description="Application for frontend roles",
                cover_letter_template="Hello,\n\nI am excited to apply for the Frontend Developer position...",
                resume_id=resume2.id,
                is_default=True,
                is_active=True
            )
            
            db.add_all([kit1, kit2])
            await db.flush()
            print(f"   ✓ Created 2 apply kits")
            
            # 11. Create job activities
            print("\n11. Creating sample job activities...")
            activity1 = JobActivity(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                job_id=job_postings[0].id,
                apply_kit_id=kit1.id,
                action="applied",
                status=ActivityStatus.APPLIED,
                notes="Applied via auto-apply",
                application_url=job_postings[0].application_url
            )
            activity2 = JobActivity(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                job_id=job_postings[1].id,
                apply_kit_id=kit2.id,
                action="viewed",
                status=ActivityStatus.VIEWED,
                notes="Viewed job posting"
            )
            
            db.add_all([activity1, activity2])
            await db.flush()
            print(f"   ✓ Created 2 job activities")
            
            # 12. Create notification settings
            print("\n12. Creating sample notification settings...")
            notif1 = NotificationSettings(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                email_on_match=True,
                email_on_application=True,
                email_on_response=True,
                email_digest_frequency="daily",
                push_notifications_enabled=True,
                sms_notifications_enabled=False
            )
            notif2 = NotificationSettings(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                email_on_match=True,
                email_on_application=False,
                email_on_response=True,
                email_digest_frequency="weekly",
                push_notifications_enabled=False,
                sms_notifications_enabled=False
            )
            
            db.add_all([notif1, notif2])
            await db.flush()
            print(f"   ✓ Created 2 notification settings")
            
            # 13. Create notification logs
            print("\n13. Creating sample notification logs...")
            notif_log1 = NotificationLog(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                notification_type="job_match",
                title="New Job Match: Senior Python Engineer",
                message="A new job matching your preferences has been found",
                is_read=False,
                sent_via="email"
            )
            notif_log2 = NotificationLog(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                notification_type="application_status",
                title="Application Status Update",
                message="Your application to Airbnb has been viewed",
                is_read=True,
                sent_via="email"
            )
            
            db.add_all([notif_log1, notif_log2])
            await db.flush()
            print(f"   ✓ Created 2 notification logs")
            
            # Commit all changes
            await db.commit()
            print("\n" + "="*50)
            print("✓ Database seeded successfully!")
            print("="*50)
            print("\nSample Data Summary:")
            print(f"  • Users: 3")
            print(f"  • Sessions: 2")
            print(f"  • Resumes: 2")
            print(f"  • Job Sources: 3")
            print(f"  • Job Postings: {len(job_postings)}")
            print(f"  • Job Matches: 2")
            print(f"  • Apply Kits: 2")
            print(f"  • Job Activities: 2")
            print(f"  • Notification Settings: 2")
            print(f"  • Notification Logs: 2")
            print("\nTest Credentials:")
            print("  • Email: john.doe@example.com")
            print("    Password: TestPass123!")
            print("  • Email: jane.smith@example.com")
            print("    Password: TestPass456!")
            print("  • Email: bob.wilson@example.com")
            print("    Password: TestPass789!")
            print("\n" + "="*50)
            
        except Exception as e:
            print(f"\n✗ Error seeding database: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
