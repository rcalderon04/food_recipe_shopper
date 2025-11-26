import unittest
from utils import clean_ingredient_name, parse_price


class TestCleanIngredientName(unittest.TestCase):
    """Test cases for ingredient name cleaning."""
    
    def test_simple_ingredient(self):
        """Test basic ingredient without measurements."""
        self.assertEqual(clean_ingredient_name("onions"), "onions")
        self.assertEqual(clean_ingredient_name("garlic"), "garlic")
    
    def test_with_quantity(self):
        """Test ingredients with quantities."""
        self.assertEqual(clean_ingredient_name("2 onions"), "onions")
        self.assertEqual(clean_ingredient_name("1 lb ground beef"), "beef")
        self.assertEqual(clean_ingredient_name("3 cups flour"), "flour")
    
    def test_with_measurements(self):
        """Test removal of measurement units."""
        self.assertEqual(clean_ingredient_name("2 cups chopped onions"), "onions")
        self.assertEqual(clean_ingredient_name("1 tablespoon olive oil"), "olive oil")
        self.assertEqual(clean_ingredient_name("3 lbs chicken breast"), "chicken breast")
    
    def test_with_prep_words(self):
        """Test removal of preparation words."""
        self.assertEqual(clean_ingredient_name("1 cup diced tomatoes"), "tomatoes")
        self.assertEqual(clean_ingredient_name("2 cloves minced garlic"), "garlic")
        self.assertEqual(clean_ingredient_name("fresh basil leaves"), "basil leaves")
    
    def test_with_fractions(self):
        """Test removal of fractions."""
        self.assertEqual(clean_ingredient_name("1/2 cup sugar"), "sugar")
        self.assertEqual(clean_ingredient_name("1.5 lbs potatoes"), "potatoes")
        self.assertEqual(clean_ingredient_name("½ teaspoon salt"), "salt")
    
    def test_with_parentheses(self):
        """Test removal of parenthetical notes."""
        self.assertEqual(clean_ingredient_name("1 cup flour (all-purpose)"), "flour")
        self.assertEqual(clean_ingredient_name("2 eggs (beaten)"), "eggs")
    
    def test_complex_ingredient(self):
        """Test complex ingredient strings."""
        self.assertEqual(
            clean_ingredient_name("2 lbs fresh ground beef (80/20)"),
            "beef"
        )
        self.assertEqual(
            clean_ingredient_name("3 tablespoons finely chopped fresh parsley"),
            "parsley"
        )
        self.assertEqual(
            clean_ingredient_name("1 can (14 oz) diced tomatoes"),
            "tomatoes"
        )
    
    def test_multi_word_ingredients(self):
        """Test ingredients with multiple words that should be kept."""
        self.assertEqual(clean_ingredient_name("2 cups olive oil"), "olive oil")
        self.assertEqual(clean_ingredient_name("1 lb ground turkey"), "turkey")
        self.assertEqual(clean_ingredient_name("3 sweet potatoes"), "sweet potatoes")
    
    def test_empty_or_none(self):
        """Test edge cases."""
        self.assertEqual(clean_ingredient_name(""), "")
        self.assertEqual(clean_ingredient_name(None), "")


class TestParsePrice(unittest.TestCase):
    """Test cases for price parsing."""
    
    def test_simple_price(self):
        """Test basic price strings."""
        self.assertEqual(parse_price("1.99"), 1.99)
        self.assertEqual(parse_price("10.50"), 10.50)
        self.assertEqual(parse_price("0.99"), 0.99)
    
    def test_with_dollar_sign(self):
        """Test prices with dollar signs."""
        self.assertEqual(parse_price("$1.99"), 1.99)
        self.assertEqual(parse_price("$10.50"), 10.50)
    
    def test_with_commas(self):
        """Test prices with comma separators."""
        self.assertEqual(parse_price("$1,234.56"), 1234.56)
        self.assertEqual(parse_price("1,000.00"), 1000.00)
    
    def test_invalid_prices(self):
        """Test invalid price strings."""
        self.assertIsNone(parse_price("N/A"))
        self.assertIsNone(parse_price(""))
        self.assertIsNone(parse_price(None))
        self.assertIsNone(parse_price("invalid"))
    
    def test_whole_numbers(self):
        """Test whole number prices."""
        self.assertEqual(parse_price("5"), 5.0)
        self.assertEqual(parse_price("$10"), 10.0)


if __name__ == '__main__':
    unittest.main()
