from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, Q, Count
from django.core.paginator import Paginator
import datetime
from .models import *
from expenses.models import Expense
from sales.models import Sales
from purchases.models import Purchase
from inventory.models import Stock, Category

# Function to format number in Indian currency style
def indian_currency_format(number):
    s = str(int(number))
    if len(s) <= 3:
        return s
    else:
        last_three = s[-3:]
        other = s[:-3]
        other = ','.join([other[max(i-2,0):i] for i in range(len(other), 0, -2)][::-1])
        return other + ',' + last_three

@login_required
def home(request):
    today = timezone.localdate()

    total_sales = Sales.objects.filter(sold_on__date=today).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    total_purchases = Purchase.objects.filter(purchase_date=today).aggregate(
        total=Sum('total_cost')
    )['total'] or 0

    total_stock = Stock.objects.aggregate(
        total=Sum(F('quantity') * F('cost_price'))
    )['total'] or 0

    total_expenses = Expense.objects.filter(incurred_on=today).aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {
        'total_sales': indian_currency_format(total_sales),
        'total_purchases': indian_currency_format(total_purchases),
        'total_stock': indian_currency_format(total_stock),
        'total_expenses': indian_currency_format(total_expenses),
    }

    return render(request, 'dashboard/home.html', context)

@login_required
def inventory(request):
    stock_list = Stock.objects.select_related('category').all().order_by('category__name', 'sizes')
    
    search_query = request.GET.get('search', '')
    if search_query:
        stock_list = stock_list.filter(
            Q(category__name__icontains=search_query) |
            Q(sizes__icontains=search_query)
        )
    
    category_filter = request.GET.get('category', '')
    if category_filter:
        stock_list = stock_list.filter(category__id=category_filter)
    
    stock_level = request.GET.get('stock_level', '')
    if stock_level == 'low':
        stock_list = stock_list.filter(quantity__lte=10)
    elif stock_level == 'out_of_stock':
        stock_list = stock_list.filter(quantity=0)
    
    paginator = Paginator(stock_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    total_inventory_value = sum(stock.quantity * stock.cost_price for stock in page_obj)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'stock_level': stock_level,
        'total_inventory_value': indian_currency_format(total_inventory_value),
        'total_items': stock_list.count(),
    }
    
    return render(request, 'dashboard/inventory.html', context)

@login_required
def purchases(request):
    # Handle purchase creation
    if request.method == 'POST':
        try:
            stock_item_id = request.POST.get('stock_item')
            quantity_purchased = int(request.POST.get('quantity_purchased', 0))
            cost_price_per_unit = float(request.POST.get('cost_price_per_unit', 0))
            purchase_date = request.POST.get('purchase_date')
            remarks = request.POST.get('remarks', '')
            
            stock_item = get_object_or_404(Stock, id=stock_item_id)
            
            # Create purchase
            purchase = Purchase(
                stock_item=stock_item,
                quantity_purchased=quantity_purchased,
                cost_price_per_unit=cost_price_per_unit,
                purchase_date=purchase_date,
                remarks=remarks
            )
            purchase.save()
            
            messages.success(request, f'Purchase created successfully! Stock updated for {stock_item.category.name} - {stock_item.sizes}')
            return redirect('purchases')
            
        except Exception as e:
            messages.error(request, f'Error creating purchase: {str(e)}')
    
    # Handle purchase deletion
    if request.method == 'POST' and 'delete_purchase' in request.POST:
        try:
            purchase_id = request.POST.get('purchase_id')
            purchase = get_object_or_404(Purchase, id=purchase_id)
            purchase.delete()
            messages.success(request, 'Purchase deleted successfully!')
            return redirect('purchases')
        except Exception as e:
            messages.error(request, f'Error deleting purchase: {str(e)}')
    
    # Get all purchases with related stock items
    purchase_list = Purchase.objects.select_related('stock_item', 'stock_item__category').all().order_by('-purchase_date', '-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        purchase_list = purchase_list.filter(
            Q(stock_item__category__name__icontains=search_query) |
            Q(stock_item__sizes__icontains=search_query) |
            Q(remarks__icontains=search_query)
        )
    
    # Date range filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            purchase_list = purchase_list.filter(purchase_date__range=[start_date_obj, end_date_obj])
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
    
    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        purchase_list = purchase_list.filter(stock_item__category__id=category_filter)
    
    # Pagination
    paginator = Paginator(purchase_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories and stock items for forms
    categories = Category.objects.all()
    stock_items = Stock.objects.select_related('category').all()
    
    # Calculate metrics
    total_purchases_amount = purchase_list.aggregate(total=Sum('total_cost'))['total'] or 0
    total_quantity_purchased = purchase_list.aggregate(total=Sum('quantity_purchased'))['total'] or 0
    
    # Today's purchases
    today = timezone.localdate()
    today_purchases = purchase_list.filter(purchase_date=today).aggregate(total=Sum('total_cost'))['total'] or 0
    
    # Calculate insights for the stats panel
    week_ago = today - datetime.timedelta(days=7)
    month_ago = today - datetime.timedelta(days=30)
    
    week_purchases = purchase_list.filter(purchase_date__gte=week_ago).aggregate(total=Sum('total_cost'))['total'] or 0
    month_purchases = purchase_list.filter(purchase_date__gte=month_ago).aggregate(total=Sum('total_cost'))['total'] or 0
    
    # Average monthly (simplified calculation)
    avg_monthly = total_purchases_amount / 3 if total_purchases_amount > 0 else 0
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'stock_items': stock_items,
        'search_query': search_query,
        'category_filter': category_filter,
        'start_date': start_date,
        'end_date': end_date,
        'total_purchases': indian_currency_format(total_purchases_amount),
        'total_quantity': total_quantity_purchased,
        'today_purchases': indian_currency_format(today_purchases),
        'week_purchases': indian_currency_format(week_purchases),
        'month_purchases': indian_currency_format(month_purchases),
        'avg_monthly': indian_currency_format(avg_monthly),
    }
    
    return render(request, 'dashboard/purchases.html', context)

@login_required
def sales(request):
    # Handle sale creation
    if request.method == 'POST':
        try:
            stock_id = request.POST.get('stock_item')
            quantity_sold = int(request.POST.get('quantity_sold', 1))
            selling_price = float(request.POST.get('selling_price', 0))
            
            stock_item = get_object_or_404(Stock, id=stock_id)
            
            # Check if sufficient stock is available
            if stock_item.quantity < quantity_sold:
                messages.error(request, f'Insufficient stock! Available: {stock_item.quantity}, Requested: {quantity_sold}')
                return redirect('sales')
            
            # Create sale
            sale = Sales(
                stock=stock_item,
                quantity_sold=quantity_sold,
                selling_price=selling_price
            )
            sale.save()
            
            messages.success(request, f'Sale created successfully! {quantity_sold} units of {stock_item.category.name} - {stock_item.sizes} sold.')
            return redirect('sales')
            
        except Exception as e:
            messages.error(request, f'Error creating sale: {str(e)}')
    
    # Handle sale deletion
    if request.method == 'POST' and 'delete_sale' in request.POST:
        try:
            sale_id = request.POST.get('sale_id')
            sale = get_object_or_404(Sales, id=sale_id)
            sale.delete()
            messages.success(request, 'Sale deleted successfully! Stock quantity restored.')
            return redirect('sales')
        except Exception as e:
            messages.error(request, f'Error deleting sale: {str(e)}')
    
    # Get all sales with related stock items
    sales_list = Sales.objects.select_related('stock', 'stock__category').all().order_by('-sold_on')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        sales_list = sales_list.filter(
            Q(stock__category__name__icontains=search_query) |
            Q(stock__sizes__icontains=search_query)
        )
    
    # Date range filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            sales_list = sales_list.filter(sold_on__date__range=[start_date_obj, end_date_obj])
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
    
    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        sales_list = sales_list.filter(stock__category__id=category_filter)
    
    # Pagination
    paginator = Paginator(sales_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories and stock items for forms
    categories = Category.objects.all()
    stock_items = Stock.objects.select_related('category').filter(quantity__gt=0)  # Only items with stock
    
    # Calculate metrics
    total_sales_amount = sales_list.aggregate(total=Sum('total_amount'))['total'] or 0
    total_quantity_sold = sales_list.aggregate(total=Sum('quantity_sold'))['total'] or 0
    total_gross_profit = sales_list.aggregate(total=Sum('gross_profit'))['total'] or 0
    
    # Today's sales
    today = timezone.localdate()
    today_sales = sales_list.filter(sold_on__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    today_profit = sales_list.filter(sold_on__date=today).aggregate(total=Sum('gross_profit'))['total'] or 0
    
    # Calculate insights for the stats panel
    week_ago = today - datetime.timedelta(days=7)
    month_ago = today - datetime.timedelta(days=30)
    
    week_sales = sales_list.filter(sold_on__date__gte=week_ago).aggregate(total=Sum('total_amount'))['total'] or 0
    month_sales = sales_list.filter(sold_on__date__gte=month_ago).aggregate(total=Sum('total_amount'))['total'] or 0
    month_profit = sales_list.filter(sold_on__date__gte=month_ago).aggregate(total=Sum('gross_profit'))['total'] or 0
    
    # Average sale value
    average_sale_value = total_sales_amount / len(sales_list) if sales_list else 0
    
    # Profit margin percentage
    profit_margin = (total_gross_profit / total_sales_amount * 100) if total_sales_amount > 0 else 0
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'stock_items': stock_items,
        'search_query': search_query,
        'category_filter': category_filter,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': indian_currency_format(total_sales_amount),
        'total_quantity_sold': total_quantity_sold,
        'total_gross_profit': indian_currency_format(total_gross_profit),
        'today_sales': indian_currency_format(today_sales),
        'today_profit': indian_currency_format(today_profit),
        'week_sales': indian_currency_format(week_sales),
        'month_sales': indian_currency_format(month_sales),
        'month_profit': indian_currency_format(month_profit),
        'average_sale': indian_currency_format(average_sale_value),
        'profit_margin': round(profit_margin, 1),
    }
    
    return render(request, 'dashboard/sales.html', context)


@login_required
def expenses(request):
    expense_list = Expense.objects.all().order_by('-incurred_on')
    
    search_query = request.GET.get('search', '')
    if search_query:
        expense_list = expense_list.filter(
            Q(expense_type__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            expense_list = expense_list.filter(incurred_on__range=[start_date, end_date])
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
    
    expense_type_filter = request.GET.get('expense_type', '')
    if expense_type_filter:
        expense_list = expense_list.filter(expense_type=expense_type_filter)
    
    paginator = Paginator(expense_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_expenses = expense_list.aggregate(total=Sum('amount'))['total'] or 0
    
    expenses_by_type = expense_list.values('expense_type').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    ).order_by('-total_amount')
    
    expense_types = Expense.EXPENSE_TYPES
    
    context = {
        'page_obj': page_obj,
        'expense_types': expense_types,
        'search_query': search_query,
        'expense_type_filter': expense_type_filter,
        'start_date': start_date,
        'end_date': end_date,
        'total_expenses': indian_currency_format(total_expenses),
        'expenses_by_type': expenses_by_type,
    }
    
    return render(request, 'dashboard/expenses.html', context)