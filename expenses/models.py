from django.db import models


class Expense(models.Model):
    EXPENSE_TYPES = [
        ('Carriage', 'Carriage'),
        ('Drawings', 'Drawings'),
        ('Wages', 'Wages'),
        ('Renumeration', 'Renumeration'),
        ('Electric Bill', 'Electric Bill'),
        ('Rent', 'Rent'),
        ('Miscellaneous', 'Miscellaneous'),
    ]

    expense_type = models.CharField(
        max_length=20,
        choices=EXPENSE_TYPES,
        default='Miscellaneous',
        verbose_name="Expense Type"
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField()
    incurred_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_expense_type_display()} - ₹{int(self.amount)}"

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-incurred_on']
