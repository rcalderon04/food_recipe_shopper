"""
Product matching utilities with confidence scoring.

Uses fuzzy string matching to calculate how well a product title
matches the ingredient search query.
"""

from rapidfuzz import fuzz
import re


# Negative keywords to avoid false positives
# Format: 'ingredient_keyword': ['negative_word1', 'negative_word2']
NEGATIVE_KEYWORDS = {
    'sausage': ['sauce', 'pizza', 'soup', 'seasoning', 'ravioli', 'lasagna'],
    'chicken': ['soup', 'broth', 'stock', 'seasoning', 'noodle', 'bouillon'],
    'beef': ['broth', 'stock', 'jerky', 'seasoning', 'bouillon'],
    'cheese': ['macaroni', 'cracker', 'snack', 'sauce'],
    'tomato': ['soup', 'ketchup', 'salsa'],
    'milk': ['chocolate', 'cookie', 'cracker'],
    'butter': ['cookie', 'cracker', 'popcorn'],
    'egg': ['noodle', 'salad'],
}

def calculate_confidence(ingredient_query, product_title):
    """
    Calculates a confidence score (0-100) for how well a product matches an ingredient.
    
    Uses multiple fuzzy matching strategies and returns the best score.
    
    Args:
        ingredient_query: Cleaned ingredient name (e.g., "basil")
        product_title: Product title from Amazon (e.g., "Fresh Basil Leaves, 0.75 oz")
        
    Returns:
        Float between 0-100 representing confidence percentage
    """
    if not ingredient_query or not product_title:
        return 0.0
    
    # Normalize both strings
    query_lower = ingredient_query.lower().strip()
    title_lower = product_title.lower().strip()
    
    # Strategy 1: Partial ratio (best for when query is substring of title)
    partial_score = fuzz.partial_ratio(query_lower, title_lower)
    
    # Strategy 2: Token sort ratio (handles word order differences)
    token_sort_score = fuzz.token_sort_ratio(query_lower, title_lower)
    
    # Strategy 3: Token set ratio (handles extra words in title)
    token_set_score = fuzz.token_set_ratio(query_lower, title_lower)
    
    # Strategy 4: Check if query words are all in title (bonus)
    query_words = set(query_lower.split())
    title_words = set(title_lower.split())
    
    if query_words.issubset(title_words):
        word_match_bonus = 10
    else:
        # Partial credit for some words matching
        matching_words = query_words.intersection(title_words)
        word_match_bonus = (len(matching_words) / len(query_words)) * 10 if query_words else 0
    
    # Take the best fuzzy score and add bonus
    best_fuzzy_score = max(partial_score, token_sort_score, token_set_score)
    final_score = min(100, best_fuzzy_score + word_match_bonus)
    
    # --- PENALTIES ---
    
    # 1. Negative Keywords Penalty
    # If the query contains a key (e.g. "sausage") but NOT the negative word (e.g. "sauce"),
    # and the title DOES contain the negative word, apply a heavy penalty.
    for key, negatives in NEGATIVE_KEYWORDS.items():
        if key in query_lower:
            for negative in negatives:
                if negative in title_lower and negative not in query_lower:
                    # Check if negative is a standalone word or part of another word
                    # Simple check: is it in the title words?
                    if negative in title_words:
                        print(f"  Penalty: '{negative}' found in title but not query")
                        final_score -= 40
    
    # 2. General "Sauce/Seasoning" Penalty
    # If query doesn't ask for sauce/seasoning/mix, but title has it, penalize.
    general_negatives = ['sauce', 'seasoning', 'mix', 'blend', 'soup', 'dip']
    for neg in general_negatives:
        if neg in title_words and neg not in query_words:
             # Only apply if the query is short (likely a raw ingredient)
             if len(query_words) <= 2:
                 final_score -= 20
                 
    return max(0, round(final_score, 1))


def rank_products_by_confidence(ingredient_query, products):
    """
    Adds confidence scores to products and sorts by confidence (descending).
    
    Args:
        ingredient_query: Cleaned ingredient name
        products: List of product dicts with 'title' key
        
    Returns:
        List of products with added 'confidence' key, sorted by confidence
    """
    for product in products:
        product['confidence'] = calculate_confidence(ingredient_query, product['title'])
    
    # Sort by confidence (descending), then by price (ascending)
    products.sort(key=lambda x: (-x.get('confidence', 0), x.get('price_float', float('inf'))))
    
    return products


def format_confidence(confidence):
    """
    Formats confidence score for display.
    
    Args:
        confidence: Float 0-100
        
    Returns:
        Formatted string with color indicator
    """
    if confidence >= 80:
        indicator = "✓"  # High confidence
    elif confidence >= 60:
        indicator = "~"  # Medium confidence
    else:
        indicator = "?"  # Low confidence
    
    return f"{indicator} {confidence:>4.0f}%"
