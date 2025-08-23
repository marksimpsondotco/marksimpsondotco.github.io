import requests
from bs4 import BeautifulSoup
import json
import re
import sqlite3
import time
import subprocess
import webbrowser
import os
from fake_useragent import UserAgent
import random
import sys
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
#os.system('''
#          osascript -e 'tell app "Terminal" to set miniaturized of front window to true'
#          ''')

# Get file name from command line or default to "default"
if len(sys.argv) > 1:
    file_name = sys.argv[1]
else:
    file_name = "default"
    print("No file specified, using default collections...")

total_record_count = 0

# Pendleton collection URLs to monitor - ALL COLLECTIONS
pendleton_collections = [
    "https://pendletonwoolenmills.eu/collections/accessories/products.json",
    "https://pendletonwoolenmills.eu/collections/aicf-collection-24/products.json",
    "https://pendletonwoolenmills.eu/collections/archive/products.json",
    "https://pendletonwoolenmills.eu/collections/baby-blankets/products.json",
    "https://pendletonwoolenmills.eu/collections/bags-wallets/products.json",
    "https://pendletonwoolenmills.eu/collections/bath-towels/products.json",
    "https://pendletonwoolenmills.eu/collections/beach-towels/products.json",
    "https://pendletonwoolenmills.eu/collections/blankets-pillows/products.json",
    "https://pendletonwoolenmills.eu/collections/books-puzzles/products.json",
    "https://pendletonwoolenmills.eu/collections/chief-joseph-blankets/products.json",
    "https://pendletonwoolenmills.eu/collections/cotton-blankets/products.json",
    "https://pendletonwoolenmills.eu/collections/hats-gloves/products.json",
    "https://pendletonwoolenmills.eu/collections/headwear/products.json",
    "https://pendletonwoolenmills.eu/collections/homeware/products.json",
    "https://pendletonwoolenmills.eu/collections/house-home/products.json",
    "https://pendletonwoolenmills.eu/collections/jackets/products.json",
    "https://pendletonwoolenmills.eu/collections/jacquard-blankets/products.json",
    "https://pendletonwoolenmills.eu/collections/jacquard-throws/products.json",
    "https://pendletonwoolenmills.eu/collections/kids/products.json",
    "https://pendletonwoolenmills.eu/collections/knitwear/products.json",
    "https://pendletonwoolenmills.eu/collections/legendary-blanket-collection/products.json",
    "https://pendletonwoolenmills.eu/collections/loungewear/products.json",
    "https://pendletonwoolenmills.eu/collections/mens/products.json",
    "https://pendletonwoolenmills.eu/collections/mugs-drinkware/products.json",
    "https://pendletonwoolenmills.eu/collections/mugs/products.json",
    "https://pendletonwoolenmills.eu/collections/national-park-blankets/products.json",
    "https://pendletonwoolenmills.eu/collections/new-arrivals-2025/products.json",
    "https://pendletonwoolenmills.eu/collections/pendleton-made-for-japan/products.json",
    "https://pendletonwoolenmills.eu/collections/pendleton-x-us-rubber-co-aw24/products.json",
    "https://pendletonwoolenmills.eu/collections/pendleton-x-us-rubber-company/products.json",
    "https://pendletonwoolenmills.eu/collections/pet-collection/products.json",
    "https://pendletonwoolenmills.eu/collections/picnic-blankets/products.json",
    "https://pendletonwoolenmills.eu/collections/pillows/products.json",
    "https://pendletonwoolenmills.eu/collections/robes/products.json",
    "https://pendletonwoolenmills.eu/collections/scarves/products.json",
    "https://pendletonwoolenmills.eu/collections/serapes/products.json",
    "https://pendletonwoolenmills.eu/collections/shirts/products.json",
    "https://pendletonwoolenmills.eu/collections/socks/products.json",
    "https://pendletonwoolenmills.eu/collections/sweatshirts/products.json",
    "https://pendletonwoolenmills.eu/collections/t-shirts/products.json",
    "https://pendletonwoolenmills.eu/collections/the-journey-west-collection/products.json",
    "https://pendletonwoolenmills.eu/collections/trousers-shorts/products.json",
    "https://pendletonwoolenmills.eu/collections/umbrellas/products.json",
    "https://pendletonwoolenmills.eu/collections/usa-classics/products.json",
    "https://pendletonwoolenmills.eu/collections/womens-jackets/products.json",
    "https://pendletonwoolenmills.eu/collections/womens-knitwear/products.json",
    "https://pendletonwoolenmills.eu/collections/womens-loungewear/products.json",
    "https://pendletonwoolenmills.eu/collections/womens-shirts/products.json",
    "https://pendletonwoolenmills.eu/collections/womens/products.json",
    "https://pendletonwoolenmills.eu/collections/wool-shirts/products.json",
    "https://pendletonwoolenmills.eu/collections/yakima-throws/products.json",
]

proxy_list = [
    'http://51.210.216.54:80',
    'http://51.89.140.240:80',
    'http://41.204.63.118:80',
    'http://68.183.143.134:80',
    'http://178.128.200.87:80',
    'http://143.110.190.83:8080',
    'http://188.215.245.235:80',
    'http://195.15.215.146:80',
    'http://149.102.133.90:80',
    'http://82.65.126.192:88',
    'http://88.153.98.211:80',
    'http://192.99.144.208:10001',
    'http://118.69.111.51:8080',
    'http://82.146.37.145:80',
    'http://85.26.146.169:80',
    'http://50.206.25.109:80',
    'http://107.1.93.212:80',
    'http://50.168.210.236:80',
    'http://51.124.209.11:80',
    'http://50.204.219.231:80',
    'http://50.174.7.153:80',
    'http://50.221.230.186:80',
    'http://50.171.32.226:80',
    'http://68.185.57.66:80',
    'http://50.222.245.47:80',
    'http://50.122.86.118:80',
    'http://50.168.210.232:80',
    'http://50.221.74.130:80',
    'http://213.157.6.50:80',
    'http://50.168.72.112:80',
    'http://50.206.25.110:80',
    'http://50.204.190.234:80',
    'http://50.223.38.2:80',
    'http://50.174.41.66:80',
    'http://50.204.219.227:80',
    'http://107.1.93.223:80',
    'http://50.174.7.162:80',
    'http://50.174.7.158:80',
    'http://50.227.121.39:80',
    'http://50.174.7.152:80',
    'http://50.169.62.105:80',
    'http://107.1.93.218:80',
    'http://198.49.68.80:80',
    'http://50.217.226.41:80',
    'http://64.201.163.133:80',
    'http://50.174.7.159:80',
    'http://50.222.245.40:80',
    'http://50.171.68.130:80',
    'http://50.174.145.10:80',
    'http://50.168.210.238:80',
    'http://50.206.25.104:80',
    'http://50.168.163.177:80',
    'http://50.168.72.117:80',
    'http://107.1.93.209:80',
    'http://50.168.163.180:80',
    'http://50.168.163.179:80',
    'http://50.172.75.124:80',
    'http://211.128.96.206:80',
    'http://50.218.57.70:80',
    'http://50.227.121.33:80',
    'http://190.58.248.86:80',
    'http://50.202.75.26:80',
    'http://50.227.121.35:80',
    'http://50.222.245.50:80',
    'http://50.170.90.25:80',
    'http://50.231.104.58:80',
    'http://50.206.25.111:80',
    'http://50.227.121.36:80',
    'http://41.230.216.70:80',
    'http://50.206.111.88:80',
    'http://50.217.226.43:80',
    'http://50.168.163.166:80',
    'http://50.206.25.106:80',
    'http://50.174.145.11:80',
    'http://50.207.199.82:80',
    'http://50.218.57.65:80',
    'http://50.168.210.235:80',
    'http://50.174.145.13:80',
    'http://50.174.145.15:80',
    'http://50.168.210.226:80',
    'http://107.1.93.213:80',
    'http://107.1.93.219:80',
    'http://50.227.121.32:80',
    'http://50.217.226.46:80',
    'http://50.204.219.225:80',
    'http://50.170.90.30:80',
    'http://47.56.110.204:8989',
    'http://0.0.0.0:80',
    'http://41.207.187.178:80',
    'http://50.206.111.91:80',
    'http://107.1.93.211:80',
    'http://113.161.131.43:80',
    'http://107.1.93.221:80',
    'http://50.168.163.178:80',
    'http://50.217.226.45:80',
    'http://50.217.29.198:80',
    'http://192.210.159.71:3128',
    'http://45.80.106.250:8085',
    'http://192.177.93.150:3128',
    'http://91.223.133.180:5433',
    'http://170.106.117.131:11573',
    'http://178.20.212.246:8085',
    'http://156.239.52.108:3128',
    'http://154.202.112.64:3128',
    'http://154.202.109.30:3128',
    'http://156.239.54.130:3128',
    'http://51.178.18.88:80',
    'http://154.202.99.30:3128',
    'http://37.27.6.46:80',
    'http://38.170.215.4:8800',
    'http://156.239.53.239:3128',
    'http://45.39.72.142:3128',
    'http://110.238.116.82:45554',
    'http://159.138.252.45:8080',
    'http://192.186.168.6:3128',
    'http://103.225.11.135:80',
    'http://156.239.49.175:3128',
    'http://82.210.56.251:80',
    'http://45.80.106.208:8085',
    'http://154.202.98.253:3128',
    'http://156.239.54.176:3128',
    'http://209.127.136.148:3128',
    'http://176.126.111.100:8085',
    'http://159.203.120.97:10005',
    'http://156.239.50.178:3128',
    'http://72.10.160.171:1513',
    'http://72.10.160.94:3395',
    'http://67.43.236.19:12217',
    'http://45.80.107.83:8085',
    'http://154.202.120.91:3128',
    'http://142.44.210.174:80',
    'http://156.239.53.225:3128',
    'http://209.127.48.9:3128',
    'http://88.218.46.212:8085',
    'http://110.238.109.146:8001',
    'http://156.239.54.14:3128',
    'http://154.202.107.136:3128',
    'http://188.132.222.2:8080',
    'http://8.213.129.20:1099',
    'http://45.66.209.123:8085',
    'http://156.239.54.42:3128',
    'http://149.18.29.30:8085',
    'http://193.233.83.149:8085',
    'http://176.98.81.85:8080',
    'http://8.219.43.134:8002',
    'http://89.19.34.246:8085',
    'http://188.40.44.83:80',
    'http://8.209.64.208:1234',
    'http://192.81.210.30:8080',
    'http://37.120.189.106:80',
    'http://167.172.96.213:80',
    'http://104.164.183.57:3128',
    'http://209.127.136.68:3128',
    'http://198.11.175.180:8058',
    'http://212.119.41.141:8085',
    'http://51.195.246.56:1080',
    'http://81.23.114.238:8080',
    'http://8.213.128.90:03',
    'http://47.243.124.21:82',
    'http://209.127.149.67:3128',
    'http://156.239.50.28:3128',
    'http://185.88.101.223:8085',
    'http://209.127.48.226:3128',
    'http://102.39.215.83:9090',
    'http://193.233.141.61:8085',
    'http://104.165.127.91:3128',
    'http://45.39.72.241:3128',
    'http://154.202.118.111:3128',
    'http://91.243.93.139:8085',
    'http://212.119.41.140:8085',
    'http://51.77.119.171:80',
    'http://91.206.229.251:3128',
    'http://5.189.146.57:80',
    'http://192.210.159.223:3128',
    'http://103.153.127.14:8080',
    'http://8.210.37.63:8118',
    'http://156.239.52.218:3128',
    'http://49.0.199.132:45554',
    'http://47.91.56.120:1080',
    'http://47.91.45.235:1234',
    'http://47.74.64.65:8080',
    'http://209.127.62.207:3128',
    'http://89.38.8.130:88',
    'http://154.201.61.187:3128',
    'http://192.177.93.85:3128',
    'http://212.119.40.157:8085',
    'http://154.202.126.75:3128',
    'http://193.233.210.19:8085',
    'http://209.127.136.37:3128',
    'http://154.201.61.13:3128',
    'http://193.93.193.26:8085'
]

proxies = {'http': random.choice(proxy_list)}
# USE ID not NAME to make this better

# Function to extract and store data in the database
def extract_and_store_data(url, conn):
    global total_record_count
    
    # GENERATE SOUP:
    ua= UserAgent()
    user_agent=ua.chrome
    new_user_agent = user_agent.replace("Chrome", "Version")
    proxies = {'http': random.choice(proxy_list)}
    
    # Set the User-Agent header in the request headers
    headers = {'User-Agent': new_user_agent}
    response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
    
    if response.status_code == 200:
        print("Connection ok")
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from {url}: {e}")
            return
    else:
        print(f"Connection not ok - Status code: {response.status_code}")    
        print(proxies)
        return  # Exit early if connection failed

    # STORE in the DB:
    cursor = conn.cursor()
    record_count = 0
    
    # Check if the expected data structure exists (Shopify format)
    try:
        products = data.get('products', [])
        if not products:
            print(f"No products found in JSON data for {url}. Skipping this URL.")
            return
    except Exception as e:
        print(f"Error accessing products data for {url}: {e}. Skipping this URL.")
        return
    
    # Loop through each product and extract information
    for product in products:
        try:
            record_count += 1
            
            # Shopify format: use product id, title, and first variant price
            id = str(product['id'])
            name = product['title']
            
            # Get price from first variant
            if product.get('variants') and len(product['variants']) > 0:
                price_str = product['variants'][0]['price']
                price = float(price_str)
            else:
                print(f"No variants found for product {name}")
                continue
            
            # Create Pendleton product URL
            handle = product['handle']
            url2 = f"https://pendletonwoolenmills.eu/products/{handle}"

            print(f"£{price} - {name} - {url2}")

            # Check if the product already exists in the database
            cursor.execute("SELECT price FROM products WHERE id = ?", (id,))
            result = cursor.fetchone()

            if result and price != 9999999999:
                existing_price = result[0]
                if price < existing_price:
                    percent_decrease = (existing_price - price) / existing_price * 100
                    if percent_decrease >= 1.0:
                        print(f"💰 PRICE DROP! '{name}' has dropped by {percent_decrease:.2f}%! Old price: £{existing_price}, New price: £{price}")
                        send_email_notification(name, existing_price, price, url2)
                    else:
                        print(f"📉 Small price drop: '{name}' dropped by {percent_decrease:.2f}% (below 1% threshold)")

                    # Always store the new lower price
                    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (price, id))
                    # Insert new price history record
                    cursor.execute("INSERT INTO price_history (product_id, price) VALUES (?, ?)", (id, price))
                elif price > existing_price:
                    print(f"📈 Price increased: '{name}' - £{existing_price} → £{price} (no action taken)")
                else:
                    print(f"💰 Price stable: '{name}' - £{price}")
            elif price != 9999999999:
                # Insert new product
                cursor.execute("INSERT INTO products (id, name, url, price) VALUES (?, ?, ?, ?)",
                            (id, name, url2, price))
                cursor.execute("INSERT INTO price_history (product_id, price) VALUES (?, ?)", (id, price))

            conn.commit()
        except KeyError as e:
            print(f"Missing expected field in product data: {e}. Skipping product.")
            continue
        except Exception as e:
            print(f"Error processing product: {e}. Skipping product.")
            continue
    total_record_count += record_count
    print(f"Processed {record_count} records for URL: {url}.")
    
def display_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    for row in rows:
        print("\t".join(map(str, row)))

def count_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print (f"Monitoring {count} items in Pendleton")




# Function to send an email notification using rich HTML format
def send_email_notification(product_name, old_price, new_price, url):
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
        # Fetch product page for rich content
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Extract product description
        description_html = ""
        desc_tag = soup.find("div", {"data-test": "product-description"})
        if desc_tag:
            # Replace <br> with HTML line breaks
            for br in desc_tag.find_all("br"):
                br.replace_with("<br>")
            description_html += str(desc_tag)
        
        # Extract bullet features
        features_ul = soup.find("ul", {"data-test": "product-features"})
        if features_ul:
            description_html += str(features_ul)
        
        # If nothing found, use fallback
        if not description_html:
            description_html = "<p>No description available.</p>"
        
        # Extract image URL
        img_url = None
        meta_img = soup.find("meta", property="og:image")
        if meta_img and meta_img.get("content"):
            img_url = meta_img["content"]
        
        # If not found, try JSON-LD
        if not img_url:
            json_ld_tag = soup.find("script", type="application/ld+json")
            if json_ld_tag:
                try:
                    data = json.loads(json_ld_tag.string)
                    if isinstance(data, dict) and "image" in data:
                        img_url = data["image"][0] if isinstance(data["image"], list) else data["image"]
                except:
                    pass
        
        # Download image
        img_data = None
        if img_url:
            # Fix URL if it starts with // (protocol-relative URL)
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            
            try:
                img_resp = requests.get(img_url, headers=headers, timeout=10)
                if img_resp.status_code == 200:
                    img_data = img_resp.content
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image: {e}")
                img_data = None
        
        # Build HTML Email with proper UTF-8 encoding
        msg = MIMEMultipart("related")
        msg["From"] = "notifier@example.com"
        # Use direct £ symbol with UTF-8 encoding
        msg["Subject"] = f"Pendleton Price Drop! {product_name} now £{format_price(new_price)} (was £{format_price(old_price)})"
        msg.set_charset('utf-8')
        
        # Use direct £ symbols in the email body
        html_body = f"""
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        </head>
          <body>
            <h2 style="color:red;">Pendleton Price Drop!</h2>
            {'<img src="cid:product_image" style="max-width:600px;"><br>' if img_data else ''}
            <h3>{product_name}</h3>
            <p><b>Old price:</b> £{format_price(old_price)}<br>
               <b>New price:</b> £{format_price(new_price)}</p>
            {description_html}
            <p><a href="{url}">View on Pendleton</a></p>
          </body>
        </html>
        """
        
        alt_part = MIMEMultipart("alternative")
        # Explicitly set charset for HTML content
        html_mime = MIMEText(html_body, "html", "utf-8")
        alt_part.attach(html_mime)
        msg.attach(alt_part)
        
        # Attach product image if available
        if img_data:
            image_part = MIMEImage(img_data)
            image_part.add_header("Content-ID", "<product_image>")
            msg.attach(image_part)
        
        # Send rich email to multiple recipients
        recipients = ['wipa963miho@post.wordpress.com','uksquire@icloud.com']
        
        for recipient in recipients:
            # Create a copy of the message for each recipient
            msg_copy = MIMEMultipart("related")
            msg_copy["From"] = msg["From"]
            msg_copy["To"] = recipient
            msg_copy["Subject"] = msg["Subject"]
            
            # Copy the content
            for part in msg.get_payload():
                msg_copy.attach(part)
            
            p = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=subprocess.PIPE)
            p.communicate(msg_copy.as_bytes())
        
        print("Rich HTML email notification sent successfully!")
        webbrowser.open(url)
        
    except Exception as e:
        print(f"Error sending rich email notification: {e}")
        # Fallback to simple text email with proper UTF-8 encoding
        subject = f"{product_name} is now £{format_price(new_price)}"
        message = f"PENDLETON:£{format_price(new_price)}. Price for '{product_name}' has changed! Old price: £{format_price(old_price)}, New price: £{format_price(new_price)}, URL: {url}"
        
        try:
            # Ensure UTF-8 encoding for mail command
            subprocess.run(['mail', '-s', subject, 'wipa963miho@post.wordpress.com'], 
                          input=message, text=True, check=True, encoding='utf-8')
            #subprocess.run(['mail', '-s', subject, 'lova494yofu@post.wordpress.com'], 
             #             input=message, text=True, check=True, encoding='utf-8')
            #subprocess.run(['mail', '-s', subject, 'pjmac123@yahoo.com'], 
            #              input=message, text=True, check=True, encoding='utf-8')
            print("Fallback text email notification sent successfully!")
            webbrowser.open(url)
        except subprocess.CalledProcessError as e:
            print("Email notification failed to send:", str(e))

# Create or connect to the SQLite database
conn = sqlite3.connect('pendleton.db')
cursor = conn.cursor()

# Create a table to store the product data if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                  (id TEXT, name TEXT, url TEXT, price REAL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
    product_id TEXT,
    price REAL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

conn.execute('PRAGMA journal_mode=WAL;')


# MAIN loop:

# while True:
start_time = time.time()
# Read URLs from a file and process each URL

# If no file provided, use default Pendleton collections
if file_name == "default" or not os.path.exists(file_name):
    print("Using default Pendleton collections...")
    lines = pendleton_collections
else:
    # Read URLs from a file and process each URL in random order
    with open(file_name, 'r') as url_file:
        lines = url_file.readlines()
    lines = [line.strip() for line in lines if line.strip()]

random.shuffle(lines)  # Shuffle the lines randomly

for line in lines:
    if isinstance(line, str):
        url = line.strip()  # Remove leading/trailing whitespace
    else:
        url = line  # Already a clean URL from the default list
    print(f"Processing URL: {url}")
    
    try:
        random_seconds = random.randint(1, 42)
        time.sleep(random_seconds)
        extract_and_store_data(url, conn)
    except Exception as e:
        print(f"Error processing {url}: {e}")
        pass



        
count_data(conn)
end_time = time.time()
elapsed_time = end_time - start_time
print(f'Elapsed time: {elapsed_time} seconds')
# At the end
print(f"Total records processed: {total_record_count}")
    # Sleep for a minute before checking again
    # count_data(conn)
    # time.sleep(180)

# Close the database connection when done
# conn.close()

