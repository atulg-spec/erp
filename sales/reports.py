from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from django.utils import timezone
from .models import Sales
from datetime import datetime
import os

def generate_sales_report(start_date, end_date, queryset=None):
    """
    Generate a premium professional sales report with Indian Rupee formatting
    """
    buffer = BytesIO()
    
    # Create PDF with professional margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        leftMargin=0.6*inch,
        rightMargin=0.6*inch,
        title="Sales Report",
        author="Sales Management System"
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ==================== PREMIUM STYLES ====================
    
    title_style = ParagraphStyle(
        'PremiumTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=8,
        spaceBefore=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=28
    )
    
    subtitle_style = ParagraphStyle(
        'PremiumSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#6c757d'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        leading=14
    )
    
    date_range_style = ParagraphStyle(
        'DateRange',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#495057'),
        spaceAfter=25,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=13
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=14,
        spaceBefore=22,
        fontName='Helvetica-Bold',
        leftIndent=0,
        borderWidth=0,
        borderPadding=0,
        borderColor=colors.HexColor('#0066cc'),
        underlineProportion=0.15,
        leading=16
    )
    
    # ==================== HEADER SECTION ====================
    
    # Decorative line
    header_line = Table([['']], colWidths=[7.3*inch])
    header_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#0066cc')),
        ('TOPPADDING', (0, 0), (-1, 0), 0),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
    ]))
    elements.append(header_line)
    elements.append(Spacer(1, 15))
    
    # Main header
    elements.append(Paragraph("SALES PERFORMANCE REPORT", title_style))
    elements.append(Paragraph("Honest accounts build honest businesses.", subtitle_style))
    elements.append(Paragraph(
        f"Reporting Period: <b>{start_date.strftime('%d %B %Y')}</b> to <b>{end_date.strftime('%d %B %Y')}</b>", 
        date_range_style
    ))
    
    # Decorative separator
    separator = Table([['']], colWidths=[7.3*inch])
    separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#dee2e6')),
    ]))
    elements.append(separator)
    elements.append(Spacer(1, 20))
    
    # ==================== DATA PROCESSING ====================
    
    if queryset is not None:
        sales = queryset.select_related('stock')
    else:
        sales = Sales.objects.filter(
            sold_on__date__gte=start_date,
            sold_on__date__lte=end_date
        ).select_related('stock')
    
    # Calculate metrics
    total_sales = sales.count()
    total_quantity = sum(sale.quantity_sold for sale in sales)
    total_revenue = sum(sale.total_amount for sale in sales)
    total_profit = sum(sale.gross_profit for sale in sales)
    total_cost = total_revenue - total_profit
    
    avg_sale_value = total_revenue / total_sales if total_sales > 0 else 0
    avg_profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    avg_profit_per_unit = total_profit / total_quantity if total_quantity > 0 else 0
    
    # Get top selling product
    from django.db.models import Sum
    top_product = sales.values('stock__name').annotate(
        total_qty=Sum('quantity_sold')
    ).order_by('-total_qty').first()
    top_product_name = top_product['stock__name'] if top_product else 'N/A'
    top_product_qty = top_product['total_qty'] if top_product else 0
    
    # Indian Rupee formatting function
    def format_inr(amount):
        """Format amount in Indian Rupee with proper comma separation"""
        return f"Rs. {amount:,.2f}"
    
    # ==================== EXECUTIVE SUMMARY ====================
    
    elements.append(Paragraph("EXECUTIVE SUMMARY", section_style))
    
    # Key Performance Indicators
    kpi_data = [
        [
            Paragraph('<b>KEY METRICS</b>', ParagraphStyle('KPIHeader', fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph('<b>VALUE</b>', ParagraphStyle('KPIHeader', fontSize=9, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_RIGHT)),
            '',
            Paragraph('<b>FINANCIAL METRICS</b>', ParagraphStyle('KPIHeader', fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph('<b>VALUE</b>', ParagraphStyle('KPIHeader', fontSize=9, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_RIGHT))
        ],
        [
            'Total Transactions', 
            f"{total_sales:,}", 
            '',
            'Total Revenue', 
            format_inr(total_revenue)
        ],
        [
            'Units Sold', 
            f"{total_quantity:,}",
            '',
            'Gross Profit', 
            format_inr(total_profit)
        ],
        [
            'Top Selling Product', 
            Paragraph(f"<font size=7>{top_product_name}</font>", ParagraphStyle('TopProduct', fontSize=7, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
            '',
            'Total Cost', 
            format_inr(total_cost)
        ],
        [
            'Top Product Units', 
            f"{top_product_qty:,}",
            '',
            'Average Sale Value', 
            format_inr(avg_sale_value)
        ],
        [
            'Avg Profit/Unit', 
            format_inr(avg_profit_per_unit),
            '',
            'Profit Margin', 
            f"{avg_profit_margin:.2f}%"
        ],
        [
            'Revenue per Unit', 
            format_inr(total_revenue / total_quantity if total_quantity > 0 else 0),
            '',
            'Cost per Unit', 
            format_inr(total_cost / total_quantity if total_quantity > 0 else 0)
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[2.2*inch, 1.2*inch, 0.3*inch, 2.2*inch, 1.2*inch])
    kpi_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#0066cc')),
        ('BACKGROUND', (3, 0), (4, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('TEXTCOLOR', (3, 0), (4, 0), colors.white),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('ALIGN', (3, 0), (3, 0), 'LEFT'),
        ('ALIGN', (4, 0), (4, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        
        # Data rows
        ('BACKGROUND', (0, 1), (1, -1), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (3, 1), (4, -1), colors.HexColor('#e9ecef')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 1), (3, -1), 'Helvetica'),
        ('FONTNAME', (4, 1), (4, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#212529')),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
        ('TOPPADDING', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        
        # Grid
        ('GRID', (0, 0), (1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('GRID', (3, 0), (4, -1), 0.5, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Spacer column
        ('BACKGROUND', (2, 0), (2, -1), colors.white),
        ('LINEAFTER', (2, 0), (2, -1), 0, colors.white),
    ]))
    
    elements.append(kpi_table)
    elements.append(Spacer(1, 30))
    
    # ==================== DETAILED TRANSACTIONS ====================
    
    if sales.exists():
        elements.append(Paragraph("TRANSACTION DETAILS", section_style))
        
        # Transaction table header
        transaction_data = [[
            Paragraph('<b>PRODUCT</b>', ParagraphStyle('TH', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph('<b>QTY</b>', ParagraphStyle('TH', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER)),
            Paragraph('<b>UNIT PRICE</b>', ParagraphStyle('TH', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_RIGHT)),
            Paragraph('<b>AMOUNT</b>', ParagraphStyle('TH', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_RIGHT)),
            Paragraph('<b>DATE</b>', ParagraphStyle('TH', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER)),
            Paragraph('<b>STATUS</b>', ParagraphStyle('TH', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_CENTER))
        ]]
        
        # Add transaction rows
        for sale in sales:
            status_icon = "✓" if sale.is_verified else "○"
            status_text = f"{status_icon} Verified" if sale.is_verified else f"{status_icon} Pending"
            
            transaction_data.append([
                Paragraph(sale.stock.name, ParagraphStyle('TD', fontSize=8, fontName='Helvetica', leading=10)),
                str(sale.quantity_sold),
                format_inr(sale.selling_price),
                format_inr(sale.total_amount),
                timezone.localtime(sale.sold_on).strftime('%d/%m/%y'),
                status_text
            ])
        
        # Create transaction table
        transaction_table = Table(
            transaction_data, 
            repeatRows=1, 
            colWidths=[1.8*inch, 0.5*inch, 0.95*inch, 0.95*inch, 0.95*inch, 0.7*inch, 0.85*inch]
        )
        
        transaction_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 11),
            ('LEFTPADDING', (0, 0), (-1, 0), 8),
            ('RIGHTPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            
            # Alignment
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Quantity
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),   # Prices
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Date
            ('ALIGN', (6, 1), (6, -1), 'CENTER'),  # Status
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Box around entire table
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#adb5bd')),
        ]))
        
        elements.append(transaction_table)
    else:
        no_data_style = ParagraphStyle(
            'NoData', 
            fontSize=10,
            textColor=colors.HexColor('#6c757d'), 
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=20,
            fontName='Helvetica-Oblique'
        )
        elements.append(Paragraph(
            "No sales transactions recorded for the selected period.", 
            no_data_style
        ))
    
    # ==================== FOOTER ====================
    
    elements.append(Spacer(1, 35))
    
    # Footer separator
    footer_line = Table([['']], colWidths=[7.3*inch])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(footer_line)
    elements.append(Spacer(1, 10))
    
    # Footer information
    generated_on = timezone.localtime(timezone.now()).strftime('%d %B %Y at %I:%M %p')
    footer_style = ParagraphStyle(
        'Footer', 
        fontSize=7.5, 
        textColor=colors.HexColor('#868e96'), 
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=10
    )
    
    footer_text = f"""
    <b>Document Generated:</b> {generated_on}<br/>
    <i>CONFIDENTIAL - For Internal Use Only</i><br/>
    This report contains proprietary business information
    """
    
    elements.append(Paragraph(footer_text, footer_style))
    
    # ==================== BUILD PDF ====================
    
    doc.build(elements)
    buffer.seek(0)
    return buffer