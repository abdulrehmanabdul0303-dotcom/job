"""
Preference detection service.
Auto-detects job preferences from resume text using simple rules and patterns.
"""
from typing import Dict, List, Optional, Set
import re
from app.models.resume import Resume
from app.schemas.preferences import PreferencesCreate


class PreferenceDetector:
    """Service for auto-detecting job preferences from resume text."""
    
    # Common job titles and their categories
    JOB_TITLES = {
        'software': ['software engineer', 'software developer', 'programmer', 'coder'],
        'frontend': ['frontend developer', 'front-end developer', 'ui developer', 'react developer', 'vue developer', 'angular developer'],
        'backend': ['backend developer', 'back-end developer', 'api developer', 'server developer'],
        'fullstack': ['full stack developer', 'fullstack developer', 'full-stack engineer'],
        'devops': ['devops engineer', 'site reliability engineer', 'sre', 'platform engineer'],
        'data': ['data scientist', 'data analyst', 'data engineer', 'ml engineer', 'machine learning engineer'],
        'mobile': ['mobile developer', 'ios developer', 'android developer', 'react native developer'],
        'qa': ['qa engineer', 'test engineer', 'quality assurance', 'sdet'],
        'manager': ['engineering manager', 'technical lead', 'team lead', 'tech lead', 'project manager'],
        'designer': ['ui designer', 'ux designer', 'product designer', 'graphic designer'],
    }
    
    # Skills that indicate specific roles
    SKILL_TO_ROLE = {
        'react': 'Frontend Developer',
        'vue': 'Frontend Developer',
        'angular': 'Frontend Developer',
        'javascript': 'Frontend Developer',
        'typescript': 'Frontend Developer',
        'node.js': 'Backend Developer',
        'python': 'Backend Developer',
        'java': 'Backend Developer',
        'go': 'Backend Developer',
        'rust': 'Backend Developer',
        'docker': 'DevOps Engineer',
        'kubernetes': 'DevOps Engineer',
        'aws': 'DevOps Engineer',
        'terraform': 'DevOps Engineer',
        'machine learning': 'Data Scientist',
        'tensorflow': 'Data Scientist',
        'pytorch': 'Data Scientist',
        'pandas': 'Data Analyst',
        'sql': 'Data Analyst',
        'swift': 'iOS Developer',
        'kotlin': 'Android Developer',
        'react native': 'Mobile Developer',
        'flutter': 'Mobile Developer',
    }
    
    # Work type keywords
    REMOTE_KEYWORDS = ['remote', 'work from home', 'wfh', 'distributed', 'telecommute']
    FULLTIME_KEYWORDS = ['full-time', 'full time', 'permanent', 'fte']
    PARTTIME_KEYWORDS = ['part-time', 'part time', 'contract', 'freelance', 'consultant']
    
    # Country codes and names
    COUNTRY_MAPPING = {
        'united states': 'US',
        'usa': 'US',
        'america': 'US',
        'us': 'US',
        'canada': 'CA',
        'united kingdom': 'GB',
        'uk': 'GB',
        'britain': 'GB',
        'germany': 'DE',
        'france': 'FR',
        'india': 'IN',
        'australia': 'AU',
        'singapore': 'SG',
        'netherlands': 'NL',
        'sweden': 'SE',
        'switzerland': 'CH',
    }
    
    @staticmethod
    def detect_from_resume(resume: Resume) -> PreferencesCreate:
        """
        Auto-detect job preferences from resume text.
        
        Args:
            resume: Resume object with raw_text
            
        Returns:
            PreferencesCreate object with detected preferences
        """
        text = (resume.raw_text or '').lower()
        
        # Detect desired role
        desired_role = PreferenceDetector._detect_role(text)
        
        # Detect preferred countries
        preferred_countries = PreferenceDetector._detect_countries(text)
        
        # Detect work type
        work_type = PreferenceDetector._detect_work_type(text)
        
        # Detect salary expectations (basic pattern matching)
        min_salary, max_salary = PreferenceDetector._detect_salary(text)
        
        return PreferencesCreate(
            desired_role=desired_role,
            preferred_countries=preferred_countries if preferred_countries else None,
            min_salary=min_salary,
            max_salary=max_salary,
            work_type=work_type,
        )
    
    @staticmethod
    def _detect_role(text: str) -> Optional[str]:
        """Detect desired job role from resume text."""
        # First, try to find explicit job titles
        for category, titles in PreferenceDetector.JOB_TITLES.items():
            for title in titles:
                if title in text:
                    return title.title()
        
        # If no explicit title found, infer from skills
        skill_scores: Dict[str, int] = {}
        for skill, role in PreferenceDetector.SKILL_TO_ROLE.items():
            if skill.lower() in text:
                skill_scores[role] = skill_scores.get(role, 0) + 1
        
        if skill_scores:
            # Return role with highest skill count
            return max(skill_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    @staticmethod
    def _detect_countries(text: str) -> List[str]:
        """Detect preferred countries from resume text."""
        detected: Set[str] = set()
        
        for country_name, country_code in PreferenceDetector.COUNTRY_MAPPING.items():
            if country_name in text:
                detected.add(country_code)
        
        return list(detected) if detected else []
    
    @staticmethod
    def _detect_work_type(text: str) -> Optional[str]:
        """Detect preferred work type from resume text."""
        # Check for remote keywords
        remote_count = sum(1 for keyword in PreferenceDetector.REMOTE_KEYWORDS if keyword in text)
        fulltime_count = sum(1 for keyword in PreferenceDetector.FULLTIME_KEYWORDS if keyword in text)
        parttime_count = sum(1 for keyword in PreferenceDetector.PARTTIME_KEYWORDS if keyword in text)
        
        # Return most mentioned type
        if remote_count > 0:
            return 'remote'
        elif fulltime_count > parttime_count:
            return 'full-time'
        elif parttime_count > 0:
            return 'part-time'
        
        # Default to full-time if nothing detected
        return 'full-time'
    
    @staticmethod
    def _detect_salary(text: str) -> tuple[Optional[int], Optional[int]]:
        """Detect salary expectations from resume text."""
        # Look for salary patterns like "$80k", "$80,000", "80k", "80000"
        salary_patterns = [
            r'\$(\d{2,3})[kK]',  # $80k
            r'\$(\d{2,3}),(\d{3})',  # $80,000
            r'(\d{2,3})[kK]',  # 80k
            r'salary.*?(\d{2,3})[kK]',  # salary: 80k
            r'expecting.*?(\d{2,3})[kK]',  # expecting 80k
        ]
        
        salaries = []
        for pattern in salary_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle patterns like $80,000
                    salary = int(match[0]) * 1000
                else:
                    # Handle patterns like 80k
                    salary = int(match) * 1000
                salaries.append(salary)
        
        if not salaries:
            return None, None
        
        # If we found salaries, use min and max
        min_salary = min(salaries)
        max_salary = max(salaries)
        
        # If only one salary found, create a range around it
        if min_salary == max_salary:
            return min_salary, int(min_salary * 1.3)  # 30% range
        
        return min_salary, max_salary
