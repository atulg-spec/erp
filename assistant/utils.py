import google.generativeai as genai
from django.conf import settings
from inventory.models import Stock
from sales.models import Sales
from purchases.models import Purchase  # Adjust name if your app is 'purchases'
from purchase_returns.models import PurchaseReturn  # Adjust name if your app is 'purchase_returns'
from utility.models import Bills  # Adjust name if your app is 'bills'        

genai.configure(api_key='AIzaSyBIiYHZWwxrnc_3iKLEvFaJFTetaG_wsx0')

def get_erp_context():
    # 1. Inventory Data (All fields)
    stocks = Stock.objects.all()
    inventory_list = []
    for s in stocks:
        inventory_list.append(
            f"ID: {s.id} | Item: {s.name} | Category: {s.category.name} | "
            f"Qty: {s.quantity} | Cost: {s.cost_price} | Sell Price: {s.selling_price} | "
            f"Last Updated: {s.last_updated.strftime('%Y-%m-%d %H:%M')}"
        )
    inventory_data = "\n".join(inventory_list)

    # 2. Sales Data (All fields including Profit and Date)
    sales = Sales.objects.all()
    sales_list = []
    for s in sales:
        sales_list.append(
            f"Date: {s.sold_on.strftime('%Y-%m-%d')} | Item: {s.stock.name} | "
            f"Qty Sold: {s.quantity_sold} | Price: {s.selling_price} | "
            f"Total: {s.total_amount} | Profit: {s.gross_profit} | Verified: {s.is_verified}"
        )
    sales_data = "\n".join(sales_list)

    # 3. Purchase Data
    purchases = Purchase.objects.all()
    purchase_list = []
    for p in purchases:
        purchase_list.append(
            f"Date: {p.purchase_date} | Item: {p.stock_item.name} | "
            f"Qty: {p.quantity_purchased} | Unit Cost: {p.cost_price_per_unit} | "
            f"Total Cost: {p.total_cost} | Received: {p.is_received}"
        )
    purchase_data = "\n".join(purchase_list)

    # 4. Returns & Bills
    returns = PurchaseReturn.objects.all()
    return_list = [f"Item: {r.stock_item.name} | Qty: {r.quantity_returned} | Processed: {r.is_processed}" for r in returns]
    
    bills = Bills.objects.all()
    bill_list = [f"Bill Date: {b.date} | File: {b.file.name}" for b in bills]

    # Combine everything into a massive context string
    return f"""
    You are the Store ERP AI Manager. Below is the COMPLETE store data:

    --- INVENTORY STOCK ---
    {inventory_data}

    --- SALES RECORDS ---
    {sales_data}

    --- PURCHASE RECORDS ---
    {purchase_data}

    --- PURCHASE RETURNS ---
    {"/n".join(return_list)}

    --- UPLOADED BILLS ---
    {"/n".join(bill_list)}

    INSTRUCTIONS:
    - Use the data above to answer user queries accurately.
    - If asked about profits, sum up the 'Profit' fields from Sales.
    - If asked about low stock, identify items with low 'Qty'.
    - Be professional and helpful.
    """

# Change this line in assistant/utils.py
def ask_gemini(user_query):
    # Use 'gemini-3-flash-preview' or 'gemini-2.5-flash'
    model = genai.GenerativeModel('gemini-3-flash-preview') 
    context = get_erp_context()
    
    response = model.generate_content(f"{context}\n\nUser Question: {user_query}")
    print(response.text)
    return response.text