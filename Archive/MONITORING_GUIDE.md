# Continuous Price Monitoring Feature

## Overview
The generic scraper now includes a continuous monitoring feature inspired by your original Argos script. This allows you to monitor product prices continuously and receive email notifications when significant price drops occur.

## Features

### 🔄 Continuous Monitoring
- Randomly selects products from your database to check
- Configurable check intervals (random between min/max)
- Monitors for price changes and updates database
- Graceful handling of errors and network issues

### 📧 Email Notifications
- Rich HTML email notifications with product images
- Price drop percentage calculations
- Beautiful formatting with emojis and styling
- Fallback to simple text emails if HTML fails
- Configurable recipient list

### ⚙️ Configurable Settings
- Minimum/maximum check intervals
- Price drop threshold for notifications
- Custom email recipients
- Per-site monitoring capabilities

## Usage

### Basic Monitoring
```bash
# Monitoring Guide

This guide explains how to use the continuous price monitoring feature of the generic scraper.

## Overview

The monitoring feature randomly checks products in your database for price changes and sends email notifications when significant price drops are detected.

## Basic Usage

```bash
# Start monitoring with default settings
python scraper_cli.py monitor <site_name>

# Example
python scraper_cli.py monitor norman
```

## Advanced Options

### Check Intervals
Control how frequently products are checked:

```bash
# Check every 30-120 seconds
python scraper_cli.py monitor norman --min-interval 30 --max-interval 120
```

### Price Drop Threshold
Set the minimum price drop percentage to trigger alerts:

```bash
# Only alert for drops of 15% or more
python scraper_cli.py monitor norman --price-threshold 15.0
```

### Email Recipients
Send notifications to specific email addresses:

```bash
# Single recipient
python scraper_cli.py monitor norman --email-recipients "user@example.com"

# Multiple recipients
python scraper_cli.py monitor norman --email-recipients "user1@example.com,user2@example.com"
```

### Auto-Refresh for New Products
Automatically run full scrapes to discover new products:

```bash
# Refresh every 6 hours to find new products
python scraper_cli.py monitor norman --auto-refresh-hours 6

# Refresh every 30 minutes (useful for testing)
python scraper_cli.py monitor norman --auto-refresh-hours 0.5
```

**Note:** When auto-refresh is enabled, the monitoring will periodically pause to run a full scrape of the site. This discovers new products that weren't in the database when monitoring started.

## Complete Example

```bash
# Monitor Norman Walsh with custom settings:
# - Check every 1-3 minutes
# - Alert on 5% price drops  
# - Send emails to two addresses
# - Refresh for new products every 4 hours
python scraper_cli.py monitor norman 
  --min-interval 60 
  --max-interval 180 
  --price-threshold 5.0 
  --email-recipients "deals@example.com,alerts@example.com" 
  --auto-refresh-hours 4
```

## Email Notifications

When a price drop is detected, you'll receive a rich HTML email containing:

- Product name and image
- Old vs new price with percentage savings
- Product description
- Direct link to the product

## Configuration

The monitoring system uses settings from `monitor_config.json` for email configuration:

```json
{
  "email": {
    "from": "price-tracker@example.com",
    "method": "sendmail"
  },
  "intervals": {
    "default_min": 60,
    "default_max": 300
  }
}
```

## Tips

1. **Start with a full scrape**: Always run `python scraper_cli.py run <site>` before monitoring
2. **Test email delivery**: Use `python test_email.py` to verify email notifications work
3. **Use reasonable intervals**: Too frequent checking may trigger rate limiting
4. **Monitor during business hours**: Price changes are more common during active shopping periods
5. **Set appropriate thresholds**: Lower thresholds generate more alerts but may include minor fluctuations
6. **Use auto-refresh for dynamic sites**: Sites that frequently add new products benefit from regular refresh

## Troubleshooting

- **No products to monitor**: Run a full scrape first to populate the database
- **Email not working**: Check system mail configuration and test with `test_email.py`
- **High resource usage**: Increase intervals or reduce auto-refresh frequency
- **Missing new products**: Enable auto-refresh or run manual scrapes periodically

# Monitor with custom intervals (10-30 seconds) and 5% threshold
python scraper_cli.py monitor norman --min-interval 10 --max-interval 30 --price-threshold 5.0

# Monitor with custom email recipients
python scraper_cli.py monitor norman --email-recipients "user1@email.com,user2@email.com"
```

### Command Options
- `--min-interval`: Minimum seconds between checks (default: 60)
- `--max-interval`: Maximum seconds between checks (default: 300)  
- `--price-threshold`: Minimum price drop percentage to trigger email (default: 10.0%)
- `--email-recipients`: Comma-separated email addresses for notifications

### Prerequisites
1. **Database with products**: Run a full scrape first
   ```bash
   python scraper_cli.py run norman
   ```

2. **Email system**: Make sure your system can send emails via `sendmail` or `mail` command

## Example Output

```
✓ Found 115 products to monitor
🔄 Starting continuous monitoring for normanwalsh.com
   Check interval: 60-300 seconds
   Price drop threshold: 10.0%
   Press Ctrl+C to stop monitoring

🔍 Checking: /products/esl20119
✓ Connected to https://normanwalsh.com/products/esl20119
💰 Price stable: Ensign Lite - Grey & Dark Grey: £105.00
   ✓ Checked 1 products
😴 Sleeping for 127 seconds...

🔍 Checking: /products/horwich-navy-suede
✓ Connected to https://normanwalsh.com/products/horwich-navy-suede
🔥 PRICE DROP! Horwich Navy Suede: £160.00 → £120.00 (25.0% off)
📧 Rich HTML email notification sent successfully!
   ✓ Checked 1 products
😴 Sleeping for 89 seconds...
```

## Email Notification Features

### HTML Email Format
- Product name and pricing details
- Percentage savings calculation
- Product images (when available)
- Store name and direct link to product
- Rich formatting with colors and styling

### Email Content Example
```
Subject: 🔥 Price Drop! Horwich Navy Suede now £120 (was £160)

🔥 Price Drop Alert! 📉
[Product Image]
Horwich Navy Suede

💰 Old price: £160
🎯 New price: £120
📊 Savings: £40 (25.0% off!)
🛒 Store: normanwalsh.com

[Product Description]
[View Product Button]
```

## Monitoring Statistics

The system tracks:
- Total checks performed
- Price drops found
- Success rate
- Average checks per hour

Periodic stats are shown every 10 checks:
```
📊 Monitoring stats:
   Total checks: 10
   Price drops found: 2
   Success rate: 100.0%
```

## Technical Implementation

### Random Selection Strategy
- Selects random product URLs from database
- Avoids predictable patterns that might trigger anti-bot measures
- Spreads load across different products

### Error Handling
- Graceful handling of network timeouts
- Continues monitoring even if individual checks fail
- Logs errors but doesn't stop the monitoring process

### Database Updates
- Updates prices when changes detected
- Maintains price history for trend analysis
- Only triggers emails for significant drops (configurable threshold)

## Integration with Existing Workflow

1. **Initial Setup**: Run full scrape to populate database
2. **Start Monitoring**: Use monitor command for continuous checking
3. **Price Alerts**: Receive emails for significant price drops
4. **Manual Checks**: Use stats command to see monitoring results

## Stopping Monitoring

Press `Ctrl+C` to gracefully stop monitoring. The system will show final statistics:

```
🛑 Monitoring stopped by user
📊 Final stats:
   Total checks performed: 45
   Price drops found: 3
   Average checks per hour: 12.5
```

## Configuration Files

### monitor_config.json (optional)
```json
{
  "monitoring": {
    "email_recipients": ["uksquire@icloud.com"],
    "default_intervals": {
      "min_interval": 60,
      "max_interval": 300
    },
    "default_price_threshold": 10.0,
    "sendmail_path": "/usr/sbin/sendmail"
  }
}
```

This feature provides all the monitoring capabilities from your original Argos script but in a more flexible, configurable way that works with any site in your scraper configuration.
