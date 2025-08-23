#!/usr/bin/env python3
"""
Test price drop detection for Pendleton
"""

import sqlite3
import json
import requests
from fake_useragent import UserAgent

def test_price_drop():
    # Connect to database
    conn = sqlite3.connect('pendleton.db')
    cursor = conn.cursor()
    
    # Get current database price for the black cap
    cursor.execute("SELECT id, name, price FROM products WHERE name LIKE '%Vintage Logo Cap - Black%'")
    result = cursor.fetchone()
    
    if not result:
        print("❌ Test product not found in database")
        return
    
    db_id, db_name, db_price = result
    print(f"📊 Database: {db_name} = £{db_price}")
    
    # Get real current price from Shopify API
    ua = UserAgent()
    headers = {'User-Agent': ua.chrome}
    
    response = requests.get("https://pendletonwoolenmills.eu/products/gm212-41157-acrylic-washed-black.json", 
                          headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        real_price = float(data['product']['variants'][0]['price'])
        print(f"🌐 Real price: {db_name} = £{real_price}")
        
        # Check for price drop
        if real_price < db_price:
            percent_decrease = (db_price - real_price) / db_price * 100
            if percent_decrease >= 1.0:
                print(f"💰 PRICE DROP DETECTED! {percent_decrease:.2f}% decrease!")
                print(f"   Old price: £{db_price}")
                print(f"   New price: £{real_price}")
                print(f"   Savings: £{db_price - real_price:.2f}")
                
                # Update database
                cursor.execute("UPDATE products SET price = ? WHERE id = ?", (real_price, db_id))
                cursor.execute("INSERT INTO price_history (product_id, price) VALUES (?, ?)", (db_id, real_price))
                conn.commit()
                print("✅ Database updated with new price")
            else:
                print(f"📉 Small price drop: {percent_decrease:.2f}% (below 1% threshold)")
        elif real_price > db_price:
            print(f"📈 Price increased: £{db_price} → £{real_price} (no action taken)")
        else:
            print(f"💰 Price stable: £{real_price}")
    else:
        print(f"❌ Failed to fetch real price: {response.status_code}")
    
    conn.close()

if __name__ == "__main__":
    test_price_drop()
