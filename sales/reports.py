from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from io import BytesIO
from django.utils import timezone
from .models import Sales
from datetime import datetime
import os

def generate_sales_report(start_date, end_date, queryset=None):
    # Create a file-like buffer to receive PDF data.
    buffer = BytesIO()
    
    # Create the PDF object with better margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Enhanced Styles
    styles = getSampleStyleSheet()
    
    # Custom styles for premium look
    title_style = ParagraphStyle(
        'PremiumTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=1,  # Center aligned
        fontName='Helvetica-Bold',
    )
    
    subtitle_style = ParagraphStyle(
        'PremiumSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=30,
        alignment=1,
        fontName='Helvetica-Oblique',
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        leftIndent=10,
        borderLeft=2,
        borderColor=colors.HexColor('#3498DB'),
        paddingLeft=10
    )
    
    # Header with company info
    header_table_data = [
        [Paragraph("SALES REPORT", title_style)],
        [Paragraph("Honest accounts build honest businesses.", subtitle_style)],
        [Paragraph(f"Period: {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}", subtitle_style)]
    ]
    
    header_table = Table(header_table_data, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Get sales data
    if queryset is not None:
        sales = queryset.select_related('stock')
    else:
        sales = Sales.objects.filter(
            sold_on__date__gte=start_date,
            sold_on__date__lte=end_date
        ).select_related('stock')
    
    # Premium Summary Statistics with Indian Rupee
    total_sales = sales.count()
    total_quantity = sum(sale.quantity_sold for sale in sales)
    total_revenue = sum(sale.total_amount for sale in sales)
    total_profit = sum(sale.gross_profit for sale in sales)
    verified_sales = sales.filter(is_verified=True).count()
    pending_sales = total_sales - verified_sales
    
    # Calculate averages
    avg_sale_value = total_revenue / total_sales if total_sales > 0 else 0
    avg_profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Indian Rupee symbol function
    def inr(amount):
        return f"₹{amount:,.2f}"
    
    # Executive Summary Section
    elements.append(Paragraph("EXECUTIVE SUMMARY", section_style))
    
    summary_data = [
        ['BUSINESS METRICS', 'VALUE', 'PERFORMANCE INDICATORS', 'VALUE'],
        [
            'Total Transactions', 
            f"{total_sales:,}", 
            'Verification Rate', 
            f"{(verified_sales/total_sales*100):.1f}%" if total_sales > 0 else "0%"
        ],
        [
            'Units Sold', 
            f"{total_quantity:,}", 
            'Pending Verification', 
            f"{pending_sales:,}"
        ],
        [
            'Total Revenue', 
            inr(total_revenue), 
            'Average Sale Value', 
            inr(avg_sale_value)
        ],
        [
            'Gross Profit', 
            inr(total_profit), 
            'Average Profit Margin', 
            f"{avg_profit_margin:.1f}%"
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 2.2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (1, -1), colors.HexColor('#ECF0F1')),
        ('BACKGROUND', (2, 1), (3, -1), colors.HexColor('#F8F9FA')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Detailed Transactions Section
    if sales.exists():
        elements.append(Paragraph("DETAILED TRANSACTIONS", section_style))
        
        # Table header
        data = [['PRODUCT', 'QTY', 'PRICE', 'TOTAL AMOUNT', 'PROFIT', 'DATE', 'STATUS']]
        
        for sale in sales:
            status = "✅ Verified" if sale.is_verified else "⏳ Pending"
            status_color = colors.HexColor('#27AE60') if sale.is_verified else colors.HexColor("#3CE742")
            
            data.append([
                Paragraph(sale.stock.name, ParagraphStyle('Product', fontName='Helvetica', fontSize=8)),
                str(sale.quantity_sold),
                inr(sale.selling_price),
                inr(sale.total_amount),
                inr(sale.gross_profit),
                sale.sold_on.strftime('%d/%m/%Y'),
                status
            ])
        
        # Create the table with premium styling
        table = Table(data, repeatRows=1, colWidths=[1.5*inch, 0.5*inch, 0.8*inch, 1*inch, 0.9*inch, 0.8*inch, 0.9*inch])
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Quantity center
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),   # Prices right aligned
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Date center
            ('ALIGN', (6, 1), (6, -1), 'CENTER'),  # Status center
            
            # Grid and background
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DBDB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Status color coding
            ('TEXTCOLOR', (6, 1), (6, -1), colors.HexColor('#27AE60'), lambda r, c, d: d[r][c] == '✅ Verified'),
            ('TEXTCOLOR', (6, 1), (6, -1), colors.HexColor('#E74C3C'), lambda r, c, d: d[r][c] == '⏳ Pending'),
            
            # Profit color coding
            ('TEXTCOLOR', (4, 1), (4, -1), colors.HexColor('#27AE60'), lambda r, c, d: float(d[r][c].replace('₹', '').replace(',', '')) > 0),
            ('TEXTCOLOR', (4, 1), (4, -1), colors.HexColor('#E74C3C'), lambda r, c, d: float(d[r][c].replace('₹', '').replace(',', '')) <= 0),
        ]))
        elements.append(table)
    else:
        no_data = Paragraph(
            "No sales transactions found for the selected period.", 
            ParagraphStyle('NoData', textColor=colors.HexColor('#7F8C8D'), alignment=1)
        )
        elements.append(no_data)
    
    # Footer with generation info
    elements.append(Spacer(1, 30))
    generated_on = timezone.now().strftime('%d %b %Y at %H:%M:%S')
    footer_text = f"Generated on {generated_on} | Confidential Business Report"
    footer = Paragraph(footer_text, ParagraphStyle('Footer', fontSize=8, textColor=colors.HexColor('#95A5A6'), alignment=1))
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer