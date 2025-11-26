"""
Helper script to clean up the chrome_user_data directory.
Run this if you're having issues with the browser session.
"""

import os
import shutil
import subprocess
import time

def cleanup_chrome_data():
    user_data_dir = os.path.join(os.getcwd(), 'chrome_user_data')
    
    print("Cleaning up chrome_user_data directory...")
    
    # Kill any chrome processes
    try:
        print("Killing Chrome processes...")
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                     capture_output=True, timeout=5)
        time.sleep(2)
    except Exception as e:
        print(f"Note: {e}")
    
    # Remove the directory
    if os.path.exists(user_data_dir):
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
            print(f"✓ Removed {user_data_dir}")
            print("\nYou'll need to log in again the next time you run the tool.")
        except Exception as e:
            print(f"✗ Error removing directory: {e}")
            print("You may need to manually delete the chrome_user_data folder.")
    else:
        print("chrome_user_data directory doesn't exist.")

if __name__ == "__main__":
    cleanup_chrome_data()
