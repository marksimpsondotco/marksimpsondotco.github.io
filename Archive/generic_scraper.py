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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


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
        self.total_processed_count = 0  # Track all products processed
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
        
        # Check if we have working details from config analysis
        working_details = self.config['request_config'].get('working_details', {})
        if working_details.get('user_agent_string'):
            print(f"🔧 Using proven working user agent from config analysis")
            user_agent = working_details['user_agent_string']
        else:
            user_agent_type = self.config['request_config'].get('user_agent_type', 'chrome')
            if user_agent_type == 'chrome_modified':
                user_agent = ua.chrome.replace("Chrome", "Version")
            elif user_agent_type == 'safari':
                user_agent = ua.safari
            elif user_agent_type == 'firefox':
                user_agent = ua.firefox
            else:
                user_agent = ua.chrome
        
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1'
        }
    
    def _get_proxies(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration if enabled"""
        if self.config['request_config'].get('use_proxy', False):
            # Check if we have a proven working proxy from config analysis
            working_details = self.config['request_config'].get('working_details', {})
            if working_details.get('working_proxy'):
                print(f"🔧 Using proven working proxy from config analysis")
                proxy = working_details['working_proxy']
                return {'http': proxy, 'https': proxy}
            else:
                return {'http': random.choice(self.proxy_list), 'https': random.choice(self.proxy_list)}
        return None
    
    def _parse_price_from_text(self, price_text: str) -> float:
        """Parse price from complex text containing multiple prices and currency symbols"""
        if not price_text:
            return None
        
        # Look for patterns like "£58.50", "£58", "$58.50", etc.
        # This regex finds currency symbol followed by digits and optional decimal
        price_matches = re.findall(r'[£$€](\d+(?:\.\d{2})?)', price_text)
        
        if price_matches:
            # Return the first price found (usually the current/sale price)
            return float(price_matches[0])
        
        # Fallback: look for any number with decimal (no currency symbol)
        decimal_matches = re.findall(r'\b(\d+\.\d{2})\b', price_text)
        if decimal_matches:
            return float(decimal_matches[0])
        
        # Fallback: look for any integer number
        integer_matches = re.findall(r'\b(\d+)\b', price_text)
        if integer_matches:
            return float(integer_matches[0])
        
        # If nothing found, return None (will be filtered out)
        return None
    
    def _make_request(self, url: str, features: str = 'html.parser') -> Optional[BeautifulSoup]:
        """Make a request with robust anti-bot evasion like config_helper.py"""
        # Use the same robust approach as config_helper.py
        approaches = [
            {"timeout": 15, "delay": 1, "user_agent": "chrome", "use_proxy": False},
            {"timeout": 25, "delay": 3, "user_agent": "firefox", "use_proxy": False},
            {"timeout": 30, "delay": 5, "user_agent": "safari", "use_proxy": False}, 
            {"timeout": 35, "delay": 7, "user_agent": "chrome_modified", "use_proxy": True},
            {"timeout": 40, "delay": 10, "user_agent": "firefox", "use_proxy": True}
        ]
        
        last_error = None
        
        for attempt, approach in enumerate(approaches, 1):
            try:
                # Get headers for this approach
                headers = self._get_request_headers_for_type(approach["user_agent"])
                proxies = self._get_proxies_for_approach(approach["use_proxy"])
                
                # Add delay before request (except first attempt)
                if attempt > 1:
                    print(f"  ⏳ Waiting {approach['delay']} seconds before retry {attempt}/{len(approaches)}...")
                    time.sleep(approach['delay'])
                
                response = self.session.get(
                    url, 
                    headers=headers, 
                    proxies=proxies, 
                    timeout=approach['timeout'],
                    allow_redirects=True,
                    verify=True
                )
                
                if response.status_code == 200:
                    print(f"✓ Connected to {url}")
                    if proxies:
                        print(f"  🔀 Via proxy: {proxies['http']}")
                    return BeautifulSoup(response.text, features)
                else:
                    last_error = f"HTTP {response.status_code}"
                    print(f"✗ Failed to connect to {url} - Status: {response.status_code}")
                    if response.status_code == 403:
                        print(f"  🚫 Blocked by anti-bot protection - trying different approach...")
                    elif response.status_code == 429:
                        print(f"  ⏱️ Rate limited - trying with longer delay...")
                    continue
                    
            except requests.exceptions.Timeout as e:
                last_error = f"Timeout after {approach['timeout']}s"
                print(f"✗ Timeout connecting to {url} (attempt {attempt}/{len(approaches)})")
                continue
                
            except requests.exceptions.ProxyError as e:
                last_error = f"Proxy error: {e}"
                print(f"✗ Proxy error connecting to {url} (attempt {attempt}/{len(approaches)})")
                continue
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                print(f"✗ Connection error connecting to {url} (attempt {attempt}/{len(approaches)})")
                continue
                
            except Exception as e:
                last_error = str(e)
                print(f"✗ Error connecting to {url} (attempt {attempt}/{len(approaches)}): {e}")
                continue
        
        print(f"❌ Could not connect to {url} after {len(approaches)} attempts. Last error: {last_error}")
        return None
    
    def _get_request_headers_for_type(self, user_agent_type: str) -> Dict[str, str]:
        """Generate headers for specific user agent type"""
        ua = UserAgent()
        
        # Check if we have working details from config analysis first
        working_details = self.config['request_config'].get('working_details', {})
        if working_details.get('user_agent_string') and user_agent_type == self.config['request_config'].get('user_agent_type'):
            user_agent = working_details['user_agent_string']
        else:
            # Generate new user agent for this type
            if user_agent_type == 'chrome_modified':
                user_agent = ua.chrome.replace("Chrome", "Version")
            elif user_agent_type == 'firefox':
                user_agent = ua.firefox
            elif user_agent_type == 'safari':
                user_agent = ua.safari
            else:
                user_agent = ua.chrome
        
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1'
        }
    
    def _get_proxies_for_approach(self, use_proxy: bool) -> Optional[Dict[str, str]]:
        """Get proxy configuration for specific approach"""
        if use_proxy:
            # Check if we have a proven working proxy from config analysis
            working_details = self.config['request_config'].get('working_details', {})
            if working_details.get('working_proxy'):
                proxy = working_details['working_proxy']
                return {'http': proxy, 'https': proxy}
            else:
                return {'http': random.choice(self.proxy_list), 'https': random.choice(self.proxy_list)}
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
        
        print(f"🔍 Looking for patterns: {patterns}")
        print(f"🚫 Excluding patterns: {exclude_patterns}")
        
        found_count = 0
        excluded_count = 0
        
        for a_tag in soup.select(selector):
            href = a_tag.get('href')
            if not href:
                continue
                
            # Check if href matches any of the required patterns
            if any(pattern in href for pattern in patterns):
                # Check if href doesn't match any exclude patterns
                if not any(exclude in href for exclude in exclude_patterns):
                    full_url = urljoin(self.base_url, href)
                    links.add(full_url)
                    found_count += 1
                    if found_count <= 10:  # Show first 10 found links
                        print(f"  ✅ Found: {full_url}")
                else:
                    excluded_count += 1
                    if excluded_count <= 5:  # Show first 5 excluded links
                        print(f"  🚫 Excluded: {href}")
        
        print(f"📊 Total found: {len(links)}, excluded: {excluded_count}")
        return list(links)
    
    def _discover_links_from_sitemap(self, config: Dict) -> List[str]:
        """Discover links from sitemap.xml, handling sitemap index files"""
        sitemap_url = urljoin(self.base_url, config['sitemap_url'])
        soup = self._make_request(sitemap_url, features="xml")
        if not soup:
            return []
        
        links = []
        patterns = config.get('category_patterns', [])
        
        # Check if this is a sitemap index file (contains <sitemapindex>)
        if soup.find('sitemapindex'):
            print("📋 Found sitemap index, processing child sitemaps...")
            
            # Get all child sitemap URLs
            child_sitemaps = []
            for sitemap in soup.find_all('sitemap'):
                loc = sitemap.find('loc')
                if loc:
                    child_url = loc.text
                    # Filter for relevant sitemaps (collections, categories, products)
                    if any(keyword in child_url.lower() for keyword in ['collection', 'category', 'product']):
                        child_sitemaps.append(child_url)
                        print(f"  📄 Found relevant sitemap: {child_url}")
            
            # Process each relevant child sitemap
            for child_sitemap_url in child_sitemaps:
                print(f"  🔍 Processing {child_sitemap_url}...")
                child_soup = self._make_request(child_sitemap_url, features="xml")
                if child_soup:
                    child_links = []
                    for loc in child_soup.find_all('loc'):
                        url = loc.text
                        if any(pattern in url for pattern in patterns):
                            child_links.append(url)
                    
                    links.extend(child_links)
                    print(f"    ✅ Found {len(child_links)} matching URLs")
                
                # Small delay between sitemap requests
                time.sleep(1)
        else:
            # Regular sitemap processing
            for loc in soup.find_all('loc'):
                url = loc.text
                if any(pattern in url for pattern in patterns):
                    links.append(url)
        
        print(f"📊 Total sitemap links found: {len(links)}")
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
        elif method == 'ajax_api':
            return self._extract_from_ajax_api(soup, url, extraction_config)
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
                        return self._process_json_products(data, fallback, soup, url)
        
        if data is None:
            print(f"✗ Could not extract JSON from {url}")
            return []

        return self._process_json_products(data, config, soup, url)
    
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
    
    def _process_json_products(self, data: Any, config: Dict, soup: BeautifulSoup = None, page_url: str = None) -> List[Dict[str, Any]]:
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
                
                # Convert price from pence to pounds if it's a large integer (likely pence)
                if 'price' in product and isinstance(product['price'], (int, float)):
                    price = product['price']
                    # If price is >= 1000 and is an integer, likely in pence format
                    if isinstance(price, int) and price >= 1000:
                        product['price'] = price / 100.0
                
                # Handle URL template
                if 'url_template' in fields_config:
                    product['url'] = fields_config['url_template'].format(**product)
                
                # If URL is still missing, construct search URL using product ID or use collection URL as fallback
                if not product.get('url') and page_url:
                    product_id = product.get('id')
                    if product_id:
                        # Extract base domain from page_url and construct search URL
                        from urllib.parse import urlparse
                        parsed_url = urlparse(page_url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        product['url'] = f"{base_url}/search?q={product_id}"
                        print(f"🔗 Using search URL for product {product_id}: {product['url']}")
                    else:
                        product['url'] = page_url
                        print(f"🔗 Using collection URL as reference for product {product.get('id', 'N/A')}: {page_url}")
                
                products.append(product)
                
            except Exception as e:
                print(f"✗ Error processing product: {e}")
                continue
        
        return products
    
    def _extract_from_dom(self, soup: BeautifulSoup, url: str, config: Dict) -> List[Dict[str, Any]]:
        """Extract data by scraping DOM elements"""
        products = []
        product_elements = soup.select(config['product_selector'])
        
        # Check if this is a single product page by URL pattern
        is_single_product_page = '/products/' in url and len([x for x in url.split('/') if x]) >= 3
        
        # If it's a single product page or no product containers found, use single product extraction
        if (is_single_product_page or not product_elements) and 'single_product_fields' in config:
            print(f"📄 {'Single product page detected' if is_single_product_page else 'No product containers found'}, treating as single product page")
            product = {}
            
            for field_name, field_config in config['single_product_fields'].items():
                try:
                    if isinstance(field_config, dict):
                        selector = field_config['selector']
                        attribute = field_config.get('attribute', 'text')
                        prefix = field_config.get('prefix', '')
                        
                        field_element = soup.select_one(selector)
                        
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
                # For single product pages, the URL and ID are the current page
                if 'id' not in product:
                    product['id'] = url
                if 'url' not in product:
                    product['url'] = url
                
                # Debug output for price extraction
                raw_price = product.get('price', 'No price')
                print(f"🔍 Raw price text: {raw_price}")
                if isinstance(raw_price, str):
                    parsed_price = self._parse_price_from_text(raw_price)
                    print(f"💰 Parsed price: £{parsed_price}")
                    product['price'] = parsed_price
                
                products.append(product)
                print(f"✓ Extracted single product: {product.get('name', 'Unknown')} - £{product.get('price', 'No price')}")
                print(f"📋 DB entry: ID={product.get('id', 'N/A')[:50]}..., Name={product.get('name', 'N/A')[:50]}..., Price={product.get('price', 'N/A')}, URL={product.get('url', 'N/A')[:80]}...")
            
            return products
        
        # Original logic for category pages with multiple products
        for element in product_elements:
            product = {}
            
            for field_name, field_config in config['fields'].items():
                try:
                    if isinstance(field_config, dict):
                        selector = field_config['selector']
                        attribute = field_config.get('attribute', 'text')
                        prefix = field_config.get('prefix', '')
                        
                        if selector == 'self':
                            # Use the product element itself
                            field_element = element
                        else:
                            # For price fields, we might have multiple matches - take the first non-badge one
                            if field_name == 'price' and '.money' in selector:
                                money_elements = element.select(selector)
                                # Filter out money elements that are inside badge elements
                                non_badge_money = [elem for elem in money_elements 
                                                 if not any(parent.name in ['badge', 'on-sale-badge'] or 
                                                           'badge' in ' '.join(parent.get('class', [])) 
                                                           for parent in elem.parents)]
                                field_element = non_badge_money[0] if non_badge_money else None
                            else:
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
            elif isinstance(current, list):
                # Handle both string and integer indices
                if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
                    index = int(key) if isinstance(key, str) else key
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                else:
                    # If we have a list and the key isn't a number, check if it's an array of objects
                    # and try to find the key in the first object (common pattern)
                    if len(current) > 0 and isinstance(current[0], dict) and key in current[0]:
                        current = current[0][key]
                    else:
                        return None
            else:
                return None
        
        return current
    
    def _extract_from_ajax_api(self, soup: BeautifulSoup, url: str, config: Dict) -> List[Dict[str, Any]]:
        """Handle sites that load products via AJAX/API calls"""
        api_type = config.get('api_type', 'unknown')
        products_in_initial = config.get('products_in_initial_load', 0)
        
        if api_type == 'algolia':
            print(f"    🔍 Detected Algolia API site - products loaded dynamically")
            print(f"    📋 Available indices: {config.get('algolia_indices', {})}")
            print(f"    📊 Products in initial page: {products_in_initial}")
            
            if products_in_initial > 0:
                print(f"    ⚡ Found {products_in_initial} products in DOM - trying fallback extraction")
            else:
                print(f"    ℹ️  No products in initial load (normal for Algolia sites)")
            
            print(f"    ⚠️  Note: {config.get('note', 'Requires API integration')}")
            
            # For now, try fallback method if available
            fallback_method = config.get('fallback_method')
            if fallback_method and fallback_method in ['json_script_tag', 'dom_scraping']:
                print(f"    🔄 Trying fallback method: {fallback_method}")
                
                if fallback_method == 'json_script_tag' and 'patterns' in config:
                    # Create a temporary config for the fallback
                    fallback_config = {
                        'patterns': config['patterns'],
                        'product_path': config.get('product_path', ['products']),
                        'fields': config.get('fields', {}),
                        'fallback_product_paths': config.get('fallback_product_paths', [])
                    }
                    products = self._extract_from_json_script(soup, url, fallback_config)
                    if products:
                        print(f"    ✅ Fallback method found {len(products)} products")
                        return products
                    else:
                        print(f"    ❌ Fallback method found no products")
                
                elif fallback_method == 'dom_scraping':
                    # For DOM scraping fallback, we'd need product_selector
                    print(f"    ❌ DOM scraping fallback not configured for AJAX site")
            
            # Provide helpful information about the site
            print(f"    💡 This site requires one of the following approaches:")
            print(f"       1. Direct Algolia API integration")
            print(f"       2. JavaScript rendering (e.g., Selenium/Playwright)")
            print(f"       3. Reverse-engineering the AJAX endpoints")
            
            return []
        
        else:
            print(f"    ❓ Unknown API type: {api_type}")
            print(f"    📊 Products in initial page: {products_in_initial}")
            print(f"    ⚠️  Note: {config.get('note', 'Manual API analysis required')}")
            
            if 'ajax_indicators' in config:
                print(f"    🔍 AJAX indicators found: {config['ajax_indicators']}")
            
            return []
    
    def save_products_to_db(self, products: List[Dict[str, Any]], source_url: str):
        """Save products to database with price tracking"""
        cursor = self.conn.cursor()
        
        for product in products:
            self.total_processed_count += 1  # Count every product processed
            try:
                product_id = str(product.get('id', ''))
                name = str(product.get('name', ''))
                price = product.get('price')
                url = product.get('url', '')
                
                # Convert price to float if it's a string
                if isinstance(price, str):
                    price = self._parse_price_from_text(price)
                
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
                        self.conn.commit()
                        # Don't increment counter for price updates
                    # else: product exists with same/higher price, skip silently
                else:
                    # Insert new product
                    cursor.execute("INSERT INTO products (id, name, url, price, site) VALUES (?, ?, ?, ?, ?)",
                                 (product_id, name, url, price, self.name))
                    cursor.execute("INSERT INTO price_history (product_id, price, site) VALUES (?, ?, ?)", 
                                 (product_id, price, self.name))
                    self.conn.commit()
                    self.total_record_count += 1  # Only increment for new products
                
            except Exception as e:
                print(f"✗ Error saving product {product}: {e}")
                continue
    
    def _send_price_alert(self, product_name: str, old_price: float, new_price: float, url: str):
        """Send rich HTML email notification for price drops"""
        if not url:
            print("No URL provided. Aborting email notification.")
            return
        
        # Helper function to format prices properly
        def format_price(price):
            """Format price to show .00 only when needed, but always show .50, .25, etc."""
            if price == int(price):
                return f"{int(price)}"  # Show "12" not "12.00"
            else:
                return f"{price:.2f}"   # Show "12.50" or "12.25"
        
        try:
            # Build full URL if relative
            if url.startswith('/'):
                full_url = urljoin(self.base_url, url)
            else:
                full_url = url
            
            # Fetch product page for rich content
            headers = self._get_request_headers()
            resp = requests.get(full_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Extract product description (site-specific)
            description_html = "<p>No description available.</p>"
            
            # Try different common selectors for product description
            desc_selectors = [
                "div[data-test='product-description']",
                ".product-description",
                ".product-details",
                ".description",
                "[class*='description']"
            ]
            
            for selector in desc_selectors:
                desc_tag = soup.select_one(selector)
                if desc_tag:
                    # Replace <br> with HTML line breaks
                    for br in desc_tag.find_all("br"):
                        br.replace_with("<br>")
                    description_html = str(desc_tag)
                    break
            
            # Extract image URL
            img_url = None
            meta_img = soup.find("meta", property="og:image")
            if meta_img and meta_img.get("content"):
                img_url = meta_img["content"]
            
            # If not found, try other common selectors
            if not img_url:
                img_selectors = [
                    "meta[property='og:image']",
                    "meta[name='twitter:image']",
                    ".product-image img",
                    ".product-photo img",
                    "[class*='product'] img"
                ]
                for selector in img_selectors:
                    img_elem = soup.select_one(selector)
                    if img_elem:
                        img_url = img_elem.get('content') or img_elem.get('src')
                        if img_url:
                            break
            
            # Download image
            img_data = None
            if img_url:
                # Fix URL if it starts with // (protocol-relative URL)
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = urljoin(self.base_url, img_url)
                
                try:
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200:
                        img_data = img_resp.content
                except requests.exceptions.RequestException as e:
                    print(f"Error downloading image: {e}")
                    img_data = None
            
            # Build HTML Email with proper UTF-8 encoding
            msg = MIMEMultipart("related")
            msg["From"] = "price-tracker@example.com"
            msg["Subject"] = f"🔥 Price Drop! {product_name} now £{format_price(new_price)} (was £{format_price(old_price)})"
            msg.set_charset('utf-8')
            
            # Calculate percentage decrease
            percent_decrease = ((old_price - new_price) / old_price) * 100
            
            html_body = f"""
            <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            </head>
              <body>
                <h2 style="color:red;">🔥 Price Drop Alert! 📉</h2>
                {'<img src="cid:product_image" style="max-width:600px;"><br>' if img_data else ''}
                <h3>{product_name}</h3>
                <p><b>💰 Old price:</b> £{format_price(old_price)}<br>
                   <b>🎯 New price:</b> <span style="color:green; font-size:1.2em;">£{format_price(new_price)}</span><br>
                   <b>📊 Savings:</b> £{format_price(old_price - new_price)} ({percent_decrease:.1f}% off!)</p>
                <p><b>🛒 Store:</b> {self.name}</p>
                {description_html}
                <p><a href="{full_url}" style="background-color:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">View Product</a></p>
              </body>
            </html>
            """
            
            alt_part = MIMEMultipart("alternative")
            html_mime = MIMEText(html_body, "html", "utf-8")
            alt_part.attach(html_mime)
            msg.attach(alt_part)
            
            # Attach product image if available
            if img_data:
                image_part = MIMEImage(img_data)
                image_part.add_header("Content-ID", "<product_image>")
                msg.attach(image_part)
            
            # Send to configured email addresses
            recipients = ['uksquire@icloud.com']  # You can make this configurable
            
            for recipient in recipients:
                msg_copy = MIMEMultipart("related")
                msg_copy["From"] = msg["From"]
                msg_copy["To"] = recipient
                msg_copy["Subject"] = msg["Subject"]
                
                for part in msg.get_payload():
                    msg_copy.attach(part)
                
                p = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=subprocess.PIPE)
                p.communicate(msg_copy.as_bytes())
            
            print("📧 Rich HTML email notification sent successfully!")
            webbrowser.open(full_url)
            
        except Exception as e:
            print(f"Error sending rich email notification: {e}")
            # Fallback to simple text email
            try:
                subject = f"{product_name} is now £{format_price(new_price)}"
                message = f"{self.name}: £{format_price(new_price)}. Price for '{product_name}' has changed! Old price: £{format_price(old_price)}, New price: £{format_price(new_price)}, URL: {full_url}"
                
                subprocess.run(['mail', '-s', subject, 'uksquire@icloud.com'], 
                              input=message, text=True, check=True, encoding='utf-8')
                print("📧 Fallback text email notification sent!")
                webbrowser.open(full_url)
            except subprocess.CalledProcessError as e:
                print(f"✗ Email notification failed: {e}")
    
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
        
        duplicates_skipped = self.total_processed_count - self.total_record_count
        
        print(f"\n🎉 Scraping complete!")
        print(f"   Site: {self.name}")
        print(f"   Total products in DB: {total_products}")
        print(f"   New products added this run: {self.total_record_count}")
        if duplicates_skipped > 0:
            print(f"   Duplicates/existing products skipped: {duplicates_skipped}")
        print(f"   Time elapsed: {elapsed_time:.2f} seconds")
    
    def run_continuous_monitoring(self, 
                                  min_interval: int = 60, 
                                  max_interval: int = 300, 
                                  min_price_drop_percent: float = 10.0,
                                  email_recipients: List[str] = None,
                                  auto_refresh_hours: float = 0):
        """
        Run continuous price monitoring by randomly selecting products to check
        
        Args:
            min_interval: Minimum seconds between checks
            max_interval: Maximum seconds between checks  
            min_price_drop_percent: Minimum price drop percentage to trigger email
            email_recipients: List of email addresses for notifications
            auto_refresh_hours: Hours between full scrapes (0 = disabled)
        """
        print(f"🔄 Starting continuous monitoring for {self.name}")
        print(f"   Check interval: {min_interval}-{max_interval} seconds")
        print(f"   Price drop threshold: {min_price_drop_percent}%")
        if auto_refresh_hours > 0:
            print(f"   Auto-refresh: Every {auto_refresh_hours} hours")
        else:
            print(f"   Auto-refresh: Disabled")
        print("   Press Ctrl+C to stop monitoring")
        
        if email_recipients:
            # Update email recipients (you could also add this to config)
            # For now, we'll keep the hardcoded one in _send_price_alert
            pass
        
        total_checks = 0
        price_drops_found = 0
        last_refresh_time = time.time()
        
        try:
            while True:
                # Check if it's time for an auto-refresh
                current_time = time.time()
                if auto_refresh_hours > 0:
                    hours_since_refresh = (current_time - last_refresh_time) / 3600
                    if hours_since_refresh >= auto_refresh_hours:
                        print(f"\n🔄 Auto-refresh triggered! ({hours_since_refresh:.1f} hours since last refresh)")
                        print("📋 Running full scrape to discover new products...")
                        
                        # Store current stats
                        cursor = self.conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM products WHERE site = ?", (self.name,))
                        products_before = cursor.fetchone()[0]
                        
                        try:
                            # Reset counters for the refresh scrape
                            original_record_count = self.total_record_count
                            original_processed_count = self.total_processed_count
                            self.total_record_count = 0
                            self.total_processed_count = 0
                            
                            # Run full scrape
                            self.run_full_scrape()
                            
                            # Calculate new products found
                            cursor.execute("SELECT COUNT(*) FROM products WHERE site = ?", (self.name,))
                            products_after = cursor.fetchone()[0]
                            new_products = products_after - products_before
                            
                            print(f"✅ Auto-refresh complete!")
                            print(f"   Products before: {products_before}")
                            print(f"   Products after: {products_after}")
                            print(f"   New products discovered: {new_products}")
                            
                            # Restore original counters
                            self.total_record_count = original_record_count + self.total_record_count
                            self.total_processed_count = original_processed_count + self.total_processed_count
                            
                            last_refresh_time = current_time
                            
                        except Exception as e:
                            print(f"❌ Auto-refresh failed: {e}")
                            print("🔄 Continuing with regular monitoring...")
                        
                        print("🔄 Resuming price monitoring...")
                
                # Get all category URLs to check (same as RUN logic)
                category_urls = self.discover_category_links()
                
                if not category_urls:
                    print("❌ No category URLs found in site config. Check site configuration.")
                    break
                
                # Randomly select a category to check
                random_category_url = random.choice(category_urls)
                
                print(f"\n🔍 Monitoring category: {random_category_url}")
                total_checks += 1
                
                try:
                    # Get database cursor for price checks  
                    cursor = self.conn.cursor()
                    
                    # Extract products from this category page (same as RUN logic)
                    products = self.extract_products_from_page(random_category_url)
                    
                    if products:
                        # Check each product for price changes
                        for product in products:
                            product_id = product.get('id')
                            current_price = product.get('price')
                            
                            if not product_id or current_price is None:
                                continue
                            
                            # Convert price to float if string
                            if isinstance(current_price, str):
                                current_price = self._parse_price_from_text(current_price)
                            
                            # Skip invalid prices
                            if current_price <= 0 or current_price == 9999999999:
                                continue
                            
                            # Check existing price in database
                            cursor.execute("SELECT price, name FROM products WHERE id = ? AND site = ?", 
                                         (product_id, self.name))
                            result = cursor.fetchone()
                            
                            if result:
                                existing_price, product_name = result
                                
                                if current_price < existing_price:
                                    percent_decrease = ((existing_price - current_price) / existing_price) * 100
                                    
                                    if percent_decrease >= min_price_drop_percent:
                                        price_drops_found += 1
                                        print(f"🔥 PRICE DROP! {product_name}: £{existing_price} → £{current_price} ({percent_decrease:.1f}% off)")
                                        
                                        # Send email notification
                                        self._send_price_alert(product_name, existing_price, current_price, random_category_url)
                                        
                                        # Update database with new price
                                        cursor.execute("UPDATE products SET price = ? WHERE id = ? AND site = ?", 
                                                     (current_price, product_id, self.name))
                                        cursor.execute("INSERT INTO price_history (product_id, price, site) VALUES (?, ?, ?)", 
                                                     (product_id, current_price, self.name))
                                        self.conn.commit()
                                    elif current_price < existing_price:
                                        print(f"📉 Small price drop: {product_name}: £{existing_price} → £{current_price} ({percent_decrease:.1f}% off)")
                                        # Update price anyway
                                        cursor.execute("UPDATE products SET price = ? WHERE id = ? AND site = ?", 
                                                     (current_price, product_id, self.name))
                                        self.conn.commit()
                                    else:
                                        print(f"💰 Price stable: {product_name}: £{current_price}")
                        
                        print(f"   ✓ Checked {len(products)} products")
                    else:
                        print(f"   ✗ No products found on page")
                
                except Exception as e:
                    print(f"   ✗ Error checking {random_category_url}: {e}")
                
                # Show statistics periodically
                if total_checks % 10 == 0:
                    print(f"\n📊 Monitoring stats:")
                    print(f"   Total checks: {total_checks}")
                    print(f"   Price drops found: {price_drops_found}")
                    print(f"   Success rate: {((total_checks - 0) / total_checks * 100):.1f}%")  # Could track failures
                
                # Random delay before next check
                sleep_time = random.randint(min_interval, max_interval)
                print(f"😴 Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Monitoring stopped by user")
            print(f"📊 Final stats:")
            print(f"   Total checks performed: {total_checks}")
            print(f"   Price drops found: {price_drops_found}")
            if auto_refresh_hours > 0:
                hours_elapsed = (time.time() - (last_refresh_time - auto_refresh_hours * 3600)) / 3600
                refreshes_performed = int(hours_elapsed / auto_refresh_hours)
                print(f"   Auto-refreshes performed: {refreshes_performed}")
            print(f"   Monitoring duration: {((time.time() - (last_refresh_time - auto_refresh_hours * 3600 if auto_refresh_hours > 0 else current_time)) / 3600):.1f} hours")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")

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
