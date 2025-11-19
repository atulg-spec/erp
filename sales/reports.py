from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from io import BytesIO
from django.utils import timezone
from .models import Sales
from datetime import datetime

def generate_sales_report(start_date, end_date, queryset=None):
    # Create a file-like buffer to receive PDF data.
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file."
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center aligned
    )
    
    # Title
    title = Paragraph("SALES REPORT", title_style)
    elements.append(title)
    
    # Date range
    date_range = Paragraph(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        styles['Normal']
    )
    elements.append(date_range)
    elements.append(Spacer(1, 20))
    
    # Get sales data - use provided queryset or filter by date
    if queryset is not None:
        sales = queryset
    else:
        sales = Sales.objects.filter(
            sold_on__date__gte=start_date,
            sold_on__date__lte=end_date
        ).select_related('stock')
    
    # Summary statistics
    total_sales = sales.count()
    total_quantity = sum(sale.quantity_sold for sale in sales)
    total_revenue = sum(sale.total_amount for sale in sales)
    total_profit = sum(sale.gross_profit for sale in sales)
    verified_sales = sales.filter(is_verified=True).count()
    
    # Summary table
    summary_data = [
        ['Total Sales', 'Total Quantity', 'Total Revenue', 'Total Profit', 'Verified Sales'],
        [str(total_sales), str(total_quantity), f"${total_revenue:,.2f}", f"${total_profit:,.2f}", str(verified_sales)]
    ]
    
    summary_table = Table(summary_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.beige),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Detailed sales table
    if sales.exists():
        # Table header
        data = [['Stock', 'Quantity', 'Price', 'Total', 'Profit', 'Date', 'Status']]
        
        for sale in sales:
            status = "Verified" if sale.is_verified else "Pending"
            data.append([
                sale.stock.name,
                str(sale.quantity_sold),
                f"${sale.selling_price:.2f}",
                f"${sale.total_amount:.2f}",
                f"${sale.gross_profit:.2f}",
                sale.sold_on.strftime('%Y-%m-%d'),
                status
            ])
        
        # Create the table
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(table)
    else:
        no_data = Paragraph("No sales data found for the selected period.", styles['BodyText'])
        elements.append(no_data)
    
    # Build PDF
    doc.build(elements)
    
    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return buffer