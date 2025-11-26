import requests
import extruct
from bs4 import BeautifulSoup
from w3lib.html import get_base_url
import json

def fetch_recipe(url):
    """Fetches the URL and returns the HTML content."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

def extract_ingredients_json_ld(html, url):
    """Extracts ingredients from Schema.org JSON-LD."""
    base_url = get_base_url(html, url)
    try:
        data = extruct.extract(html, base_url=base_url, syntaxes=['json-ld'])
    except Exception as e:
        print(f"Error in extruct: {e}")
        return []
    
    ingredients = []
    
    json_ld_data = data.get('json-ld', [])
    # print(f"DEBUG: Found {len(json_ld_data)} JSON-LD items") # Uncomment for deep debugging
    
    for item in json_ld_data:
        # Check for direct Recipe type
        if item.get('@type') == 'Recipe':
            ingredients = item.get('recipeIngredient', [])
            if ingredients:
                return ingredients
        
        # Check for graph
        if '@graph' in item:
            for node in item['@graph']:
                if node.get('@type') == 'Recipe':
                    ingredients = node.get('recipeIngredient', [])
                    if ingredients:
                        return ingredients
                        
    return ingredients

def extract_ingredients_html(html):
    """Fallback extraction from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    ingredients = []
    
    # Common patterns for ingredients
    # 1. Lists with class containing 'ingredient'
    # 2. ul/ol inside a div with id/class containing 'ingredient'
    
    potential_lists = soup.find_all(['ul', 'ol'])
    for lst in potential_lists:
        classes = lst.get('class', [])
        id_attr = lst.get('id', '')
        
        if any('ingredient' in str(cls).lower() for cls in classes) or 'ingredient' in str(id_attr).lower():
            for li in lst.find_all('li'):
                # Use separator to avoid merging words
                text = li.get_text(separator=' ', strip=True)
                # Clean up multiple spaces
                text = ' '.join(text.split())
                ingredients.append(text)
            if ingredients:
                return ingredients

    # Try finding container divs
    potential_divs = soup.find_all('div')
    for div in potential_divs:
        classes = div.get('class', [])
        id_attr = div.get('id', '')
        
        if any('ingredient' in str(cls).lower() for cls in classes) or 'ingredient' in str(id_attr).lower():
             # Look for list items inside this div
            items = div.find_all('li')
            if items:
                for item in items:
                    text = item.get_text(separator=' ', strip=True)
                    text = ' '.join(text.split())
                    ingredients.append(text)
                if ingredients:
                    return ingredients
            
            # Sometimes ingredients are just paragraphs or spans in a container
            # This is riskier, might catch garbage
            
    return ingredients

def parse_recipe(url):
    """Main function to parse recipe from URL."""
    html = fetch_recipe(url)
    if not html:
        return []
    
    print("Attempting JSON-LD extraction...")
    ingredients = extract_ingredients_json_ld(html, url)
    
    if not ingredients:
        print("JSON-LD failed or not found. Attempting HTML fallback...")
        ingredients = extract_ingredients_html(html)
        
    return ingredients

if __name__ == "__main__":
    # Test with a sample URL
    test_url = input("Enter recipe URL: ")
    if test_url:
        results = parse_recipe(test_url)
        print("\nFound Ingredients:")
        for ing in results:
            print(f"- {ing}")
