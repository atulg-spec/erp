from django.contrib import admin
from .models import Sales
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponse
from .reports import generate_sales_report
from datetime import datetime, date
from django.utils import timezone
from django.urls import path
from django.shortcuts import redirect

@admin.action(description="Verify Sales")
def verify_sale(modeladmin, request, queryset):
    if not request.user.is_superuser:
        messages.error(request, "You didn't have the permission to verify Sales.")
        return

    for sale in queryset:
        # Prevent multiple deductions
        if sale.is_verified:
            continue

        stock = sale.stock

        # Check stock availability
        if stock.quantity < sale.quantity_sold:
            # Do NOT deduct stock and skip
            continue

        # Deduct stock
        stock.quantity -= sale.quantity_sold
        stock.save()

        # Mark as verified
        sale.is_verified = True

        # Re-save to update total_amount & gross_profit
        sale.save()

class SalesAdmin(admin.ModelAdmin):
    list_display = (
        'stock',
        'quantity_sold',
        'selling_price',
        'total_amount',
        'gross_profit',
        'sold_on',
        'is_verified',
        'download_report_button'
    )
    list_filter = ('sold_on', 'stock__category', 'is_verified')
    search_fields = ('stock__category__name', 'stock__sizes')
    readonly_fields = ('total_amount', 'gross_profit', 'sold_on')
    actions = [verify_sale]
    
    # Add date hierarchy for better date filtering
    date_hierarchy = 'sold_on'

    def download_report_button(self, obj):
        return format_html(
            '<a class="button" href="download-report/">Download PDF Report</a>'
        )
    download_report_button.short_description = "Report"
    download_report_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'download-report/',
                self.admin_site.admin_view(self.download_report),
                name='sales_download_report',
            ),
        ]
        return custom_urls + urls

    def download_report(self, request):
        # Get the current filtered queryset
        filtered_qs = self.get_queryset(request)
        
        # Get date filters from request
        start_date_str = request.GET.get('sold_on__date__gte')
        end_date_str = request.GET.get('sold_on__date__lte')
        
        # If date filters are applied, use them
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                # If date parsing fails, get all data
                if filtered_qs.exists():
                    start_date = filtered_qs.earliest('sold_on').sold_on.date()
                    end_date = filtered_qs.latest('sold_on').sold_on.date()
                else:
                    start_date = timezone.now().date()
                    end_date = timezone.now().date()
        else:
            # If no date range is filtered, get the earliest and latest dates from the queryset
            if filtered_qs.exists():
                start_date = filtered_qs.earliest('sold_on').sold_on.date()
                end_date = filtered_qs.latest('sold_on').sold_on.date()
            else:
                start_date = timezone.now().date()
                end_date = timezone.now().date()
        
        try:
            # Generate PDF using the filtered queryset
            buffer = generate_sales_report(start_date, end_date, filtered_qs)
            
            # Create HTTP response
            response = HttpResponse(buffer, content_type='application/pdf')
            filename = f"sales_report_{start_date}_to_{end_date}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")
            return redirect('..')

    fieldsets = (
        ('Sale Details', {
            'fields': ('stock', 'quantity_sold', 'total_amount', 'gross_profit', 'sold_on')
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.total_amount = int(obj.selling_price * obj.quantity_sold)
        if obj.stock and obj.stock.cost_price is not None:
            obj.gross_profit = int((obj.selling_price - obj.stock.cost_price) * obj.quantity_sold)
        else:
            obj.gross_profit = 0
        super().save_model(request, obj, form, change)

admin.site.register(Sales, SalesAdmin)