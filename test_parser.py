import unittest
from unittest.mock import patch, MagicMock
from parser import parse_recipe, extract_ingredients_json_ld, extract_ingredients_html, fetch_recipe


class TestFetchRecipe(unittest.TestCase):
    """Test cases for URL fetching."""
    
    @patch('parser.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful URL fetch."""
        mock_response = MagicMock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = fetch_recipe("https://example.com/recipe")
        self.assertEqual(result, "<html>Test content</html>")
    
    @patch('parser.requests.get')
    def test_fetch_failure(self, mock_get):
        """Test fetch failure handling."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        result = fetch_recipe("https://example.com/recipe")
        self.assertIsNone(result)


class TestExtractIngredientsJsonLD(unittest.TestCase):
    """Test cases for JSON-LD extraction."""
    
    def test_simple_recipe_schema(self):
        """Test extraction from simple Recipe schema."""
        html = '''
        <html>
        <script type="application/ld+json">
        {
            "@type": "Recipe",
            "name": "Test Recipe",
            "recipeIngredient": ["2 cups flour", "1 cup sugar", "3 eggs"]
        }
        </script>
        </html>
        '''
        
        ingredients = extract_ingredients_json_ld(html, "https://example.com")
        self.assertEqual(len(ingredients), 3)
        self.assertIn("2 cups flour", ingredients)
        self.assertIn("1 cup sugar", ingredients)
        self.assertIn("3 eggs", ingredients)
    
    def test_recipe_in_graph(self):
        """Test extraction from @graph structure."""
        html = '''
        <html>
        <script type="application/ld+json">
        {
            "@graph": [
                {
                    "@type": "WebPage",
                    "name": "Recipe Page"
                },
                {
                    "@type": "Recipe",
                    "name": "Test Recipe",
                    "recipeIngredient": ["1 lb chicken", "2 tbsp olive oil"]
                }
            ]
        }
        </script>
        </html>
        '''
        
        ingredients = extract_ingredients_json_ld(html, "https://example.com")
        self.assertEqual(len(ingredients), 2)
        self.assertIn("1 lb chicken", ingredients)
        self.assertIn("2 tbsp olive oil", ingredients)
    
    def test_no_recipe_schema(self):
        """Test when no Recipe schema is present."""
        html = '''
        <html>
        <script type="application/ld+json">
        {
            "@type": "WebPage",
            "name": "Not a recipe"
        }
        </script>
        </html>
        '''
        
        ingredients = extract_ingredients_json_ld(html, "https://example.com")
        self.assertEqual(len(ingredients), 0)
    
    def test_empty_ingredients(self):
        """Test Recipe schema with no ingredients."""
        html = '''
        <html>
        <script type="application/ld+json">
        {
            "@type": "Recipe",
            "name": "Test Recipe",
            "recipeIngredient": []
        }
        </script>
        </html>
        '''
        
        ingredients = extract_ingredients_json_ld(html, "https://example.com")
        self.assertEqual(len(ingredients), 0)


class TestExtractIngredientsHTML(unittest.TestCase):
    """Test cases for HTML fallback extraction."""
    
    def test_ul_with_ingredient_class(self):
        """Test extraction from <ul> with ingredient class."""
        html = '''
        <html>
        <body>
            <ul class="recipe-ingredients">
                <li>2 cups flour</li>
                <li>1 cup sugar</li>
                <li>3 eggs</li>
            </ul>
        </body>
        </html>
        '''
        
        ingredients = extract_ingredients_html(html)
        self.assertEqual(len(ingredients), 3)
        self.assertIn("2 cups flour", ingredients)
    
    def test_ol_with_ingredient_id(self):
        """Test extraction from <ol> with ingredient id."""
        html = '''
        <html>
        <body>
            <ol id="ingredients-list">
                <li>1 lb chicken breast</li>
                <li>2 tablespoons olive oil</li>
            </ol>
        </body>
        </html>
        '''
        
        ingredients = extract_ingredients_html(html)
        self.assertEqual(len(ingredients), 2)
        self.assertIn("1 lb chicken breast", ingredients)
    
    def test_div_with_ingredient_class(self):
        """Test extraction from div container."""
        html = '''
        <html>
        <body>
            <div class="ingredients-section">
                <ul>
                    <li>Salt and pepper</li>
                    <li>Fresh herbs</li>
                </ul>
            </div>
        </body>
        </html>
        '''
        
        ingredients = extract_ingredients_html(html)
        self.assertEqual(len(ingredients), 2)
        self.assertIn("Salt and pepper", ingredients)
    
    def test_no_ingredients_found(self):
        """Test when no ingredients can be found."""
        html = '''
        <html>
        <body>
            <p>This is just a paragraph with no ingredients.</p>
        </body>
        </html>
        '''
        
        ingredients = extract_ingredients_html(html)
        self.assertEqual(len(ingredients), 0)
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        html = '''
        <html>
        <body>
            <ul class="ingredients">
                <li>  2   cups   flour  </li>
                <li>
                    1 cup
                    sugar
                </li>
            </ul>
        </body>
        </html>
        '''
        
        ingredients = extract_ingredients_html(html)
        self.assertEqual(len(ingredients), 2)
        # Should have normalized whitespace
        self.assertIn("2 cups flour", ingredients)
        self.assertIn("1 cup sugar", ingredients)


class TestParseRecipe(unittest.TestCase):
    """Integration tests for parse_recipe."""
    
    @patch('parser.fetch_recipe')
    def test_json_ld_success(self, mock_fetch):
        """Test successful JSON-LD extraction."""
        mock_fetch.return_value = '''
        <html>
        <script type="application/ld+json">
        {
            "@type": "Recipe",
            "recipeIngredient": ["flour", "sugar"]
        }
        </script>
        </html>
        '''
        
        ingredients = parse_recipe("https://example.com/recipe")
        self.assertEqual(len(ingredients), 2)
        self.assertIn("flour", ingredients)
    
    @patch('parser.fetch_recipe')
    def test_html_fallback(self, mock_fetch):
        """Test HTML fallback when JSON-LD fails."""
        mock_fetch.return_value = '''
        <html>
        <body>
            <ul class="ingredients">
                <li>flour</li>
                <li>sugar</li>
            </ul>
        </body>
        </html>
        '''
        
        ingredients = parse_recipe("https://example.com/recipe")
        self.assertEqual(len(ingredients), 2)
        self.assertIn("flour", ingredients)
    
    @patch('parser.fetch_recipe')
    def test_fetch_failure(self, mock_fetch):
        """Test when fetch fails."""
        mock_fetch.return_value = None
        
        ingredients = parse_recipe("https://example.com/recipe")
        self.assertEqual(len(ingredients), 0)


if __name__ == '__main__':
    unittest.main()
