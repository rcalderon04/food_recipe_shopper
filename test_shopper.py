from shopper import AmazonShopper
import time
import sys

def test_shopper_isolation():
    print("Starting Shopper Isolation Test...")
    shopper = None
    try:
        # Test 1: Launch and Login Check
        print("\n1. Launching Browser (Headless=False)...")
        shopper = AmazonShopper(headless=False)
        shopper.start()
        
        print("2. Checking Login Status...")
        is_logged_in = shopper.login()
        print(f"   Logged In: {is_logged_in}")
        
        # Test 2: Search for a simple item
        item = "organic bananas"
        print(f"\n3. Searching for '{item}'...")
        results = shopper.search_item(item, storefront='fresh')
        
        if results:
            print(f"   ✓ Found {len(results)} results")
            for r in results[:3]:
                print(f"     - {r['title']} (${r['price']})")
        else:
            print("   ✗ No results found")
            
        # Test 3: Search for a second item (to test session stability)
        item2 = "milk"
        print(f"\n4. Searching for '{item2}'...")
        results2 = shopper.search_item(item2, storefront='fresh')
        
        if results2:
            print(f"   ✓ Found {len(results2)} results")
        else:
            print("   ✗ No results found")

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if shopper:
            print("\nClosing shopper...")
            shopper.close()
        print("Test Complete.")

if __name__ == "__main__":
    test_shopper_isolation()
