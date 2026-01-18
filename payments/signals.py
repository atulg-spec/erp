from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from sales.models import Sales
from payments.models import Payments

@receiver(post_save, sender=Sales)
@receiver(post_delete, sender=Sales)
def update_daily_payment(sender, instance, **kwargs):
    if instance.sold_on:
        day = instance.sold_on.date()
        # Recalculate for that day to ensure accuracy
        # Filter is_verified=True as per logic
        total = Sales.objects.filter(is_verified=True, sold_on__date=day).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        Payments.objects.update_or_create(
            date=day,
            defaults={'total_sales': total}
        )
