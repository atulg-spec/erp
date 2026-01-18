from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db.models.functions import TruncDate
from sales.models import Sales
from payments.models import Payments

class Command(BaseCommand):
    help = 'Aggregates daily sales and populates the Payments model'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting population of daily payments...')
        
        # Aggregate sales by date
        # We filter by is_verified=True assuming only verified sales count as actual payments/sales
        sales_per_day = Sales.objects.filter(is_verified=True).annotate(
            day=TruncDate('sold_on')
        ).values('day').annotate(
            total=Sum('total_amount')
        ).order_by('day')

        count = 0
        for entry in sales_per_day:
            day = entry['day']
            total = entry['total']
            
            if day:  # Ensure day is not None
                Payments.objects.update_or_create(
                    date=day,
                    defaults={'total_sales': total}
                )
                count += 1
                self.stdout.write(f'Updated: {day} - {total}')
            
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {count} daily payment records.'))
