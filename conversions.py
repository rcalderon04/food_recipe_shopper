"""
Conversion tables for recipe quantities to purchase quantities.

Focuses on top 10 common ingredients with data-backed conversions.
"""

# Volume to weight conversions for common produce/ingredients
# Based on USDA data and standard cooking measurements
VOLUME_TO_WEIGHT = {
    # Vegetables
    'onion': {
        'cup': 0.35,  # 1 cup diced onion ≈ 0.35 lbs (5.6 oz)
        'medium': 0.5,  # 1 medium onion ≈ 0.5 lbs
    },
    'garlic': {
        'clove': 0.01,  # 1 clove ≈ 0.01 lbs (0.16 oz)
        'head': 0.15,  # 1 head ≈ 0.15 lbs
    },
    'tomato': {
        'cup': 0.4,  # 1 cup diced tomato ≈ 0.4 lbs
        'medium': 0.4,  # 1 medium tomato ≈ 0.4 lbs
    },
    
    # Dairy
    'cheese': {
        'cup': 4,  # 1 cup shredded cheese ≈ 4 oz
    },
    'butter': {
        'tablespoon': 0.5,  # 1 tbsp butter ≈ 0.5 oz
        'stick': 4,  # 1 stick ≈ 4 oz
    },
    
    # Dry goods
    'flour': {
        'cup': 4.5,  # 1 cup all-purpose flour ≈ 4.5 oz
    },
    'sugar': {
        'cup': 7,  # 1 cup granulated sugar ≈ 7 oz
    },
}

# Standard package sizes available at grocery stores
# Values in ounces for consistency
STANDARD_PACKAGE_SIZES = {
    'onion': [16, 32, 48, 80],  # 1 lb, 2 lb, 3 lb, 5 lb bags
    'garlic': [2, 4, 8],  # Small packages, heads, or jars
    'ground_beef': [16, 32, 48],  # 1 lb, 2 lb, 3 lb packages
    'tomato_paste': [6, 12, 16],  # 6 oz, 12 oz, 16 oz cans
    'tomato_sauce': [8, 15, 29],  # 8 oz, 15 oz, 29 oz cans
    'tomatoes_crushed': [14, 28],  # 14 oz, 28 oz cans
    'cheese': [8, 16, 32],  # 8 oz, 1 lb, 2 lb packages
    'eggs': [12, 18, 24],  # dozen, 1.5 dozen, 2 dozen
    'pasta': [12, 16, 32],  # 12 oz, 1 lb, 2 lb boxes
    'flour': [32, 80],  # 2 lb, 5 lb bags
    'sugar': [32, 64],  # 2 lb, 4 lb bags
}

# Ingredient name normalization for matching
INGREDIENT_ALIASES = {
    'onions': 'onion',
    'yellow onion': 'onion',
    'white onion': 'onion',
    'red onion': 'onion',
    'sweet onion': 'onion',
    
    'garlic cloves': 'garlic',
    'garlic clove': 'garlic',
    
    'ground beef': 'ground_beef',
    'lean beef': 'ground_beef',
    'beef': 'ground_beef',
    
    'tomato paste': 'tomato_paste',
    'tomato sauce': 'tomato_sauce',
    'crushed tomatoes': 'tomatoes_crushed',
    'tomatoes': 'tomatoes_crushed',
    
    'mozzarella cheese': 'cheese',
    'parmesan cheese': 'cheese',
    'ricotta cheese': 'cheese',
    'cheddar cheese': 'cheese',
    
    'egg': 'eggs',
    
    'lasagna noodles': 'pasta',
    'pasta': 'pasta',
    'noodles': 'pasta',
    'spaghetti': 'pasta',
    
    'all-purpose flour': 'flour',
    'white flour': 'flour',
    
    'white sugar': 'sugar',
    'granulated sugar': 'sugar',
}


def normalize_ingredient(ingredient_name):
    """Normalizes ingredient name for lookup."""
    name = ingredient_name.lower().strip()
    return INGREDIENT_ALIASES.get(name, name)


def convert_to_ounces(amount, unit):
    """
    Converts various units to ounces for standardization.
    
    Returns:
        float: Amount in ounces, or None if conversion not possible
    """
    if unit == 'oz':
        return amount
    elif unit == 'lb':
        return amount * 16
    elif unit == 'g':
        return amount * 0.035274
    elif unit == 'kg':
        return amount * 35.274
    elif unit == 'cup':
        return amount * 8  # Fluid ounces (approximate for volume)
    elif unit == 'tablespoon':
        return amount * 0.5
    elif unit == 'teaspoon':
        return amount * 0.166667
    else:
        return None


def convert_recipe_to_purchase(quantity_info, ingredient_name):
    """
    Converts recipe quantity to recommended purchase quantity.
    
    Args:
        quantity_info: Dict from quantity_parser.parse_quantity()
        ingredient_name: Cleaned ingredient name
        
    Returns:
        dict with:
            - needed_oz: Amount needed in ounces
            - needed_range: (low, high) range in ounces
            - unit: Recommended unit for display
            - recommendations: List of suitable package sizes
            - note: Human-readable note
    """
    result = {
        'needed_oz': None,
        'needed_range': None,
        'unit': 'oz',
        'recommendations': [],
        'note': None
    }
    
    # Normalize ingredient name
    normalized = normalize_ingredient(ingredient_name)
    
    # Get total amount from quantity info
    total_amount = quantity_info.get('total_amount')
    total_unit = quantity_info.get('total_unit')
    
    if not total_amount or not total_unit:
        result['note'] = "Could not determine quantity"
        return result
    
    # Convert to ounces
    needed_oz = convert_to_ounces(total_amount, total_unit)
    
    if needed_oz is None:
        # Try volume to weight conversion
        if normalized in VOLUME_TO_WEIGHT and total_unit in VOLUME_TO_WEIGHT[normalized]:
            weight_per_unit = VOLUME_TO_WEIGHT[normalized][total_unit]
            needed_oz = total_amount * weight_per_unit
    
    if needed_oz is None:
        result['note'] = f"Need {total_amount} {total_unit}"
        return result
    
    result['needed_oz'] = needed_oz
    
    # Calculate range (±20%)
    low = needed_oz * 0.8
    high = needed_oz * 1.2
    result['needed_range'] = (low, high)
    
    # Find suitable package sizes
    if normalized in STANDARD_PACKAGE_SIZES:
        sizes = STANDARD_PACKAGE_SIZES[normalized]
        
        # Find packages that meet or slightly exceed the need
        suitable = []
        for size in sizes:
            if size >= low:  # Package is large enough
                suitable.append(size)
        
        if suitable:
            result['recommendations'] = suitable[:3]  # Top 3 options
    
    # Format display unit
    if needed_oz >= 16:
        result['unit'] = 'lb'
        result['needed_oz'] = needed_oz / 16
        if result['needed_range']:
            result['needed_range'] = (low / 16, high / 16)
    
    # Create note
    if result['needed_range']:
        low_val, high_val = result['needed_range']
        if result['unit'] == 'lb':
            result['note'] = f"Need {low_val:.1f}-{high_val:.1f} lbs"
        else:
            result['note'] = f"Need {low_val:.0f}-{high_val:.0f} oz"
    
    return result


def get_size_match_indicator(product_size_oz, needed_range):
    """
    Returns a human-readable indicator of how well product size matches need.
    
    Args:
        product_size_oz: Product size in ounces
        needed_range: (low, high) tuple of needed range in ounces
        
    Returns:
        str: Indicator like "[Perfect size]", "[Larger]", etc.
    """
    if not needed_range or not product_size_oz:
        return ""
    
    low, high = needed_range
    
    if low <= product_size_oz <= high:
        return "[Perfect size]"
    elif product_size_oz < low:
        # Calculate how many needed
        count = int(low / product_size_oz) + 1
        return f"[May need {count}]"
    elif product_size_oz <= high * 1.3:
        return "[Slightly larger]"
    elif product_size_oz <= high * 1.5:
        return "[Larger than needed]"
    else:
        return "[Much larger]"


if __name__ == "__main__":
    from quantity_parser import parse_quantity
    
    # Test cases
    test_cases = [
        ("2 cups minced onion", "onion"),
        ("2 (6 ounce) cans tomato paste", "tomato paste"),
        ("1 pound ground beef", "ground beef"),
        ("3 cloves garlic", "garlic"),
        ("16 ounces ricotta cheese", "ricotta cheese"),
    ]
    
    print("Conversion Test Cases:\n")
    for ingredient_text, ingredient_name in test_cases:
        qty = parse_quantity(ingredient_text)
        conversion = convert_recipe_to_purchase(qty, ingredient_name)
        
        print(f"Input: {ingredient_text}")
        print(f"  Parsed: {qty['total_amount']} {qty['total_unit']}")
        print(f"  {conversion['note']}")
        if conversion['recommendations']:
            print(f"  Recommended sizes: {conversion['recommendations']} oz")
        print()
