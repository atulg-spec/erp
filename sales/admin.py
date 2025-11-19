from django.contrib import admin
from .models import Sales
from django.utils.html import format_html
from django.contrib import messages

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


@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = (
        'stock',
        'quantity_sold',
        'selling_price',
        'total_amount',
        'gross_profit',
        'sold_on',
        'is_verified'
    )
    list_filter = ('sold_on', 'stock__category')
    search_fields = ('stock__category__name', 'stock__sizes')
    readonly_fields = ('total_amount', 'gross_profit')
    actions = [verify_sale]

    fieldsets = (
        ('Sale Details', {
            'fields': ('stock', 'quantity_sold', 'total_amount', 'gross_profit', 'sold_on')
        }),
        # ('Auto Calculated', {
        #     # 'fields': ('total_amount', 'gross_profit', 'sold_on'),
        #     # 'classes': ('collapse',)
        # }),
    )

    def save_model(self, request, obj, form, change):
        obj.total_amount = int(obj.selling_price * obj.quantity_sold)
        if obj.stock and obj.stock.cost_price is not None:
            obj.gross_profit = int((obj.selling_price - obj.stock.cost_price) * obj.quantity_sold)
        else:
            obj.gross_profit = 0
        super().save_model(request, obj, form, change)
