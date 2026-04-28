"""
Utility module for generating CV PDF from candidate profile data.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import platform


class CVPDFGenerator:
    """Generate professional CV PDF from candidate profile."""

    def __init__(self, profile_data, filename="CV.pdf"):
        """
        Initialize PDF generator with profile data.
        
        Args:
            profile_data: HoSoUngVien instance
            filename: Output PDF filename
        """
        self.profile = profile_data
        self.filename = filename
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        # Register and select a Unicode TTF font that supports Vietnamese
        self.base_font_name = 'Helvetica'
        self.bold_font_name = 'Helvetica-Bold'
        self._register_fonts()
        self._setup_custom_styles()

    def _register_fonts(self):
        """Try to register a Unicode TTF font (DejaVu/Noto/Segoe) for Vietnamese support.

        The function searches for bundled fonts in a `fonts/` folder next to this file
        and then falls back to common system font locations. If none found, it
        keeps reportlab defaults (may not render Vietnamese diacritics).
        """
        module_dir = os.path.dirname(__file__)
        fonts_dir = os.path.join(module_dir, 'fonts')

        # Candidate font files (regular, bold)
        candidates = [
            # bundled fonts (preferred)
            (os.path.join(fonts_dir, 'DejaVuSans.ttf'), os.path.join(fonts_dir, 'DejaVuSans-Bold.ttf')),
            (os.path.join(fonts_dir, 'NotoSans-Regular.ttf'), os.path.join(fonts_dir, 'NotoSans-Bold.ttf')),
            # common system locations (Windows)
            (os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'DejaVuSans.ttf'),
             os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'DejaVuSans-Bold.ttf')),
            (os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'NotoSans-Regular.ttf'),
             os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'NotoSans-Bold.ttf')),
            (os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'segoeui.ttf'),
             os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'segoeuib.ttf')),
            (os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf'),
             os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arialbd.ttf')),
            # Linux fallbacks
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
            ('/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf', '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf'),
        ]

        for regular_path, bold_path in candidates:
            try:
                if regular_path and os.path.isfile(regular_path):
                    # register regular
                    pdfmetrics.registerFont(TTFont('CVSans', regular_path))
                    self.base_font_name = 'CVSans'

                    # register bold if available, else reuse regular
                    if bold_path and os.path.isfile(bold_path):
                        pdfmetrics.registerFont(TTFont('CVSans-Bold', bold_path))
                        self.bold_font_name = 'CVSans-Bold'
                    else:
                        self.bold_font_name = self.base_font_name

                    # stop at the first available candidate
                    return
            except Exception:
                # try next candidate
                continue

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1F4788'),
            spaceAfter=6,
            alignment=1,  # Center
            fontName=self.bold_font_name
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2C5AA0'),
            spaceAfter=8,
            spaceBefore=8,
            fontName=self.bold_font_name,
            borderBottom=1,
            borderColor=colors.HexColor('#2C5AA0'),
            borderPadding=5,
        ))

        self.styles.add(ParagraphStyle(
            name='CVSubHeading',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName=self.bold_font_name,
            textColor=colors.HexColor('#333333'),
            spaceAfter=4,
        ))

        self.styles.add(ParagraphStyle(
            name='CVBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName=self.base_font_name,
            textColor=colors.HexColor('#555555'),
            spaceAfter=6,
        ))

        self.styles.add(ParagraphStyle(
            name='CVSmallText',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName=self.base_font_name,
            textColor=colors.HexColor('#777777'),
        ))

    def generate(self):
        """
        Generate PDF and return buffer.
        
        Returns:
            BytesIO: Buffer containing PDF data
        """
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            title=self.filename,
        )

        # Build story (content)
        story = []

        # Header section
        story.extend(self._build_header())

        # Contact Info
        story.extend(self._build_contact_info())

        # Summary
        if self.profile.gioi_thieu and str(self.profile.gioi_thieu).strip():
            story.append(Spacer(1, 0.2 * inch))
            story.extend(self._build_summary())

        # Skills
        if self.profile.ky_nang:
            story.append(Spacer(1, 0.15 * inch))
            story.extend(self._build_skills())

        # Languages
        if self.profile.ngoai_ngu:
            story.append(Spacer(1, 0.15 * inch))
            story.extend(self._build_languages())

        # Projects
        if self.profile.du_an:
            story.append(Spacer(1, 0.15 * inch))
            story.extend(self._build_projects())

        # Education
        if self.profile.hoc_van or self.profile.chung_chi:
            story.append(Spacer(1, 0.15 * inch))
            story.extend(self._build_education())

        # Build PDF
        doc.build(story)
        self.buffer.seek(0)
        return self.buffer

    def _build_header(self):
        """Build CV header with name and headline."""
        story = []
        
        # Full name
        full_name = str(self.profile.ho_ten or 'Ứng viên').upper()
        story.append(Paragraph(full_name, self.styles['CustomTitle']))

        # Headline/Position
        if self.profile.vi_tri_mong_muon:
            headline = str(self.profile.vi_tri_mong_muon)
            story.append(Paragraph(
                headline,
                ParagraphStyle(
                    'Headline',
                    parent=self.styles['Normal'],
                    fontSize=11,
                    fontName=self.base_font_name,
                    textColor=colors.HexColor('#555555'),
                    alignment=1,
                    spaceAfter=4,
                )
            ))

        return story

    def _build_contact_info(self):
        """Build contact information section."""
        story = []

        contact_items = []
        if self.profile.so_dien_thoai:
            contact_items.append(f"<b>Điện thoại:</b> {self.profile.so_dien_thoai}")
        if self.profile.ung_vien and self.profile.ung_vien.email:
            contact_items.append(f"<b>Email:</b> {self.profile.ung_vien.email}")
        if self.profile.location:
            contact_items.append(f"<b>Vị trí:</b> {self.profile.location}")

        if contact_items:
            contact_text = " | ".join(contact_items)
            story.append(Paragraph(contact_text, self.styles['CVSmallText']))

        return story

    def _build_summary(self):
        """Build summary/introduction section."""
        story = []

        story.append(Paragraph("Giới thiệu", self.styles['SectionHeading']))
        story.append(Paragraph(
            str(self.profile.gioi_thieu),
            self.styles['CVBodyText']
        ))

        return story

    def _build_skills(self):
        """Build skills section."""
        story = []

        story.append(Paragraph("Kỹ năng", self.styles['SectionHeading']))

        # Parse skills
        skills = []
        if isinstance(self.profile.ky_nang, list):
            skills = self.profile.ky_nang
        elif isinstance(self.profile.ky_nang, str):
            skills = [s.strip() for s in self.profile.ky_nang.split(',') if s.strip()]

        # Create skills table for better layout
        if skills:
            skill_text = ", ".join(skills)
            story.append(Paragraph(skill_text, self.styles['CVBodyText']))

        return story

    def _build_languages(self):
        """Build languages section."""
        story = []

        story.append(Paragraph("Ngôn ngữ", self.styles['SectionHeading']))

        languages = []
        if isinstance(self.profile.ngoai_ngu, list):
            for lang in self.profile.ngoai_ngu:
                if isinstance(lang, dict):
                    name = lang.get('ten_ngoai_ngu') or lang.get('name', 'Ngoại ngữ')
                    level = lang.get('tro_cap') or lang.get('level', 'Chưa cập nhật')
                    languages.append(f"{name}: {level}")
                else:
                    languages.append(str(lang))

        if languages:
            for lang in languages:
                story.append(Paragraph(f"• {lang}", self.styles['CVBodyText']))

        return story

    def _build_projects(self):
        """Build projects section."""
        story = []

        story.append(Paragraph("Dự án", self.styles['SectionHeading']))

        projects = []
        if isinstance(self.profile.du_an, list):
            projects = self.profile.du_an

        for idx, project in enumerate(projects):
            if isinstance(project, dict):
                title = project.get('ten_du_an') or project.get('title', 'Dự án')
                description = project.get('mo_ta') or project.get('description', '')
                technologies = project.get('cong_nghe') or project.get('technologies', [])
                link = project.get('link') or project.get('url', '')

                # Project title
                story.append(Paragraph(f"<b>{title}</b>", self.styles['CVSubHeading']))

                # Description
                if description:
                    story.append(Paragraph(description, self.styles['CVBodyText']))

                # Technologies
                if technologies:
                    if isinstance(technologies, list):
                        tech_str = ", ".join(technologies)
                    else:
                        tech_str = str(technologies)
                    story.append(Paragraph(
                        f"<i>Công nghệ: {tech_str}</i>",
                        self.styles['CVSmallText']
                    ))

                # Link
                if link:
                    story.append(Paragraph(f"Link: {link}", self.styles['CVSmallText']))

                if idx < len(projects) - 1:
                    story.append(Spacer(1, 0.1 * inch))

        return story

    def _build_education(self):
        """Build education and certification section."""
        story = []

        story.append(Paragraph("Học vấn & Chứng chỉ", self.styles['SectionHeading']))

        # Education
        if self.profile.hoc_van and isinstance(self.profile.hoc_van, list):
            for edu in self.profile.hoc_van:
                if isinstance(edu, dict):
                    school = edu.get('truong', 'Trường học')
                    major = edu.get('nganh', '')
                    year = edu.get('nam_tot_nghiep', '')

                    title = f"{school}"
                    if major:
                        title += f" - {major}"
                    story.append(Paragraph(f"<b>{title}</b>", self.styles['CVSubHeading']))

                    if year:
                        story.append(Paragraph(f"Tốt nghiệp: {year}", self.styles['CVSmallText']))

                    story.append(Spacer(1, 0.05 * inch))

        # Certifications
        if self.profile.chung_chi and isinstance(self.profile.chung_chi, list):
            for cert in self.profile.chung_chi:
                if isinstance(cert, dict):
                    cert_name = cert.get('ten_chung_chi', 'Chứng chỉ')
                    cert_year = cert.get('nam_cap', '')

                    cert_text = f"• {cert_name}"
                    if cert_year:
                        cert_text += f" ({cert_year})"
                    story.append(Paragraph(cert_text, self.styles['CVBodyText']))

        return story


def generate_cv_pdf(profile_data):
    """
    Convenience function to generate CV PDF.
    
    Args:
        profile_data: HoSoUngVien instance
        
    Returns:
        BytesIO: PDF buffer ready to serve
    """
    filename = f"CV_{profile_data.ho_ten or 'CV'}_{datetime.now().strftime('%d%m%Y')}.pdf"
    generator = CVPDFGenerator(profile_data, filename)
    return generator.generate(), filename
