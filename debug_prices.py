"""
Debug script to check price extraction from Amazon Fresh search results.
"""

from shopper import AmazonShopper
from utils import parse_price
import time

def debug_price_extraction():
    print("=== Price Extraction Debug ===\n")
    
    shopper = AmazonShopper(headless=False)
    
    try:
        shopper.start()
        shopper.login()
        
        # Search for a simple item
        query = "eggs"
        print(f"Searching for: {query}\n")
        results = shopper.search_item(query)
        
        if results:
            print(f"Found {len(results)} results\n")
            
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                print(f"  Title: {result['title']}")
                print(f"  Price (raw): '{result['price']}'")
                print(f"  Price (parsed): {parse_price(result['price'])}")
                print(f"  ASIN: {result['asin']}")
                print()
                
            # Take a screenshot for debugging
            shopper.page.screenshot(path="debug_screenshot.png")
            print("Screenshot saved to debug_screenshot.png")
        else:
            print("No results found")
        
        time.sleep(5)
        
    finally:
        shopper.close()

if __name__ == "__main__":
    debug_price_extraction()
