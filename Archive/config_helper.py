#!/usr/bin/env python3
"""
Site Configuration Helper
Helps create configurations for new e-commerce sites
"""

import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent


class SiteAnalyzer:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.ua = UserAgent()
        
        # Setup proxy list from your generic scraper
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
        
        # Configure session for better compatibility
        self.session.max_redirects = 10
    
    def _get_request_headers(self, user_agent_type: str = 'chrome') -> dict:
        """Generate appropriate request headers based on type"""
        if user_agent_type == 'chrome_modified':
            user_agent = self.ua.chrome.replace("Chrome", "Version")
        elif user_agent_type == 'firefox':
            user_agent = self.ua.firefox
        elif user_agent_type == 'safari':
            user_agent = self.ua.safari
        else:
            user_agent = self.ua.chrome
            
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1'
        }
    
    def _get_proxies(self, use_proxy: bool = True) -> dict:
        """Get proxy configuration if enabled"""
        if use_proxy:
            import random
            return {'http': random.choice(self.proxy_list), 'https': random.choice(self.proxy_list)}
        return None
    
    def analyze_site(self) -> dict:
        """Analyze a site and suggest configuration"""
        print(f"🔍 Analyzing {self.base_url}...")
        
        # Try multiple approaches with different anti-bot techniques
        approaches = [
            {"timeout": 15, "delay": 1, "user_agent": "chrome", "use_proxy": False},
            {"timeout": 25, "delay": 3, "user_agent": "firefox", "use_proxy": False},
            {"timeout": 30, "delay": 5, "user_agent": "safari", "use_proxy": False}, 
            {"timeout": 35, "delay": 7, "user_agent": "chrome_modified", "use_proxy": True},
            {"timeout": 40, "delay": 10, "user_agent": "firefox", "use_proxy": True}
        ]
        
        last_error = None
        working_config = None
        
        for attempt, approach in enumerate(approaches, 1):
            try:
                import time
                import random
                
                print(f"  🔄 Attempt {attempt}/{len(approaches)} ({approach['user_agent']}, proxy: {approach['use_proxy']}, timeout: {approach['timeout']}s)...")
                
                # Get headers and proxies for this attempt
                headers = self._get_request_headers(approach["user_agent"])
                proxies = self._get_proxies(approach["use_proxy"])
                
                # Add delay before request
                if attempt > 1:
                    print(f"  ⏳ Waiting {approach['delay']} seconds...")
                    time.sleep(approach['delay'])
                
                # Make request with anti-bot measures
                if proxies:
                    print(f"  🔀 Using proxy: {proxies['http']}")
                
                response = self.session.get(
                    self.base_url, 
                    headers=headers, 
                    proxies=proxies, 
                    timeout=approach['timeout'],
                    allow_redirects=True,
                    verify=True
                )
                response.raise_for_status()
                
                print(f"  ✅ Successfully fetched {self.base_url}")
                print(f"     Status: {response.status_code}")
                print(f"     Content size: {len(response.content)} bytes")
                print(f"     User-Agent: {headers['User-Agent'][:50]}...")
                if proxies:
                    print(f"     Via proxy: {proxies['http']}")
                
                # Store the working configuration for later use
                working_config = {
                    "user_agent_type": approach["user_agent"],
                    "user_agent_string": headers['User-Agent'],
                    "use_proxy": approach["use_proxy"],
                    "working_proxy": proxies['http'] if proxies else None,
                    "timeout": approach['timeout'],
                    "delay": approach['delay']
                }
                
                soup = BeautifulSoup(response.text, 'html.parser')
                break
                
            except requests.exceptions.Timeout as e:
                last_error = f"Request timed out after {approach['timeout']} seconds"
                print(f"  ⏱️ Timeout after {approach['timeout']}s")
                continue
                
            except requests.exceptions.ProxyError as e:
                last_error = f"Proxy error: {e}"
                print(f"  🔀 Proxy error: {str(e)[:100]}...")
                continue
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                print(f"  🔌 Connection error: {str(e)[:100]}...")
                continue
                
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP error {response.status_code}: {e}"
                print(f"  ❌ HTTP error {response.status_code}")
                if response.status_code == 403:
                    print(f"     Likely blocked by anti-bot protection")
                elif response.status_code == 429:
                    print(f"     Rate limited - need longer delays")
                continue
                
            except Exception as e:
                last_error = str(e)
                print(f"  ❌ Unexpected error: {str(e)[:100]}...")
                continue
        else:
            print(f"❌ Could not fetch {self.base_url} after {len(approaches)} attempts")
            print(f"   Last error: {last_error}")
            print(f"💡 Suggestions for {self.domain}:")
            print(f"   - Site has strong anti-bot protection")
            print(f"   - Try using different proxy services") 
            print(f"   - The site might require JavaScript (try selenium/playwright)")
            print(f"   - Consider longer delays between requests")
            print(f"   - Some sites block datacenter IPs (try residential proxies)")
            return {}
        
        config = {
            "base_url": self.base_url,
            "name": self.domain,
            "category_discovery": self._analyze_category_discovery(soup),
            "pagination": self._analyze_pagination(soup),
            "data_extraction": self._analyze_data_extraction(soup),
            "request_config": {
                "timeout": working_config["timeout"],
                "use_proxy": working_config["use_proxy"],
                "user_agent_type": working_config["user_agent_type"],
                "delay_range": [working_config["delay"], working_config["delay"] + 3],
                "working_details": {
                    "user_agent_string": working_config["user_agent_string"],
                    "working_proxy": working_config["working_proxy"],
                    "connection_notes": f"Successfully connected on attempt with {working_config['user_agent_type']} user agent, proxy: {working_config['use_proxy']}"
                }
            }
        }
        
        return config
    
    def _analyze_category_discovery(self, soup: BeautifulSoup) -> dict:
        """Analyze how to discover category links"""
        print("  📂 Analyzing category discovery...")
        
        # Look for common category link patterns
        category_links = []
        patterns_found = {}
        
        # Common e-commerce patterns
        common_patterns = [
            ('/category/', 'Category paths'),
            ('/categories/', 'Categories paths'),
            ('/browse/', 'Browse paths'),
            ('/shop/', 'Shop paths'),
            ('/products/', 'Products paths'),
            ('/collections/', 'Collections paths'),
            ('c:', 'Category IDs'),
            ('cat=', 'Category parameters')
        ]
        
        for pattern, description in common_patterns:
            links = soup.find_all('a', href=lambda x: x and pattern in x)
            if links:
                patterns_found[pattern] = {
                    'count': len(links),
                    'description': description,
                    'examples': [urljoin(self.base_url, link.get('href')) for link in links[:3]]
                }
        
        if patterns_found:
            # Use the most common pattern
            best_pattern = max(patterns_found.keys(), key=lambda x: patterns_found[x]['count'])
            print(f"    ✅ Found category pattern: {best_pattern} ({patterns_found[best_pattern]['count']} links)")
            
            return {
                "method": "href_pattern",
                "patterns": [best_pattern],
                "selector": "a[href]",
                "exclude_patterns": ["sign-in", "login", "register", "cart", "checkout"]
            }
        else:
            print("    ❓ No obvious category patterns found, trying sitemap...")
            return {
                "method": "sitemap",
                "sitemap_url": "/sitemap.xml",
                "category_patterns": ["/category/", "/products/", "/collections/"]
            }
    
    def _analyze_pagination(self, soup: BeautifulSoup) -> dict:
        """Analyze pagination method"""
        print("  📄 Analyzing pagination...")
        
        # Check for <link rel="next">
        next_link = soup.find('link', rel='next')
        if next_link:
            print("    ✅ Found <link rel='next'> pagination")
            return {
                "method": "link_rel_next",
                "next_selector": "link[rel='next']",
                "next_attribute": "href"
            }
        
        # Check for common next button patterns
        next_selectors = [
            ("a[aria-label*='Next']", "ARIA labeled next"),
            ("a[aria-label*='next']", "ARIA labeled next (lowercase)"),
            (".next a", "Next class"),
            (".pagination-next", "Pagination next class"),
            ("a:contains('Next')", "Next text"),
            (".page-numbers .next", "Page numbers next")
        ]
        
        for selector, description in next_selectors:
            if soup.select(selector):
                print(f"    ✅ Found next button: {description}")
                return {
                    "method": "next_button",
                    "next_selector": selector,
                    "next_attribute": "href"
                }
        
        print("    ❓ No obvious pagination found")
        return {
            "method": "none",
            "note": "Manual configuration needed"
        }
    
    def _analyze_data_extraction(self, soup: BeautifulSoup) -> dict:
        """Analyze how to extract product data"""
        print("  🛍️  Analyzing data extraction...")
        
        page_content = str(soup)
        
        # First check for Shopify (very common)
        shopify_indicators = [
            'shopify.com',
            'cdn.shopify.com',
            'Shopify.analytics',
            'window.Shopify',
            'shopify-section',
            'theme-assets'
        ]
        
        if any(indicator in page_content for indicator in shopify_indicators):
            print("    ⚡ Detected Shopify site")
            
            # Check for JSON-LD structured data (common in Shopify)
            if '"@type":"Product"' in page_content:
                print("    ✅ Found JSON-LD Product structured data")
                return {
                    "method": "json_ld",
                    "json_ld_type": "Product",
                    "fields": {
                        "id": ["sku"],
                        "name": ["name"],
                        "price": ["offers", "price"],
                        "url": ["offers", "url"]
                    },
                    "fallback_selectors": {
                        "name": "h1, .product__title, .product-title",
                        "price": ".price-item--regular, .price__regular .price-item, [data-price]",
                        "price_attribute": "data-price"
                    },
                    "note": "Shopify site with JSON-LD structured data"
                }
            
            # Shopify without JSON-LD - use common Shopify selectors
            return {
                "method": "dom_scraping",
                "product_selector": ".product-item, .product-card, .card, [data-product]",
                "fields": {
                    "id": {"selector": "[data-product-id], [data-id]", "attribute": "data-product-id"},
                    "name": {"selector": "h1, .product__title, .product-title, .card__heading", "attribute": "text"},
                    "price": {"selector": ".price, .price-item, .money", "attribute": "text"},
                    "url": {"selector": "a", "attribute": "href"}
                },
                "note": "Shopify site with standard DOM selectors"
            }
        
        # Check for WooCommerce (WordPress e-commerce)
        woocommerce_indicators = [
            'woocommerce',
            'wp-content',
            'wp-json',
            'wc-single-product'
        ]
        
        if any(indicator in page_content for indicator in woocommerce_indicators):
            print("    🛒 Detected WooCommerce site")
            return {
                "method": "dom_scraping",
                "product_selector": ".product, .woocommerce-product",
                "fields": {
                    "id": {"selector": "[data-product_id]", "attribute": "data-product_id"},
                    "name": {"selector": ".product_title, .entry-title", "attribute": "text"},
                    "price": {"selector": ".price, .woocommerce-Price-amount", "attribute": "text"},
                    "url": {"selector": "a", "attribute": "href"}
                },
                "note": "WooCommerce site"
            }
        
        # Check for AJAX/API-based product loading
        ajax_indicators = self._check_ajax_product_loading(soup, page_content)
        
        # If we found AJAX indicators but also found products/prices in DOM, prioritize DOM scraping
        if ajax_indicators:
            products_found = ajax_indicators.get('products_in_initial_load', 0)
            
            # Check for actual price elements (stronger indicator of loaded products)
            price_elements = len(soup.select('*[data-test-id*="price"], .price, [class*="price"]'))
            
            if products_found > 5 or price_elements > 20:  # Found significant product data
                print(f"    🔄 Found AJAX indicators but also {products_found} products and {price_elements} price elements in DOM")
                print(f"    ⚡ Prioritizing DOM extraction since products appear to be loaded")
                
                # Try to create a DOM config based on price elements
                price_selector = '*[data-test-id*="price"], .price, [class*="price"]'
                price_elems = soup.select(price_selector)
                if price_elems:
                    dom_config = self._create_price_based_dom_config(soup, price_selector, price_elems)
                    if dom_config:
                        return dom_config
                
                # If DOM config creation failed, continue to other methods
                print("    ⚠️  DOM config creation failed, trying other methods...")
            else:
                return ajax_indicators
        
        # Check for JSON in script tags (like Argos)
        script_patterns = [
            ('window.App=', 'Window App object'),
            ('window.__INITIAL_STATE__=', 'Initial state object'),
            ('window.__PRELOADED_STATE__=', 'Preloaded state object'),
            ('window.__remixContext=', 'Remix context object'),
            ('window.__remixContext =', 'Remix context object (spaced)'),
            ('"@type":"Product"', 'JSON-LD Product'),
            ('window.dataLayer', 'Google Analytics DataLayer')
        ]
        
        for pattern, description in script_patterns:
            if pattern in page_content:
                if pattern == '"@type":"Product"':
                    print(f"    ✅ Found JSON-LD structured data")
                    return {
                        "method": "json_ld",
                        "json_ld_type": "Product",
                        "fields": {
                            "id": ["sku"],
                            "name": ["name"],
                            "price": ["offers", "price"],
                            "url": ["url"]
                        }
                    }
                else:
                    print(f"    ✅ Found JavaScript data: {description}")
                    
                    # Configure based on the specific pattern found
                    if 'remixContext' in pattern:
                        # Specific configuration for Remix-based sites (like Boohoo)
                        return {
                            "method": "json_script_tag",
                            "patterns": [
                                {
                                    "start": "window.__remixContext=",
                                    "end": ";</script>",
                                    "note": "Remix context data - common for modern e-commerce"
                                },
                                {
                                    "start": "window.__remixContext =",
                                    "end": ";</script>",
                                    "note": "Remix context data with spaces"
                                }
                            ],
                            "product_path": ["state", "loaderData"],
                            "fallback_product_paths": [
                                ["loaderData"],
                                ["routes"],
                                ["state"]
                            ],
                            "fields": {
                                "id": ["id", "productId", "sku"],
                                "name": ["name", "title", "productName"],
                                "price": ["price", "currentPrice", "salePrice"],
                                "url": ["url", "slug", "href"]
                            },
                            "notes": "Remix-based site - may need path adjustment based on actual data structure"
                        }
                    else:
                        # Generic configuration for other JavaScript data
                        return {
                            "method": "json_script_tag",
                            "patterns": [
                                {
                                    "start": f"{pattern}",
                                    "end": ";</script>",
                                    "note": "Manual configuration needed"
                                }
                            ],
                            "product_path": ["products"],
                            "fields": {
                                "id": ["id"],
                                "name": ["name"],
                                "price": ["price"]
                            }
                        }
        
        # Check for common product containers
        product_selectors = [
            ("[data-testid*='product']", "Data testid products"),
            ("[data-test-id*='product']", "Data test-id products"),
            (".product-item", "Product item class"),
            (".product-card", "Product card class"),
            (".product", "Product class"),
            ("[data-component-type*='product']", "Data component products"),
            ("[itemtype*='Product']", "Microdata products"),
            # Look for pricing containers that might indicate products
            ("[data-testid*='price']", "Price elements (likely products)"),
            ("[data-test-id*='price']", "Price test-id elements")
        ]
        
        for selector, description in product_selectors:
            products = soup.select(selector)
            if products:
                print(f"    ✅ Found product containers: {description} ({len(products)} found)")
                
                # For price-based selectors, we need to find the parent product container
                if 'price' in selector:
                    return self._create_price_based_dom_config(soup, selector, products)
                else:
                    return {
                        "method": "dom_scraping",
                        "product_selector": selector,
                        "fields": {
                            "id": {"selector": "[data-id], [data-product-id], [data-testid]", "attribute": "data-id"},
                            "name": {"selector": "h2, h3, .product-name, .title, [data-testid*='title']", "attribute": "text"},
                            "price": {"selector": ".price, .cost, [data-price], [data-testid*='price'], [data-test-id*='price']", "attribute": "text"},
                            "url": {"selector": "a", "attribute": "href"}
                        },
                        "note": "Selectors may need fine-tuning"
                    }
        
        print("    ❓ No obvious data extraction method found")
        return {
            "method": "manual",
            "note": "Manual analysis required"
        }
    
    def _check_ajax_product_loading(self, soup: BeautifulSoup, page_content: str) -> dict:
        """Check if the site loads products via AJAX/API calls"""
        
        # Check for Algolia (very common in e-commerce)
        if 'algolia' in page_content.lower():
            print("    🔍 Detected Algolia search API")
            
            # Extract algolia indices
            import re
            indices = {}
            algolia_patterns = [
                (r'algoliaSourceIndex[\"\']\s*:\s*[\"\'](.*?)[\"\']', 'source'),
                (r'algoliaQueryIndex[\"\']\s*:\s*[\"\'](.*?)[\"\']', 'query'),
                (r'algolia.*?index.*?[\"\'](.*?)[\"\']', 'general')
            ]
            
            for pattern, index_type in algolia_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    indices[index_type] = matches[0]
            
            # Check if there are any actual products in the DOM
            product_elements = self._count_product_elements(soup)
            
            if indices:
                print(f"    ✅ Found Algolia indices: {indices}")
                if product_elements == 0:
                    print(f"    ℹ️  No products in initial page load (expected for Algolia sites)")
                
                return {
                    "method": "ajax_api",
                    "api_type": "algolia",
                    "algolia_indices": indices,
                    "note": "Site uses Algolia search API for product loading - requires API integration or JavaScript rendering",
                    "products_in_initial_load": product_elements,
                    "fallback_method": "json_script_tag",
                    "patterns": [
                        {
                            "start": "window.__remixContext=",
                            "end": ";</script>",
                            "note": "Remix context may contain category structure but not products"
                        }
                    ]
                }
        
        # Check for other AJAX indicators
        ajax_indicators = [
            'fetch(',
            'XMLHttpRequest',
            'axios.',
            '$.ajax',
            '$.get',
            '$.post',
            '/api/',
            '/graphql'
        ]
        
        ajax_found = [indicator for indicator in ajax_indicators if indicator in page_content]
        
        # Check if there are products in DOM vs AJAX indicators
        product_elements = self._count_product_elements(soup)
        
        if len(ajax_found) >= 3:  # Multiple indicators suggest heavy AJAX use
            print(f"    🔍 Detected AJAX-heavy site (indicators: {ajax_found[:3]})")
            
            if product_elements == 0:
                print(f"    ℹ️  No products in initial page load - likely loads via AJAX")
            
            return {
                "method": "ajax_api",
                "api_type": "unknown",
                "note": "Site appears to load products via AJAX - manual API analysis required or use JavaScript rendering",
                "ajax_indicators": ajax_found[:5],
                "products_in_initial_load": product_elements
            }
        
        return None
    
    def _count_product_elements(self, soup: BeautifulSoup) -> int:
        """Count how many product-like elements are present in the DOM"""
        product_selectors = [
            "[data-testid*='product']",
            "[data-test-id*='product']",  # Alternative format
            "[data-testid*='item']",
            "[data-test-id*='item']",
            ".product-item",
            ".product-card", 
            ".product",
            "[data-component-type*='product']",
            "[itemtype*='Product']",
            "a[href*='/product/']",
            # Pricing elements that indicate products
            "[data-testid*='price']",
            "[data-test-id*='price']",
            ".price",
            "[class*='price']"
        ]
        
        total_products = 0
        found_selectors = []
        
        for selector in product_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    total_products += len(elements)
                    found_selectors.append(f"{selector}: {len(elements)}")
            except:
                continue
        
        # Debug information - show what was found
        if found_selectors:
            print(f"    🔍 Product elements found: {found_selectors[:3]}")
        
        return total_products
    
    def _create_price_based_dom_config(self, soup: BeautifulSoup, price_selector: str, price_elements) -> dict:
        """Create DOM scraping config when products are detected via price elements"""
        print(f"    🎯 Analyzing product structure based on pricing elements...")
        
        # Try to find the common parent container for price elements
        parent_candidates = []
        
        for price_elem in price_elements[:5]:  # Check first 5 price elements
            # Go up the DOM tree to find potential product containers
            current = price_elem
            for level in range(1, 6):  # Check up to 5 levels up
                current = current.parent
                if not current:
                    break
                
                # Look for containers that might represent individual products
                classes = current.get('class', [])
                tag_name = current.name
                
                # Score this container
                score = 0
                if any('item' in str(cls).lower() for cls in classes):
                    score += 2
                if any('card' in str(cls).lower() for cls in classes):
                    score += 2
                if any('product' in str(cls).lower() for cls in classes):
                    score += 3
                if tag_name in ['article', 'li']:
                    score += 1
                
                if score > 0:
                    # Create a selector for this parent type
                    if classes:
                        selector = f".{classes[0]}"
                    else:
                        selector = tag_name
                    
                    parent_candidates.append((selector, score, level))
        
        # Choose the best parent selector
        if parent_candidates:
            # Sort by score (highest first), then by level (lowest first - closer to price)
            parent_candidates.sort(key=lambda x: (-x[1], x[2]))
            best_selector = parent_candidates[0][0]
            
            print(f"    ✅ Found potential product container: {best_selector}")
            
            return {
                "method": "dom_scraping", 
                "product_selector": best_selector,
                "fields": {
                    "id": {
                        "selector": "[data-id], [data-product-id], [data-testid], [data-test-id]", 
                        "attribute": "data-id"
                    },
                    "name": {
                        "selector": "h1, h2, h3, h4, .title, [data-testid*='title'], [data-test-id*='title'], [data-testid*='name'], [data-test-id*='name']", 
                        "attribute": "text"
                    },
                    "price": {
                        "selector": price_selector.replace('[', '').replace(']', ''), 
                        "attribute": "text"
                    },
                    "url": {
                        "selector": "a", 
                        "attribute": "href"
                    }
                },
                "note": f"Detected via price elements - product containers: {best_selector}"
            }
        else:
            # Fallback - use price elements directly and try to extract from siblings
            print(f"    ⚠️  Using price elements directly - may need manual refinement")
            
            return {
                "method": "dom_scraping",
                "product_selector": price_selector,
                "fields": {
                    "id": {
                        "selector": "[data-id], [data-product-id], [data-testid], [data-test-id]", 
                        "attribute": "data-id",
                        "note": "May need to search in parent elements"
                    },
                    "name": {
                        "selector": "~ *, preceding-sibling::*, following-sibling::*", 
                        "attribute": "text",
                        "note": "Searches siblings of price element"
                    },
                    "price": {
                        "selector": "self", 
                        "attribute": "text"
                    },
                    "url": {
                        "selector": "ancestor::a, a", 
                        "attribute": "href"
                    }
                },
                "note": "Price-element based extraction - may need manual adjustment for product boundaries"
            }


def create_config_interactive():
    """Interactive configuration creator"""
    print("🚀 Generic E-commerce Scraper - Configuration Creator")
    print("=" * 60)
    
    base_url = input("Enter the base URL of the site (e.g., https://example.com): ").strip()
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url
    
    analyzer = SiteAnalyzer(base_url)
    config = analyzer.analyze_site()
    
    if not config:
        print("❌ Could not analyze site")
        return
    
    # Display the configuration
    print("\n" + "=" * 60)
    print("🔧 Generated Configuration:")
    print("=" * 60)
    print(json.dumps(config, indent=2))
    
    # Ask if user wants to save
    save = input("\n💾 Save this configuration? (y/n): ").lower().strip()
    if save == 'y':
        site_name = input("Enter a name for this site configuration: ").strip().lower().replace(' ', '_')
        
        try:
            # Load existing configs
            try:
                with open('site_configs.json', 'r') as f:
                    all_configs = json.load(f)
            except FileNotFoundError:
                all_configs = {}
            
            # Add new config
            all_configs[site_name] = config
            
            # Save updated configs
            with open('site_configs.json', 'w') as f:
                json.dump(all_configs, f, indent=2)
            
            print(f"✅ Configuration saved as '{site_name}'")
            print(f"🚀 You can now run: python generic_scraper.py {site_name}")
            
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
    
    return config


def main():
    create_config_interactive()


if __name__ == "__main__":
    main()
