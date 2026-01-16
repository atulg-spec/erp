from django.db import models
from django.utils import timezone

class Bills(models.Model):
    file = models.FileField(upload_to='bills/')
    date = models.DateField(default=timezone.now)
    bill_amount = models.FloatField(default=0)

    def __str__(self):
        return f"Bill - {self.date}"

    class Meta:
        verbose_name = "Bill"
        verbose_name_plural = "Bills"
