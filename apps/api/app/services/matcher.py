"""
Job matching service.
Computes match scores using TF-IDF, skill overlap, and location preferences.
"""
from typing import Dict, List, Tuple, Optional, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import logging
import re

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for computing job matches."""
    
    # Common tech skills dictionary
    TECH_SKILLS = {
        'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'rust',
        'react', 'vue', 'angular', 'node.js', 'express', 'django', 'flask',
        'fastapi', 'spring', 'rails', 'laravel', 'asp.net',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'terraform',
        'git', 'ci/cd', 'jenkins', 'github actions', 'gitlab ci',
        'machine learning', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas',
        'html', 'css', 'sass', 'tailwind', 'bootstrap',
        'rest api', 'graphql', 'websockets', 'grpc',
        'agile', 'scrum', 'kanban', 'jira',
        'linux', 'unix', 'windows', 'macos',
        'testing', 'pytest', 'jest', 'mocha', 'rspec',
        'devops', 'sre', 'monitoring', 'logging', 'observability',
    }
    
    # Soft skills
    SOFT_SKILLS = {
        'communication', 'leadership', 'teamwork', 'problem solving',
        'critical thinking', 'time management', 'project management',
        'mentoring', 'collaboration', 'adaptability', 'creativity',
    }
    
    @staticmethod
    def extract_skills_from_text(text: str) -> Tuple[List[str], List[str]]:
        """
        Extract tech and soft skills from text.
        
        Args:
            text: Resume or job description text
            
        Returns:
            Tuple of (tech_skills, soft_skills)
        """
        text_lower = text.lower()
        
        # Extract tech skills
        tech_skills = []
        for skill in MatchingService.TECH_SKILLS:
            if skill in text_lower:
                tech_skills.append(skill)
        
        # Extract soft skills
        soft_skills = []
        for skill in MatchingService.SOFT_SKILLS:
            if skill in text_lower:
                soft_skills.append(skill)
        
        return tech_skills, soft_skills
    
    @staticmethod
    def compute_tf_idf_similarity(resume_text: str, job_description: str) -> float:
        """
        Compute TF-IDF cosine similarity between resume and job description.
        
        Args:
            resume_text: Resume content
            job_description: Job description content
            
        Returns:
            Similarity score (0-1)
        """
        try:
            if not resume_text or not job_description:
                return 0.0
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                lowercase=True,
                ngram_range=(1, 2),
            )
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
            
            # Compute cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error computing TF-IDF similarity: {e}")
            return 0.0
    
    @staticmethod
    def compute_skill_overlap(resume_skills: List[str], job_skills: List[str]) -> Tuple[float, List[str]]:
        """
        Compute skill overlap score and missing skills.
        
        Args:
            resume_skills: Skills from resume
            job_skills: Skills from job description
            
        Returns:
            Tuple of (overlap_score 0-1, missing_skills list)
        """
        if not job_skills:
            return 1.0, []
        
        resume_skills_set = set(s.lower() for s in resume_skills)
        job_skills_set = set(s.lower() for s in job_skills)
        
        # Find overlap
        overlap = resume_skills_set.intersection(job_skills_set)
        missing = job_skills_set - resume_skills_set
        
        # Score: percentage of job skills that candidate has
        overlap_score = len(overlap) / len(job_skills_set) if job_skills_set else 1.0
        
        return min(overlap_score, 1.0), list(missing)
    
    @staticmethod
    def compute_location_bonus(
        user_location: Optional[str],
        user_remote_preference: Optional[str],
        job_location: Optional[str],
        job_work_type: Optional[str],
    ) -> float:
        """
        Compute location/remote preference bonus.
        
        Args:
            user_location: User's preferred location
            user_remote_preference: User's remote preference (remote, full-time, etc)
            job_location: Job location
            job_work_type: Job work type (remote, full-time, etc)
            
        Returns:
            Bonus score (0-0.2)
        """
        bonus = 0.0
        
        # Remote preference bonus
        if user_remote_preference == 'remote' and job_work_type == 'remote':
            bonus += 0.15
        elif user_remote_preference == 'hybrid' and job_work_type in ['hybrid', 'remote']:
            bonus += 0.10
        
        # Location match bonus
        if user_location and job_location:
            user_loc_lower = user_location.lower()
            job_loc_lower = job_location.lower()
            
            if user_loc_lower in job_loc_lower or job_loc_lower in user_loc_lower:
                bonus += 0.05
        
        return min(bonus, 0.2)
    
    @staticmethod
    def compute_match_score(
        resume_text: str,
        job_description: str,
        resume_skills: List[str],
        job_skills: List[str],
        user_location: Optional[str],
        user_remote_preference: Optional[str],
        job_location: Optional[str],
        job_work_type: Optional[str],
    ) -> Dict[str, Any]:
        """
        Compute overall match score and explanation.
        
        Args:
            resume_text: Resume content
            job_description: Job description
            resume_skills: Skills from resume
            job_skills: Skills from job
            user_location: User's location
            user_remote_preference: User's remote preference
            job_location: Job location
            job_work_type: Job work type
            
        Returns:
            Dictionary with score, breakdown, explanation, and missing skills
        """
        # Compute components
        tf_idf_score = MatchingService.compute_tf_idf_similarity(resume_text, job_description)
        skill_overlap, missing_skills = MatchingService.compute_skill_overlap(resume_skills, job_skills)
        location_bonus = MatchingService.compute_location_bonus(
            user_location, user_remote_preference, job_location, job_work_type
        )
        
        # Weighted combination
        # TF-IDF: 50%, Skill Overlap: 40%, Location Bonus: 10%
        match_score = (
            tf_idf_score * 0.50 +
            skill_overlap * 0.40 +
            location_bonus * 0.10
        )
        
        # Convert to 0-100 scale
        match_score_100 = match_score * 100
        
        # Build explanation
        reasons = []
        strengths = []
        
        if tf_idf_score > 0.7:
            strengths.append("Strong content match with job description")
        elif tf_idf_score > 0.5:
            reasons.append("Moderate content match with job description")
        else:
            reasons.append("Limited content match - consider tailoring resume")
        
        if skill_overlap > 0.8:
            strengths.append(f"Has {int(skill_overlap * 100)}% of required skills")
        elif skill_overlap > 0.5:
            reasons.append(f"Has {int(skill_overlap * 100)}% of required skills - missing some key skills")
        else:
            reasons.append(f"Only has {int(skill_overlap * 100)}% of required skills")
        
        if location_bonus > 0.1:
            strengths.append("Matches location/remote preferences")
        
        return {
            'match_score': match_score_100,
            'score_breakdown': {
                'tf_idf': tf_idf_score * 100,
                'skill_overlap': skill_overlap * 100,
                'location_bonus': location_bonus * 100,
            },
            'why': {
                'reasons': reasons,
                'strengths': strengths,
            },
            'missing_skills': missing_skills,
        }
