"""
AI Interview Preparation Service.
Handles interview question generation, coaching, and preparation kits.
"""
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.resume import Resume
from app.models.job import JobPosting
from app.models.ai_interview import InterviewKit, InterviewQuestion, STARExample, CompanyInsight
import uuid


class InterviewPreparationEngine:
    """Core engine for AI-powered interview preparation."""
    
    def __init__(self):
        self.question_templates = {
            "technical": [
                "Explain your experience with {skill}",
                "How would you approach {technical_challenge}?",
                "What's the difference between {concept_a} and {concept_b}?",
                "Describe a time when you had to debug {technical_issue}",
                "How do you ensure code quality in {technology}?",
                "What are the best practices for {technical_area}?",
                "How would you optimize {performance_area}?",
                "Explain how you would implement {feature_type}",
                "What testing strategies do you use for {technology}?",
                "How do you handle {technical_problem} in production?"
            ],
            "behavioral": [
                "Tell me about a time when you had to {behavioral_situation}",
                "Describe a situation where you {leadership_scenario}",
                "How do you handle {conflict_situation}?",
                "Give me an example of when you {achievement_scenario}",
                "Tell me about a time you failed and what you learned",
                "Describe your approach to {work_style_question}",
                "How do you prioritize tasks when {pressure_situation}?",
                "Tell me about a time you had to {collaboration_scenario}",
                "Describe a situation where you {problem_solving_scenario}",
                "How do you handle feedback and criticism?"
            ],
            "company_specific": [
                "Why do you want to work at {company}?",
                "How do you align with {company}'s values?",
                "What do you know about {company}'s recent {news_topic}?",
                "How would you contribute to {company}'s mission?",
                "What interests you about {company}'s {product_service}?",
                "How do you see yourself fitting into {company}'s culture?",
                "What questions do you have about working at {company}?",
                "How would you handle {company_specific_challenge}?",
                "What do you think about {company}'s approach to {business_area}?",
                "How would you improve {company}'s {improvement_area}?"
            ]
        }
        
        self.star_competencies = [
            "Leadership", "Problem Solving", "Communication", "Teamwork", 
            "Adaptability", "Initiative", "Time Management", "Conflict Resolution",
            "Innovation", "Customer Focus", "Decision Making", "Mentoring"
        ]
    
    async def generate_interview_kit(
        self,
        db: AsyncSession,
        user_id: str,
        job_id: str,
        difficulty_level: str = "intermediate",
        include_company_research: bool = True
    ) -> Dict[str, Any]:
        """Generate a comprehensive interview preparation kit."""
        start_time = time.time()
        
        try:
            # Check if kit already exists
            existing_kit = await self._get_existing_kit(db, user_id, job_id)
            if existing_kit:
                return await self._format_kit_response(existing_kit)
            
            # Get user resume and job posting
            user_resume = await self._get_user_resume(db, user_id)
            job_posting = await self._get_job_posting(db, job_id)
            
            if not user_resume or not job_posting:
                raise ValueError("Resume or job posting not found")
            
            # Parse data
            resume_data = self._parse_resume_content(user_resume.parsed_data)
            job_requirements = self._parse_job_requirements(job_posting)
            
            # Generate interview questions
            questions = await self._generate_questions(
                resume_data, job_requirements, difficulty_level
            )
            
            # Generate personalized talking points
            talking_points = await self._generate_talking_points(
                resume_data, job_requirements
            )
            
            # Generate STAR examples
            star_examples = await self._generate_star_examples(
                resume_data, job_requirements
            )
            
            # Get company insights
            company_insights = {}
            if include_company_research:
                company_insights = await self._get_company_insights(
                    db, job_posting.company
                )
            
            # Generate preparation checklist
            prep_checklist = self._generate_preparation_checklist(
                job_requirements, difficulty_level
            )
            
            # Calculate estimated prep time
            estimated_prep_time = self._calculate_prep_time(
                len(questions), difficulty_level
            )
            
            # Create interview kit
            kit = InterviewKit(
                id=str(uuid.uuid4()),
                user_id=user_id,
                job_id=job_id,
                questions=json.dumps(questions),
                talking_points=json.dumps(talking_points),
                company_insights=json.dumps(company_insights),
                star_examples=json.dumps(star_examples),
                preparation_checklist=json.dumps(prep_checklist),
                difficulty_level=difficulty_level,
                estimated_prep_time=estimated_prep_time
            )
            
            db.add(kit)
            await db.flush()
            
            # Create individual question records
            await self._create_question_records(db, kit.id, user_id, questions)
            
            # Create STAR example records
            await self._create_star_records(db, kit.id, user_id, star_examples, resume_data)
            
            await db.commit()
            
            processing_time = time.time() - start_time
            print(f"Interview kit generated in {processing_time:.2f}s")
            
            return await self._format_kit_response(kit)
            
        except Exception as e:
            await db.rollback()
            raise
    
    async def get_interview_kit(
        self, 
        db: AsyncSession, 
        user_id: str, 
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing interview kit for a job."""
        kit = await self._get_existing_kit(db, user_id, job_id)
        if kit:
            return await self._format_kit_response(kit)
        return None
    
    async def analyze_answer(
        self,
        db: AsyncSession,
        user_id: str,
        question_id: str,
        user_answer: str
    ) -> Dict[str, Any]:
        """Analyze user's answer and provide AI feedback."""
        try:
            # Get the question
            result = await db.execute(
                select(InterviewQuestion).where(
                    InterviewQuestion.id == question_id,
                    InterviewQuestion.user_id == user_id
                )
            )
            question = result.scalar_one_or_none()
            
            if not question:
                raise ValueError("Question not found")
            
            # Analyze the answer
            feedback = await self._analyze_user_answer(
                question.question_text,
                question.category,
                user_answer,
                json.loads(question.suggested_answer) if question.suggested_answer else {}
            )
            
            # Update question with user answer and feedback
            question.user_answer = user_answer
            question.ai_feedback = json.dumps(feedback["feedback"])
            question.feedback_score = feedback["score"]
            question.is_practiced = True
            question.updated_at = datetime.utcnow()
            
            await db.commit()
            
            return {
                "question_id": question_id,
                "score": feedback["score"],
                "feedback": feedback["feedback"],
                "suggestions": feedback["suggestions"],
                "strengths": feedback["strengths"]
            }
            
        except Exception as e:
            await db.rollback()
            raise
    
    async def get_company_insights(
        self,
        db: AsyncSession,
        company_name: str
    ) -> Dict[str, Any]:
        """Get or generate company insights."""
        return await self._get_company_insights(db, company_name)
    
    # Private helper methods
    
    async def _get_existing_kit(
        self, db: AsyncSession, user_id: str, job_id: str
    ) -> Optional[InterviewKit]:
        """Get existing interview kit."""
        result = await db.execute(
            select(InterviewKit).where(
                InterviewKit.user_id == user_id,
                InterviewKit.job_id == job_id,
                InterviewKit.is_active == True
            ).order_by(InterviewKit.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def _get_user_resume(
        self, db: AsyncSession, user_id: str
    ) -> Optional[Resume]:
        """Get user's primary resume."""
        result = await db.execute(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.is_parsed == True
            ).order_by(Resume.uploaded_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def _get_job_posting(
        self, db: AsyncSession, job_id: str
    ) -> Optional[JobPosting]:
        """Get job posting by ID."""
        result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        return result.scalar_one_or_none()
    
    def _parse_resume_content(self, parsed_data: str) -> Dict[str, Any]:
        """Parse resume content from stored JSON."""
        if not parsed_data:
            return {}
        try:
            return json.loads(parsed_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def _parse_job_requirements(self, job_posting: JobPosting) -> Dict[str, Any]:
        """Parse job requirements and extract key information."""
        return {
            "title": job_posting.title,
            "company": job_posting.company,
            "description": job_posting.description,
            "requirements": job_posting.requirements,
            "skills": self._extract_skills(f"{job_posting.description} {job_posting.requirements}"),
            "seniority": self._extract_seniority(job_posting.title),
            "industry": self._extract_industry(job_posting.company)
        }
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from job text."""
        text_lower = text.lower()
        common_skills = [
            "python", "javascript", "react", "node.js", "sql", "aws", "docker",
            "kubernetes", "machine learning", "ai", "data science", "fastapi",
            "postgresql", "mongodb", "redis", "git", "ci/cd", "devops",
            "java", "c++", "go", "rust", "typescript", "angular", "vue.js",
            "django", "flask", "spring", "microservices", "api", "rest",
            "graphql", "terraform", "jenkins", "linux", "agile", "scrum"
        ]
        
        found_skills = [skill for skill in common_skills if skill in text_lower]
        return found_skills[:10]  # Top 10 skills
    
    def _extract_seniority(self, title: str) -> str:
        """Extract seniority level from job title."""
        title_lower = title.lower()
        if any(word in title_lower for word in ["senior", "sr", "lead", "principal", "staff"]):
            return "senior"
        elif any(word in title_lower for word in ["junior", "jr", "entry", "associate"]):
            return "junior"
        else:
            return "mid"
    
    def _extract_industry(self, company: str) -> str:
        """Extract industry from company name (simplified)."""
        company_lower = company.lower()
        if any(word in company_lower for word in ["tech", "software", "ai", "data"]):
            return "technology"
        elif any(word in company_lower for word in ["bank", "finance", "capital"]):
            return "finance"
        elif any(word in company_lower for word in ["health", "medical", "pharma"]):
            return "healthcare"
        else:
            return "general"
    
    async def _generate_questions(
        self, 
        resume_data: Dict[str, Any], 
        job_requirements: Dict[str, Any],
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """Generate interview questions based on job and resume."""
        questions = []
        
        # Technical questions (40% of total)
        tech_questions = await self._generate_technical_questions(
            resume_data, job_requirements, difficulty_level
        )
        questions.extend(tech_questions)
        
        # Behavioral questions (40% of total)
        behavioral_questions = await self._generate_behavioral_questions(
            resume_data, job_requirements, difficulty_level
        )
        questions.extend(behavioral_questions)
        
        # Company-specific questions (20% of total)
        company_questions = await self._generate_company_questions(
            job_requirements, difficulty_level
        )
        questions.extend(company_questions)
        
        return questions
    
    async def _generate_technical_questions(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any],
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """Generate technical interview questions."""
        questions = []
        skills = job_requirements.get("skills", [])
        
        # Generate 6-8 technical questions
        question_count = 8 if difficulty_level == "advanced" else 6
        
        for i in range(min(question_count, len(skills) + 2)):
            if i < len(skills):
                skill = skills[i]
                template = self.question_templates["technical"][i % len(self.question_templates["technical"])]
                question_text = template.format(
                    skill=skill,
                    technical_challenge=f"{skill} implementation",
                    concept_a=skill,
                    concept_b="alternative approach",
                    technical_issue=f"{skill} performance issue",
                    technology=skill,
                    technical_area=skill,
                    performance_area=f"{skill} performance",
                    feature_type=f"{skill}-based feature",
                    technical_problem=f"{skill} scaling issue"
                )
            else:
                # General technical questions
                general_questions = [
                    "How do you approach system design for scalable applications?",
                    "Describe your experience with code reviews and quality assurance.",
                    "How do you handle technical debt in your projects?",
                    "What's your approach to debugging complex issues?",
                    "How do you stay updated with new technologies?"
                ]
                question_text = general_questions[i - len(skills)]
            
            questions.append({
                "id": str(uuid.uuid4()),
                "text": question_text,
                "category": "technical",
                "difficulty": difficulty_level,
                "suggested_approach": self._generate_answer_approach("technical", question_text),
                "key_points": self._generate_key_points("technical", question_text, skills),
                "follow_ups": self._generate_follow_ups("technical", question_text)
            })
        
        return questions
    
    async def _generate_behavioral_questions(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any],
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """Generate behavioral interview questions."""
        questions = []
        
        # Core behavioral questions
        behavioral_scenarios = [
            "overcome a significant technical challenge",
            "lead a team through a difficult project",
            "handle conflicting priorities",
            "deal with a difficult team member",
            "implement a solution under tight deadlines",
            "learn a new technology quickly",
            "improve a process or system",
            "handle failure or setbacks"
        ]
        
        question_count = 8 if difficulty_level == "advanced" else 6
        
        for i in range(min(question_count, len(behavioral_scenarios))):
            scenario = behavioral_scenarios[i]
            question_text = f"Tell me about a time when you had to {scenario}."
            
            questions.append({
                "id": str(uuid.uuid4()),
                "text": question_text,
                "category": "behavioral",
                "difficulty": difficulty_level,
                "suggested_approach": "Use the STAR method (Situation, Task, Action, Result)",
                "key_points": self._generate_key_points("behavioral", scenario, []),
                "follow_ups": self._generate_follow_ups("behavioral", question_text)
            })
        
        return questions
    
    async def _generate_company_questions(
        self,
        job_requirements: Dict[str, Any],
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """Generate company-specific questions."""
        questions = []
        company = job_requirements.get("company", "the company")
        
        company_questions = [
            f"Why do you want to work at {company}?",
            f"What do you know about {company}'s products/services?",
            f"How do you align with {company}'s values and culture?",
            f"What questions do you have about working at {company}?",
            f"How would you contribute to {company}'s success?"
        ]
        
        question_count = 5 if difficulty_level == "advanced" else 3
        
        for i in range(min(question_count, len(company_questions))):
            question_text = company_questions[i]
            
            questions.append({
                "id": str(uuid.uuid4()),
                "text": question_text,
                "category": "company_specific",
                "difficulty": difficulty_level,
                "suggested_approach": f"Research {company} thoroughly and connect your values with theirs",
                "key_points": self._generate_key_points("company_specific", company, []),
                "follow_ups": self._generate_follow_ups("company_specific", question_text)
            })
        
        return questions
    
    def _generate_answer_approach(self, category: str, question: str) -> str:
        """Generate suggested approach for answering a question."""
        if category == "technical":
            return "Start with a brief overview, then dive into specifics. Use concrete examples from your experience."
        elif category == "behavioral":
            return "Use the STAR method: describe the Situation, Task, Action you took, and Result achieved."
        else:
            return "Be specific and authentic. Connect your answer to the company's values and mission."
    
    def _generate_key_points(self, category: str, context: str, skills: List[str]) -> List[str]:
        """Generate key points to cover in the answer."""
        if category == "technical":
            return [
                "Demonstrate deep understanding of the technology",
                "Provide specific examples from your experience",
                "Discuss best practices and trade-offs",
                "Show problem-solving approach"
            ]
        elif category == "behavioral":
            return [
                "Set clear context (Situation)",
                "Define your responsibility (Task)",
                "Explain your actions (Action)",
                "Quantify the outcome (Result)",
                "Reflect on lessons learned"
            ]
        else:
            return [
                "Show genuine interest and research",
                "Connect your values with company values",
                "Demonstrate understanding of company's mission",
                "Ask thoughtful questions"
            ]
    
    def _generate_follow_ups(self, category: str, question: str) -> List[str]:
        """Generate potential follow-up questions."""
        if category == "technical":
            return [
                "How would you scale this solution?",
                "What alternatives did you consider?",
                "How would you test this implementation?"
            ]
        elif category == "behavioral":
            return [
                "What would you do differently next time?",
                "How did this experience change your approach?",
                "What did you learn from this situation?"
            ]
        else:
            return [
                "What specific aspects interest you most?",
                "How do you see yourself contributing?",
                "What questions do you have for us?"
            ]
    
    async def _generate_talking_points(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized talking points."""
        talking_points = []
        
        # Experience highlights
        if "experience" in resume_data:
            for exp in resume_data["experience"][:2]:  # Top 2 experiences
                talking_points.append(
                    f"At {exp.get('company', 'previous role')}, I {exp.get('description', 'contributed to key projects')}"
                )
        
        # Skills alignment
        user_skills = resume_data.get("skills", [])
        job_skills = job_requirements.get("skills", [])
        matching_skills = [skill for skill in job_skills if skill.lower() in [s.lower() for s in user_skills]]
        
        if matching_skills:
            talking_points.append(
                f"My experience with {', '.join(matching_skills[:3])} directly aligns with your requirements"
            )
        
        # Achievements
        if "projects" in resume_data:
            for project in resume_data["projects"][:1]:  # Top project
                talking_points.append(
                    f"I successfully {project.get('description', 'delivered a key project')} using {', '.join(project.get('technologies', [])[:2])}"
                )
        
        # Career motivation
        talking_points.append(
            f"I'm excited about this {job_requirements.get('title', 'role')} because it combines my passion for {job_skills[0] if job_skills else 'technology'} with growth opportunities"
        )
        
        return talking_points
    
    async def _generate_star_examples(
        self,
        resume_data: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate STAR method examples from user's experience."""
        star_examples = []
        
        if "experience" in resume_data:
            for i, exp in enumerate(resume_data["experience"][:3]):  # Top 3 experiences
                competency = self.star_competencies[i % len(self.star_competencies)]
                
                star_example = {
                    "competency": competency,
                    "situation": f"At {exp.get('company', 'my previous role')}, we faced a challenge with {exp.get('description', 'a critical project')}",
                    "task": f"As {exp.get('position', 'a team member')}, I was responsible for finding a solution",
                    "action": f"I implemented {', '.join(job_requirements.get('skills', ['technical solutions'])[:2])} to address the issue",
                    "result": "This resulted in improved performance and team efficiency",
                    "relevance_score": 85.0
                }
                
                star_examples.append(star_example)
        
        return star_examples
    
    async def _get_company_insights(
        self,
        db: AsyncSession,
        company_name: str
    ) -> Dict[str, Any]:
        """Get or generate company insights."""
        # Check if we have existing insights
        result = await db.execute(
            select(CompanyInsight).where(
                CompanyInsight.company_name == company_name
            ).order_by(CompanyInsight.last_updated.desc())
        )
        existing_insight = result.scalar_one_or_none()
        
        if existing_insight:
            return {
                "culture": json.loads(existing_insight.culture_info) if existing_insight.culture_info else {},
                "values": json.loads(existing_insight.values) if existing_insight.values else [],
                "interview_process": json.loads(existing_insight.interview_process) if existing_insight.interview_process else {},
                "talking_points": json.loads(existing_insight.key_talking_points) if existing_insight.key_talking_points else [],
                "questions_to_ask": json.loads(existing_insight.questions_to_ask) if existing_insight.questions_to_ask else []
            }
        
        # Generate new insights (simplified for demo)
        insights = {
            "culture": {
                "description": f"{company_name} values innovation, collaboration, and excellence",
                "work_environment": "Fast-paced, collaborative, results-oriented"
            },
            "values": ["Innovation", "Collaboration", "Excellence", "Customer Focus"],
            "interview_process": {
                "stages": ["Phone Screen", "Technical Interview", "Team Interview", "Final Round"],
                "duration": "2-3 weeks",
                "focus": "Technical skills, cultural fit, problem-solving"
            },
            "talking_points": [
                f"Research {company_name}'s recent product launches",
                f"Understand {company_name}'s market position",
                f"Know {company_name}'s key competitors",
                f"Be familiar with {company_name}'s leadership team"
            ],
            "questions_to_ask": [
                "What are the biggest challenges facing the team?",
                "How do you measure success in this role?",
                "What opportunities are there for professional growth?",
                f"How does this role contribute to {company_name}'s goals?"
            ]
        }
        
        # Store insights for future use
        company_insight = CompanyInsight(
            id=str(uuid.uuid4()),
            company_name=company_name,
            culture_info=json.dumps(insights["culture"]),
            values=json.dumps(insights["values"]),
            interview_process=json.dumps(insights["interview_process"]),
            key_talking_points=json.dumps(insights["talking_points"]),
            questions_to_ask=json.dumps(insights["questions_to_ask"]),
            confidence_score=75.0
        )
        
        db.add(company_insight)
        await db.flush()
        
        return insights
    
    def _generate_preparation_checklist(
        self,
        job_requirements: Dict[str, Any],
        difficulty_level: str
    ) -> List[str]:
        """Generate preparation checklist."""
        checklist = [
            "Review your resume and be ready to discuss each experience",
            f"Research {job_requirements.get('company', 'the company')} thoroughly",
            "Prepare STAR method examples for behavioral questions",
            "Practice technical questions related to required skills",
            "Prepare thoughtful questions to ask the interviewer",
            "Review the job description and requirements",
            "Practice your elevator pitch (30-60 seconds)",
            "Prepare examples of your problem-solving approach"
        ]
        
        if difficulty_level == "advanced":
            checklist.extend([
                "Prepare system design examples",
                "Review leadership and mentoring experiences",
                "Prepare questions about company strategy and vision"
            ])
        
        return checklist
    
    def _calculate_prep_time(self, question_count: int, difficulty_level: str) -> int:
        """Calculate estimated preparation time in minutes."""
        base_time = question_count * 10  # 10 minutes per question
        
        if difficulty_level == "advanced":
            base_time *= 1.5
        elif difficulty_level == "beginner":
            base_time *= 0.8
        
        # Add time for research and practice
        total_time = base_time + 60  # 1 hour for research and practice
        
        return int(total_time)
    
    async def _create_question_records(
        self,
        db: AsyncSession,
        kit_id: str,
        user_id: str,
        questions: List[Dict[str, Any]]
    ):
        """Create individual question records."""
        for i, q in enumerate(questions):
            question = InterviewQuestion(
                id=q["id"],
                kit_id=kit_id,
                user_id=user_id,
                question_text=q["text"],
                category=q["category"],
                difficulty=q["difficulty"],
                suggested_answer=json.dumps({
                    "approach": q["suggested_approach"],
                    "key_points": q["key_points"]
                }),
                key_points=json.dumps(q["key_points"]),
                follow_up_questions=json.dumps(q["follow_ups"]),
                order_index=i
            )
            db.add(question)
    
    async def _create_star_records(
        self,
        db: AsyncSession,
        kit_id: str,
        user_id: str,
        star_examples: List[Dict[str, Any]],
        resume_data: Dict[str, Any]
    ):
        """Create STAR example records."""
        for star in star_examples:
            star_record = STARExample(
                id=str(uuid.uuid4()),
                kit_id=kit_id,
                user_id=user_id,
                situation=star["situation"],
                task=star["task"],
                action=star["action"],
                result=star["result"],
                competency=star["competency"],
                source_experience=json.dumps(resume_data.get("experience", [])),
                relevance_score=star["relevance_score"]
            )
            db.add(star_record)
    
    async def _analyze_user_answer(
        self,
        question_text: str,
        category: str,
        user_answer: str,
        suggested_answer: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze user's answer and provide feedback."""
        # Simple analysis (in production, this would use advanced NLP)
        answer_length = len(user_answer.split())
        
        # Score based on length and content
        score = min(100, max(20, answer_length * 2))  # Basic scoring
        
        feedback = {
            "score": score,
            "feedback": {
                "overall": "Good structure and content" if score > 70 else "Consider adding more specific details",
                "length": "Appropriate length" if 50 <= answer_length <= 200 else "Consider adjusting the length",
                "specificity": "Good use of specific examples" if "I" in user_answer and ("project" in user_answer.lower() or "experience" in user_answer.lower()) else "Add more specific examples"
            },
            "suggestions": [
                "Use the STAR method for behavioral questions",
                "Include quantifiable results when possible",
                "Connect your answer to the job requirements"
            ],
            "strengths": [
                "Clear communication" if answer_length > 30 else "Concise response",
                "Relevant experience mentioned" if any(word in user_answer.lower() for word in ["project", "team", "developed", "implemented"]) else "Good foundation"
            ]
        }
        
        return feedback
    
    async def _format_kit_response(self, kit: InterviewKit) -> Dict[str, Any]:
        """Format interview kit for API response."""
        return {
            "id": kit.id,
            "job_id": kit.job_id,
            "questions": json.loads(kit.questions),
            "talking_points": json.loads(kit.talking_points),
            "company_insights": json.loads(kit.company_insights) if kit.company_insights else {},
            "star_examples": json.loads(kit.star_examples) if kit.star_examples else [],
            "preparation_checklist": json.loads(kit.preparation_checklist) if kit.preparation_checklist else [],
            "difficulty_level": kit.difficulty_level,
            "estimated_prep_time": kit.estimated_prep_time,
            "created_at": kit.created_at.isoformat(),
            "updated_at": kit.updated_at.isoformat() if kit.updated_at else None
        }