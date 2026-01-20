#!/usr/bin/env python
"""
Test PDF export functionality locally - NO FastAPI needed
"""

import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.colors import HexColor, grey
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    import io
    
    print("✅ ReportLab imported successfully")
except ImportError as e:
    print(f"❌ ReportLab import failed: {e}")
    sys.exit(1)

def create_simple_pdf():
    """Create a simple test PDF"""
    
    print("🧪 Testing PDF Generation...")
    
    # Color scheme
    PRIMARY_COLOR = HexColor("#6b9080")
    DARK_COLOR = HexColor("#4d7464")
    TEXT_COLOR = HexColor("#636e72")
    BORDER_COLOR = HexColor("#e0ddd5")
    LIGHT_BG = HexColor("#f9f8f6")
    
    # Sample data
    summary_data = {
        "total_income": 50000,
        "total_expenses": 35000,
        "net_savings": 15000,
        "savings_rate": 30.0,
        "daily_average_expense": 1166.67,
    }
    
    try:
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=DARK_COLOR,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph("MindSpend Analytics Report", title_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Summary table
        normal_style = styles['Normal']
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=PRIMARY_COLOR,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph("Summary Statistics", heading_style))
        
        summary_rows = [['Metric', 'Value']]
        for key, label in [('total_income', 'Total Income'),
                          ('total_expenses', 'Total Expenses'),
                          ('net_savings', 'Net Savings'),
                          ('savings_rate', 'Savings Rate')]:
            if key in summary_data:
                value = summary_data[key]
                if key == 'savings_rate':
                    formatted = f"{value:.1f}%"
                else:
                    formatted = f"₹{value:,.2f}"
                summary_rows.append([label, formatted])
        
        summary_table = Table(summary_rows, colWidths=[2.5 * inch, 2.5 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, 'white']),
        ]))
        
        elements.append(summary_table)
        
        # Build PDF
        doc.build(elements)
        pdf_buffer.seek(0)
        
        # Save to file
        output_path = "test_output.pdf"
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        file_size = len(pdf_buffer.getvalue())
        print(f"✅ PDF generated successfully!")
        print(f"   File size: {file_size} bytes")
        print(f"   Saved to: {output_path}")
        print(f"\n📁 Location: {os.path.abspath(output_path)}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_simple_pdf()
    sys.exit(0 if success else 1)
