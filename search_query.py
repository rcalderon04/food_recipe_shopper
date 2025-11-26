"""
Enhanced ingredient name extraction that preserves important context.

Uses quantity information to create better search queries.
"""

from quantity_parser import parse_quantity
from utils import clean_ingredient_name


def create_search_query(ingredient_text):
    """
    Creates an optimized search query from ingredient text.
    
    Preserves important context like:
    - Container types (can, jar, box)
    - Package sizes for pre-packaged items
    - Product forms (crushed, diced, whole)
    
    Examples:
        "2 (6 ounce) cans tomato paste" → "6 oz can tomato paste"
        "1 (28 ounce) can crushed tomatoes" → "28 oz can crushed tomatoes"
        "2 cups minced onion" → "onion"
        "1 pound ground beef" → "ground beef"
    
    Args:
        ingredient_text: Raw ingredient string from recipe
        
    Returns:
        Optimized search query string
    """
    # Parse quantity information
    qty_info = parse_quantity(ingredient_text)
    
    # Get basic cleaned name
    base_name = clean_ingredient_name(ingredient_text)
    
    # Restore important forms that might have been cleaned
    # (crushed, diced, whole, sliced, chopped, ground, shredded, dried, frozen)
    text_lower = ingredient_text.lower()
    preserved_forms = [
        'crushed', 'diced', 'whole', 'sliced', 'chopped', 'ground', 
        'shredded', 'dried', 'frozen', 'stewed', 'puree', 'paste'
    ]
    
    # Check for specific product-form combinations where form is crucial
    # Or if it's a canned/packaged item, the form is usually part of the product
    is_packaged = 'can' in text_lower or 'jar' in text_lower or 'frozen' in text_lower
    
    for form in preserved_forms:
        if form in text_lower:
            # If it's a known product-form combo OR it's a packaged item
            # We want to keep the form (e.g. "crushed tomatoes", "frozen spinach")
            should_preserve = is_packaged
            
            if not should_preserve:
                # Check specific overrides
                product_forms = [
                    'tomatoes', 'beef', 'pork', 'turkey', 'chicken', 
                    'cheese', 'spinach', 'corn', 'peas', 'beans'
                ]
                for prod in product_forms:
                    if prod in base_name:
                        should_preserve = True
                        break
            
            if should_preserve and form not in base_name:
                base_name = f"{form} {base_name}"
    
    # Check if this is a pre-packaged item (has container)
    if qty_info.get('container') and qty_info.get('amount') and qty_info.get('unit'):
        # For pre-packaged items, include size and container
        # e.g., "6 oz can tomato paste"
        size = qty_info['amount']
        unit = qty_info['unit']
        container = qty_info['container']
        
        # Build query: "size unit container product"
        query = f"{size} {unit} {container} {base_name}"
        return query.strip()
    
    # Check if "can" or "jar" is mentioned (even without quantity parsing)
    # This catches cases like "can crushed tomatoes"
    container_keywords = ['can', 'cans', 'jar', 'jars', 'box', 'boxes', 'package', 'packages']
    for keyword in container_keywords:
        if keyword in text_lower.split():
            # Add container to search if not already there
            if keyword.rstrip('s') not in base_name:
                # Use singular form
                container_singular = keyword.rstrip('s')
                base_name = f"{container_singular} {base_name}"
            break
    
    return base_name.strip()


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "2 (6 ounce) cans tomato paste",
        "1 (28 ounce) can crushed tomatoes",
        "2 (6.5 ounce) cans canned tomato sauce",
        "2 cups minced onion",
        "1 pound ground beef",
        "¾ pound lean ground beef",
        "16 ounces ricotta cheese",
        "12 lasagna noodles",
        "1 can crushed tomatoes",
        "2 cups shredded mozzarella cheese",
    ]
    
    print("Search Query Optimization Test:\n")
    for ingredient in test_cases:
        query = create_search_query(ingredient)
        print(f"Input:  {ingredient}")
        print(f"Query:  {query}")
        print()
