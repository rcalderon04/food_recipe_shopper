"""
Test script to verify persistent login.
Run this script to open the browser, log in to Amazon manually, and then close it.
Run it again to verify that you are still logged in.
"""

from shopper import AmazonShopper
import time

def test_persistent_login():
    print("Starting Amazon Shopper with persistent profile...")
    shopper = AmazonShopper(headless=False)
    
    try:
        shopper.start()
        shopper.login()
        
        print("\n" + "="*60)
        print("BROWSER IS OPEN")
        print("If you are not logged in, please log in manually now.")
        print("The session will be saved to the 'chrome_user_data' folder.")
        print("="*60 + "\n")
        
        # Keep the browser open for a while to allow manual login
        print("Waiting 60 seconds for you to interact...")
        time.sleep(60)
        
        print("Closing browser...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        shopper.close()

if __name__ == "__main__":
    test_persistent_login()
