from django.db import models
from inventory.models import Stock

class PurchaseReturn(models.Model):
    stock_item = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='returns')
    quantity_returned = models.PositiveIntegerField()
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return for {self.stock_item.name} - {self.quantity_returned} pcs"
