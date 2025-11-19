from django.contrib import admin
from .models import Sales
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponse
from .reports import generate_sales_report
from datetime import datetime
from django.utils import timezone

def get_local_date(dt):
    """Convert datetime to Asia/Kolkata local date."""
    return timezone.localtime(dt).date()


@admin.action(description="✅ Verify Selected Sales")
def verify_sale(modeladmin, request, queryset):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to verify Sales.")
        return

    verified_count = 0
    for sale in queryset:
        if sale.is_verified:
            continue

        stock = sale.stock

        if stock.quantity < sale.quantity_sold:
            continue

        stock.quantity -= sale.quantity_sold
        stock.save()

        sale.is_verified = True
        sale.save()
        verified_count += 1

    if verified_count > 0:
        messages.success(request, f"Successfully verified {verified_count} sales.")
    else:
        messages.warning(request, "No sales were verified.")



@admin.action(description="📊 Download Sales Report")
def download_sales_report(modeladmin, request, queryset):
    """
    Generate PDF report for currently filtered sales.
    Works even without selecting items.
    Always uses Asia/Kolkata local timezone.
    """

    # --- Helper to convert datetime to local date ---
    def local_date(dt):
        return timezone.localtime(dt).date()

    # Get current filtered queryset (ignore selected checkboxes)
    filtered_qs = modeladmin.get_queryset(request)

    # Get filter dates from URL params
    start_date_str = request.GET.get('sold_on__date__gte')
    end_date_str = request.GET.get('sold_on__date__lte')

    # --- Case 1: User applied date filters manually ---
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
            end_date = None
    else:
        start_date = None
        end_date = None

    # --- Case 2: If filters missing OR parsing failed → determine dates from queryset ---
    if not start_date or not end_date:
        if filtered_qs.exists():
            start_date = local_date(filtered_qs.earliest('sold_on').sold_on)
            end_date = local_date(filtered_qs.latest('sold_on').sold_on)
        else:
            today = local_date(timezone.now())
            start_date = today
            end_date = today

    # --- Generate the PDF ---
    try:
        buffer = generate_sales_report(start_date, end_date, filtered_qs)

        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"Sales_Report_{start_date}_to_{end_date}.pdf"
        response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'

        messages.success(request, f"📈 Sales report generated for {start_date} → {end_date}")
        return response

    except Exception as e:
        messages.error(request, f"❌ Error generating report: {str(e)}")
        return



@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = (
        'stock',
        'quantity_sold',
        'selling_price',
        'total_amount',
        'gross_profit',
        'sold_on',
        'is_verified_display'
    )
    list_filter = ('sold_on', 'stock__category', 'is_verified')
    search_fields = ('stock__category__name', 'stock__sizes', 'stock__name')
    readonly_fields = ('total_amount', 'gross_profit', 'sold_on')
    actions = [verify_sale, download_sales_report]
    
    # Add date hierarchy for better date filtering
    date_hierarchy = 'sold_on'

    def is_verified_display(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: green; font-weight: bold;">✅ Verified</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">⏳ Pending</span>')
    is_verified_display.short_description = 'Status'

    # Simple solution: Always return actions without complex overrides
    def get_actions(self, request):
        actions = super().get_actions(request)
        return actions

    fieldsets = (
        ('Sale Details', {
            'fields': ('stock', 'quantity_sold', 'total_amount', 'gross_profit', 'sold_on'),
            'description': 'Sales information with auto-calculated fields'
        }),
        ('Verification Status', {
            'fields': ('is_verified',),
            'classes': ('collapse',),
            'description': 'Mark as verified to update stock levels'
        }),
    )

    def save_model(self, request, obj, form, change):
        # Auto-calculate fields
        obj.total_amount = obj.selling_price * obj.quantity_sold
        if obj.stock and obj.stock.cost_price is not None:
            obj.gross_profit = (obj.selling_price - obj.stock.cost_price) * obj.quantity_sold
        else:
            obj.gross_profit = 0
        super().save_model(request, obj, form, change)