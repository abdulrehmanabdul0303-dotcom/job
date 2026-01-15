"""
Enhanced seed database with comprehensive sample data for AI Extensions testing.
This includes data for Resume Versioning, Interview Preparation, Skill Gap Analysis,
Smart Job Alerts, Career Roadmap, and Analytics Dashboard.

Run this after initializing the database and running the base seed_data.py.
"""
import asyncio
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.models.job import JobPosting, JobSource
from app.models.match import JobMatch
from app.models.apply import JobActivity, ActivityStatus
from app.services.auth import get_password_hash
import uuid
import json
import random


# Sample data for AI testing
AI_SAMPLE_DATA = {
    "users": [
        {
            "email": "alex.chen@example.com",
            "password": "AITest123!",
            "full_name": "Alex Chen",
            "profile": {
                "title": "Senior Full Stack Developer",
                "experience_years": 6,
                "skills": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "AWS", "Docker", "Kubernetes"],
                "education": "BS Computer Science, Stanford University",
                "certifications": ["AWS Solutions Architect", "Google Cloud Professional"],
                "languages": ["English", "Mandarin"],
                "location": "San Francisco, CA"
            }
        },
        {
            "email": "maria.rodriguez@example.com", 
            "password": "AITest456!",
            "full_name": "Maria Rodriguez",
            "profile": {
                "title": "Data Scientist",
                "experience_years": 4,
                "skills": ["Python", "R", "Machine Learning", "TensorFlow", "PyTorch", "SQL", "Tableau", "Statistics"],
                "education": "MS Data Science, MIT",
                "certifications": ["Google Analytics", "Tableau Desktop Specialist"],
                "languages": ["English", "Spanish"],
                "location": "New York, NY"
            }
        },
        {
            "email": "david.kim@example.com",
            "password": "AITest789!",
            "full_name": "David Kim",
            "profile": {
                "title": "DevOps Engineer",
                "experience_years": 5,
                "skills": ["Kubernetes", "Docker", "AWS", "Terraform", "Jenkins", "Python", "Bash", "Monitoring"],
                "education": "BS Software Engineering, UC Berkeley",
                "certifications": ["CKA", "AWS DevOps Professional"],
                "languages": ["English", "Korean"],
                "location": "Seattle, WA"
            }
        },
        {
            "email": "sarah.johnson@example.com",
            "password": "AITest101!",
            "full_name": "Sarah Johnson",
            "profile": {
                "title": "Frontend Developer",
                "experience_years": 3,
                "skills": ["JavaScript", "React", "Vue.js", "TypeScript", "CSS", "HTML", "Figma", "Jest"],
                "education": "BS Computer Science, University of Washington",
                "certifications": ["Google UX Design Certificate"],
                "languages": ["English"],
                "location": "Austin, TX"
            }
        }
    ],
    
    "job_postings": [
        {
            "title": "Senior Software Engineer - AI/ML",
            "company": "Meta",
            "location": "Menlo Park, CA",
            "salary_min": 200000,
            "salary_max": 300000,
            "description": """We are seeking a Senior Software Engineer to join our AI/ML team. You will work on cutting-edge machine learning systems that serve billions of users worldwide.

Key Responsibilities:
- Design and implement scalable ML infrastructure
- Collaborate with research teams to productionize ML models
- Optimize model performance and inference speed
- Build robust data pipelines for training and serving

Requirements:
- 5+ years of software engineering experience
- Strong proficiency in Python and C++
- Experience with PyTorch, TensorFlow, or similar ML frameworks
- Knowledge of distributed systems and microservices
- Experience with cloud platforms (AWS, GCP, Azure)

Preferred Qualifications:
- PhD in Computer Science, Machine Learning, or related field
- Experience with large-scale recommendation systems
- Knowledge of computer vision or NLP
- Contributions to open-source ML projects""",
            "requirements": "Python, C++, PyTorch, TensorFlow, AWS, Distributed Systems, Machine Learning",
            "skills_required": ["Python", "C++", "Machine Learning", "PyTorch", "TensorFlow", "AWS", "Distributed Systems"],
            "skills_nice_to_have": ["PhD", "Computer Vision", "NLP", "Recommendation Systems"],
            "work_type": "full-time",
            "remote_ok": False,
            "application_url": "https://meta.com/careers/ai-ml-engineer"
        },
        {
            "title": "Full Stack Developer - FinTech",
            "company": "Stripe",
            "location": "San Francisco, CA",
            "salary_min": 160000,
            "salary_max": 240000,
            "description": """Join Stripe's engineering team to build the future of online payments. We're looking for a Full Stack Developer to work on our core payment processing platform.

What you'll do:
- Build and maintain web applications using React and Node.js
- Design APIs that handle millions of transactions daily
- Collaborate with product and design teams
- Ensure high availability and performance of payment systems
- Implement security best practices for financial data

Requirements:
- 3+ years of full stack development experience
- Proficiency in JavaScript, React, and Node.js
- Experience with PostgreSQL or similar databases
- Understanding of RESTful API design
- Knowledge of payment processing or financial systems

Nice to have:
- Experience with TypeScript
- Knowledge of microservices architecture
- Familiarity with Kubernetes and Docker
- Previous fintech or payments experience""",
            "requirements": "JavaScript, React, Node.js, PostgreSQL, API Design, Payment Systems",
            "skills_required": ["JavaScript", "React", "Node.js", "PostgreSQL", "API Design"],
            "skills_nice_to_have": ["TypeScript", "Microservices", "Kubernetes", "Docker", "FinTech"],
            "work_type": "full-time",
            "remote_ok": True,
            "application_url": "https://stripe.com/careers/fullstack-dev"
        },
        {
            "title": "Data Scientist - Recommendation Systems",
            "company": "Netflix",
            "location": "Los Gatos, CA",
            "salary_min": 180000,
            "salary_max": 280000,
            "description": """Netflix is looking for a Data Scientist to join our Recommendation Systems team. You'll work on algorithms that help 200+ million members discover content they love.

Responsibilities:
- Develop and improve recommendation algorithms
- Analyze user behavior and content consumption patterns
- Design and run A/B tests to measure algorithm performance
- Collaborate with engineering teams to productionize models
- Present findings to stakeholders and leadership

Requirements:
- MS/PhD in Statistics, Computer Science, or related field
- 3+ years of experience in data science or machine learning
- Proficiency in Python and R
- Experience with recommendation systems or personalization
- Strong statistical analysis and experimental design skills
- Experience with big data tools (Spark, Hadoop)

Preferred:
- Experience with deep learning frameworks
- Knowledge of content understanding and NLP
- Previous experience in media or entertainment industry
- Publications in top-tier ML conferences""",
            "requirements": "Python, R, Machine Learning, Statistics, Recommendation Systems, Spark, A/B Testing",
            "skills_required": ["Python", "R", "Machine Learning", "Statistics", "Recommendation Systems", "Spark"],
            "skills_nice_to_have": ["Deep Learning", "NLP", "Hadoop", "PhD", "Publications"],
            "work_type": "full-time",
            "remote_ok": False,
            "application_url": "https://netflix.com/careers/data-scientist"
        },
        {
            "title": "DevOps Engineer - Cloud Infrastructure",
            "company": "Airbnb",
            "location": "San Francisco, CA",
            "salary_min": 170000,
            "salary_max": 250000,
            "description": """Airbnb is seeking a DevOps Engineer to help scale our infrastructure to support millions of hosts and guests worldwide.

What you'll do:
- Design and maintain cloud infrastructure on AWS
- Implement CI/CD pipelines and deployment automation
- Monitor system performance and reliability
- Collaborate with development teams on infrastructure needs
- Ensure security and compliance across all systems

Requirements:
- 4+ years of DevOps or infrastructure experience
- Strong experience with AWS services (EC2, EKS, RDS, etc.)
- Proficiency with Kubernetes and Docker
- Experience with Infrastructure as Code (Terraform, CloudFormation)
- Knowledge of monitoring tools (Datadog, New Relic, etc.)
- Scripting skills in Python or Bash

Preferred:
- Experience with service mesh (Istio, Linkerd)
- Knowledge of security best practices
- Previous experience at high-scale companies
- Certifications in AWS or Kubernetes""",
            "requirements": "AWS, Kubernetes, Docker, Terraform, Python, Monitoring, CI/CD",
            "skills_required": ["AWS", "Kubernetes", "Docker", "Terraform", "Python", "CI/CD"],
            "skills_nice_to_have": ["Istio", "Security", "Certifications", "Service Mesh"],
            "work_type": "full-time",
            "remote_ok": True,
            "application_url": "https://airbnb.com/careers/devops-engineer"
        },
        {
            "title": "Frontend Engineer - React",
            "company": "Shopify",
            "location": "Toronto, ON",
            "salary_min": 120000,
            "salary_max": 180000,
            "description": """Join Shopify's frontend team to build beautiful, performant user interfaces that power commerce for millions of merchants worldwide.

Responsibilities:
- Build responsive web applications using React and TypeScript
- Collaborate with designers to implement pixel-perfect UIs
- Optimize application performance and user experience
- Write comprehensive tests for frontend components
- Participate in code reviews and technical discussions

Requirements:
- 2+ years of frontend development experience
- Strong proficiency in React and JavaScript
- Experience with modern CSS and responsive design
- Knowledge of testing frameworks (Jest, React Testing Library)
- Understanding of web performance optimization

Nice to have:
- Experience with TypeScript
- Knowledge of GraphQL
- Familiarity with design systems
- Previous e-commerce experience
- Contributions to open-source projects""",
            "requirements": "React, JavaScript, CSS, Testing, Web Performance",
            "skills_required": ["React", "JavaScript", "CSS", "Testing", "HTML"],
            "skills_nice_to_have": ["TypeScript", "GraphQL", "Design Systems", "E-commerce"],
            "work_type": "full-time",
            "remote_ok": True,
            "application_url": "https://shopify.com/careers/frontend-engineer"
        },
        {
            "title": "Machine Learning Engineer - Computer Vision",
            "company": "Tesla",
            "location": "Palo Alto, CA",
            "salary_min": 190000,
            "salary_max": 290000,
            "description": """Tesla is looking for a Machine Learning Engineer to work on computer vision systems for our Autopilot and Full Self-Driving capabilities.

Key Responsibilities:
- Develop computer vision algorithms for autonomous driving
- Train and optimize deep neural networks
- Work with large-scale datasets and distributed training
- Collaborate with hardware teams on model deployment
- Ensure safety and reliability of ML systems

Requirements:
- MS/PhD in Computer Science, Electrical Engineering, or related field
- 3+ years of experience in computer vision or deep learning
- Proficiency in Python and C++
- Experience with PyTorch or TensorFlow
- Knowledge of computer vision techniques (object detection, segmentation, etc.)
- Understanding of autonomous systems or robotics

Preferred:
- Experience with automotive or robotics applications
- Knowledge of sensor fusion and multi-modal learning
- Experience with edge deployment and optimization
- Publications in computer vision conferences (CVPR, ICCV, etc.)""",
            "requirements": "Computer Vision, Deep Learning, Python, C++, PyTorch, TensorFlow, Autonomous Systems",
            "skills_required": ["Computer Vision", "Deep Learning", "Python", "C++", "PyTorch", "TensorFlow"],
            "skills_nice_to_have": ["Robotics", "Sensor Fusion", "Edge Deployment", "Publications"],
            "work_type": "full-time",
            "remote_ok": False,
            "application_url": "https://tesla.com/careers/ml-engineer"
        }
    ],
    
    "interview_questions": {
        "technical": [
            "Explain the difference between supervised and unsupervised learning",
            "How would you design a scalable web application architecture?",
            "What are the trade-offs between SQL and NoSQL databases?",
            "Describe how you would implement a recommendation system",
            "Explain the concept of microservices and their benefits",
            "How do you handle database migrations in a production environment?",
            "What is the difference between Docker and Kubernetes?",
            "Explain how machine learning model deployment works",
            "How would you optimize a slow-running database query?",
            "Describe the CI/CD pipeline you would set up for a web application"
        ],
        "behavioral": [
            "Tell me about a time when you had to learn a new technology quickly",
            "Describe a challenging project you worked on and how you overcame obstacles",
            "How do you handle disagreements with team members?",
            "Tell me about a time when you had to make a difficult technical decision",
            "Describe a situation where you had to work under tight deadlines",
            "How do you stay updated with new technologies and industry trends?",
            "Tell me about a time when you mentored a junior developer",
            "Describe a project where you had to collaborate with non-technical stakeholders",
            "How do you approach debugging a complex issue?",
            "Tell me about a time when you had to refactor legacy code"
        ],
        "company_specific": {
            "Meta": [
                "How would you approach building a feature for 3 billion users?",
                "What do you think about Meta's approach to the metaverse?",
                "How would you handle content moderation at scale?"
            ],
            "Stripe": [
                "How would you ensure payment security and compliance?",
                "What challenges do you see in global payment processing?",
                "How would you design an API for financial transactions?"
            ],
            "Netflix": [
                "How would you improve Netflix's recommendation algorithm?",
                "What metrics would you use to measure content success?",
                "How would you handle video streaming at global scale?"
            ]
        }
    },
    
    "skill_categories": {
        "programming_languages": ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "R", "Scala"],
        "web_frameworks": ["React", "Vue.js", "Angular", "Django", "Flask", "Express.js", "Spring Boot", "FastAPI"],
        "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB"],
        "cloud_platforms": ["AWS", "Google Cloud", "Azure", "DigitalOcean", "Heroku"],
        "devops_tools": ["Docker", "Kubernetes", "Terraform", "Jenkins", "GitLab CI", "Ansible", "Prometheus"],
        "ml_frameworks": ["TensorFlow", "PyTorch", "Scikit-learn", "Keras", "XGBoost", "Spark MLlib"],
        "data_tools": ["Pandas", "NumPy", "Jupyter", "Tableau", "Power BI", "Apache Spark", "Airflow"],
        "testing": ["Jest", "Pytest", "JUnit", "Cypress", "Selenium", "React Testing Library"],
        "soft_skills": ["Leadership", "Communication", "Problem Solving", "Team Collaboration", "Project Management"]
    },
    
    "learning_resources": [
        {
            "skill": "Machine Learning",
            "resources": [
                {"title": "Machine Learning Course", "provider": "Coursera", "type": "course", "duration_hours": 60, "cost": 49},
                {"title": "Hands-On Machine Learning", "provider": "O'Reilly", "type": "book", "duration_hours": 40, "cost": 35},
                {"title": "Kaggle Learn ML", "provider": "Kaggle", "type": "course", "duration_hours": 20, "cost": 0}
            ]
        },
        {
            "skill": "React",
            "resources": [
                {"title": "React - The Complete Guide", "provider": "Udemy", "type": "course", "duration_hours": 48, "cost": 89},
                {"title": "React Documentation", "provider": "React.dev", "type": "documentation", "duration_hours": 15, "cost": 0},
                {"title": "React Testing Library", "provider": "Testing Library", "type": "tutorial", "duration_hours": 8, "cost": 0}
            ]
        },
        {
            "skill": "Kubernetes",
            "resources": [
                {"title": "Certified Kubernetes Administrator", "provider": "Linux Foundation", "type": "certification", "duration_hours": 100, "cost": 395},
                {"title": "Kubernetes in Action", "provider": "Manning", "type": "book", "duration_hours": 50, "cost": 45},
                {"title": "Kubernetes Basics", "provider": "Kubernetes.io", "type": "tutorial", "duration_hours": 12, "cost": 0}
            ]
        }
    ]
}


async def seed_ai_extensions_data():
    """Seed database with comprehensive AI extensions sample data."""
    async with AsyncSessionLocal() as db:
        try:
            print("Seeding database with AI Extensions sample data...")
            print("="*60)
            
            # 1. Create AI test users with detailed profiles
            print("\n1. Creating AI test users with detailed profiles...")
            ai_users = []
            for user_data in AI_SAMPLE_DATA["users"]:
                user = User(
                    id=str(uuid.uuid4()),
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_active=True,
                    is_verified=True
                )
                ai_users.append(user)
                db.add(user)
            
            await db.flush()
            print(f"   ✓ Created {len(ai_users)} AI test users")
            
            # 2. Create detailed resumes for AI users
            print("\n2. Creating detailed resumes for AI users...")
            ai_resumes = []
            for idx, user in enumerate(ai_users):
                profile = AI_SAMPLE_DATA["users"][idx]["profile"]
                
                # Create comprehensive resume content
                resume_content = {
                    "name": user.full_name,
                    "email": user.email,
                    "phone": f"+1-555-{1000 + idx:04d}",
                    "location": profile["location"],
                    "title": profile["title"],
                    "summary": f"{profile['title']} with {profile['experience_years']} years of experience in software development and technology.",
                    "skills": profile["skills"],
                    "education": profile["education"],
                    "certifications": profile.get("certifications", []),
                    "languages": profile.get("languages", ["English"]),
                    "experience": [
                        {
                            "company": f"Tech Company {idx + 1}",
                            "position": profile["title"],
                            "duration": f"{2024 - profile['experience_years']}-Present",
                            "description": f"Led development of scalable applications using {', '.join(profile['skills'][:3])}",
                            "achievements": [
                                "Improved system performance by 40%",
                                "Led team of 5 developers",
                                "Implemented CI/CD pipeline"
                            ]
                        },
                        {
                            "company": f"Previous Company {idx + 1}",
                            "position": f"Senior {profile['title'].split()[-1]}",
                            "duration": f"{2024 - profile['experience_years'] - 2}-{2024 - profile['experience_years']}",
                            "description": f"Developed and maintained applications using {', '.join(profile['skills'][3:6])}",
                            "achievements": [
                                "Reduced deployment time by 60%",
                                "Mentored junior developers",
                                "Implemented automated testing"
                            ]
                        }
                    ],
                    "projects": [
                        {
                            "name": f"AI-Powered {profile['title'].split()[0]} Platform",
                            "description": f"Built scalable platform using {', '.join(profile['skills'][:4])}",
                            "technologies": profile["skills"][:6],
                            "achievements": ["Served 100K+ users", "99.9% uptime", "Real-time processing"]
                        }
                    ]
                }
                
                resume = Resume(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    filename=f"{user.full_name.lower().replace(' ', '_')}_resume.pdf",
                    file_path=f"/uploads/resumes/{user.full_name.lower().replace(' ', '_')}_resume.pdf",
                    file_size=random.randint(200000, 400000),
                    mime_type="application/pdf",
                    is_primary=True,
                    parsed_content=json.dumps(resume_content)
                )
                ai_resumes.append(resume)
                db.add(resume)
            
            await db.flush()
            print(f"   ✓ Created {len(ai_resumes)} detailed resumes")
            
            # 3. Create comprehensive job postings for AI testing
            print("\n3. Creating comprehensive job postings for AI testing...")
            
            # First, get or create job sources
            existing_sources = await db.execute("SELECT * FROM job_sources LIMIT 1")
            source = existing_sources.fetchone()
            if not source:
                # Create a source if none exists
                ai_source = JobSource(
                    id=str(uuid.uuid4()),
                    name="AI Test Jobs",
                    source_type="api",
                    url="https://api.aitestjobs.com",
                    is_active=True,
                    fetch_frequency_hours=24,
                    last_fetch_status="success",
                    jobs_fetched_count=len(AI_SAMPLE_DATA["job_postings"])
                )
                db.add(ai_source)
                await db.flush()
                source_id = ai_source.id
            else:
                source_id = source[0]  # Use existing source ID
            
            ai_jobs = []
            for idx, job_data in enumerate(AI_SAMPLE_DATA["job_postings"]):
                import hashlib
                url_hash = hashlib.sha256(job_data["application_url"].encode()).hexdigest()
                
                job = JobPosting(
                    id=str(uuid.uuid4()),
                    source_id=source_id,
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
                    raw_data=json.dumps({
                        **job_data,
                        "skills_required": job_data["skills_required"],
                        "skills_nice_to_have": job_data["skills_nice_to_have"],
                        "remote_ok": job_data["remote_ok"]
                    })
                )
                ai_jobs.append(job)
                db.add(job)
            
            await db.flush()
            print(f"   ✓ Created {len(ai_jobs)} comprehensive job postings")
            
            # 4. Create job matches with detailed scoring
            print("\n4. Creating job matches with detailed AI scoring...")
            ai_matches = []
            
            # Create matches between users and jobs based on skill alignment
            for user_idx, user in enumerate(ai_users):
                user_profile = AI_SAMPLE_DATA["users"][user_idx]["profile"]
                user_skills = set(user_profile["skills"])
                
                for job_idx, job in enumerate(ai_jobs):
                    job_data = AI_SAMPLE_DATA["job_postings"][job_idx]
                    required_skills = set(job_data["skills_required"])
                    nice_to_have_skills = set(job_data["skills_nice_to_have"])
                    
                    # Calculate match score based on skill overlap
                    required_match = len(user_skills.intersection(required_skills)) / len(required_skills) if required_skills else 0
                    nice_to_have_match = len(user_skills.intersection(nice_to_have_skills)) / len(nice_to_have_skills) if nice_to_have_skills else 0
                    
                    # Overall match score (weighted)
                    match_score = int((required_match * 0.7 + nice_to_have_match * 0.3) * 100)
                    
                    # Only create matches above 50% threshold
                    if match_score >= 50:
                        match_reasons = []
                        
                        # Add specific match reasons
                        matching_required = user_skills.intersection(required_skills)
                        if matching_required:
                            match_reasons.append(f"Required skills match: {', '.join(list(matching_required)[:3])}")
                        
                        matching_nice = user_skills.intersection(nice_to_have_skills)
                        if matching_nice:
                            match_reasons.append(f"Nice-to-have skills: {', '.join(list(matching_nice)[:2])}")
                        
                        # Experience level matching
                        if user_profile["experience_years"] >= 5:
                            match_reasons.append("Senior experience level")
                        elif user_profile["experience_years"] >= 3:
                            match_reasons.append("Mid-level experience")
                        
                        # Location matching
                        if job_data.get("remote_ok", False) or user_profile["location"].split(",")[0] in job_data["location"]:
                            match_reasons.append("Location preference match")
                        
                        match = JobMatch(
                            id=str(uuid.uuid4()),
                            user_id=user.id,
                            job_id=job.id,
                            match_score=match_score,
                            match_reasons=json.dumps(match_reasons),
                            is_applied=random.choice([True, False]) if match_score > 70 else False,
                            is_rejected=False
                        )
                        ai_matches.append(match)
                        db.add(match)
            
            await db.flush()
            print(f"   ✓ Created {len(ai_matches)} job matches with AI scoring")
            
            # 5. Create sample job activities for analytics
            print("\n5. Creating sample job activities for analytics...")
            ai_activities = []
            
            for match in ai_matches[:20]:  # Create activities for first 20 matches
                # Create various activity types
                activity_types = ["viewed", "saved", "applied", "interview_scheduled", "offer_received"]
                weights = [0.4, 0.25, 0.2, 0.1, 0.05]  # Probability weights
                
                activity_type = random.choices(activity_types, weights=weights)[0]
                
                # Map activity types to statuses
                status_mapping = {
                    "viewed": ActivityStatus.VIEWED,
                    "saved": ActivityStatus.SAVED,
                    "applied": ActivityStatus.APPLIED,
                    "interview_scheduled": ActivityStatus.INTERVIEW,
                    "offer_received": ActivityStatus.OFFER
                }
                
                activity = JobActivity(
                    id=str(uuid.uuid4()),
                    user_id=match.user_id,
                    job_id=match.job_id,
                    action=activity_type,
                    status=status_mapping[activity_type],
                    notes=f"AI-generated {activity_type} activity for testing",
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                ai_activities.append(activity)
                db.add(activity)
            
            await db.flush()
            print(f"   ✓ Created {len(ai_activities)} job activities for analytics")
            
            # 6. Create sample data for skill gap analysis
            print("\n6. Creating sample skill gap analysis data...")
            
            # This will be used by the AI system to generate skill gaps
            skill_market_data = {
                "trending_skills": {
                    "2024": ["AI/ML", "Kubernetes", "TypeScript", "React", "Python", "AWS", "Docker", "GraphQL"],
                    "growth_rate": {
                        "AI/ML": 45,
                        "Kubernetes": 38,
                        "TypeScript": 32,
                        "React": 28,
                        "Python": 25,
                        "AWS": 22,
                        "Docker": 20,
                        "GraphQL": 18
                    }
                },
                "salary_impact": {
                    "AI/ML": 25000,
                    "Kubernetes": 18000,
                    "TypeScript": 12000,
                    "React": 10000,
                    "Python": 8000,
                    "AWS": 15000,
                    "Docker": 8000,
                    "GraphQL": 6000
                }
            }
            
            # Store this as metadata for the AI system
            print(f"   ✓ Prepared skill market data for {len(skill_market_data['trending_skills']['2024'])} trending skills")
            
            # 7. Create sample interview preparation data
            print("\n7. Creating sample interview preparation data...")
            
            # Store interview questions and company insights
            interview_data = {
                "questions_by_role": {
                    "Software Engineer": AI_SAMPLE_DATA["interview_questions"]["technical"][:5] + AI_SAMPLE_DATA["interview_questions"]["behavioral"][:3],
                    "Data Scientist": ["Explain bias-variance tradeoff", "How do you handle missing data?"] + AI_SAMPLE_DATA["interview_questions"]["behavioral"][:3],
                    "DevOps Engineer": ["Explain CI/CD pipeline", "How do you monitor system health?"] + AI_SAMPLE_DATA["interview_questions"]["behavioral"][:3],
                    "Frontend Developer": ["Explain React lifecycle", "How do you optimize web performance?"] + AI_SAMPLE_DATA["interview_questions"]["behavioral"][:3]
                },
                "company_insights": {
                    "Meta": {
                        "culture": "Move fast, be bold, focus on impact",
                        "interview_process": "Technical screen, coding interview, system design, behavioral",
                        "values": ["Be Bold", "Focus on Impact", "Move Fast", "Be Open", "Build Social Value"]
                    },
                    "Stripe": {
                        "culture": "User-first, high-quality, global mindset",
                        "interview_process": "Technical screen, coding interview, integration interview, behavioral",
                        "values": ["Users First", "Optimism", "Rigorous Thinking", "Trust and Transparency"]
                    }
                }
            }
            
            print(f"   ✓ Prepared interview data for {len(interview_data['questions_by_role'])} roles")
            
            # 8. Create sample analytics data
            print("\n8. Creating sample analytics data...")
            
            # Generate historical application data for analytics
            analytics_data = {
                "application_funnel": {
                    "total_jobs_viewed": len(ai_matches),
                    "jobs_saved": len([m for m in ai_matches if random.random() < 0.3]),
                    "applications_sent": len([m for m in ai_matches if m.is_applied]),
                    "interviews_scheduled": len([a for a in ai_activities if a.status == ActivityStatus.INTERVIEW]),
                    "offers_received": len([a for a in ai_activities if a.status == ActivityStatus.OFFER])
                },
                "success_rates": {
                    "application_to_interview": 0.15,
                    "interview_to_offer": 0.25,
                    "overall_success": 0.0375
                },
                "top_job_sources": [
                    {"source": "LinkedIn", "applications": 45, "success_rate": 0.12},
                    {"source": "Company Website", "applications": 23, "success_rate": 0.18},
                    {"source": "Referral", "applications": 12, "success_rate": 0.35}
                ]
            }
            
            print(f"   ✓ Generated analytics data with {analytics_data['application_funnel']['total_jobs_viewed']} data points")
            
            # Commit all changes
            await db.commit()
            
            print("\n" + "="*60)
            print("✓ AI Extensions sample data seeded successfully!")
            print("="*60)
            print("\nAI Extensions Sample Data Summary:")
            print(f"  • AI Test Users: {len(ai_users)}")
            print(f"  • Detailed Resumes: {len(ai_resumes)}")
            print(f"  • Comprehensive Job Postings: {len(ai_jobs)}")
            print(f"  • AI-Scored Job Matches: {len(ai_matches)}")
            print(f"  • Job Activities: {len(ai_activities)}")
            print(f"  • Skill Categories: {len(AI_SAMPLE_DATA['skill_categories'])}")
            print(f"  • Learning Resources: {len(AI_SAMPLE_DATA['learning_resources'])}")
            print(f"  • Interview Questions: {sum(len(q) for q in AI_SAMPLE_DATA['interview_questions'].values() if isinstance(q, list))}")
            
            print("\nAI Test Credentials:")
            for user_data in AI_SAMPLE_DATA["users"]:
                print(f"  • Email: {user_data['email']}")
                print(f"    Password: {user_data['password']}")
                print(f"    Profile: {user_data['profile']['title']} ({user_data['profile']['experience_years']} years)")
            
            print("\nFeature Testing Scenarios:")
            print("  🎯 Resume Versioning: Test with different job types and skill requirements")
            print("  🎤 Interview Preparation: Generate questions for various roles and companies")
            print("  📊 Skill Gap Analysis: Compare user skills with job requirements")
            print("  🔔 Smart Job Alerts: Test relevance scoring and alert thresholds")
            print("  🗺️  Career Roadmap: Generate learning paths based on skill gaps")
            print("  📈 Analytics Dashboard: View application funnel and success metrics")
            
            print("\n" + "="*60)
            
        except Exception as e:
            print(f"\n✗ Error seeding AI extensions data: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_ai_extensions_data())