import argparse
from parser import parse_recipe
from shopper import AmazonShopper
from utils import clean_ingredient_name, parse_price
from matcher import rank_products_by_confidence, format_confidence
from quantity_parser import parse_quantity
from conversions import convert_recipe_to_purchase, get_size_match_indicator
from search_query import create_search_query
import sys

def main():
    print("=== Recipe to Amazon Fresh Shopping List Tool ===")
    
    # Get Recipe URL
    url = input("Enter Recipe URL: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return

    # Parse Ingredients
    print(f"\nParsing recipe from: {url}")
    ingredients = parse_recipe(url)
    
    if not ingredients:
        print("No ingredients found. Exiting.")
        return
        
    print(f"\nFound {len(ingredients)} ingredients:")
    for i, ing in enumerate(ingredients, 1):
        print(f"{i}. {ing}")
        
    confirm = input("\nProceed to search on Amazon Fresh? (y/n): ").lower()
    if confirm != 'y':
        print("Exiting.")
        return

    # Start Shopper
    headless_input = input("Run in headless mode? (y/n) [default: n]: ").lower()
    headless = headless_input == 'y'
    
    print("\nStarting Amazon Shopper...")
    shopper = AmazonShopper(headless=headless)
    
    try:
        shopper.start()
        shopper.login()
        
        cart_count = 0
        
        for ingredient in ingredients:
            print(f"\nProcessing: {ingredient}")
            
            # Parse quantity from original ingredient
            qty_info = parse_quantity(ingredient)
            
            # Create optimized search query (preserves container types, sizes, etc.)
            search_query = create_search_query(ingredient)
            
            # Convert to purchase quantity
            purchase_info = convert_recipe_to_purchase(qty_info, search_query)
            
            # Display quantity info if available
            if purchase_info['note']:
                print(f"  Recipe needs: {purchase_info['note']}")
            
            print(f"  Searching for: {search_query}")
            
            results = shopper.search_item(search_query)
            
            if not results:
                print(f"No results found for '{search_query}'")
                continue
                
            # Selection Logic: Show top 3 options with confidence scores
            # Parse prices and filter out invalid ones
            for r in results:
                r['price_float'] = parse_price(r['price'])
            
            valid_results = [r for r in results if r['price_float'] is not None]
            
            if not valid_results:
                print("No items with price found.")
                continue
            
            # Rank by confidence (uses fuzzy matching)
            ranked_results = rank_products_by_confidence(search_query, valid_results)
            
            # Show top 3 options with confidence scores and size info
            top_options = ranked_results[:3]
            print("\n  Top options (sorted by match confidence):")
            for idx, option in enumerate(top_options, 1):
                confidence_str = format_confidence(option.get('confidence', 0))
                
                # Add size indicator if we have quantity info
                size_indicator = ""
                needed_quantity = 1
                
                if purchase_info['needed_range']:
                    # Try to extract product size from title (simple approach)
                    # Look for patterns like "1 lb", "16 oz", etc.
                    import re
                    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(lb|oz|ounce|pound)', option['title'], re.IGNORECASE)
                    if size_match:
                        size_val = float(size_match.group(1))
                        size_unit = size_match.group(2).lower()
                        
                        # Convert to ounces for comparison
                        if size_unit in ['lb', 'pound']:
                            product_oz = size_val * 16
                        else:
                            product_oz = size_val
                        
                        # Get needed range in ounces
                        needed_low, needed_high = purchase_info['needed_range']
                        if purchase_info['unit'] == 'lb':
                            needed_low *= 16
                            needed_high *= 16
                        
                        indicator_text = get_size_match_indicator(product_oz, (needed_low, needed_high))
                        size_indicator = " " + indicator_text
                        
                        # Calculate needed quantity if "May need X" is in indicator
                        if "May need" in indicator_text:
                            try:
                                needed_quantity = int(re.search(r'May need (\d+)', indicator_text).group(1))
                            except:
                                needed_quantity = 1
                
                # Format price display
                price_str = f"${option['price']:>6}"
                if needed_quantity > 1:
                    try:
                        unit_price = float(option['price'])
                        total_price = unit_price * needed_quantity
                        price_str = f"${unit_price} ea (Total: ${total_price:.2f})"
                    except:
                        pass
                
                print(f"  [{idx}] {confidence_str} | {price_str} - {option['title'][:55]}{size_indicator}")
                
            # Get user selection
            selection = input(f"\n  Select option (1-{len(top_options)}), or 's' to skip: ").lower()
            
            if selection == 's':
                print("  Skipped.")
                continue
                
            try:
                choice_idx = int(selection) - 1
                if 0 <= choice_idx < len(top_options):
                    selected_item = top_options[choice_idx]
                    
                    # Re-calculate needed quantity for the selected item
                    qty_to_add = 1
                    if purchase_info['needed_range']:
                        import re
                        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(lb|oz|ounce|pound)', selected_item['title'], re.IGNORECASE)
                        if size_match:
                            size_val = float(size_match.group(1))
                            size_unit = size_match.group(2).lower()
                            if size_unit in ['lb', 'pound']:
                                product_oz = size_val * 16
                            else:
                                product_oz = size_val
                            
                            needed_low, needed_high = purchase_info['needed_range']
                            if purchase_info['unit'] == 'lb':
                                needed_low *= 16
                                needed_high *= 16
                            
                            indicator = get_size_match_indicator(product_oz, (needed_low, needed_high))
                            if "May need" in indicator:
                                try:
                                    qty_to_add = int(re.search(r'May need (\d+)', indicator).group(1))
                                except:
                                    pass
                    
                    print(f"  Adding: {selected_item['title'][:60]} (Qty: {qty_to_add})...")
                    
                    success = shopper.add_to_cart(selected_item, quantity=qty_to_add)
                    if success:
                        print("  ✓ Added to cart.")
                        cart_count += 1
                    else:
                        print("  ✗ Failed to add to cart.")
                else:
                    print("  Invalid selection. Skipped.")
            except ValueError:
                print("  Invalid input. Skipped.")
                
        print(f"\nFinished! Added {cart_count} items to cart.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        shopper.close()

if __name__ == "__main__":
    main()
