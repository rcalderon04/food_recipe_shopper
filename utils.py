import re

# Common measurement words to remove
MEASUREMENTS = {
    'cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
    'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb', 'lbs', 'gram', 'grams', 'g',
    'kilogram', 'kilograms', 'kg', 'milliliter', 'milliliters', 'ml', 'liter', 'liters', 'l',
    'pint', 'pints', 'quart', 'quarts', 'gallon', 'gallons', 'piece', 'pieces', 'slice', 'slices',
    'can', 'cans', 'jar', 'jars', 'package', 'packages', 'bag', 'bags', 'box', 'boxes',
    'bunch', 'bunches', 'clove', 'cloves', 'head', 'heads', 'stalk', 'stalks'
}

# Common preparation/descriptor words to remove
PREP_WORDS = {
    'chopped', 'diced', 'sliced', 'minced', 'crushed', 'grated', 'shredded', 'julienned',
    'peeled', 'seeded', 'deveined', 'trimmed', 'cubed', 'halved', 'quartered',
    'fresh', 'frozen', 'dried', 'canned', 'cooked', 'raw', 'whole', 'ground',
    'finely', 'roughly', 'thinly', 'thickly', 'large', 'small', 'medium',
    'optional', 'to', 'taste', 'for', 'serving', 'garnish', 'divided'
}

# Common articles and connectors
ARTICLES = {'a', 'an', 'the', 'of', 'or', 'and'}

def clean_ingredient_name(ingredient_text):
    """
    Extracts the core product name from an ingredient string.
    
    Examples:
        "2 cups chopped onions" -> "onions"
        "1 lb ground beef" -> "beef"
        "3 tablespoons olive oil" -> "olive oil"
    
    Args:
        ingredient_text: Raw ingredient string from recipe
        
    Returns:
        Cleaned product name suitable for searching
    """
    if not ingredient_text:
        return ""
    
    # Convert to lowercase for processing
    text = ingredient_text.lower().strip()
    
    # Remove parenthetical notes (e.g., "1 cup flour (all-purpose)")
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Remove fractions and numbers (including unicode fractions)
    # Match patterns like: 1, 1.5, 1/2, ½, etc.
    text = re.sub(r'\d+\.?\d*', '', text)  # Regular numbers
    text = re.sub(r'[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]', '', text)  # Unicode fractions
    text = re.sub(r'\d+/\d+', '', text)  # Fractions like 1/2
    
    # Remove dashes that might separate quantity from ingredient
    text = re.sub(r'\s*-\s*', ' ', text)
    
    # Split into words
    words = text.split()
    
    # Filter out measurement, prep, and article words
    filtered_words = []
    for word in words:
        # Remove punctuation from word for comparison
        clean_word = re.sub(r'[^\w\s-]', '', word)
        if clean_word and clean_word not in MEASUREMENTS and \
           clean_word not in PREP_WORDS and clean_word not in ARTICLES:
            filtered_words.append(word)
    
    # Join remaining words
    result = ' '.join(filtered_words).strip()
    
    # If we filtered everything out, return original (better than nothing)
    if not result:
        return ingredient_text
    
    # Remove any remaining punctuation at start/end
    result = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', result)
    
    return result


def parse_price(price_string):
    """
    Parses a price string into a float.
    
    Examples:
        "$1.99" -> 1.99
        "1.99" -> 1.99
        "$1,234.56" -> 1234.56
        "N/A" -> None
    
    Args:
        price_string: Price as a string
        
    Returns:
        Float value or None if parsing fails
    """
    if not price_string or price_string == "N/A":
        return None
    
    try:
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,]', '', price_string)
        return float(cleaned)
    except (ValueError, TypeError):
        return None
