"""
Test script to verify department dropdown selection works correctly.
Run this with visible browser (headless=False) to see the dropdown interaction.
"""

from shopper import AmazonShopper
import time

def test_department_selection():
    print("="*60)
    print("Testing Department Dropdown Selection")
    print("="*60)
    
    # Create shopper with visible browser
    shopper = AmazonShopper(headless=False)
    
    try:
        shopper.start()
        
        # Login if needed
        if not shopper.login():
            print("Login failed or was cancelled")
            return
        
        print("\n" + "="*60)
        print("Test 1: Amazon Fresh Department")
        print("="*60)
        results = shopper.search_item("bananas", storefront='fresh')
        print(f"Found {len(results)} results for bananas in Amazon Fresh")
        time.sleep(3)
        
        print("\n" + "="*60)
        print("Test 2: Whole Foods Department")
        print("="*60)
        results = shopper.search_item("organic milk", storefront='wholefoods')
        print(f"Found {len(results)} results for organic milk in Whole Foods")
        time.sleep(3)
        
        print("\n" + "="*60)
        print("Test 3: All Departments (Amazon.com)")
        print("="*60)
        results = shopper.search_item("laptop", storefront='amazon')
        print(f"Found {len(results)} results for laptop in All Departments")
        time.sleep(3)
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)
        
    finally:
        shopper.close()

if __name__ == "__main__":
    test_department_selection()
