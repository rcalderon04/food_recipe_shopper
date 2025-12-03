"""
Debug script to inspect search result DOM for department indicators.
Searches for 'sweet italian sausage' and prints details about the results.
"""

from shopper import AmazonShopper
import time
import json

def debug_department_detection():
    print("="*60)
    print("Debugging Department Detection")
    print("="*60)
    
    # Create shopper with visible browser
    shopper = AmazonShopper(headless=False)
    
    try:
        shopper.start()
        
        # Login if needed
        if not shopper.login():
            print("Login failed or was cancelled")
            return
        
        # Test 1: Search in All Departments (most challenging case)
        print("\n" + "="*60)
        print("Search Context: All Departments (Amazon.com)")
        print("="*60)
        
        # We want to see what a Fresh item looks like in the All Departments search
        # But first, let's try searching specifically for the item the user found
        query = "sweet italian sausage"
        
        # Manually navigate and search to ensure we get the page state
        shopper.page.goto("https://www.amazon.com")
        time.sleep(2)
        shopper.page.fill('#twotabsearchtextbox', query)
        shopper.page.click('#nav-search-submit-button')
        time.sleep(3)
        
        # Find the specific item "Amazon Grocery, Mild Italian Sausage"
        # We'll look for any item containing "Sausage" and print its details
        items = shopper.page.query_selector_all('[data-component-type="s-search-result"]')
        
        with open('debug_output.txt', 'w', encoding='utf-8') as f:
            f.write(f"Found {len(items)} items. Inspecting for Fresh indicators...\n")
            
            for i, item in enumerate(items[:5]):
                f.write(f"\n--- Item {i+1} ---\n")
                title_el = item.query_selector('h2')
                title = title_el.inner_text().strip() if title_el else "No Title"
                f.write(f"Title: {title}\n")
                
                # 1. Inner Text
                text = item.inner_text()
                f.write(f"Inner Text contains 'Fresh': {'fresh' in text.lower()}\n")
                f.write(f"Inner Text contains 'Whole Foods': {'whole foods' in text.lower()}\n")
                f.write(f"Inner Text contains 'Amazon Grocery': {'amazon grocery' in text.lower()}\n")
                f.write(f"Full Inner Text: {text[:200]}...\n") # Print start of text
                
                # 2. Image Alt Tags
                imgs = item.query_selector_all('img')
                for img in imgs:
                    alt = img.get_attribute('alt')
                    src = img.get_attribute('src')
                    if alt:
                        f.write(f"Image Alt: {alt}\n")
                    # Check src for fresh/wholefoods keywords
                    if 'fresh' in src.lower():
                         f.write(f"Image Src contains 'fresh': {src}\n")
                        
                # 3. Delivery Info
                delivery = item.query_selector('.a-size-small .a-color-base')
                if delivery:
                    f.write(f"Delivery Text: {delivery.inner_text()}\n")
                    
                # 4. Badges
                badges = item.query_selector_all('.a-badge-text')
                for badge in badges:
                    f.write(f"Badge Text: {badge.inner_text()}\n")

    finally:
        # Keep open briefly to see
        time.sleep(2)
        shopper.close()

if __name__ == "__main__":
    debug_department_detection()
