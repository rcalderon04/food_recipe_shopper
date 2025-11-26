"""
Quick test script for the shopping list tool.

This script demonstrates the enhanced 3-option selection feature with confidence scoring.
"""

from parser import parse_recipe
from shopper import AmazonShopper
from utils import clean_ingredient_name, parse_price
from matcher import rank_products_by_confidence, format_confidence

# Test recipe URL - using a simple recipe for testing
TEST_URL = "https://www.allrecipes.com/recipe/23600/worlds-best-lasagna/"

def test_parser():
    """Test the recipe parser."""
    print("=" * 60)
    print("TESTING RECIPE PARSER")
    print("=" * 60)
    print(f"\nURL: {TEST_URL}\n")
    
    ingredients = parse_recipe(TEST_URL)
    
    if ingredients:
        print(f"✓ Found {len(ingredients)} ingredients:\n")
        for i, ing in enumerate(ingredients, 1):
            cleaned = clean_ingredient_name(ing)
            print(f"{i:2}. {ing}")
            print(f"    → Search query: '{cleaned}'")
        return ingredients
    else:
        print("✗ No ingredients found")
        return []

def test_shopper_search(ingredients):
    """Test Amazon Fresh search with the enhanced UI."""
    print("\n" + "=" * 60)
    print("TESTING AMAZON FRESH SEARCH (Enhanced 3-Option UI)")
    print("=" * 60)
    
    print("\nStarting browser (headless=False for visibility)...")
    shopper = AmazonShopper(headless=False)
    
    try:
        shopper.start()
        print("\n⚠️  You will need to log in to Amazon Fresh manually.")
        print("    The browser will stay open for 30 seconds for login.")
        shopper.login()
        
        # Test with first 2 ingredients only
        test_ingredients = ingredients[:2]
        
        for ingredient in test_ingredients:
            print(f"\n{'─' * 60}")
            print(f"Ingredient: {ingredient}")
            
            search_query = clean_ingredient_name(ingredient)
            print(f"Search query: '{search_query}'")
            
            results = shopper.search_item(search_query)
            
            if results:
                print(f"\n✓ Found {len(results)} results")
                
                # Parse prices
                for r in results:
                    r['price_float'] = parse_price(r['price'])
                
                valid_results = [r for r in results if r['price_float'] is not None]
                
                # Rank by confidence
                ranked_results = rank_products_by_confidence(search_query, valid_results)
                
                # Show top 3 with confidence scores
                top_options = ranked_results[:3]
                print("\nTop 3 options (with confidence scores):")
                for idx, option in enumerate(top_options, 1):
                    confidence_str = format_confidence(option.get('confidence', 0))
                    print(f"  [{idx}] {confidence_str} | ${option['price']:>6} - {option['title'][:60]}")
                
                print("\n(In real usage, you would select an option here)")
            else:
                print("✗ No results found")
        
        print("\n" + "=" * 60)
        print("Test complete! Browser will close in 10 seconds...")
        import time
        time.sleep(10)
        
    finally:
        shopper.close()

if __name__ == "__main__":
    print("\n🛒 Shopping List Tool - Test Script\n")
    
    # Test 1: Parser
    ingredients = test_parser()
    
    if not ingredients:
        print("\n❌ Parser test failed. Cannot proceed with shopper test.")
        exit(1)
    
    # Ask if user wants to continue to shopper test
    print("\n" + "=" * 60)
    response = input("\nContinue to Amazon Fresh search test? (y/n): ").lower()
    
    if response == 'y':
        test_shopper_search(ingredients)
    else:
        print("\nTest stopped. Run 'python test_run.py' again to continue.")
