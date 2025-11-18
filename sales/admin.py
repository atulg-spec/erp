from django.contrib import admin
from .models import Sales
from django.utils.html import format_html

@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = (
        'stock',
        'quantity_sold',
        'selling_price',
        'total_amount',
        'gross_profit',
        'sold_on'
    )
    list_filter = ('sold_on', 'stock__category')
    search_fields = ('stock__category__name', 'stock__sizes')
    # readonly_fields = ('total_amount', 'gross_profit', 'sold_on')

    fieldsets = (
        ('Sale Details', {
            'fields': ('stock', 'quantity_sold', 'sold_on')
        }),
        ('Auto Calculated', {
            'fields': ('total_amount', 'gross_profit', 'sold_on'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.total_amount = int(obj.selling_price * obj.quantity_sold)
        if obj.stock and obj.stock.cost_price is not None:
            obj.gross_profit = int((obj.selling_price - obj.stock.cost_price) * obj.quantity_sold)
        else:
            obj.gross_profit = 0
        super().save_model(request, obj, form, change)
