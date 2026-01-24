from django.contrib import admin
from .models import Purchase
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
from inventory.models import Stock

@admin.action(description="Mark selected purchases as Received and Update Stock")
def mark_as_received(modeladmin, request, queryset):
    if not request.user.is_superuser:
        messages.error(request, "You don't have the permission to receive Purchases.")
        return

    # Group purchases by Stock
    purchase_groups = {}
    for p in queryset:
        if not p.is_received:
            purchase_groups.setdefault(p.stock_item_id, []).append(p)

    try:
        with transaction.atomic():  # Lock everything safely
            for stock_id, purchases in purchase_groups.items():

                # Lock stock row
                stock = Stock.objects.select_for_update().get(id=stock_id)

                old_qty = stock.quantity
                old_cost = stock.cost_price

                total_new_qty = sum(p.quantity_purchased for p in purchases)
                total_new_cost = sum(p.quantity_purchased * p.cost_price_per_unit for p in purchases)

                # Update quantity
                stock.quantity = old_qty + total_new_qty

                # Weighted average cost
                if stock.quantity > 0:
                    new_avg_cost = ((old_qty * old_cost) + total_new_cost) / stock.quantity
                    stock.cost_price = p.cost_price_per_unit
                    stock.selling_price = p.selling_price

                # Update selling price if provided in any purchase
                for p in purchases:
                    if p.selling_price:
                        stock.selling_price = p.selling_price

                stock.save()

                # Mark all purchases as received
                for p in purchases:
                    p.is_received = True
                    p.save()

    except Exception as e:
        messages.error(request, f"Error updating stock: {e}")
        return

    messages.success(request, "Selected purchases marked as received and stock updated successfully.")



@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("stock_item", "quantity_purchased", 'selling_price', "cost_price_per_unit", 'total_cost',
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
    search_fields = ('stock_item__name',)
    actions = [mark_as_received]



# 🌟 Optional: Global Admin Branding
admin.site.site_header = "Inventory Management"
admin.site.site_title = "Inventory Dashboard"
admin.site.index_title = "Welcome to the Inventory Admin Panel"
