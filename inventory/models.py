from django.db import models
from accounts.models import CustomUser

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Stock(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='stocks')
    name = models.CharField(max_length=100, unique=True, default="")
    cost_price = models.FloatField(default=0)
    selling_price = models.FloatField(default=0)
    quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)  # ✅ FIXED

    def __str__(self):
        return f"{self.name} - {self.category.name}"

    class Meta:
        ordering = ['-last_updated']

    def save_model(self, request, obj, form, change):
        if not change or not obj.user:   # If creating new object
            obj.user = request.user
        super().save_model(request, obj, form, change)
