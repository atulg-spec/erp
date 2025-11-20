from django.contrib import admin
from .models import Purchase
from django.utils.html import format_html
from django.contrib import messages

@admin.action(description="Mark selected purchases as Received and Update Stock")
def mark_as_received(modeladmin, request, queryset):
    if not request.user.is_superuser:
        messages.error(request, "You don't have the permission to receive Purchases.")
        return
    for purchase in queryset:

        # Prevent double updates
        if purchase.is_received:
            continue

        stock = purchase.stock_item

        # Weighted Average Cost calculation
        old_qty = stock.quantity
        old_cost = stock.cost_price

        new_qty = purchase.quantity_purchased
        new_cost = purchase.cost_price_per_unit

        # Update total quantity FIRST
        stock.quantity = old_qty + new_qty

        # Avoid division by zero
        if old_qty + new_qty > 0:
            avg_cost = ((old_qty * old_cost) + (new_qty * new_cost)) / (old_qty + new_qty)
            stock.cost_price = round(avg_cost, 2)

        # Update selling price ONLY if given
        if purchase.selling_price:
            stock.selling_price = purchase.selling_price

        stock.save()

        # Mark purchase as received
        purchase.is_received = True
        purchase.save()


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("stock_item", "quantity_purchased", "cost_price_per_unit", 'total_cost',
                    "is_received", "purchase_date")
    list_filter = ("is_received", "purchase_date", 'stock_item')
    readonly_fields = ('total_cost', 'created_at', 'last_updated')

    fieldsets = (
        ("Purchase Details", {
            "fields": (
                "stock_item",
                "quantity_purchased",
                "cost_price_per_unit",
                "selling_price",
                "total_cost",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "last_updated"),
        }),
    )

    actions = [mark_as_received]



# 🌟 Optional: Global Admin Branding
admin.site.site_header = "Inventory Management"
admin.site.site_title = "Inventory Dashboard"
admin.site.index_title = "Welcome to the Inventory Admin Panel"
