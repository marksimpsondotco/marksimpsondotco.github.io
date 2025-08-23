#!/usr/bin/env python3
import requests
import re
import json

def extract_yeti_urls():
    """Extract product URLs from Yeti collection page"""
    url = "https://uk.yeti.com/collections/tumblers"
    response = requests.get(url)
    content = response.text
    
    # Look for the web pixels manager data
    pattern = r'"events":\[\["page_viewed",\{\}\],\["collection_viewed",\{[^}]+?\}]\]'
    match = re.search(pattern, content)
    
    if match:
        print("Found events data, let me extract it...")
        events_str = match.group(0)
        print(f"Events string: {events_str[:200]}...")
        
    # Try to find collection_viewed data with productVariants
    pattern2 = r'"collection_viewed",\{[^}]*"collection":\{[^}]*"productVariants":\[[^\]]+\][^}]*\}'
    match2 = re.search(pattern2, content)
    
    if match2:
        print("\n\nFound collection_viewed data:")
        collection_data = match2.group(0)
        print(f"Collection data: {collection_data[:500]}...")
        
        # Extract URLs specifically
        url_pattern = r'"url":"([^"]+)"'
        urls = re.findall(url_pattern, collection_data)
        print(f"\nFound {len(urls)} URLs:")
        for i, url in enumerate(urls[:10]):  # Show first 10
            print(f"{i+1}: {url}")
    
    # Also try to find the web-pixels-manager script data
    pattern3 = r'window\.webPixelsManager\.init\([^)]+\)'
    match3 = re.search(pattern3, content)
    
    if match3:
        print("\n\nFound web pixels manager init:")
        init_data = match3.group(0)
        print(f"Init data: {init_data[:500]}...")

if __name__ == "__main__":
    extract_yeti_urls()
