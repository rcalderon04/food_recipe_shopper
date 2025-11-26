from flask import Flask, render_template, request, jsonify
from shopper import AmazonShopper
from parser import parse_recipe
from search_query import create_search_query
from matcher import rank_products_by_confidence
from conversions import convert_recipe_to_purchase
import threading
import time

app = Flask(__name__)

# Global shopper instance
# We use a single instance because launch_persistent_context locks the user data directory
shopper = None
shopper_lock = threading.Lock()

def get_shopper():
    global shopper
    if shopper is None:
        print("\n" + "="*70)
        print("🌐 LAUNCHING BROWSER - Please check for a Chrome window!")
        print("="*70 + "\n")
        
        try:
            shopper = AmazonShopper(headless=False)
            shopper.start()
            print("\n" + "="*70)
            print("🔐 BROWSER OPENED - Checking login status...")
            print("If you see a login prompt, please log in to Amazon.")
            print("="*70 + "\n")
            shopper.login()
        except Exception as e:
            print(f"Error starting shopper: {e}")
            print("Attempting to clean up chrome_user_data and retry...")
            
            # Try to clean up and retry once
            import shutil
            import os
            user_data_dir = os.path.join(os.getcwd(), 'chrome_user_data')
            if os.path.exists(user_data_dir):
                try:
                    # Kill any chrome processes that might be holding locks
                    import subprocess
                    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                                 capture_output=True, timeout=5)
                    import time
                    time.sleep(2)
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                    print("Cleaned up chrome_user_data directory")
                except Exception as cleanup_error:
                    print(f"Cleanup failed: {cleanup_error}")
            
            # Retry
            try:
                shopper = AmazonShopper(headless=False)
                shopper.start()
                shopper.login()
            except Exception as retry_error:
                print(f"Retry failed: {retry_error}")
                raise
    return shopper

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/parse', methods=['POST'])
def parse_recipe_endpoint():
    print("\n>>> /api/parse endpoint called", flush=True)
    data = request.json
    print(f">>> Received URL: {data.get('url')}", flush=True)
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        print(f">>> Parsing recipe from: {url}", flush=True)
        ingredients = parse_recipe(url)
        print(f">>> Found {len(ingredients)} ingredients", flush=True)
        return jsonify({'ingredients': ingredients})
    except Exception as e:
        print(f">>> ERROR in parse: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_ingredient_endpoint():
    print("\n>>> /api/search endpoint called", flush=True)
    data = request.json
    ingredient_text = data.get('ingredient')
    storefront = data.get('storefront', 'fresh')  # Default to fresh
    print(f">>> Searching for: {ingredient_text} in {storefront}", flush=True)
    
    if not ingredient_text:
        return jsonify({'error': 'Ingredient text is required'}), 400
        
    try:
        print(f"\n=== Searching for ingredient: {ingredient_text} ===")
        
        # 1. Analyze quantity needs
        from quantity_parser import parse_quantity
        qty_info = parse_quantity(ingredient_text)
        print(f"  Quantity info: {qty_info}")
        
        purchase_info = convert_recipe_to_purchase(qty_info, ingredient_text)
        print(f"  Purchase info: {purchase_info}")
        
        # 2. Create search query
        query = create_search_query(ingredient_text)
        print(f"  Search query: {query}")
        
        # 3. Search on Amazon (thread-safe access)
        print(f"  Acquiring shopper lock...")
        with shopper_lock:
            print(f"  Getting shopper instance...")
            s = get_shopper()
            print(f"  Performing search...")
            results = s.search_item(query, storefront=storefront)
            print(f"  Got {len(results)} results")
            
        if not results:
            print(f"  WARNING: No results found for {query}")
            return jsonify({'error': f'No products found for "{query}"'}), 200
            
        # 4. Rank and format results
        print(f"  Ranking results...")
        ranked = rank_products_by_confidence(query, results)
        top_options = ranked[:3]
        print(f"  Top 3 options selected")
        
        # 5. Add recommendation info
        formatted_options = []
        for opt in top_options:
            rec = {
                'title': opt['title'],
                'price': opt['price'],
                'asin': opt['asin'],
                'confidence': opt.get('confidence', 0),
                'image': opt.get('image', ''),
                'quantity_recommendation': 1,
                'total_price': opt['price']
            }
            
            # Calculate quantity needed
            if purchase_info['needed_range']:
                import re
                # Extract size from title
                size_match = re.search(r'(\d+(?:\.\d+)?)\s*(lb|oz|ounce|pound)', opt['title'], re.IGNORECASE)
                if size_match:
                    size_val = float(size_match.group(1))
                    size_unit = size_match.group(2).lower()
                    
                    if size_unit in ['lb', 'pound']:
                        product_oz = size_val * 16
                    else:
                        product_oz = size_val
                        
                    needed_low, _ = purchase_info['needed_range']
                    if purchase_info['unit'] == 'lb':
                        needed_low *= 16
                    
                    # Simple calculation: ceil(needed / product_size)
                    import math
                    if product_oz > 0:
                        rec['quantity_recommendation'] = math.ceil(needed_low / product_oz)
            
            # Calculate total price
            try:
                unit_price = float(str(opt['price']).replace('$', '').replace(',', ''))
                rec['total_price'] = unit_price * rec['quantity_recommendation']
            except:
                rec['total_price'] = "N/A"
                
            formatted_options.append(rec)
        
        print(f"  Returning {len(formatted_options)} formatted options")
        print(f"=== Search complete for: {ingredient_text} ===\n")
            
        return jsonify({
            'query': query,
            'options': formatted_options,
            'purchase_info': purchase_info
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"ERROR searching for {ingredient_text}:")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/api/cart', methods=['POST'])
def add_to_cart_endpoint():
    data = request.json
    items = data.get('items', [])
    
    if not items:
        return jsonify({'error': 'No items provided'}), 400
    
    results = []
    
    # Process sequentially to avoid bot detection
    with shopper_lock:
        s = get_shopper()
        for item in items:
            try:
                success = s.add_to_cart(item, quantity=item.get('quantity', 1))
                results.append({
                    'asin': item['asin'],
                    'success': success,
                    'title': item.get('title', 'Unknown')
                })
                # Delay between adds
                time.sleep(2)
            except Exception as e:
                results.append({
                    'asin': item['asin'],
                    'success': False,
                    'error': str(e)
                })
                
    return jsonify({'results': results})

if __name__ == '__main__':
    # Don't initialize shopper at startup - do it lazily when first API call comes in
    # This avoids crashes if chrome_user_data is locked
    try:
        # Run single-threaded to play nice with Playwright
        app.run(debug=True, port=5000, threaded=False, use_reloader=False)
    finally:
        if shopper:
            shopper.close()
