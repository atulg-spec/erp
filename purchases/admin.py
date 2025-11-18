from django.contrib import admin
from .models import Purchase
from django.utils.html import format_html

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):

    list_display = (
        'stock_item',
        'category_display',
        'quantity_purchased',
        'cost_price_per_unit',
        'selling_price',
        'total_cost',
        'purchase_date',
        'last_updated',
    )

    fieldsets = (
        ("Purchase Details", {
            "fields": (
                "stock_item",
                "quantity_purchased",
                "cost_price_per_unit",
                "selling_price",
                "total_cost",
                "remarks",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "last_updated"),
        }),
    )

    readonly_fields = ('total_cost', 'created_at', 'last_updated')

    def category_display(self, obj):
        return obj.stock_item.category.name
    category_display.short_description = "Category"


# 🌟 Optional: Global Admin Branding
admin.site.site_header = "Inventory Management"
admin.site.site_title = "Inventory Dashboard"
admin.site.index_title = "Welcome to the Inventory Admin Panel"
