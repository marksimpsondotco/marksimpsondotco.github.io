#!/usr/bin/env python3
"""
Export price drop data to JSON format
"""

import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse, parse_qs, unquote


class PriceDropExporter:
    def __init__(self, sites_dir="sites"):
        self.sites_dir = Path(sites_dir)
        self.product_cache = {}
        
    def extract_real_url(self, url):
        """Extract the real URL from affiliate link"""
        if not url:
            return None
        
        if 'awin1.com' in url or 'awin' in url:
            try:
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                
                if 'ued' in params:
                    real_url = unquote(params['ued'][0])
                    return real_url
            except Exception:
                pass
        
        return url
    
    def get_product_url(self, site_name, product_name):
        """Get product URL from the site's database"""
        cache_key = f"{site_name}:{product_name}"
        if cache_key in self.product_cache:
            return self.product_cache[cache_key]
        
        db_path = self.sites_dir / site_name / f"{site_name}.db"
        if not db_path.exists():
            return None
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT url FROM products WHERE name = ? LIMIT 1", (product_name,))
            result = cursor.fetchone()
            
            if not result:
                cursor.execute("SELECT url FROM products WHERE name LIKE ? LIMIT 1", (f"%{product_name[:30]}%",))
                result = cursor.fetchone()
            
            conn.close()
            
            if result:
                url = result[0]
                self.product_cache[cache_key] = url
                return url
        except Exception:
            pass
        
        return None
        
    def parse_log_file(self, log_path):
        """Parse a single log file for price drop information"""
        drops = []
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if '📉' in line or '💰 PRICE DROP!' in line:
                    price_drop_match = re.search(r'📉.*?(\d+\.?\d*)%', line)
                    if not price_drop_match:
                        price_drop_match = re.search(r'PRICE DROP!.*?-(\d+\.?\d*)%', line)
                    
                    if price_drop_match:
                        percentage = float(price_drop_match.group(1))
                        
                        product_name = "Unknown Product"
                        old_price = None
                        new_price = None
                        
                        price_match = re.search(r'Was £([\d,]+\.?\d*), now £([\d,]+\.?\d*)', line)
                        if price_match:
                            old_price = price_match.group(1).replace(',', '')
                            new_price = price_match.group(2).replace(',', '')
                        
                        for j in range(i-1, max(0, i-10), -1):
                            check_line = lines[j].strip()
                            
                            if not check_line or '💰 PRICE DROP!' in check_line or '📉' in check_line:
                                continue
                            
                            product_match = re.search(r'[✅❌]\s*£[\d,]+\.?\d*\s*-\s*(.+)', check_line)
                            if product_match:
                                product_name = product_match.group(1).strip()
                                break
                        
                        site_name = log_path.parent.parent.name
                        log_time = datetime.fromtimestamp(log_path.stat().st_mtime)
                        
                        drops.append({
                            'site': site_name,
                            'product': product_name,
                            'percentage': percentage,
                            'old_price': old_price,
                            'new_price': new_price,
                            'timestamp': log_time.isoformat(),
                            'url': None
                        })
                
                i += 1
                
        except Exception as e:
            pass
            
        return drops
    
    def deduplicate_drops(self, drops):
        """Deduplicate price drops"""
        drop_groups = defaultdict(list)
        
        for drop in drops:
            key = f"{drop['site']}:{drop['product']}:{drop['url']}"
            drop_groups[key].append(drop)
        
        deduplicated = []
        for key, group in drop_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                with_prices = [d for d in group if d['old_price'] and d['new_price']]
                
                if with_prices:
                    best = max(with_prices, key=lambda x: x['percentage'])
                    deduplicated.append(best)
                else:
                    best = max(group, key=lambda x: x['percentage'])
                    deduplicated.append(best)
        
        return deduplicated
    
    def scan_all_logs(self):
        """Scan all log files and return structured data"""
        all_drops = []
        
        log_files = list(self.sites_dir.glob("*/logs/*.log"))
        
        for log_file in log_files:
            drops = self.parse_log_file(log_file)
            
            for drop in drops:
                url = self.get_product_url(drop['site'], drop['product'])
                drop['url'] = self.extract_real_url(url) if url else None
            
            all_drops.extend(drops)
        
        all_drops = self.deduplicate_drops(all_drops)
        
        # Sort by percentage
        all_drops.sort(key=lambda x: x['percentage'], reverse=True)
        
        return all_drops
    
    def generate_site_stats(self, drops):
        """Generate site statistics"""
        site_stats = defaultdict(lambda: {'count': 0, 'max_drop': 0, 'total_savings': 0})
        
        for drop in drops:
            site = drop['site']
            site_stats[site]['count'] += 1
            site_stats[site]['max_drop'] = max(site_stats[site]['max_drop'], drop['percentage'])
            
            if drop['old_price'] and drop['new_price']:
                try:
                    savings = float(drop['old_price']) - float(drop['new_price'])
                    site_stats[site]['total_savings'] += savings
                except:
                    pass
        
        # Convert to list and sort
        stats_list = [
            {
                'site': site,
                'count': stats['count'],
                'max_drop': round(stats['max_drop'], 2),
                'total_savings': round(stats['total_savings'], 2)
            }
            for site, stats in site_stats.items()
        ]
        
        stats_list.sort(key=lambda x: x['max_drop'], reverse=True)
        
        return stats_list
    
    def export_json(self, output_file="price_drops.json", limit=100):
        """Export price drops to JSON file"""
        print("Scanning logs for price drops...")
        all_drops = self.scan_all_logs()
        
        print(f"Found {len(all_drops)} unique price drops")
        
        # Generate statistics
        site_stats = self.generate_site_stats(all_drops)
        
        # Limit the number of drops
        top_drops = all_drops[:limit]
        
        # Create export data
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'total_drops': len(all_drops),
            'top_drops_shown': len(top_drops),
            'site_stats': site_stats,
            'drops': top_drops
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported to {output_file}")
        print(f"   Total drops: {len(all_drops)}")
        print(f"   Top drops in export: {len(top_drops)}")
        print(f"   Sites tracked: {len(site_stats)}")
        
        return output_file


def main():
    """Main entry point"""
    import sys
    
    sites_dir = sys.argv[1] if len(sys.argv) > 1 else "sites"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "price_drops.json"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    exporter = PriceDropExporter(sites_dir)
    exporter.export_json(output_file, limit)


if __name__ == "__main__":
    main()
