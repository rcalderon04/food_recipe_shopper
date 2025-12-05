from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import traceback
import threading
import re
import math
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recipe_parser import RecipeParser
from shopper import AmazonShopper
from matcher import rank_products_by_confidence
from search_query import create_search_query
from quantity_parser import parse_quantity

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Global shopper instance
shopper = None
shopper_lock = threading.Lock()

def get_shopper(headless_request=True):
    global shopper
    with shopper_lock:
        # If headless request but not started, start it
        if shopper is None:
            print(f"Initializing shopper (headless={headless_request})...")
            shopper = AmazonShopper(headless=headless_request)
            shopper.start()
            
            # Check login status immediately
            if not shopper.check_is_logged_in():
                print("Shopper not logged in. Switching to headful mode for login...")
                shopper.stop()
                time.sleep(2) # Wait for cleanup
                shopper = AmazonShopper(headless=False)
                shopper.start()
                
                if not shopper.login():
                    print("Login failed or cancelled.")
                    shopper.stop()
                    shopper = None
                    return None
                    
                print("Login successful. Continuing session.")
                
        # Check if we need to switch modes (e.g. was headless, now need headful for debugging/login)
        elif shopper.headless != headless_request:
            print(f"Switching shopper mode (Current: {shopper.headless}, Requested: {headless_request})")
            shopper.stop()
            time.sleep(2) # Wait for cleanup
            shopper = AmazonShopper(headless=headless_request)
            shopper.start()
            
            # Check login after restart
            if not shopper.check_is_logged_in(): 
                 pass

        return shopper

def calculate_quantity_needed(needed_amount, needed_unit, product_title, container_count=None):
    """
    Calculates how many of a product are needed to meet the recipe requirement.
    Conservative approach: defaults to 1 for most items.
    Only calculates multiples for packaged goods where it's clearly needed.
    
    Args:
        needed_amount: Amount needed from recipe (e.g., 6 from "6 ounce")
        needed_unit: Unit from recipe (e.g., "ounce")
        product_title: Product title to extract size from
        container_count: Number of containers from recipe (e.g., 2 from "2 (6 ounce) cans")
    """
    if not needed_amount or not needed_unit:
        return 1
    
    # For very small amounts (spices, herbs), always return 1
    # These are typically bought in containers that last many recipes
    if needed_unit.lower() in ['tsp', 'teaspoon', 'teaspoons', 'tbsp', 'tablespoon', 'tablespoons']:
        return 1
    
    # For liquids in small amounts (cups, etc), default to 1
    # Most products are larger than recipe needs
    if needed_unit.lower() in ['cup', 'cups', 'ml', 'milliliter', 'milliliters']:
        return 1
    
    # Extract size from product title
    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(-)?\s*(oz|ounce|lb|pound|kg|g|gram)', product_title, re.IGNORECASE)
    
    if not size_match:
        # If we have a container count but can't parse product size, use container count
        return container_count if container_count else 1
    
    prod_amount = float(size_match.group(1))
    prod_unit = size_match.group(3).lower()
    
    # Convert both to ounces for comparison
    prod_oz = 0
    if prod_unit in ['oz', 'ounce']:
        prod_oz = prod_amount
    elif prod_unit in ['lb', 'pound']:
        prod_oz = prod_amount * 16
    elif prod_unit in ['kg']:
        prod_oz = prod_amount * 35.274
    elif prod_unit in ['g', 'gram']:
        prod_oz = prod_amount * 0.035274
    
    needed_oz = 0
    needed_unit_lower = needed_unit.lower()
    if needed_unit_lower in ['oz', 'ounce']:
        needed_oz = needed_amount
    elif needed_unit_lower in ['lb', 'pound']:
        needed_oz = needed_amount * 16
    elif needed_unit_lower in ['kg']:
        needed_oz = needed_amount * 35.274
    elif needed_unit_lower in ['g', 'gram']:
        needed_oz = needed_amount * 0.035274
    
    # If we have container_count, calculate based on total needed weight
    if container_count and prod_oz > 0 and needed_oz > 0:
        total_needed_oz = needed_oz * container_count
        ratio = total_needed_oz / prod_oz
        # If product is close to the container size (within 20%), use container count
        if 0.8 <= ratio <= 1.2:
            return container_count
        # Otherwise calculate based on total weight
        return math.ceil(ratio)
    
    # No container count - calculate based on weight ratio
    if prod_oz > 0 and needed_oz > 0:
        ratio = needed_oz / prod_oz
        if ratio > 1.2:  # Need at least 20% more than one unit
            return math.ceil(ratio)
    
    return 1

@app.route('/api/parse', methods=['POST'])
def parse_recipe():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        parser = RecipeParser()
        recipe_data = parser.parse(url)
        
        if not recipe_data:
             return jsonify({'error': 'Failed to parse recipe'}), 400

        return jsonify(recipe_data)

    except Exception as e:
        print(f"Error parsing recipe: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_products():
    print("=== SEARCH REQUEST RECEIVED ===")
    data = request.json
    ingredient_text = data.get('ingredient', '')
    storefront = data.get('storefront', 'amazon')
    headless_req = data.get('headless', False) # Default to False (headful) if not specified, or match UI default
    print(f"Request data: ingredient='{ingredient_text}', storefront='{storefront}', headless={headless_req}")
    
    if not ingredient_text:
        return jsonify({'error': 'Ingredient is required'}), 400
    
    try:
        # 1. Clean the search query
        search_query = create_search_query(ingredient_text)
        print(f"Original: '{ingredient_text}' -> Query: '{search_query}'")
        
        # 2. Parse quantity info from original text
        qty_info = parse_quantity(ingredient_text)
        needed_amount = qty_info.get('amount')
        needed_unit = qty_info.get('unit')
        container_count = qty_info.get('count')  # e.g., 2 from "2 (6 oz) cans"
        
        print(f"Searching for: {search_query} in {storefront}")
        print(f"Quantity info: amount={needed_amount}, unit={needed_unit}, count={container_count}")
        
        # Search Amazon (with retry logic)
        max_retries = 2
        results = []
        
        for attempt in range(max_retries + 1):
            try:
                # Get shopper instance (inside loop to retry initialization if needed)
                s = get_shopper(headless_request=headless_req)
                if not s:
                     raise Exception("Failed to initialize shopper")

                results = s.search_item(search_query, storefront=storefront)
                break # Success
            except Exception as search_err:
                print(f"Search attempt {attempt+1} failed: {search_err}")
                if "TargetClosedError" in str(search_err) or "frame" in str(search_err) or "closed" in str(search_err) or attempt < max_retries:
                    print("Restarting shopper and retrying...")
                    time.sleep(1) # Wait for potential zombie cleanup
                    
                    # Force restart
                    with shopper_lock:
                        if shopper:
                            try:
                                shopper.stop()
                            except:
                                pass
                            shopper = None
                    
                    time.sleep(1) # Wait for pipes to close fully
                    
                    if attempt < max_retries:
                        continue
                    else:
                        raise search_err
                else:
                    raise search_err
        
        # Fallback logic
        if not results:
            print(f"No results in {storefront}, trying fallbacks...")
            fallbacks = ['fresh', 'wholefoods', 'amazon']
            if storefront in fallbacks:
                fallbacks.remove(storefront)
            
            for fb_store in fallbacks:
                print(f"Fallback: Searching in {fb_store}...")
                fb_results = s.search_item(search_query, storefront=fb_store)
                if fb_results:
                    print(f"Found {len(fb_results)} results in {fb_store}")
                    results = fb_results
                    break
        
        if not results:
            print(f"No results found for {search_query}")
            return jsonify({'options': [], 'query': search_query})
        
        # Rank results
        ranked = rank_products_by_confidence(search_query, results)
        top_options = ranked[:4]  # Return top 4
        
        # Format results
        formatted_options = []
        for opt in top_options:
            # Calculate recommended quantity
            rec_qty = calculate_quantity_needed(needed_amount, needed_unit, opt['title'], container_count)
            
            rec = {
                'title': opt['title'],
                'price': opt['price'],
                'asin': opt['asin'],
                'url': opt.get('url', f"https://www.amazon.com/dp/{opt['asin']}"),
                'confidence': opt.get('confidence', 0),
                'image': opt.get('image', ''),
                'department': opt.get('department', 'Amazon.com'),
                'quantity_recommendation': rec_qty
            }
            formatted_options.append(rec)
        
        print(f"Returning {len(formatted_options)} products")
        return jsonify({'options': formatted_options, 'query': search_query})
        
    except Exception as e:
        print(f"Error searching: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# For local testing
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True, port=5000, threaded=False, use_reloader=False)
    finally:
        if shopper:
            shopper.close()
