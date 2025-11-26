import unittest
from unittest.mock import MagicMock, patch, mock_open
from shopper import AmazonShopper
import json


class TestAmazonShopperInit(unittest.TestCase):
    """Test cases for AmazonShopper initialization."""
    
    def test_init_default_params(self):
        """Test initialization with default parameters."""
        shopper = AmazonShopper()
        self.assertFalse(shopper.headless)
        self.assertEqual(shopper.cookies_file, 'amazon_cookies.json')
        self.assertIsNone(shopper.playwright)
        self.assertIsNone(shopper.browser)
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        shopper = AmazonShopper(headless=True, cookies_file='custom.json')
        self.assertTrue(shopper.headless)
        self.assertEqual(shopper.cookies_file, 'custom.json')


class TestCookieManagement(unittest.TestCase):
    """Test cases for cookie save/load functionality."""
    
    @patch('shopper.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='[{"name": "test", "value": "cookie"}]')
    def test_load_cookies_success(self, mock_file, mock_exists):
        """Test successful cookie loading."""
        mock_exists.return_value = True
        
        shopper = AmazonShopper()
        shopper.playwright = MagicMock()
        shopper.browser = MagicMock()
        shopper.context = MagicMock()
        shopper.page = MagicMock()
        
        # Simulate start() loading cookies
        with patch.object(shopper.context, 'add_cookies') as mock_add_cookies:
            if mock_exists.return_value:
                with open(shopper.cookies_file, 'r') as f:
                    cookies = json.load(f)
                    shopper.context.add_cookies(cookies)
        
        mock_add_cookies.assert_called_once()
    
    @patch('shopper.os.path.exists')
    def test_no_cookies_file(self, mock_exists):
        """Test when no cookies file exists."""
        mock_exists.return_value = False
        shopper = AmazonShopper()
        # Should not raise an error
        self.assertEqual(shopper.cookies_file, 'amazon_cookies.json')
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_cookies(self, mock_file):
        """Test cookie saving."""
        shopper = AmazonShopper()
        shopper.context = MagicMock()
        shopper.context.cookies.return_value = [{"name": "test", "value": "cookie"}]
        
        shopper._save_cookies()
        
        mock_file.assert_called_once_with('amazon_cookies.json', 'w')


class TestSearchItem(unittest.TestCase):
    """Test cases for search functionality."""
    
    def test_search_result_parsing(self):
        """Test parsing of search results."""
        shopper = AmazonShopper()
        shopper.page = MagicMock()
        
        # Mock search results
        mock_item = MagicMock()
        mock_item.get_attribute.return_value = 'B07ZLF9G83'
        
        mock_title = MagicMock()
        mock_title.inner_text.return_value = 'Organic Bananas'
        
        mock_price_whole = MagicMock()
        mock_price_whole.inner_text.return_value = '1'
        
        mock_price_fraction = MagicMock()
        mock_price_fraction.inner_text.return_value = '99'
        
        mock_item.query_selector.side_effect = lambda sel: {
            'h2 a span': mock_title,
            '.a-price-whole': mock_price_whole,
            '.a-price-fraction': mock_price_fraction
        }.get(sel)
        
        shopper.page.query_selector_all.return_value = [mock_item]
        shopper.page.wait_for_selector = MagicMock()
        shopper.page.fill = MagicMock()
        shopper.page.click = MagicMock()
        shopper.page.wait_for_load_state = MagicMock()
        
        results = shopper.search_item("bananas")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Organic Bananas')
        self.assertEqual(results[0]['price'], '1.99')
        self.assertEqual(results[0]['asin'], 'B07ZLF9G83')


class TestOutOfStockDetection(unittest.TestCase):
    """Test cases for out-of-stock detection."""
    
    def test_is_out_of_stock_true(self):
        """Test detection of out-of-stock items."""
        shopper = AmazonShopper()
        shopper.page = MagicMock()
        
        mock_element = MagicMock()
        mock_element.inner_text.return_value = "Currently unavailable"
        shopper.page.query_selector.return_value = mock_element
        
        result = shopper._is_out_of_stock()
        self.assertTrue(result)
    
    def test_is_out_of_stock_false(self):
        """Test when item is in stock."""
        shopper = AmazonShopper()
        shopper.page = MagicMock()
        
        mock_element = MagicMock()
        mock_element.inner_text.return_value = "In Stock"
        shopper.page.query_selector.return_value = mock_element
        
        result = shopper._is_out_of_stock()
        self.assertFalse(result)
    
    def test_is_out_of_stock_no_element(self):
        """Test when availability element not found."""
        shopper = AmazonShopper()
        shopper.page = MagicMock()
        shopper.page.query_selector.return_value = None
        
        result = shopper._is_out_of_stock()
        self.assertFalse(result)


class TestFindAddToCartButton(unittest.TestCase):
    """Test cases for add to cart button detection."""
    
    def test_find_button_by_id(self):
        """Test finding button by ID selector."""
        shopper = AmazonShopper()
        shopper.page = MagicMock()
        
        mock_button = MagicMock()
        mock_button.is_visible.return_value = True
        shopper.page.wait_for_selector.return_value = mock_button
        
        result = shopper._find_add_to_cart_button()
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_button)
    
    def test_find_button_by_text(self):
        """Test finding button by text content."""
        shopper = AmazonShopper()
        shopper.page = MagicMock()
        
        # First strategy fails
        shopper.page.wait_for_selector.side_effect = Exception("Not found")
        
        # Second strategy succeeds
        mock_button = MagicMock()
        mock_button.inner_text.return_value = "Add to Cart"
        mock_button.get_attribute.return_value = None
        mock_button.is_visible.return_value = True
        
        shopper.page.query_selector_all.return_value = [mock_button]
        
        result = shopper._find_add_to_cart_button()
        self.assertIsNotNone(result)
    
    def test_button_not_found(self):
        """Test when button cannot be found."""
        shopper = AmazonShopper()
        shopper.page = MagicMock()
        
        shopper.page.wait_for_selector.side_effect = Exception("Not found")
        shopper.page.query_selector_all.return_value = []
        
        result = shopper._find_add_to_cart_button()
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
