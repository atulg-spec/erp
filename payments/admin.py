from django.contrib import admin
from .models import Payments

@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_sales')
    ordering = ('-date',)
