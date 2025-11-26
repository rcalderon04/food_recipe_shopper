"""
Quick test for quantity-aware matching feature.
"""

from quantity_parser import parse_quantity
from conversions import convert_recipe_to_purchase

# Test ingredients from the lasagna recipe
test_ingredients = [
    "2 cups minced onion",
    "2 (6 ounce) cans tomato paste",
    "2 (6.5 ounce) cans canned tomato sauce",
    "1 pound sweet Italian sausage",
    "¾ pound lean ground beef",
    "16 ounces ricotta cheese",
    "3 cloves garlic",
]

print("=" * 70)
print("QUANTITY-AWARE MATCHING TEST")
print("=" * 70)
print()

for ingredient in test_ingredients:
    print(f"Ingredient: {ingredient}")
    
    # Parse quantity
    qty = parse_quantity(ingredient)
    print(f"  Parsed: {qty['total_amount']} {qty['total_unit']}")
    if qty['container']:
        print(f"  Container: {qty['count']} {qty['container']}(s) of {qty['amount']} {qty['unit']} each")
    
    # Convert to purchase
    from utils import clean_ingredient_name
    clean_name = clean_ingredient_name(ingredient)
    purchase = convert_recipe_to_purchase(qty, clean_name)
    
    if purchase['note']:
        print(f"  {purchase['note']}")
    
    if purchase['recommendations']:
        print(f"  Recommended sizes: {purchase['recommendations']} oz")
    
    print()

print("=" * 70)
print("\nTest complete! Run 'python main.py' to see this in action with Amazon Fresh.")
