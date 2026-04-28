"""
Phase 2: Advanced PDF Templates for CV Download Feature
Supports multiple template styles with customization
"""
from abc import ABC, abstractmethod
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from modules.profiles.pdf_generator import CVPDFGenerator


class CVTemplateBase(CVPDFGenerator, ABC):
    """Base class for CV templates with customization options."""

    def __init__(self, profile_data, filename="CV.pdf", **kwargs):
        """
        Initialize template with custom options.
        
        Kwargs:
            - primary_color: Hex color for headings (default: #1F4788)
            - secondary_color: Hex color for accents (default: #2C5AA0)
            - accent_color: Hex color for highlights (default: #555555)
            - include_sections: List of sections to include
            - font_size_multiplier: Font size adjustment (default: 1.0)
        """
        super().__init__(profile_data, filename)
        
        # Template customization
        self.primary_color = kwargs.get('primary_color', '#1F4788')
        self.secondary_color = kwargs.get('secondary_color', '#2C5AA0')
        self.accent_color = kwargs.get('accent_color', '#555555')
        self.font_multiplier = kwargs.get('font_size_multiplier', 1.0)
        
        # Sections to include
        default_sections = ['header', 'contact', 'summary', 'skills', 'languages', 'projects', 'education']
        self.include_sections = kwargs.get('include_sections', default_sections)

    @abstractmethod
    def _setup_custom_styles(self):
        """Override to define template-specific styles."""
        pass

    @abstractmethod
    def _build_layout(self, story):
        """Override to define custom layout structure."""
        pass

    def generate(self):
        """Generate PDF with custom template layout."""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            title=self.filename,
        )

        story = []

        # Use custom layout
        self._build_layout(story)

        # Build PDF
        doc.build(story)
        self.buffer.seek(0)
        return self.buffer


class ModernTemplate(CVTemplateBase):
    """Modern template with contemporary design and colors."""

    def _setup_custom_styles(self):
        """Setup modern style with vibrant colors."""
        self.styles.add(ParagraphStyle(
            name='ModernTitle',
            parent=self.styles['Heading1'],
            fontSize=int(20 * self.font_multiplier),
            textColor=colors.HexColor(self.primary_color),
            spaceAfter=4,
            alignment=1,
            fontName='Helvetica-Bold',
            letterSpacing=1,
        ))

        self.styles.add(ParagraphStyle(
            name='ModernHeading',
            parent=self.styles['Heading2'],
            fontSize=int(13 * self.font_multiplier),
            textColor=colors.HexColor(self.secondary_color),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            textTransform='uppercase',
            letterSpacing=0.5,
        ))

        self.styles.add(ParagraphStyle(
            name='ModernSubHeading',
            parent=self.styles['Normal'],
            fontSize=int(11 * self.font_multiplier),
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.primary_color),
            spaceAfter=4,
        ))

        self.styles.add(ParagraphStyle(
            name='ModernBody',
            parent=self.styles['Normal'],
            fontSize=int(10 * self.font_multiplier),
            textColor=colors.HexColor(self.accent_color),
            spaceAfter=6,
            leading=13,
        ))

    def _build_layout(self, story):
        """Build modern layout with enhanced typography."""
        # Header
        if 'header' in self.include_sections:
            full_name = str(self.profile.ho_ten or 'Ứng viên').upper()
            story.append(Paragraph(full_name, self.styles['ModernTitle']))
            
            if self.profile.vi_tri_mong_muon:
                story.append(Paragraph(
                    str(self.profile.vi_tri_mong_muon),
                    ParagraphStyle(
                        'ModernHeadline',
                        parent=self.styles['Normal'],
                        fontSize=int(12 * self.font_multiplier),
                        textColor=colors.HexColor(self.secondary_color),
                        alignment=1,
                        spaceAfter=8,
                    )
                ))

        # Contact Info
        if 'contact' in self.include_sections:
            contact_items = []
            if self.profile.so_dien_thoai:
                contact_items.append(f"📱 {self.profile.so_dien_thoai}")
            if self.profile.ung_vien and self.profile.ung_vien.email:
                contact_items.append(f"✉ {self.profile.ung_vien.email}")
            if self.profile.location:
                contact_items.append(f"📍 {self.profile.location}")
            
            if contact_items:
                story.append(Spacer(1, 0.1 * inch))
                story.append(Paragraph(
                    " • ".join(contact_items),
                    self.styles['ModernBody']
                ))

        # Summary
        if 'summary' in self.include_sections and (self.profile.gioi_thieu or self.profile.overview):
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Tóm tắt", self.styles['ModernHeading']))
            story.append(Paragraph(
                str(self.profile.gioi_thieu or self.profile.overview),
                self.styles['ModernBody']
            ))

        # Skills
        if 'skills' in self.include_sections and (self.profile.ky_nang or self.profile.skills):
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph("Kỹ năng", self.styles['ModernHeading']))
            
            skills = []
            if isinstance(self.profile.ky_nang, str):
                skills = [s.strip() for s in self.profile.ky_nang.split(',') if s.strip()]
            elif isinstance(self.profile.skills, list):
                skills = self.profile.skills
            
            if skills:
                # Display as tag-like format
                skill_text = " • ".join(skills)
                story.append(Paragraph(skill_text, self.styles['ModernBody']))

        # Languages
        if 'languages' in self.include_sections and (self.profile.ngoai_ngu or self.profile.languages):
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph("Ngôn ngữ", self.styles['ModernHeading']))
            
            languages = self.profile.languages or self.profile.ngoai_ngu
            if isinstance(languages, list):
                for lang in languages[:5]:  # Limit to 5
                    if isinstance(lang, dict):
                        lang_name = lang.get('name') or lang.get('ten_ngoai_ngu', 'Ngôn ngữ')
                        lang_level = lang.get('level') or lang.get('tro_cap', 'Trình độ')
                        story.append(Paragraph(
                            f"<b>{lang_name}</b> - {lang_level}",
                            self.styles['ModernBody']
                        ))

        # Projects
        if 'projects' in self.include_sections and (self.profile.projects or self.profile.du_an):
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph("Dự án tiêu biểu", self.styles['ModernHeading']))
            
            projects = self.profile.projects or self.profile.du_an
            if isinstance(projects, list):
                for idx, project in enumerate(projects[:4]):  # Limit to 4
                    if isinstance(project, dict):
                        title = project.get('title') or project.get('ten_du_an', 'Dự án')
                        story.append(Paragraph(
                            f"<b>{title}</b>",
                            self.styles['ModernSubHeading']
                        ))
                        
                        desc = project.get('description') or project.get('mo_ta', '')
                        if desc:
                            story.append(Paragraph(desc, self.styles['ModernBody']))

        # Education
        if 'education' in self.include_sections and (self.profile.education_timeline or self.profile.hoc_van):
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph("Học vấn & Chứng chỉ", self.styles['ModernHeading']))
            
            education = self.profile.education_timeline or self.profile.hoc_van
            if isinstance(education, list):
                for edu in education[:3]:  # Limit to 3
                    if isinstance(edu, dict):
                        title = edu.get('title') or edu.get('truong', 'Trường học')
                        story.append(Paragraph(
                            f"<b>{title}</b>",
                            self.styles['ModernSubHeading']
                        ))


class MinimalTemplate(CVTemplateBase):
    """Minimal template with clean, simple design - text only."""

    def _setup_custom_styles(self):
        """Setup minimal style with simple typography."""
        self.styles.add(ParagraphStyle(
            name='MinimalTitle',
            parent=self.styles['Heading1'],
            fontSize=int(16 * self.font_multiplier),
            textColor=colors.HexColor(self.primary_color),
            spaceAfter=2,
            alignment=0,
            fontName='Helvetica-Bold',
        ))

        self.styles.add(ParagraphStyle(
            name='MinimalHeading',
            parent=self.styles['Heading2'],
            fontSize=int(11 * self.font_multiplier),
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=10,
            fontName='Helvetica-Bold',
        ))

        self.styles.add(ParagraphStyle(
            name='MinimalBody',
            parent=self.styles['Normal'],
            fontSize=int(9.5 * self.font_multiplier),
            textColor=colors.black,
            spaceAfter=4,
            leading=11,
        ))

    def _build_layout(self, story):
        """Build minimal, clean layout."""
        # Header
        if 'header' in self.include_sections:
            full_name = str(self.profile.ho_ten or 'Ứng viên')
            story.append(Paragraph(full_name, self.styles['MinimalTitle']))
            
            if self.profile.vi_tri_mong_muon:
                story.append(Paragraph(
                    str(self.profile.vi_tri_mong_muon),
                    self.styles['MinimalBody']
                ))

        # Contact (minimal)
        if 'contact' in self.include_sections:
            contact_items = []
            if self.profile.so_dien_thoai:
                contact_items.append(self.profile.so_dien_thoai)
            if self.profile.ung_vien and self.profile.ung_vien.email:
                contact_items.append(self.profile.ung_vien.email)
            if self.profile.location:
                contact_items.append(self.profile.location)
            
            if contact_items:
                story.append(Spacer(1, 0.08 * inch))
                story.append(Paragraph(
                    " | ".join(contact_items),
                    self.styles['MinimalBody']
                ))

        # Summary
        if 'summary' in self.include_sections and (self.profile.gioi_thieu or self.profile.overview):
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("SUMMARY", self.styles['MinimalHeading']))
            story.append(Paragraph(
                str(self.profile.gioi_thieu or self.profile.overview),
                self.styles['MinimalBody']
            ))

        # Skills
        if 'skills' in self.include_sections and (self.profile.ky_nang or self.profile.skills):
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("SKILLS", self.styles['MinimalHeading']))
            
            skills = []
            if isinstance(self.profile.ky_nang, str):
                skills = [s.strip() for s in self.profile.ky_nang.split(',') if s.strip()]
            elif isinstance(self.profile.skills, list):
                skills = self.profile.skills
            
            if skills:
                skill_text = ", ".join(skills)
                story.append(Paragraph(skill_text, self.styles['MinimalBody']))

        # Languages (minimal)
        if 'languages' in self.include_sections and (self.profile.ngoai_ngu or self.profile.languages):
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("LANGUAGES", self.styles['MinimalHeading']))
            
            languages = self.profile.languages or self.profile.ngoai_ngu
            if isinstance(languages, list):
                for lang in languages[:3]:
                    if isinstance(lang, dict):
                        lang_name = lang.get('name') or lang.get('ten_ngoai_ngu', 'Language')
                        lang_level = lang.get('level') or lang.get('tro_cap', 'Level')
                        story.append(Paragraph(
                            f"{lang_name}: {lang_level}",
                            self.styles['MinimalBody']
                        ))

        # Projects (minimal)
        if 'projects' in self.include_sections and (self.profile.projects or self.profile.du_an):
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("PROJECTS", self.styles['MinimalHeading']))
            
            projects = self.profile.projects or self.profile.du_an
            if isinstance(projects, list):
                for project in projects[:3]:
                    if isinstance(project, dict):
                        title = project.get('title') or project.get('ten_du_an', 'Project')
                        desc = project.get('description') or project.get('mo_ta', '')
                        
                        project_text = f"<b>{title}</b>"
                        if desc:
                            project_text += f" - {desc}"
                        story.append(Paragraph(project_text, self.styles['MinimalBody']))

        # Education (minimal)
        if 'education' in self.include_sections and (self.profile.education_timeline or self.profile.hoc_van):
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("EDUCATION", self.styles['MinimalHeading']))
            
            education = self.profile.education_timeline or self.profile.hoc_van
            if isinstance(education, list):
                for edu in education[:2]:
                    if isinstance(edu, dict):
                        title = edu.get('title') or edu.get('truong', 'School')
                        story.append(Paragraph(title, self.styles['MinimalBody']))


# Template registry for easy access
AVAILABLE_TEMPLATES = {
    'professional': CVPDFGenerator,  # Phase 1 default
    'modern': ModernTemplate,
    'minimal': MinimalTemplate,
}


def get_template_class(template_name):
    """Get template class by name."""
    return AVAILABLE_TEMPLATES.get(template_name, CVPDFGenerator)
