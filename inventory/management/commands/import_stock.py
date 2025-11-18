import pandas as pd
from django.utils import timezone
from inventory.models import Category, Stock

df = pd.read_excel("stock_data.xlsx")

def extract_category(stock_name: str):
    name = stock_name.lower().strip()
    if "kid" in name:
        if "shoe" in name:
            return "Kid's Shoes"
        elif "sandal" in name:
            return "Kid's Sandal"
        elif "jean" in name:
            return "Kid's Jeans"
        elif "shirt" in name:
            return "Kid's Shirt"
        elif "bag" in name:
            return "Kid's Bags"
        elif "crocks" in name or "flip" in name:
            return "Kid's Footwear"
        else:
            return "Kid's Wear"
    elif "men" in name:
        if "shoe" in name:
            return "Men's Shoes"
        elif "jean" in name:
            return "Men's Jeans"
        elif "shirt" in name:
            return "Men's Shirts"
        elif "pant" in name or "trouser" in name:
            return "Men's Trousers"
        elif "cargo" in name:
            return "Men's Cargo"
        elif "lower" in name:
            return "Men's Lower"
        else:
            return "Men's Wear"
    elif "shoe" in name:
        return "Shoes"
    elif "lofer" in name:
        return "Lofer Shoes"
    elif "hitway" in name or "abros" in name:
        return "Sports Shoes"
    else:
        return "Miscellaneous"

for index, row in df.iterrows():
    stock_name = str(row['Stock']).strip().title()
    cost_price = float(row['Price'])
    qty = int(row['Qty'])

    category_name = extract_category(stock_name)
    category, _ = Category.objects.get_or_create(
        name=category_name,
        defaults={'icon_image': 'category_icons/default.png', 'sizes_covered': ''}
    )

    Stock.objects.create(
        category=category,
        name=stock_name,
        cost_price=cost_price,
        sizes="",
        quantity=qty,
        last_updated=timezone.now()
    )

print("✅ Stock data imported with smart categories!")
