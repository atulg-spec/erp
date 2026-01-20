import google.generativeai as genai
from django.conf import settings
from inventory.models import Stock
from sales.models import Sales
from purchases.models import Purchase  # Adjust name if your app is 'purchases'

genai.configure(api_key='AIzaSyCFA_Gh6lYggQFZZcKhGghHe5G89-JXEDg')

def get_erp_context():
    # Gather data from your models to give to Gemini
    stocks = Stock.objects.all()
    sales = Sales.objects.all()[:10]  # Last 10 sales
    
    inventory_data = "\n".join([
        f"Item: {s.name}, Qty: {s.quantity}, Price: {s.selling_price}" 
        for s in stocks
    ])
    
    sales_data = "\n".join([
        f"Sold {s.quantity_sold} of {s.stock.name} for {s.total_amount}" 
        for s in sales
    ])

    return f"""
    You are an ERP Assistant. Here is the current store status:
    
    Inventory:
    {inventory_data}
    
    Recent Sales:
    {sales_data}
    
    Answer the user's question based on this data. Be concise.
    """

# Change this line in assistant/utils.py
def ask_gemini(user_query):
    # Use 'gemini-3-flash-preview' or 'gemini-2.5-flash'
    model = genai.GenerativeModel('gemini-3-flash-preview') 
    context = get_erp_context()
    
    response = model.generate_content(f"{context}\n\nUser Question: {user_query}")
    return response.text