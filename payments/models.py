from django.db import models

class Payments(models.Model):
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = 'Payment (Daily)'
        verbose_name_plural = 'Payments (Daily)'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date}: {self.total_sales}"
