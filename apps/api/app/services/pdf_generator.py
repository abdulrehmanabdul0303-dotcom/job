"""
PDF Generation Service for Application Packets.

Task 2.5: PDF download functionality.

Uses reportlab for PDF generation.
"""
from typing import Dict, List, Any
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# Try to import reportlab, fall back to simple text if not available
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed - PDF generation will use fallback")


class PDFGenerator:
    """Service for generating PDF documents from application packets."""
    
    @staticmethod
    def generate_apply_kit_pdf(
        cover_letter: str,
        tailored_bullets: List[str],
        qa: Dict[str, str],
        job_title: str = "Position",
        company_name: str = "Company",
    ) -> BytesIO:
        """
        Generate a PDF from application packet content.
        
        Task 2.5: PDF generation for application packets.
        
        Args:
            cover_letter: Cover letter text
            tailored_bullets: List of tailored resume bullets
            qa: Dictionary of interview questions and answers
            job_title: Job title for header
            company_name: Company name for header
            
        Returns:
            BytesIO buffer containing PDF data
        """
        if REPORTLAB_AVAILABLE:
            return PDFGenerator._generate_with_reportlab(
                cover_letter, tailored_bullets, qa, job_title, company_name
            )
        else:
            return PDFGenerator._generate_fallback(
                cover_letter, tailored_bullets, qa, job_title, company_name
            )
    
    @staticmethod
    def _generate_with_reportlab(
        cover_letter: str,
        tailored_bullets: List[str],
        qa: Dict[str, str],
        job_title: str,
        company_name: str,
    ) -> BytesIO:
        """Generate PDF using reportlab."""
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2C3E50',
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor='#34495E',
            spaceAfter=12,
            spaceBefore=12,
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
        )
        
        # Title
        title = Paragraph(
            f"Application Packet<br/>{job_title} at {company_name}",
            title_style
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Cover Letter Section
        elements.append(Paragraph("Cover Letter", heading_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Split cover letter into paragraphs
        for para in cover_letter.split('\n\n'):
            if para.strip():
                elements.append(Paragraph(para.strip(), body_style))
                elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(PageBreak())
        
        # Tailored Resume Bullets Section
        elements.append(Paragraph("Tailored Resume Bullets", heading_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        for bullet in tailored_bullets:
            bullet_text = f"• {bullet}"
            elements.append(Paragraph(bullet_text, body_style))
            elements.append(Spacer(1, 0.05 * inch))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        # Interview Q&A Section
        elements.append(Paragraph("Interview Preparation", heading_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        for question, answer in qa.items():
            # Question
            q_style = ParagraphStyle(
                'Question',
                parent=body_style,
                fontSize=12,
                textColor='#2980B9',
                fontName='Helvetica-Bold',
                spaceAfter=6,
            )
            elements.append(Paragraph(f"Q: {question}", q_style))
            
            # Answer
            elements.append(Paragraph(f"A: {answer}", body_style))
            elements.append(Spacer(1, 0.15 * inch))
        
        # Build PDF
        doc.build(elements)
        
        # Reset buffer position
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def _generate_fallback(
        cover_letter: str,
        tailored_bullets: List[str],
        qa: Dict[str, str],
        job_title: str,
        company_name: str,
    ) -> BytesIO:
        """
        Generate a simple text-based PDF fallback.
        
        Used when reportlab is not available.
        """
        buffer = BytesIO()
        
        # Create simple text content
        content = f"""APPLICATION PACKET
{job_title} at {company_name}
{'=' * 80}

COVER LETTER
{'-' * 80}

{cover_letter}

{'=' * 80}

TAILORED RESUME BULLETS
{'-' * 80}

"""
        
        for bullet in tailored_bullets:
            content += f"• {bullet}\n"
        
        content += f"\n{'=' * 80}\n\nINTERVIEW PREPARATION\n{'-' * 80}\n\n"
        
        for question, answer in qa.items():
            content += f"Q: {question}\n\nA: {answer}\n\n"
        
        # Write to buffer
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def get_content_type() -> str:
        """Get the appropriate content type for the PDF."""
        if REPORTLAB_AVAILABLE:
            return "application/pdf"
        else:
            return "text/plain"
    
    @staticmethod
    def get_file_extension() -> str:
        """Get the appropriate file extension."""
        if REPORTLAB_AVAILABLE:
            return "pdf"
        else:
            return "txt"
