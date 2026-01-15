"""
Apply kit generation service.
Generates cover letters, tailored bullets, and interview Q&A.

Task 2.3: Made generation deterministic for property-based testing.
"""
from typing import Dict, List, Optional, Any
import json
import logging
import hashlib

logger = logging.getLogger(__name__)


class ApplyKitGenerator:
    """Service for generating application kits."""
    
    # Common interview questions (sorted for determinism)
    INTERVIEW_QUESTIONS = sorted([
        "Tell me about yourself",
        "Why are you interested in this role?",
        "What are your strengths?",
        "What are your weaknesses?",
        "Describe a challenging project you worked on",
        "How do you handle conflicts with team members?",
        "Where do you see yourself in 5 years?",
        "What is your greatest achievement?",
        "Why should we hire you?",
        "What are your salary expectations?",
    ])
    
    @staticmethod
    def _generate_seed(user_name: str, job_title: str, company_name: str) -> int:
        """
        Generate a deterministic seed from input parameters.
        
        This ensures that the same inputs always produce the same outputs,
        which is critical for property-based testing.
        
        Args:
            user_name: User's name
            job_title: Job title
            company_name: Company name
            
        Returns:
            Integer seed for deterministic generation
        """
        # Create a hash of the inputs
        hash_input = f"{user_name}|{job_title}|{company_name}".encode('utf-8')
        hash_value = hashlib.sha256(hash_input).hexdigest()
        # Convert first 8 characters of hash to integer
        return int(hash_value[:8], 16)
    
    @staticmethod
    def generate_cover_letter(
        user_name: str,
        job_title: str,
        company_name: str,
        resume_text: str,
        job_description: str,
        seed: Optional[int] = None,  # Task 2.3: Added for determinism
    ) -> str:
        """
        Generate a tailored cover letter.
        
        Task 2.3: Made deterministic by using seed-based selection.
        
        Args:
            user_name: User's name
            job_title: Job title
            company_name: Company name
            resume_text: Resume content
            job_description: Job description
            seed: Optional seed for deterministic generation
            
        Returns:
            Generated cover letter
        """
        try:
            # Generate deterministic seed if not provided
            if seed is None:
                seed = ApplyKitGenerator._generate_seed(user_name, job_title, company_name)
            
            # Extract key skills from resume (sorted for determinism)
            resume_lower = resume_text.lower()
            skills = []
            
            # Common skill keywords (sorted)
            skill_keywords = sorted([
                'python', 'javascript', 'java', 'react', 'node.js', 'fastapi',
                'leadership', 'project management', 'communication', 'teamwork',
                'agile', 'scrum', 'docker', 'kubernetes', 'aws', 'gcp',
            ])
            
            for skill in skill_keywords:
                if skill in resume_lower:
                    skills.append(skill)
            
            # Extract key requirements from job description (sorted)
            job_lower = job_description.lower()
            requirements = []
            
            for skill in skill_keywords:
                if skill in job_lower:
                    requirements.append(skill)
            
            # Generate achievement using deterministic selection
            achievement = ApplyKitGenerator._generate_achievement(resume_text, seed)
            
            # Generate cover letter
            cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. With my background in {', '.join(skills[:3]) if skills else 'software development'}, I am confident that I can make a significant contribution to your team.

Throughout my career, I have developed expertise in {', '.join(sorted(set(skills[:5]))) if skills else 'various technologies'}. I am particularly drawn to this opportunity because of {company_name}'s commitment to innovation and excellence. The role aligns perfectly with my professional goals and skills.

In my current role, I have successfully {achievement}. I am excited about the opportunity to bring this experience to {company_name} and help achieve your team's objectives.

I am particularly interested in the {', '.join(sorted(requirements[:2])) if requirements else 'technical challenges'} mentioned in the job description. My experience with {', '.join(sorted(set(skills[:3]))) if skills else 'modern technologies'} positions me well to contribute immediately.

Thank you for considering my application. I would welcome the opportunity to discuss how my skills and experience can benefit {company_name}. I am available for an interview at your convenience.

Best regards,
{user_name}"""
            
            return cover_letter
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return f"Dear Hiring Manager,\n\nI am interested in the {job_title} position at {company_name}. I believe my skills and experience make me a strong candidate for this role.\n\nBest regards,\n{user_name}"
    
    @staticmethod
    def _generate_achievement(resume_text: str, seed: int) -> str:
        """
        Extract or generate an achievement statement deterministically.
        
        Task 2.3: Uses seed for consistent selection.
        
        Args:
            resume_text: Resume content
            seed: Seed for deterministic selection
            
        Returns:
            Achievement statement
        """
        achievements = sorted([  # Sorted for determinism
            "led a team to deliver a critical project on time",
            "improved system performance by optimizing code",
            "mentored junior developers and improved team productivity",
            "implemented new features that increased user engagement",
            "reduced technical debt and improved code quality",
        ])
        
        # Try to find achievement keywords in resume
        resume_lower = resume_text.lower()
        for achievement in achievements:
            if any(word in resume_lower for word in achievement.split()):
                return achievement
        
        # Use seed to select deterministically
        index = seed % len(achievements)
        return achievements[index]
    
    @staticmethod
    def generate_tailored_bullets(
        resume_text: str,
        job_description: str,
        job_title: str,
        seed: Optional[int] = None,  # Task 2.3: Added for determinism
    ) -> List[str]:
        """
        Generate tailored resume bullets for the job.
        
        Task 2.3: Made deterministic by sorting outputs.
        
        Args:
            resume_text: Resume content
            job_description: Job description
            job_title: Job title
            seed: Optional seed for deterministic generation
            
        Returns:
            List of tailored bullets (sorted for determinism)
        """
        try:
            # Extract key requirements from job description
            job_lower = job_description.lower()
            
            # Skill keywords to match (sorted for determinism)
            skill_keywords = {
                'agile': 'Agile methodologies',
                'aws': 'AWS cloud services',
                'docker': 'Docker containerization',
                'fastapi': 'FastAPI',
                'gcp': 'Google Cloud Platform',
                'javascript': 'JavaScript/TypeScript',
                'kubernetes': 'Kubernetes orchestration',
                'leadership': 'Team leadership',
                'node.js': 'Node.js backend',
                'project management': 'Project management',
                'python': 'Python development',
                'react': 'React frontend',
                'scrum': 'Scrum practices',
            }
            
            tailored_bullets = []
            
            # Generate bullets based on job requirements (sorted order)
            for skill in sorted(skill_keywords.keys()):
                description = skill_keywords[skill]
                
                if skill in job_lower:
                    if skill in resume_text.lower():
                        # Skill match - create tailored bullet
                        if skill == 'python':
                            tailored_bullets.append(
                                "Developed scalable Python applications using FastAPI and SQLAlchemy"
                            )
                        elif skill == 'javascript':
                            tailored_bullets.append(
                                "Built responsive web applications with React and TypeScript"
                            )
                        elif skill == 'react':
                            tailored_bullets.append(
                                "Created interactive user interfaces with React and modern CSS frameworks"
                            )
                        elif skill == 'docker':
                            tailored_bullets.append(
                                "Containerized applications using Docker for consistent deployment"
                            )
                        elif skill == 'kubernetes':
                            tailored_bullets.append(
                                "Orchestrated microservices using Kubernetes in production environments"
                            )
                        elif skill == 'aws':
                            tailored_bullets.append(
                                "Deployed and managed applications on AWS using EC2, S3, and RDS"
                            )
                        elif skill == 'leadership':
                            tailored_bullets.append(
                                "Led cross-functional teams to deliver projects on time and within budget"
                            )
                        elif skill == 'agile':
                            tailored_bullets.append(
                                "Implemented Agile methodologies to improve team productivity and delivery"
                            )
            
            # Add generic bullets if not enough (sorted)
            if len(tailored_bullets) < 3:
                generic_bullets = sorted([
                    "Collaborated with stakeholders to understand requirements and deliver solutions",
                    "Improved code quality through code reviews and best practices",
                    "Mentored junior team members and contributed to team growth",
                ])
                tailored_bullets.extend(generic_bullets)
            
            # Return top 5 bullets, sorted for determinism
            return sorted(tailored_bullets[:5])
            
        except Exception as e:
            logger.error(f"Error generating tailored bullets: {e}")
            return sorted([
                "Collaborated with cross-functional teams",
                "Developed and maintained software solutions",
                "Improved system performance and reliability",
            ])
    
    @staticmethod
    def generate_interview_qa(
        resume_text: str,
        job_description: str,
        job_title: str,
        seed: Optional[int] = None,  # Task 2.3: Added for determinism
    ) -> Dict[str, str]:
        """
        Generate interview Q&A based on resume and job.
        
        Task 2.3: Made deterministic by using sorted outputs.
        
        Args:
            resume_text: Resume content
            job_description: Job description
            job_title: Job title
            seed: Optional seed for deterministic generation
            
        Returns:
            Dictionary of questions and answers (sorted keys for determinism)
        """
        try:
            qa = {}
            
            # Question 1: Tell me about yourself
            qa["Tell me about yourself"] = (
                f"I'm a professional with experience in software development. "
                f"I'm particularly interested in the {job_title} role at your company because "
                f"it aligns with my career goals and allows me to contribute my skills in a meaningful way."
            )
            
            # Question 2: Why this role?
            qa["Why are you interested in this role?"] = (
                f"I'm excited about the {job_title} position because it offers the opportunity to work on "
                f"challenging projects and grow my skills. Your company's commitment to innovation and "
                f"excellence resonates with my professional values."
            )
            
            # Question 3: Strengths (sorted for determinism)
            strengths = []
            resume_lower = resume_text.lower()
            
            if 'python' in resume_lower or 'javascript' in resume_lower:
                strengths.append("strong programming skills")
            if 'leadership' in resume_lower or 'led' in resume_lower:
                strengths.append("leadership experience")
            if 'communication' in resume_lower or 'presentation' in resume_lower:
                strengths.append("excellent communication abilities")
            
            if not strengths:
                strengths = sorted(["attention to detail", "problem-solving", "teamwork"])
            else:
                strengths = sorted(strengths)
            
            qa["What are your strengths?"] = (
                f"My key strengths include {', '.join(strengths[:3])}. "
                f"I'm also known for my ability to learn quickly and adapt to new technologies."
            )
            
            # Question 4: Weaknesses
            qa["What are your weaknesses?"] = (
                "I tend to be a perfectionist, which sometimes means I spend more time on details than necessary. "
                "However, I've learned to balance this by setting priorities and focusing on what matters most. "
                "I'm also continuously working to improve my public speaking skills."
            )
            
            # Question 5: Challenge
            qa["Describe a challenging project you worked on"] = (
                "In a recent project, I faced the challenge of optimizing a slow database query that was affecting user experience. "
                "I analyzed the query execution plan, identified the bottleneck, and implemented an index strategy that improved performance by 40%. "
                "This experience taught me the importance of data-driven problem solving."
            )
            
            # Question 6: Conflict resolution
            qa["How do you handle conflicts with team members?"] = (
                "I believe in open communication and understanding different perspectives. "
                "When conflicts arise, I listen actively to understand the other person's viewpoint, "
                "find common ground, and work collaboratively toward a solution that benefits the team."
            )
            
            # Question 7: Future goals
            qa["Where do you see yourself in 5 years?"] = (
                "I see myself as a senior professional with deeper expertise in my field, "
                "potentially in a leadership role where I can mentor others and contribute to strategic decisions. "
                "I'm committed to continuous learning and staying current with industry trends."
            )
            
            # Question 8: Why hire you
            qa["Why should we hire you?"] = (
                f"I bring a combination of technical skills, problem-solving ability, and strong work ethic. "
                f"I'm particularly well-suited for the {job_title} role because my experience aligns with your requirements, "
                f"and I'm genuinely excited about contributing to your team's success."
            )
            
            # Return with sorted keys for determinism
            return dict(sorted(qa.items()))
            
        except Exception as e:
            logger.error(f"Error generating interview Q&A: {e}")
            return {
                "Tell me about yourself": "I'm a professional with experience in software development.",
                "Why this role?": "I'm interested in this opportunity to grow and contribute.",
            }
