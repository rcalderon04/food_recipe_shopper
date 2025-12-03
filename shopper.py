from playwright.sync_api import sync_playwright
import time
import random
import json
import os

class AmazonShopper:
    def __init__(self, headless=False, cookies_file='amazon_cookies.json'):
        self.headless = headless
        self.cookies_file = cookies_file
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """Starts the browser session with a persistent context."""
        self.playwright = sync_playwright().start()
        
        # Use a persistent user data directory to keep cookies/login state
        user_data_dir = os.path.join(os.getcwd(), 'chrome_user_data')
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
            
        print(f"Starting browser with persistent profile at: {user_data_dir}")
        
        # Launch persistent context
        # This acts like a real browser profile, saving cookies/local storage automatically
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=self.headless,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
            # Add arguments to help avoid detection
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars',
            ]
        )
        
        # Get the default page or create one
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
            
        # We don't need to manually load cookies anymore as the profile handles it,
        # but we'll keep the file attribute for backward compatibility if needed.
        
    def login(self, force_relogin=False):
        """Navigates to Amazon and waits for user login."""
        print("Navigating to Amazon Fresh...")
        # Direct link to Amazon Fresh or just Amazon
        self.page.goto("https://www.amazon.com/alm/storefront?almBrandId=QW1hem9uIEZyZXNo", timeout=30000)
        
        # Wait for page to load
        time.sleep(3)
        
        # Check if already logged in by looking for account element
        try:
            # Wait briefly to see if we're already logged in
            account_element = self.page.wait_for_selector('#nav-link-accountList', timeout=5000)
            if account_element and not force_relogin:
                # Double-check by looking for the account name/email
                try:
                    account_text = account_element.inner_text()
                    if account_text and 'Hello' in account_text:
                        print(f"Already logged in (session restored from cookies): {account_text}")
                        return True
                except:
                    pass
        except:
            pass
            
        # Check for error page
        if self._check_for_error_page():
             print("Warning: Amazon error page detected during login check.")
        
        # Not logged in or session expired
        print("\n" + "="*60)
        print("⚠️  NOT LOGGED IN TO AMAZON")
        print("Please log in to your Amazon account in the browser window.")
        print("The session will be saved for future use.")
        print("="*60 + "\n")
        
        # Wait for login - check periodically if user has logged in
        max_wait = 60  # 60 seconds
        check_interval = 2  # Check every 2 seconds
        
        for i in range(0, max_wait, check_interval):
            time.sleep(check_interval)
            try:
                account_element = self.page.wait_for_selector('#nav-link-accountList', timeout=1000)
                if account_element:
                    account_text = account_element.inner_text()
                    if account_text and 'Hello' in account_text:
                        print(f"✓ Login detected: {account_text}")
                        time.sleep(2)  # Give it a moment to fully load
                        return True
            except:
                continue
        
        print("⚠️  Login timeout - please ensure you're logged in before using the tool.")
        return False

    def search_item(self, query, storefront='fresh'):
        """
        Searches for an item on Amazon.
        
        Args:
            query (str): The search query
            storefront (str): 'fresh', 'wholefoods', or 'amazon'
        """
        print(f"Searching for: {query} in {storefront}")
        
        # Storefront URLs
        store_urls = {
            'fresh': "https://www.amazon.com/alm/storefront?almBrandId=QW1hem9uIEZyZXNo",
            'wholefoods': "https://www.amazon.com/alm/storefront?almBrandId=V2hvbGUgRm9vZHM=",
            'amazon': "https://www.amazon.com/"
        }
        
        target_url = store_urls.get(storefront, store_urls['fresh'])
        
        # Add random delay before search (human-like behavior but faster)
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)
        
        # Random mouse movement to mimic human behavior
        try:
            viewport = self.page.viewport_size
            if viewport:
                # Move mouse to random positions
                for _ in range(random.randint(2, 4)):
                    x = random.randint(100, viewport['width'] - 100)
                    y = random.randint(100, viewport['height'] - 100)
                    self.page.mouse.move(x, y, steps=random.randint(5, 15))
                    time.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass
        
        try:
            # Check if we need to switch storefronts
            # We check the URL or a specific element to see where we are
            current_url = self.page.url
            needs_switch = False
            
            if storefront == 'fresh' and 'almBrandId=QW1hem9uIEZyZXNo' not in current_url and 'amazonfresh' not in current_url:
                needs_switch = True
            elif storefront == 'wholefoods' and 'almBrandId=V2hvbGUgRm9vZHM=' not in current_url and 'wholefoods' not in current_url:
                needs_switch = True
            elif storefront == 'amazon' and ('almBrandId' in current_url or 'amazonfresh' in current_url):
                needs_switch = True
                
            # If we're on an error page, we definitely need to switch/reload
            if self._check_for_error_page():
                print("  ✗ Amazon error page detected. Reloading...")
                needs_switch = True
                
            if needs_switch:
                print(f"  Switching to {storefront} storefront...")
                try:
                    self.page.goto(target_url, timeout=15000)
                    time.sleep(2)
                except Exception as e:
                    print(f"  ✗ Navigation failed: {e}")
                    return []
            
            # Check for CAPTCHA
            if self._is_captcha_page():
                print("  ✗ CAPTCHA detected! Please solve it manually in the browser window.")
                # Wait a bit to give user a chance to see it, but don't hang forever
                time.sleep(5)
                return []
            
            # Scroll to top to ensure search bar is visible
            try:
                self.page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)
            except:
                pass
            
            # Select the appropriate department from the dropdown
            department_map = {
                'fresh': 'Amazon Fresh',
                'wholefoods': 'Whole Foods Market',
                'amazon': 'All Departments'
            }
            
            target_department = department_map.get(storefront, 'All Departments')
            print(f"  Selecting department: {target_department}")
            
            try:
                # Try to find and click the department dropdown
                dropdown_selectors = [
                    'select#searchDropdownBox',
                    '#searchDropdownBox',
                    'select[name="url"]',
                    '#nav-search-dropdown-card'
                ]
                
                dropdown = None
                for selector in dropdown_selectors:
                    try:
                        dropdown = self.page.wait_for_selector(selector, timeout=2000)
                        if dropdown:
                            break
                    except:
                        continue
                
                if dropdown:
                    # Get current selected value
                    try:
                        current_value = dropdown.evaluate('el => el.value')
                        print(f"  Current department: {current_value}")
                    except:
                        pass
                    
                    # Try to select by visible text first
                    try:
                        # Get all options and find the one matching our target department
                        options = self.page.query_selector_all(f'{dropdown_selectors[0] if dropdown else "select#searchDropdownBox"} option')
                        
                        for option in options:
                            option_text = option.inner_text().strip()
                            if target_department.lower() in option_text.lower():
                                option_value = option.get_attribute('value')
                                print(f"  Found matching option: {option_text} (value: {option_value})")
                                
                                # Select the option
                                dropdown.select_option(value=option_value)
                                print(f"  ✓ Selected department: {target_department}")
                                time.sleep(random.uniform(0.3, 0.6))
                                break
                    except Exception as e:
                        print(f"  ⚠ Could not select department by text: {e}")
                        # Fallback: try selecting by partial match or index
                        try:
                            if storefront == 'fresh':
                                # Try common Fresh department values
                                for val in ['search-alias=amazonfresh', 'search-alias=amazon-fresh', 'amazonfresh']:
                                    try:
                                        dropdown.select_option(value=val)
                                        print(f"  ✓ Selected Amazon Fresh (fallback)")
                                        break
                                    except:
                                        continue
                            elif storefront == 'wholefoods':
                                # Try common Whole Foods department values
                                for val in ['search-alias=wholefoods', 'search-alias=whole-foods', 'wholefoods']:
                                    try:
                                        dropdown.select_option(value=val)
                                        print(f"  ✓ Selected Whole Foods (fallback)")
                                        break
                                    except:
                                        continue
                        except Exception as e2:
                            print(f"  ⚠ Fallback selection also failed: {e2}")
                else:
                    print(f"  ⚠ Department dropdown not found, proceeding with default")
                    
            except Exception as e:
                print(f"  ⚠ Error selecting department: {e}")
                print(f"  Continuing with search anyway...")
            
            # Define selectors for search box and submit button
            search_selectors = [
                'input[id="twotabsearchtextbox"]',
                'input[name="field-keywords"]',
                'input[type="text"][placeholder*="Search"]',
                '#nav-search-bar-form input[type="text"]'
            ]
            button_selectors = [
                'input[id="nav-search-submit-button"]',
                'button[id="nav-search-submit-button"]',
                'input[type="submit"][value="Go"]',
                '#nav-search-bar-form input[type="submit"]',
                '#nav-search-bar-form button[type="submit"]'
            ]

            # Locate the search box
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.page.wait_for_selector(selector, timeout=3000)
                    if search_box:
                        # Human-like mouse movement to the box
                        try:
                            bbox = search_box.bounding_box()
                            if bbox:
                                x = bbox['x'] + bbox['width'] / 2
                                y = bbox['y'] + bbox['height'] / 2
                                self.page.mouse.move(x, y, steps=random.randint(5, 15))
                                self.page.mouse.click(x, y)
                        except Exception:
                            pass
                        break
                except Exception:
                    continue
            
            if not search_box:
                print("  ✗ Could not find search box")
                return []

            # Clear any existing text and type the query slowly
            search_box.click()
            self.page.keyboard.press('Control+A')
            time.sleep(0.1)
            # Type faster but still with some variance
            search_box.type(query, delay=random.uniform(10, 50))

            # Small pause before submitting
            time.sleep(random.uniform(0.2, 0.5))

            # Click the submit button with human-like mouse movement
            search_clicked = False
            for selector in button_selectors:
                try:
                    button = self.page.query_selector(selector)
                    if button:
                        try:
                            bbox = button.bounding_box()
                            if bbox:
                                x = bbox['x'] + bbox['width'] / 2
                                y = bbox['y'] + bbox['height'] / 2
                                self.page.mouse.move(x, y, steps=random.randint(5, 15))
                                self.page.mouse.click(x, y)
                        except Exception:
                            pass
                        self.page.keyboard.press('Enter')
                        search_clicked = True
                        print("  ✓ Submitted search")
                        break
                except Exception:
                    continue
            
            if not search_clicked:
                # Fallback to pressing Enter directly
                try:
                    self.page.keyboard.press('Enter')
                    search_clicked = True
                    print("  ✓ Submitted search via Enter key")
                except Exception:
                    print("  ✗ Could not submit search")
                    return []

            # Wait for navigation and dynamic content
            try:
                self.page.wait_for_load_state('domcontentloaded', timeout=20000)
            except Exception:
                print("  ⚠ Page load timeout, checking for errors...")
                if self._check_for_error_page():
                    print("  ✗ Amazon error page encountered")
                    return []
            
            time.sleep(random.uniform(1.0, 1.5))

            # Scroll to trigger lazy loading (faster)
            try:
                self.page.evaluate('window.scrollBy(0, Math.floor(Math.random()*200)+100)')
                time.sleep(random.uniform(0.5, 1.0))
            except Exception:
                pass
            
            for _ in range(random.randint(1, 2)):
                try:
                    self.page.evaluate('window.scrollBy(0, Math.floor(Math.random()*300)+200)')
                    time.sleep(random.uniform(0.2, 0.5))
                except Exception:
                    pass
            
            # Extract results with multiple selector strategies
            results = []
            
            # Try to find result items
            result_selectors = [
                'div.s-result-item[data-asin]',
                'div[data-component-type="s-search-result"]',
                'div.s-search-result',
                '[data-asin]:not([data-asin=""])'
            ]
            
            items = []
            for selector in result_selectors:
                try:
                    items = self.page.query_selector_all(selector)
                    if items:
                        print(f"  ✓ Found {len(items)} results with selector: {selector}")
                        break
                except:
                    continue
            
            if not items:
                print("  ✗ No result items found")
                return []
            
            for item in items[:10]:  # Check top 10 results
                try:
                    # Check if it's a real product (has ASIN)
                    asin = item.get_attribute('data-asin')
                    if not asin or len(asin) < 10:
                        continue

                    # Try multiple selectors for title
                    title = None
                    title_selectors = [
                        'h2 a span',
                        'h2 span',
                        '.s-title-instructions-style span',
                        'h2',
                        '[data-cy="title-recipe"]'
                    ]
                    
                    for title_sel in title_selectors:
                        try:
                            title_el = item.query_selector(title_sel)
                            if title_el:
                                title = title_el.inner_text().strip()
                                if title:
                                    break
                        except:
                            continue
                    
                    if not title:
                        continue
                    
                    # Extract product URL
                    product_url = ""
                    try:
                        # Try to find the link element (usually wraps the title)
                        link_selectors = [
                            'h2 a',
                            'a.a-link-normal.s-no-outline',
                            'a.a-link-normal[href*="/dp/"]',
                            f'a[href*="{asin}"]'
                        ]
                        
                        for link_sel in link_selectors:
                            try:
                                link_el = item.query_selector(link_sel)
                                if link_el:
                                    href = link_el.get_attribute('href')
                                    if href:
                                        # Make sure it's a full URL
                                        if href.startswith('http'):
                                            product_url = href
                                        elif href.startswith('/'):
                                            product_url = f"https://www.amazon.com{href}"
                                        else:
                                            product_url = f"https://www.amazon.com/{href}"
                                        break
                            except:
                                continue
                        
                        # Fallback: construct URL from ASIN if we couldn't find the link
                        if not product_url:
                            product_url = f"https://www.amazon.com/dp/{asin}"
                            
                    except Exception as e:
                        # Ultimate fallback
                        product_url = f"https://www.amazon.com/dp/{asin}"
                    
                    # Try to get price with multiple strategies
                    price = "N/A"
                    try:
                        # Strategy 1: Separate whole and fraction elements
                        price_whole_el = item.query_selector('.a-price-whole')
                        price_fraction_el = item.query_selector('.a-price-fraction')
                        
                        if price_whole_el and price_fraction_el:
                            whole = price_whole_el.inner_text().replace(',', '').replace('.', '').strip()
                            fraction = price_fraction_el.inner_text().strip()
                            price = f"{whole}.{fraction}"
                        elif price_whole_el:
                            # Sometimes the whole price includes the decimal
                            whole_text = price_whole_el.inner_text().replace(',', '').strip()
                            price = whole_text
                        
                        # Strategy 2: Try getting the full price element
                        if price == "N/A":
                            price_el = item.query_selector('.a-price .a-offscreen')
                            if price_el:
                                price_text = price_el.inner_text().strip()
                                # Remove currency symbol and clean
                                price = price_text.replace('$', '').replace(',', '').strip()
                        
                        # Strategy 3: Try span with price data
                        if price == "N/A":
                            price_span = item.query_selector('span[data-a-color="price"]')
                            if price_span:
                                price_text = price_span.inner_text().strip()
                                price = price_text.replace('$', '').replace(',', '').strip()
                                
                    except Exception as e:
                        pass
                    
                    # Extract image URL
                    image_url = ""
                    try:
                        img_el = item.query_selector('img.s-image')
                        if img_el:
                            image_url = img_el.get_attribute('src')
                    except:
                        pass
                    
                    # Extract department/storefront info
                    department = "Amazon.com" # Default
                    try:
                        # Check for Fresh/Whole Foods text in the item
                        # We look for specific indicators usually found in delivery/sold by text
                        item_text = item.inner_text().lower()
                        if "amazon fresh" in item_text:
                            department = "Amazon Fresh"
                        elif "whole foods" in item_text:
                            department = "Whole Foods"
                    except:
                        pass

                    results.append({
                        'title': title,
                        'price': price,
                        'asin': asin,
                        'url': product_url,
                        'image': image_url,
                        'department': department,
                        'element': item
                    })
                    
                    # Stop after finding 5 valid results
                    if len(results) >= 5:
                        break
                        
                except Exception as e:
                    continue
            
            print(f"  ✓ Extracted {len(results)} valid products")
            return results
            
        except Exception as e:
            print(f"  ✗ Error searching for {query}: {e}")
            return []

    def _is_captcha_page(self):
        """Checks if the current page is a CAPTCHA page."""
        try:
            # Check for common CAPTCHA text or elements
            if "Type the characters you see in this image" in self.page.content():
                return True
            if self.page.query_selector("input#captchacharacters"):
                return True
            return False
        except:
            return False

    def _check_for_error_page(self):
        """Checks if current page is an Amazon error page."""
        try:
            # Common error page indicators
            error_indicators = [
                'Sorry! Something went wrong',
                'To discuss automated access to Amazon data',
                'Robot Check',
                'Enter the characters you see below',
                'Type the characters you see in this image',
            ]
            
            page_text = self.page.content()
            for indicator in error_indicators:
                if indicator in page_text:
                    return True
            
            return False
        except:
            return False

    def add_to_cart(self, item, quantity=1):
        """Adds the given item to the cart, optionally multiple times."""
        print(f"Adding '{item['title']}' to cart (Quantity: {quantity})...")
        try:
            # Use the product URL if provided, otherwise construct from ASIN
            if 'url' in item and item['url']:
                product_url = item['url']
                print(f"  Using provided URL: {product_url}")
            else:
                # Fallback: Construct URL from ASIN
                product_url = f"https://www.amazon.com/dp/{item['asin']}?almBrandId=QW1hem9uIEZyZXNo"
                print(f"  Constructed URL from ASIN: {product_url}")
            
            self.page.goto(product_url, timeout=15000)
            
            # Check if item is out of stock
            if self._is_out_of_stock():
                print("⚠️  Item is out of stock or unavailable.")
                return False
            
            # Wait for Add to Cart button with multiple strategies
            button = self._find_add_to_cart_button()
            
            if button:
                # Click the button 'quantity' times
                # Note: This is a simple approach. Some pages might require waiting for the cart to update.
                # Amazon Fresh often changes the button to "1 in cart" after the first click.
                # However, clicking the "+" button is harder to locate reliably.
                # Often, clicking the main "Add to Cart" button again (if it reverts or stays) works,
                # or finding the specific incrementer.
                
                # For now, we'll try to click the initial button once.
                # If quantity > 1, we'll try to find the increment button or just click again if possible.
                
                button.click()
                print("✓ Clicked 'Add to Cart'.")
                time.sleep(2) # Wait for action
                
                if quantity > 1:
                    # Try to find the plus button to increment
                    # Selectors for the plus button in the cart widget or on page
                    plus_selectors = [
                        'button[name="submit.addToCart"]', # Sometimes it stays as add to cart
                        '#freshAddToCartButton',
                        '.a-button-input[value="+"]',
                        'button[aria-label="Increase quantity"]',
                        'button[data-action="increment-item-quantity"]'
                    ]
                    
                    for _ in range(quantity - 1):
                        clicked_plus = False
                        for selector in plus_selectors:
                            try:
                                plus_btn = self.page.query_selector(selector)
                                if plus_btn and plus_btn.is_visible():
                                    plus_btn.click()
                                    clicked_plus = True
                                    print("  + Incremented quantity")
                                    time.sleep(1)
                                    break
                            except:
                                continue
                        
                        if not clicked_plus:
                            print(f"  ⚠ Could not find button to increment quantity to {quantity}. Added 1.")
                            break
                
                return True
            else:
                print("❌ Could not find 'Add to Cart' button.")
                return False
                
        except Exception as e:
            print(f"Error adding to cart: {e}")
            return False
    
    def _is_out_of_stock(self):
        """Checks if the current product page shows out of stock."""
        try:
            # Common out-of-stock indicators
            out_of_stock_selectors = [
                '#availability .a-color-price',  # "Currently unavailable"
                '#availability .a-color-state',   # "Out of Stock"
            ]
            
            for selector in out_of_stock_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        text = element.inner_text().lower()
                        if 'unavailable' in text or 'out of stock' in text:
                            return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def _find_add_to_cart_button(self):
        """Finds the Add to Cart button using multiple strategies."""
        # Strategy 1: Common ID/name selectors
        add_button_selectors = [
            'input[name="submit.addToCart"]',
            '#add-to-cart-button',
            '#freshAddToCartButton',
            'input[id="add-to-cart-button"]',
            'button[id="add-to-cart-button"]',
            '#buy-now-button',  # Sometimes this is present instead
        ]
        
        for selector in add_button_selectors:
            try:
                button = self.page.wait_for_selector(selector, timeout=2000)
                if button and button.is_visible():
                    return button
            except:
                continue
        
        # Strategy 2: Find by text content
        try:
            buttons = self.page.query_selector_all('button, input[type="submit"]')
            for button in buttons:
                try:
                    text = button.inner_text().lower()
                    value = button.get_attribute('value')
                    if value:
                        value = value.lower()
                    
                    if ('add to cart' in text or 
                        (value and 'add to cart' in value)):
                        if button.is_visible():
                            return button
                except:
                    continue
        except:
            pass
        
        return None
    
    def _save_cookies(self):
        """Saves the current browser cookies to file."""
        try:
            cookies = self.context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            print(f"Session saved to {self.cookies_file}")
        except Exception as e:
            print(f"Failed to save cookies: {e}")

    def close(self):
        """Closes the browser."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

if __name__ == "__main__":
    # Test the shopper
    shopper = AmazonShopper(headless=True) # Headless=True for automated testing
    try:
        shopper.start()
        shopper.login()
        results = shopper.search_item("organic bananas")
        print("\nSearch Results:")
        for res in results:
            print(f"- {res['title']} (${res['price']})")
            
        # Keep open for a bit to see
        time.sleep(10)
    finally:
        shopper.close()
