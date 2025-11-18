from django.db import models
from inventory.models import Stock

class Sales(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='sales')
    quantity_sold = models.PositiveIntegerField(default=1)
    selling_price = models.FloatField(default=0)
    total_amount = models.FloatField(editable=False)
    gross_profit = models.FloatField(editable=False, default=0)
    sold_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate total amount
        self.selling_price = self.stock.selling_price
        self.total_amount = int(self.quantity_sold * self.selling_price)

        # Calculate gross profit if cost_price is available
        if self.stock and self.stock.cost_price is not None:
            profit = (self.selling_price - self.stock.cost_price) * self.quantity_sold
            self.gross_profit = int(profit)
        else:
            self.gross_profit = 0

        # Adjust stock quantity
        if self.stock:
            stock_item = self.stock

            # If updating an existing sale
            if self.pk:
                old_sale = Sales.objects.get(pk=self.pk)
                difference = self.quantity_sold - old_sale.quantity_sold
                if stock_item.quantity - difference < 0:
                    raise ValueError("Not enough stock to update this sale.")
                stock_item.quantity -= difference
            else:
                # New sale
                if stock_item.quantity < self.quantity_sold:
                    raise ValueError("Not enough stock available.")
                stock_item.quantity -= self.quantity_sold

            stock_item.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.stock} - {self.quantity_sold} pcs"

    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ['-sold_on']
