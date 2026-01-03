# inventory/context_processors.py
from django.db.models import Sum, Count, F, Q, Avg
from django.utils import timezone
from datetime import timedelta
from inventory.models import Stock
from purchases.models import Purchase
from sales.models import Sales

def dashboard_stats(request):
    """
    Context processor for dashboard statistics
    """
    if not request.user.is_authenticated:
        return {}
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Create base querysets with user filter for non-superusers
    stock_base = Stock.objects.all()
    sales_base = Sales.objects.all()
    purchase_base = Purchase.objects.all()
    
    # Apply user filter only if not superuser
    if not request.user.is_superuser:
        stock_base = stock_base.filter(user=request.user)
        # Note: Sales and Purchase models might need user filtering too if they have user fields
        # If they don't have user fields, you might need to adjust this
    
    # Total Stock Value
    total_stock_value = stock_base.aggregate(
        total=Sum(F('quantity') * F('cost_price'))
    )['total'] or 0
    
    # Total Inventory Items
    total_items = stock_base.aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    # Low Stock Items (less than 10 units)
    low_stock_count = stock_base.filter(quantity__lt=4).count()
    
    # Out of Stock Items
    out_of_stock = stock_base.filter(quantity=0).count()
    
    # Today's Sales
    today_sales = sales_base.filter(
        sold_on__date=today,
        is_verified=True
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )

    # Unverified Sales
    unverified_sales = sales_base.filter(
        sold_on__date=today,
        is_verified=False
    ).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )

    
    # This Week's Sales
    week_sales = sales_base.filter(
        sold_on__date__gte=week_ago,
        is_verified=True
    ).aggregate(
        total=Sum('total_amount'),
        profit=Sum('gross_profit')
    )
    
    # This Month's Sales
    month_sales = sales_base.filter(
        sold_on__date__gte=month_ago,
        is_verified=True
    ).aggregate(
        total=Sum('total_amount'),
        profit=Sum('gross_profit'),
        count=Count('id')
    )
    
    # Total Revenue (All Time)
    total_revenue = sales_base.filter(is_verified=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Total Profit (All Time)
    total_profit = sales_base.filter(is_verified=True).aggregate(
        total=Sum('gross_profit')
    )['total'] or 0
    
    # Pending Purchases
    pending_purchases = purchase_base.filter(is_received=False).count()
    
    # This Month's Purchases
    month_purchases = purchase_base.filter(
        purchase_date__gte=month_ago
    ).aggregate(
        total=Sum('total_cost'),
        count=Count('id')
    )
    
    # Top Selling Products (This Month)
    top_products = sales_base.filter(
        sold_on__date__gte=month_ago,
        is_verified=True
    ).values(
        'stock__name', 
        'stock__category__name'
    ).annotate(
        total_sold=Sum('quantity_sold'),
        revenue=Sum('total_amount')
    ).order_by('-total_sold')[:5]
    
    # Category-wise Stock Distribution
    category_distribution = stock_base.values('category__name').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('cost_price'))
    ).order_by('-total_value')
    
    # Daily Sales Chart Data (Last 7 Days)
    daily_sales = []
    for i in range(10, -1, -1):
        date = today - timedelta(days=i)
        sales = sales_base.filter(
            sold_on__date=date,
            is_verified=True
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        daily_sales.append({
            'date': date.strftime('%b %d'),
            'amount': float(sales)
        })
    
    # Monthly Sales Chart Data (Last 6 Months)
    monthly_sales = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        sales = sales_base.filter(
            sold_on__date__gte=month_start,
            sold_on__date__lt=month_start + timedelta(days=31),
            is_verified=True
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        monthly_sales.append({
            'month': month_start.strftime('%b'),
            'amount': float(sales)
        })
    
    # Recent Sales (Last 10)
    recent_sales = sales_base.filter(is_verified=True).select_related('stock')[:10]
    
    # Stock Alert Items
    stock_alerts = stock_base.filter(
        quantity__lt=4
    ).order_by('quantity')
    
    # Profit Margin Analysis
    avg_profit_margin = sales_base.filter(
        is_verified=True,
        total_amount__gt=0
    ).aggregate(
        avg_margin=Avg(F('gross_profit') / F('total_amount') * 100)
    )['avg_margin'] or 0
    
    return {
        'dashboard': {
            'today': today,
            'total_stock_value': round(total_stock_value, 2),
            'total_items': total_items,
            'low_stock_count': low_stock_count,
            'out_of_stock': out_of_stock,
            'today_sales_total': round(today_sales['total'] or 0, 2),
            'unverified_sales': round(unverified_sales['total'] or 0, 2),
            'today_sales_count': today_sales['count'] or 0,
            'week_sales_total': round(week_sales['total'] or 0, 2),
            'week_sales_profit': round(week_sales['profit'] or 0, 2),
            'month_sales_total': round(month_sales['total'] or 0, 2),
            'month_sales_profit': round(month_sales['profit'] or 0, 2),
            'month_sales_count': month_sales['count'] or 0,
            'total_revenue': round(total_revenue, 2),
            'total_profit': round(total_profit, 2),
            'pending_purchases': pending_purchases,
            'month_purchases_total': round(month_purchases['total'] or 0, 2),
            'month_purchases_count': month_purchases['count'] or 0,
            'top_products': list(top_products),
            'category_distribution': list(category_distribution),
            'daily_sales': daily_sales,
            'monthly_sales': monthly_sales,
            'recent_sales': recent_sales,
            'stock_alerts': stock_alerts,
            'avg_profit_margin': round(avg_profit_margin, 2),
        }
    }