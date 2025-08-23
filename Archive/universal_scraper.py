#!/usr/bin/env python3
"""
Universal E-commerce Scraper
Drop-in replacement for argos.py that works with any e-commerce site
"""

import sys
import json
from generic_scraper import GenericEcommerceScraper

def main():
    """Main entry point that mimics the original argos.py interface"""
    if len(sys.argv) not in [2, 3]:
        print("Usage: python universal_scraper.py <url_file> [site_config]")
        print()
        print("Examples:")
        print("  python universal_scraper.py argos_all_pages.txt                # Uses argos_file config")
        print("  python universal_scraper.py amazon_urls.txt amazon             # Uses amazon config")
        print("  python universal_scraper.py my_urls.txt my_custom_site         # Uses custom config")
        print()
        print("Available configurations:")
        try:
            with open('site_configs.json', 'r') as f:
                configs = json.load(f)
            for name, config in configs.items():
                print(f"  {name:<20} - {config['name']}")
        except:
            print("  (No configurations found)")
        sys.exit(1)
    
    url_file = sys.argv[1]
    
    # If no site config specified, try to guess from filename
    if len(sys.argv) == 3:
        site_name = sys.argv[2]
    else:
        # Auto-detect from filename
        filename_lower = url_file.lower()
        if 'argos' in filename_lower:
            site_name = 'argos_file'
        elif 'amazon' in filename_lower:
            site_name = 'amazon'
        else:
            site_name = 'argos_file'  # Default fallback
        
        print(f"🔍 Auto-detected site configuration: {site_name}")
    
    # Load the configuration and modify it to use the specified file
    try:
        with open('site_configs.json', 'r') as f:
            all_configs = json.load(f)
        
        if site_name not in all_configs:
            print(f"❌ Site configuration '{site_name}' not found")
            print(f"Available configurations: {', '.join(all_configs.keys())}")
            sys.exit(1)
        
        config = all_configs[site_name].copy()
        
        # Override the file path if using file-based discovery
        if config['category_discovery']['method'] == 'url_file':
            config['category_discovery']['file_path'] = url_file
        
        print(f"🚀 Starting scrape using {config['name']} configuration")
        print(f"📁 URL file: {url_file}")
        
        # Run the scraper
        scraper = GenericEcommerceScraper(config)
        try:
            scraper.run_full_scrape()
        finally:
            scraper.close()
        
    except FileNotFoundError:
        print("❌ site_configs.json not found")
        print("Run 'python config_helper.py' to create site configurations")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
