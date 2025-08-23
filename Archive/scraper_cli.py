#!/usr/bin/env python3
"""
Generic E-commerce Scraper CLI
Command-line interface for managing and running scrapers
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from generic_scraper import GenericEcommerceScraper


def list_sites():
    """List all available site configurations"""
    try:
        with open('site_configs.json', 'r') as f:
            configs = json.load(f)
        
        print("Available site configurations:")
        print("-" * 40)
        for site_name, config in configs.items():
            print(f"  {site_name:<15} - {config['name']}")
            print(f"  {'URL:':<15} {config['base_url']}")
            print()
        
    except FileNotFoundError:
        print("❌ No site configurations found. Run 'python config_helper.py' to create one.")
    except json.JSONDecodeError as e:
        print(f"❌ Error reading configuration file: {e}")


def show_stats(site_name=None):
    """Show database statistics"""
    db_files = list(Path('.').glob('*.db'))
    
    if not db_files:
        print("No database files found.")
        return
    
    print("Database Statistics:")
    print("=" * 50)
    
    for db_file in db_files:
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            print(f"\n📊 {db_file}")
            
            # Total products
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            print(f"   Total products: {total_products:,}")
            
            # Products by site (if site column exists)
            try:
                cursor.execute("SELECT site, COUNT(*) FROM products GROUP BY site")
                site_counts = cursor.fetchall()
                if site_counts:
                    print("   By site:")
                    for site, count in site_counts:
                        print(f"     {site}: {count:,}")
            except sqlite3.OperationalError:
                pass  # Site column doesn't exist
            
            # Price ranges
            cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM products WHERE price > 0")
            min_price, max_price, avg_price = cursor.fetchone()
            if min_price:
                print(f"   Price range: £{min_price:.2f} - £{max_price:.2f} (avg: £{avg_price:.2f})")
            
            # Recent price changes
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM price_history 
                    WHERE date >= datetime('now', '-7 days')
                """)
                recent_changes = cursor.fetchone()[0]
                print(f"   Price changes (last 7 days): {recent_changes:,}")
            except sqlite3.OperationalError:
                pass  # price_history table doesn't exist
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"❌ Error reading {db_file}: {e}")


def run_scraper(site_name: str, dry_run: bool = False):
    """Run the scraper for a specific site"""
    try:
        with open('site_configs.json', 'r') as f:
            all_configs = json.load(f)
        
        if site_name not in all_configs:
            print(f"❌ Site '{site_name}' not found in configuration")
            print(f"Available sites: {', '.join(all_configs.keys())}")
            return False
        
        config = all_configs[site_name]
        
        if dry_run:
            print(f"🧪 DRY RUN for {config['name']}")
            print("Would perform the following actions:")
            print(f"  1. Discover category links from {config['base_url']}")
            print(f"  2. Extract products using method: {config['data_extraction']['method']}")
            print(f"  3. Save to database: {site_name}.db")
            print("\nRun without --dry-run to execute.")
            return True
        
        scraper = GenericEcommerceScraper(config)
        try:
            scraper.run_full_scrape()
            return True
        finally:
            scraper.close()
            
    except FileNotFoundError:
        print("❌ site_configs.json not found. Run 'python config_helper.py' to create configurations.")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing configuration: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        return False


def test_site(site_name: str):
    """Test site configuration with a single page"""
    try:
        with open('site_configs.json', 'r') as f:
            all_configs = json.load(f)
        
        if site_name not in all_configs:
            print(f"❌ Site '{site_name}' not found")
            return False
        
        config = all_configs[site_name]
        
        print(f"🧪 Testing configuration for {config['name']}")
        
        scraper = GenericEcommerceScraper(config)
        try:
            # Test category discovery
            print("1. Testing category discovery...")
            categories = scraper.discover_category_links()
            print(f"   ✅ Found {len(categories)} categories")
            
            if categories:
                # Test first category
                print("2. Testing pagination...")
                test_category = categories[0]
                print(f"   Testing: {test_category}")
                pages = scraper.get_paginated_urls(test_category)
                print(f"   ✅ Found {len(pages)} pages")
                
                if pages:
                    # Test product extraction
                    print("3. Testing product extraction...")
                    test_page = pages[0]
                    products = scraper.extract_products_from_page(test_page)
                    print(f"   ✅ Extracted {len(products)} products")
                    
                    if products:
                        print("   Sample products:")
                        for i, product in enumerate(products[:3]):
                            print(f"     {i+1}. {product}")
                    else:
                        print("   ❌ No products extracted - configuration may need adjustment")
                else:
                    print("   ❌ No pages found")
            else:
                print("   ❌ No categories found - check category discovery configuration")
            
            return True
            
        finally:
            scraper.close()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def run_monitor(site_name: str, 
                min_interval: int = 60, 
                max_interval: int = 300, 
                price_threshold: float = 10.0,
                email_recipients: str = None,
                auto_refresh_hours: float = 0):
    """Run continuous price monitoring for a site"""
    try:
        with open('site_configs.json', 'r') as f:
            configs = json.load(f)
        
        if site_name not in configs:
            print(f"❌ Site '{site_name}' not found in configuration")
            print(f"Available sites: {', '.join(configs.keys())}")
            return False
        
        config = configs[site_name]
        
    except FileNotFoundError:
        print("❌ No site configurations found. Run 'python config_helper.py' to create one.")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error reading configuration file: {e}")
        return False
    
    # Parse email recipients
    recipients = []
    if email_recipients:
        recipients = [email.strip() for email in email_recipients.split(',')]
    
    # Initialize scraper
    scraper = GenericEcommerceScraper(config)
    
    try:
        # Check if database has products
        cursor = scraper.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE site = ?", (scraper.name,))
        product_count = cursor.fetchone()[0]
        
        if product_count == 0:
            print(f"❌ No products found in database for {site_name}")
            print("   Run a full scrape first: python scraper_cli.py run {site_name}")
            return False
        
        print(f"✓ Found {product_count} products to monitor")
        
        # Start monitoring
        scraper.run_continuous_monitoring(
            min_interval=min_interval,
            max_interval=max_interval,
            min_price_drop_percent=price_threshold,
            email_recipients=recipients,
            auto_refresh_hours=auto_refresh_hours
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Error running monitor: {e}")
        return False
    finally:
        scraper.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generic E-commerce Scraper CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scraper_cli.py list                              # List all configured sites
  python scraper_cli.py run argos                         # Run Argos scraper
  python scraper_cli.py run amazon --dry-run              # Dry run for Amazon
  python scraper_cli.py test argos                        # Test Argos configuration
  python scraper_cli.py stats                             # Show database statistics
  python scraper_cli.py monitor norman                    # Monitor Norman Walsh prices
  python scraper_cli.py monitor argos --min-interval 30   # Monitor Argos with 30s min interval
  
To add new sites, run: python config_helper.py
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all configured sites')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run scraper for a site')
    run_parser.add_argument('site', help='Site name to scrape')
    run_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test site configuration')
    test_parser.add_argument('site', help='Site name to test')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Run continuous price monitoring')
    monitor_parser.add_argument('site', help='Site name to monitor')
    monitor_parser.add_argument('--min-interval', type=int, default=60, 
                               help='Minimum seconds between checks (default: 60)')
    monitor_parser.add_argument('--max-interval', type=int, default=300,
                               help='Maximum seconds between checks (default: 300)')
    monitor_parser.add_argument('--price-threshold', type=float, default=10.0,
                               help='Minimum price drop percentage to trigger email (default: 10.0)')
    monitor_parser.add_argument('--email-recipients', type=str,
                               help='Comma-separated email addresses for notifications')
    monitor_parser.add_argument('--auto-refresh-hours', type=float, default=0,
                               help='Hours between full scrapes to discover new products (0=disabled, default: 0)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'list':
        list_sites()
    elif args.command == 'run':
        success = run_scraper(args.site, args.dry_run)
        sys.exit(0 if success else 1)
    elif args.command == 'test':
        success = test_site(args.site)
        sys.exit(0 if success else 1)
    elif args.command == 'stats':
        show_stats()
    elif args.command == 'monitor':
        success = run_monitor(
            args.site,
            args.min_interval,
            args.max_interval,
            args.price_threshold,
            args.email_recipients,
            args.auto_refresh_hours
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
