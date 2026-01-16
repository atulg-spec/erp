from django.contrib import admin
from .models import Bills
from sales.models import Sales
from django.utils import timezone
from django.db.models import Sum
from django.utils.html import format_html
from django.contrib import messages

@admin.register(Bills)
class BillsAdmin(admin.ModelAdmin):
    list_display = ('date', 'bill_amount', 'file_link')
    list_filter = ('date',)
    
    @admin.display(description="Bill File")
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View</a>', obj.file.url)
        return "-"