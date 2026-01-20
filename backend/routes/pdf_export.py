"""
PDF Export Routes - Generate professional PDF reports with charts
"""

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse, StreamingResponse
from datetime import datetime
import json
import io
from typing import Optional, Dict, List, Any

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib.colors import HexColor, grey
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

router = APIRouter(prefix="/api/pdf", tags=["PDF Export"])

# Color scheme matching frontend
PRIMARY_COLOR = HexColor("#6b9080")
DARK_COLOR = HexColor("#4d7464")
TEXT_COLOR = HexColor("#636e72")
BORDER_COLOR = HexColor("#e0ddd5")
LIGHT_BG = HexColor("#f9f8f6")


def create_styled_pdf(
    filename: str,
    title: str,
    summary_data: Dict[str, Any],
    charts_data: Optional[Dict[str, str]] = None,
    insights: Optional[str] = None
) -> bytes:
    """
    Create a professional PDF with summary statistics, charts, and insights.
    
    Args:
        filename: Output filename
        title: Report title
        summary_data: Dictionary with metrics (total_expenses, total_income, etc.)
        charts_data: Optional dict with chart names as keys and base64 images as values
        insights: Optional insights text
    
    Returns:
        PDF bytes
    """
    
    if not REPORTLAB_AVAILABLE:
        raise ValueError("ReportLab not installed. Run: pip install reportlab")
    
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
    
    # Container for PDF elements
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=DARK_COLOR,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=TEXT_COLOR,
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=TEXT_COLOR,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    # ============================================
    # TITLE SECTION
    # ============================================
    
    elements.append(Paragraph(title or "MindSpend Analytics Report", title_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Report date
    date_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    elements.append(Paragraph(date_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # ============================================
    # SUMMARY STATISTICS SECTION
    # ============================================
    
    if summary_data:
        elements.append(Paragraph("Summary Statistics", heading_style))
        
        # Create summary table
        summary_rows = [['Metric', 'Value']]
        
        # Add data rows
        metrics_to_show = [
            ('total_income', 'Total Income'),
            ('total_expenses', 'Total Expenses'),
            ('net_savings', 'Net Savings'),
            ('savings_rate', 'Savings Rate'),
            ('daily_average_expense', 'Daily Average'),
            ('largest_expense', 'Largest Expense'),
        ]
        
        for key, label in metrics_to_show:
            if key in summary_data:
                value = summary_data[key]
                
                # Format value
                if isinstance(value, float):
                    if key == 'savings_rate':
                        formatted_value = f"{value:.1f}%"
                    else:
                        formatted_value = f"₹{value:,.2f}"
                else:
                    formatted_value = str(value)
                
                summary_rows.append([label, formatted_value])
        
        # Create table
        summary_table = Table(summary_rows, colWidths=[2.5 * inch, 2.5 * inch])
        summary_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Row styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, 'white']),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))
    
    # ============================================
    # CHARTS SECTION
    # ============================================
    
    if charts_data:
        elements.append(Paragraph("Financial Charts", heading_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Chart information
        chart_info = {
            'monthly': {
                'name': 'Monthly Expenses',
                'description': 'Shows your total spending by month. Use this to track spending trends over time and identify high-spending months.'
            },
            'category': {
                'name': 'Expenses by Category',
                'description': 'Breakdown of your expenses across different categories. Helps identify which areas consume the most of your budget.'
            },
            'weekly': {
                'name': 'Weekly Spending Trend',
                'description': 'Displays spending patterns throughout the week. Useful for understanding which days of the week you spend more.'
            },
            'incomeExpense': {
                'name': 'Income vs Expenses',
                'description': 'Compares your total income against total expenses. Shows your net savings position visually.'
            },
            'topTrans': {
                'name': 'Top 10 Transactions',
                'description': 'Lists your largest transactions. Helps identify major expenses that significantly impact your budget.'
            },
            'daily': {
                'name': 'Daily Spending Pattern',
                'description': 'Shows daily spending variations. Useful for understanding daily financial habits and identifying unusual spending days.'
            }
        }
        
        chart_list = []
        
        try:
            for chart_key in ['monthly', 'category', 'weekly', 'incomeExpense', 'topTrans', 'daily']:
                if chart_key in charts_data and charts_data[chart_key]:
                    # Decode base64 image
                    import base64
                    chart_bytes = base64.b64decode(charts_data[chart_key].split(',')[-1])
                    chart_img_buf = io.BytesIO(chart_bytes)
                    
                    # Create image object (3.2 inches wide for single column)
                    img = Image(chart_img_buf, width=4.5*inch, height=3*inch)
                    chart_list.append({
                        'key': chart_key,
                        'image': img,
                        'info': chart_info.get(chart_key, {'name': chart_key, 'description': ''})
                    })
        except Exception as e:
            elements.append(Paragraph(f"Note: Could not embed charts - {str(e)}", normal_style))
        
        # Add charts in groups of 3 per page
        charts_per_page = 3
        for page_num in range(0, len(chart_list), charts_per_page):
            page_charts = chart_list[page_num:page_num + charts_per_page]
            
            for chart_data in page_charts:
                # Add chart title
                chart_title = ParagraphStyle(
                    'ChartTitle',
                    parent=styles['Heading3'],
                    fontSize=12,
                    textColor=PRIMARY_COLOR,
                    spaceAfter=6,
                    spaceBefore=8,
                    fontName='Helvetica-Bold'
                )
                
                elements.append(Paragraph(chart_data['info']['name'], chart_title))
                
                # Add chart image
                elements.append(chart_data['image'])
                
                # Add description
                desc_style = ParagraphStyle(
                    'ChartDesc',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=TEXT_COLOR,
                    spaceAfter=12,
                    leading=11
                )
                elements.append(Paragraph(chart_data['info']['description'], desc_style))
                elements.append(Spacer(1, 0.15 * inch))
            
            # Add page break after each group of 3 charts (except the last one)
            if page_num + charts_per_page < len(chart_list):
                elements.append(PageBreak())
        
        elements.append(Spacer(1, 0.2 * inch))
    
    # ============================================
    # INSIGHTS SECTION
    # ============================================
    
    if insights:
        elements.append(Paragraph("Key Insights", heading_style))
        
        # Parse insights if it's JSON
        try:
            if isinstance(insights, str):
                insights_list = json.loads(insights) if insights.startswith('[') else [insights]
            else:
                insights_list = insights if isinstance(insights, list) else [insights]
        except:
            insights_list = [insights] if insights else []
        
        for insight in insights_list[:5]:  # Limit to 5 insights
            insight_text = str(insight) if insight else ""
            elements.append(Paragraph(f"• {insight_text}", normal_style))
            elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Spacer(1, 0.3 * inch))
    
    # ============================================
    # FOOTER SECTION
    # ============================================
    
    footer_text = "This report was generated by MindSpend Labs - Personal Behavioral Analyst"
    elements.append(Spacer(1, 0.2 * inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    # ============================================
    # BUILD PDF
    # ============================================
    
    try:
        doc.build(elements)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    except Exception as e:
        raise ValueError(f"PDF generation failed: {str(e)}")


# ============================================
# API ENDPOINTS
# ============================================

@router.post("/export-analytics")
async def export_analytics_pdf(
    title: str = "MindSpend Analytics Report",
    summary_data: Dict[str, Any] = Body(...),
    insights: Optional[str] = None,
    charts: Optional[Dict[str, str]] = None
):
    """
    Export analytics data as a professional PDF report with charts.
    
    POST /api/pdf/export-analytics
    
    Request Body:
    {
        "title": "MindSpend Analytics Report",
        "summary_data": {
            "total_income": 50000,
            "total_expenses": 35000,
            "net_savings": 15000,
            "savings_rate": 30.0,
            "daily_average_expense": 1166.67,
            "largest_expense": 5000
        },
        "insights": "Your spending has decreased by 15% this month",
        "charts": {
            "monthly": "data:image/png;base64,...",
            "category": "data:image/png;base64,...",
            ...
        }
    }
    """
    
    try:
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="PDF generation not available. Install reportlab: pip install reportlab"
            )
        
        # Generate PDF with charts
        pdf_bytes = create_styled_pdf(
            filename="analytics.pdf",
            title=title,
            summary_data=summary_data,
            charts_data=charts,
            insights=insights
        )
        
        # Return as streaming response
        filename = f"MindSpend-Analytics-{datetime.now().strftime('%Y-%m-%d')}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")


@router.get("/test-export")
async def test_export():
    """
    Test PDF export with sample data.
    
    GET /api/pdf/test-export
    """
    
    try:
        sample_data = {
            "total_income": 50000,
            "total_expenses": 35000,
            "net_savings": 15000,
            "savings_rate": 30.0,
            "daily_average_expense": 1166.67,
            "largest_expense": 5000
        }
        
        sample_insights = [
            "Your spending has decreased by 15% this month",
            "Food is your largest expense category at 35%",
            "You're on track to meet your savings goal",
            "Transportation costs are up 20% compared to last month"
        ]
        
        pdf_bytes = create_styled_pdf(
            filename="test.pdf",
            title="MindSpend Analytics - Test Report",
            summary_data=sample_data,
            insights=json.dumps(sample_insights)
        )
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=MindSpend-Test.pdf"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
