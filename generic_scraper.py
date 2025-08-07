import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import time
import subprocess
import webbrowser
import os
from fake_useragent import UserAgent
import random
import sys
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Any, Optional, Union


class GenericEcommerceScraper:
    def __init__(self, site_config: Dict, db_path: str = None):
        """Initialize the generic scraper with site-specific configuration"""
        self.config = site_config
        self.base_url = site_config['base_url']
        self.name = site_config['name']
        self.db_path = db_path or f"{urlparse(self.base_url).netloc.replace('.', '_')}.db"
        
        # Setup proxy list (you can move this to config too)
        self.proxy_list = [
            'http://51.210.216.54:80', 'http://51.89.140.240:80', 'http://41.204.63.118:80',
            'http://68.183.143.134:80', 'http://178.128.200.87:80', 'http://143.110.190.83:8080',
            'http://188.215.245.235:80', 'http://195.15.215.146:80', 'http://149.102.133.90:80',
            'http://82.65.126.192:88', 'http://88.153.98.211:80', 'http://192.99.144.208:10001',
            'http://118.69.111.51:8080', 'http://82.146.37.145:80', 'http://85.26.146.169:80',
            'http://50.206.25.109:80', 'http://107.1.93.212:80', 'http://50.168.210.236:80',
            'http://51.124.209.11:80', 'http://50.204.219.231:80', 'http://50.174.7.153:80',
            'http://50.221.230.186:80', 'http://50.171.32.226:80', 'http://68.185.57.66:80',
            'http://50.222.245.47:80', 'http://50.122.86.118:80', 'http://50.168.210.232:80',
            'http://50.221.74.130:80', 'http://213.157.6.50:80', 'http://50.168.72.112:80',
            'http://50.206.25.110:80', 'http://50.204.190.234:80', 'http://50.223.38.2:80',
            'http://50.174.41.66:80', 'http://50.204.219.227:80', 'http://107.1.93.223:80'
        ]
        
        self.session = requests.Session()
        self.total_record_count = 0
        self._setup_database()
    
    def _setup_database(self):
        """Initialize the database with required tables"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                          (id TEXT, name TEXT, url TEXT, price REAL, site TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
            product_id TEXT,
            price REAL,
            site TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS category_links (
            url TEXT PRIMARY KEY,
            site TEXT,
            discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS page_links (
            url TEXT PRIMARY KEY,
            category_url TEXT,
            site TEXT,
            discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        self.conn.execute('PRAGMA journal_mode=WAL;')
        self.conn.commit()
    
    def _get_request_headers(self) -> Dict[str, str]:
        """Generate appropriate request headers based on config"""
        ua = UserAgent()
        
        user_agent_type = self.config['request_config'].get('user_agent_type', 'chrome')
        if user_agent_type == 'chrome_modified':
            user_agent = ua.chrome.replace("Chrome", "Version")
        elif user_agent_type == 'safari':
            user_agent = ua.safari
        else:
            user_agent = ua.chrome
            
        return {'User-Agent': user_agent}
    
    def _get_proxies(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration if enabled"""
        if self.config['request_config'].get('use_proxy', False):
            return {'http': random.choice(self.proxy_list)}
        return None
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Make a request with proper error handling and configuration"""
        headers = self._get_request_headers()
        proxies = self._get_proxies()
        timeout = self.config['request_config'].get('timeout', 5)
        
        try:
            response = self.session.get(url, headers=headers, proxies=proxies, timeout=timeout)
            
            if response.status_code == 200:
                print(f"✓ Connected to {url}")
                return BeautifulSoup(response.text, 'html.parser')
            else:
                print(f"✗ Failed to connect to {url} - Status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Error connecting to {url}: {e}")
            return None
    
    def discover_category_links(self) -> List[str]:
        """Discover category links from the main site based on configuration"""
        discovery_config = self.config['category_discovery']
        method = discovery_config['method']
        
        if method == 'href_pattern':
            return self._discover_links_by_href_pattern(discovery_config)
        elif method == 'sitemap':
            return self._discover_links_from_sitemap(discovery_config)
        elif method == 'url_file':
            return self._discover_links_from_file(discovery_config)
        else:
            raise ValueError(f"Unknown category discovery method: {method}")
    
    def _discover_links_by_href_pattern(self, config: Dict) -> List[str]:
        """Discover links by scanning href attributes for patterns"""
        soup = self._make_request(self.base_url)
        if not soup:
            return []
        
        links = set()
        patterns = config['patterns']
        exclude_patterns = config.get('exclude_patterns', [])
        selector = config.get('selector', 'a[href]')
        
        for a_tag in soup.select(selector):
            href = a_tag.get('href')
            if not href:
                continue
                
            # Check if href matches all required patterns
            if all(pattern in href for pattern in patterns):
                # Check if href doesn't match any exclude patterns
                if not any(exclude in href for exclude in exclude_patterns):
                    full_url = urljoin(self.base_url, href)
                    links.add(full_url)
        
        return list(links)
    
    def _discover_links_from_sitemap(self, config: Dict) -> List[str]:
        """Discover links from sitemap.xml"""
        sitemap_url = urljoin(self.base_url, config['sitemap_url'])
        soup = self._make_request(sitemap_url)
        if not soup:
            return []
        
        links = []
        patterns = config.get('category_patterns', [])
        
        for loc in soup.find_all('loc'):
            url = loc.text
            if any(pattern in url for pattern in patterns):
                links.append(url)
        
        return links
    
    def _discover_links_from_file(self, config: Dict) -> List[str]:
        """Read category links from a file"""
        file_path = config['file_path']
        links = []
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):  # Skip empty lines and comments
                        links.append(url)
            
            print(f"📁 Loaded {len(links)} URLs from {file_path}")
            
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
        except Exception as e:
            print(f"❌ Error reading file {file_path}: {e}")
        
        return links
    
    def get_paginated_urls(self, category_url: str) -> List[str]:
        """Get all paginated URLs for a category"""
        pagination_config = self.config['pagination']
        method = pagination_config['method']
        
        if method == 'link_rel_next':
            return self._paginate_by_link_rel_next(category_url, pagination_config)
        elif method == 'next_button':
            return self._paginate_by_next_button(category_url, pagination_config)
        elif method == 'url_parameter':
            return self._paginate_by_url_parameter(category_url, pagination_config)
        elif method == 'none':
            # No pagination, just return the original URL
            return [category_url]
        else:
            # Default: no pagination, just return the original URL
            return [category_url]
    
    def _paginate_by_link_rel_next(self, start_url: str, config: Dict) -> List[str]:
        """Paginate using <link rel="next"> tags"""
        pages = []
        current_url = start_url
        
        while current_url:
            soup = self._make_request(current_url)
            if not soup:
                break
                
            pages.append(current_url)
            
            # Find next page link
            next_link = soup.find('link', rel='next')
            if next_link:
                next_href = next_link.get('href')
                if next_href:
                    if next_href.startswith('/'):
                        current_url = urljoin(self.base_url, next_href)
                    else:
                        current_url = next_href
                else:
                    break
            else:
                break
        
        return pages
    
    def _paginate_by_next_button(self, start_url: str, config: Dict) -> List[str]:
        """Paginate using next button/link"""
        pages = []
        current_url = start_url
        
        while current_url:
            soup = self._make_request(current_url)
            if not soup:
                break
                
            pages.append(current_url)
            
            # Find next button
            next_element = soup.select_one(config['next_selector'])
            if next_element:
                next_href = next_element.get(config['next_attribute'])
                if next_href:
                    current_url = urljoin(self.base_url, next_href)
                else:
                    break
            else:
                break
        
        return pages
    
    def _paginate_by_url_parameter(self, start_url: str, config: Dict) -> List[str]:
        """Paginate by incrementing URL parameter (basic implementation)"""
        # This would need more sophisticated logic for real implementation
        # For now, just return the original URL
        return [start_url]
    
    def extract_products_from_page(self, url: str) -> List[Dict[str, Any]]:
        """Extract product data from a single page"""
        soup = self._make_request(url)
        if not soup:
            return []
        
        extraction_config = self.config['data_extraction']
        method = extraction_config['method']
        
        if method == 'json_script_tag':
            return self._extract_from_json_script(soup, url, extraction_config)
        elif method == 'dom_scraping':
            return self._extract_from_dom(soup, url, extraction_config)
        elif method == 'json_ld':
            return self._extract_from_json_ld(soup, url, extraction_config)
        else:
            raise ValueError(f"Unknown extraction method: {method}")
    
    def _extract_from_json_script(self, soup: BeautifulSoup, url: str, config: Dict) -> List[Dict[str, Any]]:
        """Extract data from JSON in script tags (like Argos)"""
        file_contents = str(soup)
        data = None
        
        # Try different patterns
        for pattern in config['patterns']:
            try:
                start_marker = pattern['start']
                end_marker = pattern['end']
                
                if start_marker in file_contents and end_marker in file_contents:
                    start = file_contents.index(start_marker) + len(start_marker)
                    end = file_contents.index(end_marker)
                    extracted_text = file_contents[start:end]
                    data = json.loads(extracted_text)
                    print(f"✓ JSON extracted using pattern: {start_marker[:20]}...{end_marker[:20]}")
                    break
            except (ValueError, json.JSONDecodeError) as e:
                continue
        
        # If no data found, try fallback patterns
        if data is None and 'fallback_patterns' in config:
            print("🔄 Trying fallback extraction methods...")
            for fallback in config['fallback_patterns']:
                if fallback['method'] == 'json_application_script':
                    data = self._extract_from_application_json_script(soup, fallback)
                    if data:
                        # Use the fallback's product path and fields
                        return self._process_json_products(data, fallback)
        
        if data is None:
            print(f"✗ Could not extract JSON from {url}")
            return []
        
        return self._process_json_products(data, config)
    
    def _extract_from_application_json_script(self, soup: BeautifulSoup, fallback_config: Dict) -> Any:
        """Extract data from <script type="application/json"> tags"""
        scripts = soup.select(fallback_config['selector'])
        
        for script in scripts:
            content = script.string or script.get_text()
            if content:
                try:
                    data = json.loads(content)
                    print("✓ JSON extracted from application/json script")
                    return data
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _process_json_products(self, data: Any, config: Dict) -> List[Dict[str, Any]]:
        """Process JSON data to extract products"""
        # Navigate to products using the path
        products_data = data
        product_path = config['product_path']
        print(f"📊 Navigating JSON path: {product_path}")
        print(f"📊 Initial data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        for i, key in enumerate(product_path):
            if isinstance(products_data, dict) and key in products_data:
                products_data = products_data[key]
                if isinstance(products_data, dict):
                    print(f"📊 After {key}: dict with keys {list(products_data.keys())}")
                elif isinstance(products_data, list):
                    print(f"📊 After {key}: list with {len(products_data)} items")
                else:
                    print(f"📊 After {key}: {type(products_data)} = {products_data}")
            else:
                available_keys = list(products_data.keys()) if isinstance(products_data, dict) else "Not a dict"
                print(f"✗ Key '{key}' not found in step {i}. Available keys: {available_keys}")
                return []
        
        if not products_data:
            print(f"✗ No products found at path {product_path} (products_data is None or empty)")
            return []
        
        # Extract individual products
        products = []
        fields_config = config['fields']
        
        for product_data in products_data:
            try:
                product = {}
                
                # Extract each field
                for field_name, field_path in fields_config.items():
                    if field_name == 'url_template':
                        continue  # Handle this separately
                    
                    value = self._extract_field_value(product_data, field_path)
                    product[field_name] = value
                
                # Handle URL template
                if 'url_template' in fields_config:
                    product['url'] = fields_config['url_template'].format(**product)
                
                products.append(product)
                
            except Exception as e:
                print(f"✗ Error processing product: {e}")
                continue
        
        return products
    
    def _extract_from_dom(self, soup: BeautifulSoup, url: str, config: Dict) -> List[Dict[str, Any]]:
        """Extract data by scraping DOM elements"""
        products = []
        product_elements = soup.select(config['product_selector'])
        
        for element in product_elements:
            product = {}
            
            for field_name, field_config in config['fields'].items():
                try:
                    if isinstance(field_config, dict):
                        selector = field_config['selector']
                        attribute = field_config.get('attribute', 'text')
                        prefix = field_config.get('prefix', '')
                        
                        field_element = element.select_one(selector)
                        if field_element:
                            if attribute == 'text':
                                value = field_element.get_text(strip=True)
                            else:
                                value = field_element.get(attribute, '')
                            
                            if prefix and value:
                                value = prefix + value
                                
                            product[field_name] = value
                    
                except Exception as e:
                    print(f"✗ Error extracting {field_name}: {e}")
                    continue
            
            if product:  # Only add if we got some data
                products.append(product)
        
        return products
    
    def _extract_from_json_ld(self, soup: BeautifulSoup, url: str, config: Dict) -> List[Dict[str, Any]]:
        """Extract data from JSON-LD structured data"""
        products = []
        
        # Find all JSON-LD scripts
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                
                # Handle different JSON-LD structures
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == config['json_ld_type']:
                            product = self._extract_json_ld_product(item, config['fields'])
                            if product:
                                products.append(product)
                elif isinstance(data, dict):
                    if data.get('@type') == config['json_ld_type']:
                        product = self._extract_json_ld_product(data, config['fields'])
                        if product:
                            products.append(product)
                
            except json.JSONDecodeError:
                continue
        
        return products
    
    def _extract_json_ld_product(self, data: Dict, fields_config: Dict) -> Dict[str, Any]:
        """Extract a single product from JSON-LD data"""
        product = {}
        
        for field_name, field_path in fields_config.items():
            value = self._extract_field_value(data, field_path)
            if value:
                product[field_name] = value
        
        return product
    
    def _extract_field_value(self, data: Any, path: List[str]) -> Any:
        """Extract a value from nested data using a path"""
        current = data
        
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current
    
    def save_products_to_db(self, products: List[Dict[str, Any]], source_url: str):
        """Save products to database with price tracking"""
        cursor = self.conn.cursor()
        
        for product in products:
            try:
                product_id = str(product.get('id', ''))
                name = str(product.get('name', ''))
                price = product.get('price')
                url = product.get('url', '')
                
                # Convert price to float if it's a string
                if isinstance(price, str):
                    price = float(re.sub(r'[^0-9.]', '', price))
                
                if not product_id or price is None or price == 9999999999:
                    continue
                
                print(f"£{price} - {name} - {url}")
                
                # Check if product exists
                cursor.execute("SELECT price FROM products WHERE id = ? AND site = ?", (product_id, self.name))
                result = cursor.fetchone()
                
                if result:
                    existing_price = result[0]
                    if price < existing_price:
                        percent_decrease = (existing_price - price) / existing_price * 100
                        if percent_decrease >= 50:
                            print(f"🔥 Price drop! '{name}' down {percent_decrease:.2f}%! Old: £{existing_price}, New: £{price}")
                            self._send_price_alert(name, existing_price, price, url)
                        
                        # Update with new lower price
                        cursor.execute("UPDATE products SET price = ?, name = ?, url = ? WHERE id = ? AND site = ?", 
                                     (price, name, url, product_id, self.name))
                        cursor.execute("UPDATE price_history SET price = ? WHERE product_id = ? AND site = ?", 
                                     (price, product_id, self.name))
                else:
                    # Insert new product
                    cursor.execute("INSERT INTO products (id, name, url, price, site) VALUES (?, ?, ?, ?, ?)",
                                 (product_id, name, url, price, self.name))
                    cursor.execute("INSERT INTO price_history (product_id, price, site) VALUES (?, ?, ?)", 
                                 (product_id, price, self.name))
                
                self.conn.commit()
                self.total_record_count += 1
                
            except Exception as e:
                print(f"✗ Error saving product {product}: {e}")
                continue
    
    def _send_price_alert(self, product_name: str, old_price: float, new_price: float, url: str):
        """Send price alert notification"""
        try:
            subject = f"{product_name} is now £{new_price}"
            message = f"{self.name}: £{new_price}. Price for '{product_name}' has changed! Old price: £{old_price}, New price: £{new_price}, URL: {url}"
            
            command = f"echo '{message}' | mail -s '{subject}' uksquire@icloud.com"
            subprocess.run(command, shell=True, check=True)
            print("📧 Email notification sent!")
            webbrowser.open(url)
            
        except Exception as e:
            print(f"✗ Failed to send notification: {e}")
    
    def run_full_scrape(self):
        """Run the complete scraping workflow"""
        print(f"🚀 Starting scrape for {self.name}")
        start_time = time.time()
        
        # Step 1: Discover category links
        print("📋 Discovering category links...")
        category_links = self.discover_category_links()
        print(f"✓ Found {len(category_links)} category links")
        
        # Step 2: Get all page links from categories
        print("📄 Discovering paginated pages...")
        all_page_urls = []
        for category_url in category_links:
            print(f"  Processing category: {category_url}")
            pages = self.get_paginated_urls(category_url)
            all_page_urls.extend(pages)
            
            # Add delay between categories
            delay_range = self.config['request_config'].get('delay_range', [1, 3])
            time.sleep(random.randint(*delay_range))
        
        print(f"✓ Found {len(all_page_urls)} total pages")
        
        # Step 3: Extract products from all pages
        print("🛍️  Extracting products...")
        random.shuffle(all_page_urls)  # Randomize order
        
        for page_url in all_page_urls:
            try:
                print(f"  Processing: {page_url}")
                products = self.extract_products_from_page(page_url)
                
                if products:
                    self.save_products_to_db(products, page_url)
                    print(f"    ✓ Saved {len(products)} products")
                else:
                    print(f"    ✗ No products found")
                
                # Add delay between pages
                delay_range = self.config['request_config'].get('delay_range', [1, 3])
                time.sleep(random.randint(*delay_range))
                
            except Exception as e:
                print(f"    ✗ Error processing {page_url}: {e}")
                continue
        
        # Final summary
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE site = ?", (self.name,))
        total_products = cursor.fetchone()[0]
        
        print(f"\n🎉 Scraping complete!")
        print(f"   Site: {self.name}")
        print(f"   Total products in DB: {total_products}")
        print(f"   Products processed this run: {self.total_record_count}")
        print(f"   Time elapsed: {elapsed_time:.2f} seconds")
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python generic_scraper.py <site_name>")
        print("Available sites: argos, amazon, generic_json_ld")
        sys.exit(1)
    
    site_name = sys.argv[1]
    
    # Load site configuration
    try:
        with open('site_configs.json', 'r') as f:
            all_configs = json.load(f)
        
        if site_name not in all_configs:
            print(f"Error: Site '{site_name}' not found in configuration")
            print(f"Available sites: {', '.join(all_configs.keys())}")
            sys.exit(1)
        
        config = all_configs[site_name]
        
    except FileNotFoundError:
        print("Error: site_configs.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing site_configs.json: {e}")
        sys.exit(1)
    
    # Run the scraper
    scraper = GenericEcommerceScraper(config)
    try:
        scraper.run_full_scrape()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
