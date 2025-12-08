from backend_api.quantity_parser import clean_ingredient_name

test_cases = [
    "4 tablespoons chopped fresh parsley, divided",
    "1 ½ teaspoons dried basil leaves",
    "1 ½ teaspoons salt, divided, or to taste",
    "2 cups chopped onion",
    "1/2 cup fresh cilantro leaves"
]

print("Testing clean_ingredient_name failures:")
for t in test_cases:
    print(f"Input: '{t}'")
    print(f"Output: '{clean_ingredient_name(t)}'")
    print("-" * 20)
