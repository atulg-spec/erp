from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Stock


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_display_links = ('name',)
    ordering = ('name',)

    fieldsets = (
        ("Category Details", {
            "fields": ("name",)
        }),
    )


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_name', 'cost_price', 'selling_price', 'quantity', 'user', 'last_updated')
    list_filter = ('category__name', 'user', 'last_updated')
    search_fields = ('category__name',)
    readonly_fields = ('last_updated',)
    date_hierarchy = 'last_updated'
    ordering = ('-last_updated',)

    fieldsets = (
        ("Stock Details", {
            "fields": ("category", "name", 'selling_price')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change or not obj.user:  # When creating a new stock entry
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def category_name(self, obj):
        return obj.category.name

    category_name.short_description = "Category"



# Optional: Customize Admin Site Branding
admin.site.site_header = "ERP"
admin.site.site_title = "ERP Dashboard"
admin.site.index_title = "Welcome to the ERP Admin Panel"
