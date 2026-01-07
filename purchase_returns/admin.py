from django.contrib import admin
from django import forms
from .models import PurchaseReturn
from django.db import transaction
from django.contrib import messages
from inventory.models import Stock

class StockChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name} (Available: {obj.quantity})"

class PurchaseReturnForm(forms.ModelForm):
    stock_item = StockChoiceField(queryset=Stock.objects.all())

    class Meta:
        model = PurchaseReturn
        fields = '__all__'

@admin.action(description="Process Return and Deduct Inventory")
def process_return(modeladmin, request, queryset):
    processed_count = 0
    try:
        with transaction.atomic():
            for ret in queryset:
                if ret.is_processed:
                    continue

                stock = ret.stock_item
                # Lock stock row for safety
                stock = Stock.objects.select_for_update().get(id=stock.id)

                if stock.quantity < ret.quantity_returned:
                    raise Exception(f"Insufficient stock for {stock.name}. Available: {stock.quantity}, Return Amount: {ret.quantity_returned}")

                stock.quantity -= ret.quantity_returned
                stock.save()

                ret.is_processed = True
                ret.save()
                processed_count += 1
        
        if processed_count > 0:
            messages.success(request, f"Successfully processed {processed_count} returns.")
        else:
            messages.info(request, "No unprocessed returns found in selected items.")

    except Exception as e:
        messages.error(request, f"Error processing returns: {e}")

@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    form = PurchaseReturnForm
    list_display = ('stock_item', 'quantity_returned', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('stock_item__name',)

    fieldsets = (
        ('Stock Details', {
            'fields': ('stock_item', 'quantity_returned'),
            'description': 'Stock information with auto-calculated fields'
        }),
    )

    actions = [process_return]