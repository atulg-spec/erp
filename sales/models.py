from django.db import models
from inventory.models import Stock

class Sales(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='sales')
    quantity_sold = models.PositiveIntegerField(default=1)
    selling_price = models.FloatField(default=0)
    total_amount = models.FloatField(editable=False)
    gross_profit = models.FloatField(editable=False, default=0)
    sold_on = models.DateTimeField()
    is_verified = models.BooleanField(default=False)  # <-- VERY IMPORTANT

    def save(self, *args, **kwargs):
        # Auto fetch selling price from stock
        self.selling_price = self.stock.selling_price

        # Calculate total amount
        self.total_amount = self.quantity_sold * self.selling_price

        # Calculate profit
        if self.stock.cost_price is not None:
            self.gross_profit = (self.selling_price - self.stock.cost_price) * self.quantity_sold
        else:
            self.gross_profit = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.stock.name} - {self.quantity_sold} pcs"

    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ['-sold_on']
