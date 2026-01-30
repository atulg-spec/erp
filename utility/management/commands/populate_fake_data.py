import random
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker

# Import your models
from inventory.models import Category, Stock
from sales.models import Sales
from purchases.models import Purchase
from purchase_returns.models import PurchaseReturn
from utility.models import Bills
from partners.models import * # Just in case, though empty
# Payments are handled by signals, but we might want to verify or trigger manually if needed
from payments.models import Payments

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with fake data for testing (Indian context)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Number of days of history to generate')
        parser.add_argument('--flush', action='store_true', help='Flush the database before generating data')
        parser.add_argument('--users', type=int, default=5, help='Number of extra users to create')
        parser.add_argument('--products', type=int, default=20, help='Number of products (stocks) to create')
        parser.add_argument('--sales-per-day', type=int, default=15, help='Average sales per day')

    def handle(self, *args, **options):
        # Initialize Faker with Indian locale
        self.fake = Faker('en_IN')
        
        days = options['days']
        flush = options['flush']
        num_users = options['users']
        num_products = options['products']
        sales_per_day = options['sales_per_day']

        if flush:
            self.stdout.write(self.style.WARNING('Flushing database...'))
            # Be careful with flush in production, but this is for fake data
            # We will just delete specific tables to be safer/faster than full flush
            Sales.objects.all().delete()
            Purchase.objects.all().delete()
            PurchaseReturn.objects.all().delete()
            Bills.objects.all().delete()
            Payments.objects.all().delete()
            Stock.objects.all().delete()
            Category.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()
            self.stdout.write(self.style.SUCCESS('Database flushed.'))

        with transaction.atomic():
            self.create_users(num_users)
            self.create_categories_and_stocks(num_products)
            self.generate_history(days, sales_per_day)

        self.stdout.write(self.style.SUCCESS(f'Successfully populated database with {days} days of data.'))

    def create_users(self, count):
        self.stdout.write('Creating users...')
        roles = ['Partner', 'Manager']
        for _ in range(count):
            profile = self.fake.profile()
            username = profile['username']
            email = profile['mail']
            if User.objects.filter(username=username).exists():
                continue
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                phone_number=self.fake.phone_number().replace('+91', '').strip()[:10],
                role=random.choice(roles),
                region_name=self.fake.state(),
                city=self.fake.city(),
                zip_code=self.fake.postcode(),
                is_active=True
            )
            # Add some Indian-specific randomness
            if random.random() > 0.5:
                user.isp = random.choice(['Jio', 'Airtel', 'Vi', 'BSNL'])
            user.save()
        self.stdout.write(self.style.SUCCESS(f'Created {count} users.'))

    def create_categories_and_stocks(self, count):
        self.stdout.write('Creating inventory...')
        categories = ['T-Shirts', 'Jeans', 'Kurtas', 'Sarees', 'Leggings', 'Jackets', 'Shirts', 'Trousers']
        category_objs = []
        for name in categories:
            cat, created = Category.objects.get_or_create(name=name)
            category_objs.append(cat)

        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('No users found to assign stock to.'))
            return

        for _ in range(count):
            category = random.choice(category_objs)
            name = f"{self.fake.word().title()} {category.name}"
            # Ensure unique name
            while Stock.objects.filter(name=name).exists():
                name = f"{self.fake.word().title()} {category.name} {random.randint(1, 999)}"
            
            cost_price = random.randint(200, 2000)
            selling_price = cost_price + random.randint(50, 1000)
            
            Stock.objects.create(
                user=random.choice(users),
                category=category,
                name=name,
                cost_price=cost_price,
                selling_price=selling_price,
                quantity=random.randint(0, 50) # Initial stock, will grow with purchases
            )
        self.stdout.write(self.style.SUCCESS(f'Created {count} stock items.'))

    def generate_history(self, days, sales_daily_avg):
        self.stdout.write(f'Generating {days} days of history...')
        stocks = list(Stock.objects.all())
        if not stocks:
            return

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        current_date = start_date
        while current_date <= end_date:
            self.stdout.write(f'Processing {current_date.date()}...', ending='\r')
            
            # 1. Purchases (Restock)
            # Randomly purchase valid stock items
            if random.random() > 0.3: # 70% chance to have purchases on a day
                num_purchases = random.randint(1, 5)
                for _ in range(num_purchases):
                    stock = random.choice(stocks)
                    qty = random.randint(10, 100)
                    cost = stock.cost_price # Assume stable cost for simplicity, or vary it slightly
                    
                    purchase = Purchase.objects.create(
                        stock_item=stock,
                        purchase_date=current_date.date(),
                        quantity_purchased=qty,
                        cost_price_per_unit=cost,
                        selling_price=stock.selling_price,
                        is_received=True
                    )
                    # Manually update stock as Purchase model save method comment said "do NOT update stock here"
                    # But we are mocking the flow. If signals don't do it, we do it.
                    # Looking at Purchase model, it doesn't seem to have a signal mentioned but let's assume manual update is needed
                    # as per standard logic or if we want to simulate the "Receive" action.
                    # Since is_received=True, we update stock.
                    stock.quantity += qty
                    stock.save()

            # 2. Sales
            daily_sales_count = random.randint(sales_daily_avg - 5, sales_daily_avg + 5)
            if daily_sales_count < 0: daily_sales_count = 0
            
            for _ in range(daily_sales_count):
                stock = random.choice(stocks)
                if stock.quantity <= 0:
                    continue # Out of stock
                
                qty_sold = random.randint(1, min(10, stock.quantity))
                
                sale = Sales(
                    stock=stock,
                    quantity_sold=qty_sold,
                    # selling_price auto-filled by model save
                    # sold_on auto-add-now, so we need to hack it for past dates
                    is_verified=random.choice([True, True, True, False]) # Mostly verified
                )
                sale.save()
                
                # Override the auto_now_add sold_on
                sale.sold_on = current_date
                sale.save(update_fields=['sold_on'])
                
                # Signal `update_daily_payment` triggers on post_save.
                # However, since we updated `sold_on` AFTER first save, the signal might have run with "now".
                # We should re-save or manually trigger signal logic? 
                # The signal checks `instance.sold_on.date()`. 
                # If we updated `sold_on` post-facto, we might need to trigger the signal again or just trust the signal 
                # logic handles updates. 
                # Actually, standard Django auto_now_add is immutable? No, we can update it.
                # To be clean, let's manually call the signal logic for this date if we want realistic payments.
                # The signal `update_daily_payment` listens to post_save.
                # Calling save() again triggers it again with new date.
                sale.save() # Trigger signal with correct date

                # Update Stock
                stock.quantity -= qty_sold
                stock.save()

            # 3. Bills (random expenses)
            if random.random() > 0.7: # 30% chance of bill
                Bills.objects.create(
                    file='bills/dummy.pdf', # We won't create actual file, just path
                    date=current_date.date(),
                    bill_amount=random.randint(500, 50000)
                )

            # 4. Purchase Returns
            if random.random() > 0.9: # 10% chance
                stock = random.choice(stocks)
                PurchaseReturn.objects.create(
                    stock_item=stock,
                    quantity_returned=random.randint(1, 5),
                    is_processed=True,
                    # created_at is auto_now_add, we can leave it or try to mock it if needed
                )
                # Assuming return logic reduces stock or is just a record?
                # Usually return OUT reduces stock. Return IN (sales return) increases.
                # This is PurchaseReturn, so return to vendor -> Reduces stock.
                if stock.quantity >= 1:
                    stock.quantity -= 1
                    stock.save()

            current_date += timedelta(days=1)
