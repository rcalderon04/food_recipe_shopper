import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_parse():
    print("Testing /api/parse...")
    url = "https://www.allrecipes.com/recipe/23600/worlds-best-lasagna/"
    try:
        response = requests.post(f"{BASE_URL}/api/parse", json={"url": url})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            ingredients = data.get('ingredients', [])
            print(f"Found {len(ingredients)} ingredients")
            return ingredients
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Exception: {e}")
        return []

def test_search(ingredient):
    print(f"\nTesting /api/search for '{ingredient}'...")
    try:
        response = requests.post(f"{BASE_URL}/api/search", json={
            "ingredient": ingredient,
            "storefront": "fresh",
            "headless": False
        })
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('error'):
                print(f"API Error: {data['error']}")
            else:
                options = data.get('options', [])
                print(f"Found {len(options)} options")
                for opt in options:
                    print(f"  - {opt['title']} (${opt['price']}) [{opt.get('department')}]")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    ingredients = test_parse()
    if ingredients:
        # Test search with the first ingredient
        test_search(ingredients[0])
