"""
ATS Scoring Service - Calculates resume ATS score with detailed breakdown.
Scoring: Contact(20) + Sections(20) + Keywords(30) + Formatting(15) + Impact(15) = 100
"""
import re
from typing import Dict, Any, List, Tuple


class ATSScorer:
    """Calculate ATS score and provide detailed analysis."""
    
    # Industry-standard keywords by category
    TECHNICAL_KEYWORDS = [
        'Python', 'JavaScript', 'Java', 'C++', 'SQL', 'React', 'Node.js', 'AWS',
        'Docker', 'Kubernetes', 'Git', 'API', 'Database', 'Cloud', 'Agile', 'CI/CD'
    ]
    
    SOFT_SKILLS = [
        'leadership', 'communication', 'teamwork', 'problem-solving', 'analytical',
        'project management', 'collaboration', 'strategic', 'innovative'
    ]
    
    IMPACT_VERBS = [
        'achieved', 'improved', 'increased', 'reduced', 'led', 'managed', 'developed',
        'implemented', 'designed', 'created', 'optimized', 'delivered', 'launched'
    ]
    
    REQUIRED_SECTIONS = ['experience', 'education', 'skills']
    OPTIONAL_SECTIONS = ['summary', 'certifications']
    
    @classmethod
    def calculate_score(cls, parsed_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Calculate comprehensive ATS score.
        
        Returns:
            Dict with scores, breakdown, and recommendations
        """
        # Calculate individual scores
        contact_score = cls._score_contact_info(parsed_data)
        sections_score = cls._score_sections(parsed_data)
        keywords_score, missing_keywords = cls._score_keywords(parsed_data, raw_text)
        formatting_score, formatting_issues = cls._score_formatting(raw_text)
        impact_score = cls._score_impact(parsed_data, raw_text)
        
        # Calculate total
        ats_score = contact_score + sections_score + keywords_score + formatting_score + impact_score
        
        # Generate suggestions
        suggestions = cls._generate_suggestions(
            contact_score, sections_score, keywords_score, 
            formatting_score, impact_score, parsed_data
        )
        
        # Identify strengths
        strengths = cls._identify_strengths(
            contact_score, sections_score, keywords_score,
            formatting_score, impact_score, parsed_data
        )
        
        return {
            'ats_score': ats_score,
            'contact_score': contact_score,
            'sections_score': sections_score,
            'keywords_score': keywords_score,
            'formatting_score': formatting_score,
            'impact_score': impact_score,
            'missing_keywords': missing_keywords,
            'formatting_issues': formatting_issues,
            'suggestions': suggestions,
            'strengths': strengths
        }
    
    @classmethod
    def _score_contact_info(cls, parsed_data: Dict[str, Any]) -> int:
        """Score contact information completeness (0-20)."""
        score = 0
        
        # Email (8 points)
        if parsed_data.get('email'):
            score += 8
        
        # Phone (6 points)
        if parsed_data.get('phone'):
            score += 6
        
        # Name (4 points)
        if parsed_data.get('name'):
            score += 4
        
        # Location (2 points)
        if parsed_data.get('location'):
            score += 2
        
        return score
    
    @classmethod
    def _score_sections(cls, parsed_data: Dict[str, Any]) -> int:
        """Score presence of required sections (0-20)."""
        score = 0
        
        # Experience section (8 points)
        if parsed_data.get('experience') and len(parsed_data['experience']) > 0:
            score += 8
        
        # Education section (6 points)
        if parsed_data.get('education') and len(parsed_data['education']) > 0:
            score += 6
        
        # Skills section (4 points)
        if parsed_data.get('skills') and len(parsed_data['skills']) > 0:
            score += 4
        
        # Summary/Objective (2 points bonus)
        if parsed_data.get('summary'):
            score += 2
        
        return min(score, 20)  # Cap at 20
    
    @classmethod
    def _score_keywords(cls, parsed_data: Dict[str, Any], raw_text: str) -> Tuple[int, List[str]]:
        """Score keyword presence (0-30) and return missing keywords."""
        found_keywords = []
        missing_keywords = []
        
        # Check technical keywords
        for keyword in cls.TECHNICAL_KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', raw_text, re.IGNORECASE):
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Check soft skills
        for skill in cls.SOFT_SKILLS:
            if re.search(r'\b' + re.escape(skill) + r'\b', raw_text, re.IGNORECASE):
                found_keywords.append(skill)
        
        # Calculate score based on keyword density
        keyword_count = len(found_keywords)
        
        if keyword_count >= 15:
            score = 30
        elif keyword_count >= 10:
            score = 25
        elif keyword_count >= 7:
            score = 20
        elif keyword_count >= 5:
            score = 15
        elif keyword_count >= 3:
            score = 10
        else:
            score = 5
        
        # Return top 10 missing keywords
        return score, missing_keywords[:10]
    
    @classmethod
    def _score_formatting(cls, raw_text: str) -> Tuple[int, List[str]]:
        """Score ATS-friendly formatting (0-15)."""
        score = 15
        issues = []
        
        # Check length (too short or too long)
        word_count = len(raw_text.split())
        if word_count < 200:
            score -= 3
            issues.append("Resume is too short (less than 200 words)")
        elif word_count > 1500:
            score -= 2
            issues.append("Resume is too long (over 1500 words)")
        
        # Check for bullet points (good for ATS)
        if not re.search(r'[•\-\*]', raw_text):
            score -= 2
            issues.append("No bullet points found - use bullets for better readability")
        
        # Check for excessive special characters
        special_char_count = len(re.findall(r'[^\w\s\-\.,;:()\[\]/@]', raw_text))
        if special_char_count > 50:
            score -= 3
            issues.append("Too many special characters - keep formatting simple")
        
        # Check for proper spacing
        if re.search(r'\n{4,}', raw_text):
            score -= 2
            issues.append("Excessive blank lines - reduce whitespace")
        
        # Check for tables/columns (can confuse ATS)
        if re.search(r'\t{2,}', raw_text):
            score -= 2
            issues.append("Multiple tabs detected - avoid complex tables")
        
        return max(score, 0), issues
    
    @classmethod
    def _score_impact(cls, parsed_data: Dict[str, Any], raw_text: str) -> int:
        """Score impact statements and quantifiable achievements (0-15)."""
        score = 0
        
        # Check for impact verbs
        impact_verb_count = 0
        for verb in cls.IMPACT_VERBS:
            impact_verb_count += len(re.findall(r'\b' + re.escape(verb) + r'\b', raw_text, re.IGNORECASE))
        
        if impact_verb_count >= 10:
            score += 6
        elif impact_verb_count >= 6:
            score += 4
        elif impact_verb_count >= 3:
            score += 2
        
        # Check for quantifiable metrics (numbers, percentages)
        metrics = re.findall(r'\d+%|\$\d+|\d+\+|increased by \d+|reduced by \d+', raw_text, re.IGNORECASE)
        metric_count = len(metrics)
        
        if metric_count >= 8:
            score += 6
        elif metric_count >= 5:
            score += 4
        elif metric_count >= 3:
            score += 2
        
        # Check experience descriptions quality
        experiences = parsed_data.get('experience', [])
        if experiences:
            for exp in experiences:
                desc = exp.get('description', '')
                if len(desc) > 50:  # Meaningful description
                    score += 1
        
        return min(score, 15)  # Cap at 15
    
    @classmethod
    def _generate_suggestions(cls, contact: int, sections: int, keywords: int,
                             formatting: int, impact: int, parsed_data: Dict) -> List[str]:
        """Generate actionable improvement suggestions."""
        suggestions = []
        
        if contact < 15:
            if not parsed_data.get('email'):
                suggestions.append("Add a professional email address")
            if not parsed_data.get('phone'):
                suggestions.append("Include a phone number for contact")
            if not parsed_data.get('location'):
                suggestions.append("Add your location (city, state/country)")
        
        if sections < 15:
            if not parsed_data.get('experience') or len(parsed_data['experience']) == 0:
                suggestions.append("Add work experience section with job titles and dates")
            if not parsed_data.get('skills') or len(parsed_data['skills']) < 5:
                suggestions.append("List more relevant technical and soft skills")
            if not parsed_data.get('summary'):
                suggestions.append("Add a professional summary at the top")
        
        if keywords < 20:
            suggestions.append("Include more industry-specific keywords and technical skills")
            suggestions.append("Add relevant certifications and tools you've used")
        
        if formatting < 12:
            suggestions.append("Use bullet points to organize information")
            suggestions.append("Keep formatting simple - avoid tables and complex layouts")
            suggestions.append("Maintain consistent spacing and structure")
        
        if impact < 10:
            suggestions.append("Use action verbs (achieved, led, improved, developed)")
            suggestions.append("Quantify achievements with numbers and percentages")
            suggestions.append("Focus on results and impact, not just responsibilities")
        
        return suggestions[:8]  # Return top 8 suggestions
    
    @classmethod
    def _identify_strengths(cls, contact: int, sections: int, keywords: int,
                           formatting: int, impact: int, parsed_data: Dict) -> List[str]:
        """Identify resume strengths."""
        strengths = []
        
        if contact >= 18:
            strengths.append("Complete contact information")
        
        if sections >= 18:
            strengths.append("Well-structured with all key sections")
        
        if keywords >= 25:
            strengths.append("Strong keyword optimization")
        
        if formatting >= 13:
            strengths.append("ATS-friendly formatting")
        
        if impact >= 12:
            strengths.append("Strong impact statements with quantifiable results")
        
        if parsed_data.get('skills') and len(parsed_data['skills']) >= 8:
            strengths.append(f"Comprehensive skills list ({len(parsed_data['skills'])} skills)")
        
        if parsed_data.get('experience') and len(parsed_data['experience']) >= 3:
            strengths.append("Solid work experience history")
        
        if parsed_data.get('certifications') and len(parsed_data['certifications']) > 0:
            strengths.append("Professional certifications included")
        
        return strengths[:6]  # Return top 6 strengths
