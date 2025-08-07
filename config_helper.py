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
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.ua.chrome})
    
    def analyze_site(self) -> dict:
        """Analyze a site and suggest configuration"""
        print(f"🔍 Analyzing {self.base_url}...")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"❌ Could not fetch {self.base_url}: {e}")
            return {}
        
        config = {
            "base_url": self.base_url,
            "name": self.domain,
            "category_discovery": self._analyze_category_discovery(soup),
            "pagination": self._analyze_pagination(soup),
            "data_extraction": self._analyze_data_extraction(soup),
            "request_config": {
                "timeout": 5,
                "use_proxy": False,
                "user_agent_type": "chrome",
                "delay_range": [1, 3]
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
        
        # Check for JSON in script tags (like Argos)
        script_patterns = [
            ('window.App=', 'Window App object'),
            ('window.__INITIAL_STATE__=', 'Initial state object'),
            ('window.__PRELOADED_STATE__=', 'Preloaded state object'),
            ('"@type":"Product"', 'JSON-LD Product'),
            ('window.dataLayer', 'Google Analytics DataLayer')
        ]
        
        page_content = str(soup)
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
                    # This would need manual configuration
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
            (".product-item", "Product item class"),
            (".product-card", "Product card class"),
            (".product", "Product class"),
            ("[data-component-type*='product']", "Data component products"),
            ("[itemtype*='Product']", "Microdata products")
        ]
        
        for selector, description in product_selectors:
            products = soup.select(selector)
            if products:
                print(f"    ✅ Found product containers: {description} ({len(products)} found)")
                return {
                    "method": "dom_scraping",
                    "product_selector": selector,
                    "fields": {
                        "id": {"selector": "[data-id], [data-product-id]", "attribute": "data-id"},
                        "name": {"selector": "h2, h3, .product-name, .title", "attribute": "text"},
                        "price": {"selector": ".price, .cost, [data-price]", "attribute": "text"},
                        "url": {"selector": "a", "attribute": "href"}
                    },
                    "note": "Selectors may need fine-tuning"
                }
        
        print("    ❓ No obvious data extraction method found")
        return {
            "method": "manual",
            "note": "Manual analysis required"
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
