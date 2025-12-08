"""
Quantity parsing for recipe ingredients.

Extracts structured quantity information including amounts, units, and handles
complex cases like "2 (6 ounce) cans tomato paste".
"""

import re
from fractions import Fraction


# Unicode fraction mapping
UNICODE_FRACTIONS = {
    '¼': 0.25, '½': 0.5, '¾': 0.75,
    '⅐': 1/7, '⅑': 1/9, '⅒': 0.1,
    '⅓': 1/3, '⅔': 2/3,
    '⅕': 0.2, '⅖': 0.4, '⅗': 0.6, '⅘': 0.8,
    '⅙': 1/6, '⅚': 5/6,
    '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875
}

# Common units (normalized to singular)
UNIT_MAPPINGS = {
    # Volume
    'cup': 'cup', 'cups': 'cup', 'c': 'cup',
    'tablespoon': 'tablespoon', 'tablespoons': 'tablespoon', 'tbsp': 'tablespoon', 'tbs': 'tablespoon',
    'teaspoon': 'teaspoon', 'teaspoons': 'teaspoon', 'tsp': 'teaspoon',
    'fluid ounce': 'fl oz', 'fluid ounces': 'fl oz', 'fl oz': 'fl oz', 'fl. oz': 'fl oz',
    'pint': 'pint', 'pints': 'pint', 'pt': 'pint',
    'quart': 'quart', 'quarts': 'quart', 'qt': 'quart',
    'gallon': 'gallon', 'gallons': 'gallon', 'gal': 'gallon',
    'milliliter': 'ml', 'milliliters': 'ml', 'ml': 'ml',
    'liter': 'liter', 'liters': 'liter', 'l': 'liter',
    
    # Weight
    'pound': 'lb', 'pounds': 'lb', 'lb': 'lb', 'lbs': 'lb',
    'ounce': 'oz', 'ounces': 'oz', 'oz': 'oz',
    'gram': 'g', 'grams': 'g', 'g': 'g',
    'kilogram': 'kg', 'kilograms': 'kg', 'kg': 'kg',
    
    # Count
    'piece': 'piece', 'pieces': 'piece',
    'clove': 'clove', 'cloves': 'clove',
    'can': 'can', 'cans': 'can',
    'jar': 'jar', 'jars': 'jar',
    'package': 'package', 'packages': 'package', 'pkg': 'package',
    'bag': 'bag', 'bags': 'bag',
    'box': 'box', 'boxes': 'box',
    'bunch': 'bunch', 'bunches': 'bunch',
    'head': 'head', 'heads': 'head',
    'stalk': 'stalk', 'stalks': 'stalk',
}


def parse_number(text):
    """
    Parses a number from text, handling fractions, decimals, and unicode fractions.
    
    Examples:
        "2" → 2.0
        "1.5" → 1.5
        "1/2" → 0.5
        "1 1/2" → 1.5
        "½" → 0.5
        "2½" → 2.5
    """
    text = text.strip()
    
    # Check for unicode fractions
    for unicode_frac, value in UNICODE_FRACTIONS.items():
        if unicode_frac in text:
            # Handle cases like "2½"
            before = text.split(unicode_frac)[0].strip()
            if before:
                try:
                    return float(before) + value
                except:
                    return value
            return value
    
    # Handle mixed fractions like "1 1/2"
    mixed_match = re.match(r'(\d+)\s+(\d+)/(\d+)', text)
    if mixed_match:
        whole = int(mixed_match.group(1))
        numerator = int(mixed_match.group(2))
        denominator = int(mixed_match.group(3))
        return whole + (numerator / denominator)
    
    # Handle simple fractions like "1/2"
    frac_match = re.match(r'(\d+)/(\d+)', text)
    if frac_match:
        numerator = int(frac_match.group(1))
        denominator = int(frac_match.group(2))
        return numerator / denominator
    
    # Handle decimals and integers
    try:
        return float(text)
    except:
        return None


def parse_quantity(ingredient_text):
    """
    Extracts quantity information from ingredient text.
    
    Handles complex cases like:
    - "2 cups minced onion" → {count: 1, amount: 2, unit: 'cup'}
    - "2 (6 ounce) cans tomato paste" → {count: 2, amount: 6, unit: 'oz', container: 'can'}
    - "1 pound ground beef" → {count: 1, amount: 1, unit: 'lb'}
    - "3 cloves garlic" → {count: 3, amount: 3, unit: 'clove'}
    
    Returns:
        dict with keys:
            - count: Number of items/containers (e.g., 2 cans)
            - amount: Amount per item (e.g., 6 oz per can)
            - unit: Unit of measurement
            - container: Type of container (can, jar, etc.) if applicable
            - total_amount: Total quantity (count * amount)
            - total_unit: Unit for total
            - original: Original text
    """
    result = {
        'count': None,
        'amount': None,
        'unit': None,
        'container': None,
        'total_amount': None,
        'total_unit': None,
        'original': ingredient_text
    }
    
    # Pattern for complex cases: "2 (6 ounce) cans"
    # Captures: count (size unit) container
    complex_pattern = r'(\d+(?:\s+\d+/\d+)?|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])\s*\((\d+(?:\.\d+)?(?:\s+\d+/\d+)?|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])\s*([a-zA-Z\s]+)\)\s*([a-zA-Z]+)'
    
    complex_match = re.search(complex_pattern, ingredient_text)
    if complex_match:
        count_str = complex_match.group(1)
        amount_str = complex_match.group(2)
        unit_str = complex_match.group(3).strip().lower()
        container_str = complex_match.group(4).strip().lower()
        
        result['count'] = parse_number(count_str)
        result['amount'] = parse_number(amount_str)
        result['unit'] = UNIT_MAPPINGS.get(unit_str, unit_str)
        result['container'] = UNIT_MAPPINGS.get(container_str, container_str)
        
        if result['count'] and result['amount']:
            result['total_amount'] = result['count'] * result['amount']
            result['total_unit'] = result['unit']
        
        return result
    
    # Pattern for simple cases: "2 cups" or "1 pound" or "3 cloves"
    # Captures: amount unit
    simple_pattern = r'(\d+(?:\.\d+)?(?:\s+\d+/\d+)?|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])\s*([a-zA-Z\s]+?)(?:\s|,|$)'
    
    simple_match = re.search(simple_pattern, ingredient_text)
    if simple_match:
        amount_str = simple_match.group(1)
        unit_str = simple_match.group(2).strip().lower()
        
        # Check if unit is valid
        normalized_unit = UNIT_MAPPINGS.get(unit_str)
        if normalized_unit:
            result['amount'] = parse_number(amount_str)
            result['unit'] = normalized_unit
            result['count'] = 1
            result['total_amount'] = result['amount']
            result['total_unit'] = result['unit']
            
            return result
    
    # No quantity found
    return result


def format_quantity_range(amount, unit, margin=0.2):
    """
    Formats a quantity as a range with margin.
    
    Args:
        amount: Base amount
        unit: Unit of measurement
        margin: Margin as percentage (0.2 = ±20%)
        
    Returns:
        Formatted string like "0.8-1.2 lbs" or "10-14 oz"
    """
    if amount is None:
        return "unknown amount"
    
    low = amount * (1 - margin)
    high = amount * (1 + margin)
    
    # Round to reasonable precision
    if amount >= 10:
        low = round(low)
        high = round(high)
    elif amount >= 1:
        low = round(low, 1)
        high = round(high, 1)
    else:
        low = round(low, 2)
        high = round(high, 2)
    
    return f"{low}-{high} {unit}"


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "2 cups minced onion",
        "2 (6 ounce) cans tomato paste",
        "1 pound ground beef",
        "3 cloves garlic",
        "½ cup water",
        "1 ½ teaspoons salt",
        "2 (6.5 ounce) cans tomato sauce",
        "12 lasagna noodles",
    ]
    
    print("Quantity Parser Test Cases:\n")
    for test in test_cases:
        result = parse_quantity(test)
        print(f"Input: {test}")
        print(f"  Count: {result['count']}")
        print(f"  Amount: {result['amount']} {result['unit']}")
        if result['container']:
            print(f"  Container: {result['container']}")
        if result['total_amount']:
            print(f"  Total: {result['total_amount']} {result['total_unit']}")
            print(f"  Range: {format_quantity_range(result['total_amount'], result['total_unit'])}")
            
        print(f"  Clean Name: {clean_ingredient_name(test)}")
        print()

def clean_ingredient_name(text):
    """
    Removes quantity, unit, and container info to get the raw ingredient name.
    Example: "1 tablespoon dill" -> "dill"
             "2 (6 oz) cans tomato paste" -> "tomato paste"
    """
    if not text: return ""
    
    # 1. Remove complex patterns like "2 (6 oz) cans"
    # Matches: number + space + (number unit) + space + word
    complex_pattern = r'(\d+(?:\s+\d+/\d+)?|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])\s*\(.*?\)\s*[a-zA-Z]+\s*'
    text = re.sub(complex_pattern, '', text).strip()
    
    # 2. Remove simple quantities and units
    
    # Better number pattern including fractions and unicode combos
    # Matches: "1 1/2", "1 ½", "1/2", "½", "1-2", "1.5", "1"
    number_pattern = r'^(\d+\s+\d+/\d+|\d+\s*[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+/\d+|\d+\.\d+|\d+\s*-\s*\d+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+)\s*'
    text = re.sub(number_pattern, '', text).strip()
    
    # Remove unit words if they appear at the start now
    units = list(UNIT_MAPPINGS.keys())
    units.sort(key=len, reverse=True)
    
    # Match unit + optional "of" + space
    unit_pattern = r'^(' + '|'.join(map(re.escape, units)) + r')\.?(?:s)?\s+(?:of\s+)?'
    text = re.sub(unit_pattern, '', text, flags=re.IGNORECASE).strip()
    
    # NEW: Remove common preparation adjectives and filler words
    prep_words = [
        'chopped', 'minced', 'sliced', 'diced', 'crushed', 'ground', 'grated', 'shredded',
        'cubed', 'peeled', 'cored', 'seeded', 'julienned', 'halved', 'quartered', 
        'beaten', 'sifted', 'melted', 'softened', 'finely', 'coarsely', 'roughly',
        'leaves', 'leaf', 'stems' 
    ]
    
    # Remove prep words from start
    prep_pattern = r'^(' + '|'.join(map(re.escape, prep_words)) + r')\s+'
    for _ in range(3):
        text = re.sub(prep_pattern, '', text, flags=re.IGNORECASE).strip()
        
    # Remove specific trailing phrases
    trailing_phrases = [
        r',\s*divided.*$',
        r',\s*or to taste.*$',
        r',\s*plus more.*$',
        r',\s*to taste.*$',
        r',\s*optional.*$'
    ]
    for pattern in trailing_phrases:
         text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
         
    # Remove specific suffixes (words that often appear at the end)
    suffix_words = ['leaves', 'leaf', 'stems', 'florets', 'spears', 'wedges', 'ribs']
    suffix_pattern = r'\s+(' + '|'.join(map(re.escape, suffix_words)) + r')$'
    text = re.sub(suffix_pattern, '', text, flags=re.IGNORECASE).strip()
    
    return text
