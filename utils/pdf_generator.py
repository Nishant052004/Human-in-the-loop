import os
import html
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf(
    project,
    review,
    risk,
    docker,
    k8s,
    cicd,
    confidence_score=90,
    risk_level="Low",
    audit_hash="N/A"
):
    pdf_file = "Devops_Report.pdf"
    
    # Setup document
    doc = SimpleDocTemplate(
        pdf_file,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles for better aesthetics
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E3A8A'), # Navy Blue
        alignment=0, # Left aligned
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0D9488'), # Teal
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#374151') # Charcoal
    )
    
    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B'), # Slate
        backColor=colors.HexColor('#F8FAFC'),
        borderColor=colors.HexColor('#E2E8F0'),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=5,
        spaceAfter=5
    )
    
    content = []
    
    # Header Title
    content.append(Paragraph("HAULT - Human-in-the-Loop DevOps Audit Report", title_style))
    content.append(Spacer(1, 10))
    
    # Summary Dashboard Table (escaped context)
    proj_escaped = html.escape(str(project)[:100]) + "..."
    hash_escaped = html.escape(str(audit_hash))
    
    metrics_data = [
        [Paragraph("<b>Project Summary</b>", body_style), Paragraph(proj_escaped, body_style)],
        [Paragraph("<b>AI Confidence Score</b>", body_style), Paragraph(f"{confidence_score}%", body_style)],
        [Paragraph("<b>Security Risk Level</b>", body_style), Paragraph(f"{risk_level}", body_style)],
        [Paragraph("<b>Audit Trail Hash</b>", body_style), Paragraph(f"<font size='7'>{hash_escaped}</font>", body_style)]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[150, 350])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1E293B')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94A3B8')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    
    content.append(metrics_table)
    content.append(Spacer(1, 15))
    
    # Setup sections
    sections = [
        ("AI Code Review Details", review),
        ("Risk Assessment Summary", risk),
        ("Generated Dockerfile", docker),
        ("Generated Kubernetes YAML", k8s),
        ("Generated CI/CD Actions Workflow", cicd)
    ]
    
    for title, text in sections:
        content.append(Paragraph(title, h2_style))
        
        # Escape XML characters to prevent ReportLab parsing crash
        escaped_text = html.escape(str(text))
        text_str = escaped_text.replace("\n", "<br/>")
        
        if "Generated" in title:
            # Preserve spacing indentation for code displays
            text_str = text_str.replace(" ", "&nbsp;")
            content.append(Paragraph(text_str, code_style))
        else:
            content.append(Paragraph(text_str, body_style))
        content.append(Spacer(1, 8))
        
    doc.build(content)
    return pdf_file