"""
Resume parsing service - extracts structured data from PDF/DOCX files.
"""
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import PyPDF2
import docx


class ResumeParser:
    """Parse resumes and extract structured profile data."""
    
    # Common section headers
    SECTION_PATTERNS = {
        'experience': r'(?i)(work\s+experience|professional\s+experience|employment\s+history|experience)',
        'education': r'(?i)(education|academic\s+background|qualifications)',
        'skills': r'(?i)(skills|technical\s+skills|core\s+competencies)',
        'certifications': r'(?i)(certifications?|licenses?)',
        'summary': r'(?i)(summary|profile|objective|about\s+me)',
    }
    
    # Contact info patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
        return text
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
        return text
    
    @classmethod
    def extract_text(cls, file_path: str, mime_type: str) -> str:
        """Extract text based on file type."""
        if mime_type == "application/pdf":
            return cls.extract_text_from_pdf(file_path)
        elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            return cls.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")
    
    @classmethod
    def extract_contact_info(cls, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information from text."""
        contact = {
            'email': None,
            'phone': None,
            'name': None,
            'location': None
        }
        
        # Extract email
        email_match = re.search(cls.EMAIL_PATTERN, text)
        if email_match:
            contact['email'] = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(cls.PHONE_PATTERN, text)
        if phone_match:
            contact['phone'] = phone_match.group(0)
        
        # Extract name (first non-empty line, heuristic)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Name is usually in first 3 lines
            for line in lines[:3]:
                if len(line) < 50 and not re.search(cls.EMAIL_PATTERN, line) and not re.search(cls.PHONE_PATTERN, line):
                    contact['name'] = line
                    break
        
        return contact
    
    @classmethod
    def extract_sections(cls, text: str) -> Dict[str, str]:
        """Extract major sections from resume text."""
        sections = {}
        
        for section_name, pattern in cls.SECTION_PATTERNS.items():
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                start_pos = match.end()
                # Find next section or end of text
                next_section_pos = len(text)
                for other_pattern in cls.SECTION_PATTERNS.values():
                    other_match = re.search(other_pattern, text[start_pos:], re.MULTILINE)
                    if other_match:
                        pos = start_pos + other_match.start()
                        if pos < next_section_pos:
                            next_section_pos = pos
                
                sections[section_name] = text[start_pos:next_section_pos].strip()
        
        return sections
    
    @classmethod
    def extract_skills(cls, text: str, skills_section: Optional[str] = None) -> List[str]:
        """Extract skills from resume."""
        skills = []
        
        # Use skills section if available
        search_text = skills_section if skills_section else text
        
        # Common skill keywords (simplified list)
        skill_keywords = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes',
            'AWS', 'Azure', 'GCP', 'Git', 'CI/CD', 'Agile', 'Scrum', 'REST', 'GraphQL',
            'Machine Learning', 'AI', 'Data Science', 'TensorFlow', 'PyTorch',
        ]
        
        for skill in skill_keywords:
            if re.search(r'\b' + re.escape(skill) + r'\b', search_text, re.IGNORECASE):
                skills.append(skill)
        
        return list(set(skills))  # Remove duplicates
    
    @classmethod
    def parse(cls, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Parse resume and extract structured data.
        
        Returns:
            Dict with raw_text and parsed_data
        """
        # Extract raw text
        raw_text = cls.extract_text(file_path, mime_type)
        
        if not raw_text.strip():
            raise ValueError("No text could be extracted from the resume")
        
        # Extract contact info
        contact = cls.extract_contact_info(raw_text)
        
        # Extract sections
        sections = cls.extract_sections(raw_text)
        
        # Extract skills
        skills = cls.extract_skills(raw_text, sections.get('skills'))
        
        # Build parsed data structure
        parsed_data = {
            'name': contact.get('name'),
            'email': contact.get('email'),
            'phone': contact.get('phone'),
            'location': contact.get('location'),
            'summary': sections.get('summary', '')[:500] if sections.get('summary') else None,
            'experience': cls._parse_experience(sections.get('experience', '')),
            'education': cls._parse_education(sections.get('education', '')),
            'skills': skills,
            'certifications': cls._parse_certifications(sections.get('certifications', '')),
            'languages': []  # Placeholder for future enhancement
        }
        
        return {
            'raw_text': raw_text,
            'parsed_data': parsed_data
        }
    
    @staticmethod
    def _parse_experience(text: str) -> List[Dict[str, Any]]:
        """Parse experience section (simplified)."""
        if not text:
            return []
        
        # Split by common delimiters (years, bullet points)
        experiences = []
        lines = text.split('\n')
        
        current_exp = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for year patterns (e.g., 2020-2023, 2020 - Present)
            year_match = re.search(r'(20\d{2})\s*[-–]\s*(20\d{2}|Present|Current)', line, re.IGNORECASE)
            if year_match:
                if current_exp:
                    experiences.append(current_exp)
                current_exp = {
                    'title': line,
                    'period': year_match.group(0),
                    'description': ''
                }
            elif current_exp:
                current_exp['description'] += line + ' '
        
        if current_exp:
            experiences.append(current_exp)
        
        return experiences[:5]  # Limit to 5 most recent
    
    @staticmethod
    def _parse_education(text: str) -> List[Dict[str, Any]]:
        """Parse education section (simplified)."""
        if not text:
            return []
        
        education = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for degree keywords
            if re.search(r'(Bachelor|Master|PhD|B\.S\.|M\.S\.|MBA|Diploma)', line, re.IGNORECASE):
                education.append({
                    'degree': line,
                    'institution': '',
                    'year': ''
                })
        
        return education[:3]  # Limit to 3
    
    @staticmethod
    def _parse_certifications(text: str) -> List[str]:
        """Parse certifications section (simplified)."""
        if not text:
            return []
        
        certifications = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:  # Filter out empty or very short lines
                certifications.append(line)
        
        return certifications[:5]  # Limit to 5
