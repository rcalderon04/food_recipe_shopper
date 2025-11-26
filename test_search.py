# Test script for AmazonShopper search_item with anti-bot improvements

from shopper import AmazonShopper
import time

if __name__ == "__main__":
    shopper = AmazonShopper(headless=True)
    try:
        shopper.start()
        shopper.login()
        query = "organic bananas"
        results = shopper.search_item(query)
        print("\nSearch results for:", query)
        for i, res in enumerate(results[:5], 1):
            print(f"{i}. {res['title']} - ${res['price']}")
        # Keep browser open briefly to observe (if needed)
        time.sleep(5)
    finally:
        shopper.close()
