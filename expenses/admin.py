from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_type', 'description', 'amount_display', 'incurred_on')
    list_filter = ('expense_type', 'incurred_on')
    search_fields = ('description',)
    readonly_fields = ('incurred_on',)

    fieldsets = (
        ('Expense Details', {
            'fields': ('expense_type', 'description', 'amount')
        }),
        ('Auto Data', {
            'fields': ('incurred_on',),
            'classes': ('collapse',)
        }),
    )

    def amount_display(self, obj):
        # Display rounded integer amount for readability
        return f"₹{int(obj.amount)}"
    amount_display.short_description = "Amount"

    def save_model(self, request, obj, form, change):
        # Round amount to integer before saving
        obj.amount = int(obj.amount)
        super().save_model(request, obj, form, change)
