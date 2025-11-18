from django.db import models
from django.utils import timezone
from inventory.models import Stock


class Purchase(models.Model):
    stock_item = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='purchases')
    purchase_date = models.DateField(default=timezone.now)
    quantity_purchased = models.PositiveIntegerField()
    cost_price_per_unit = models.FloatField(help_text="Cost per unit at purchase time")
    selling_price = models.FloatField(blank=True, null=True)
    total_cost = models.FloatField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date']
        verbose_name = "Add Purchase"
        verbose_name_plural = "Add Purchases"

    def __str__(self):
        return f"{self.stock_item.category.name} - {self.quantity_purchased} pcs"

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity_purchased * self.cost_price_per_unit
    
        if self.stock_item:
            stock = self.stock_item
            old_qty = stock.quantity
            old_cost = stock.cost_price
    
            new_qty = self.quantity_purchased
            new_cost = self.cost_price_per_unit
    
            # Weighted Average Cost (rounded to integer)
            if old_qty + new_qty > 0:
                average_cost = ((old_qty * old_cost) + (new_qty * new_cost)) / (old_qty + new_qty)
                stock.cost_price = int(round(average_cost))  # 👈 Rounds and converts to integer
    
            # Update total quantity
            stock.quantity += new_qty
            stock.selling_price += self.selling_price
            stock.save()
    
        super().save(*args, **kwargs)


