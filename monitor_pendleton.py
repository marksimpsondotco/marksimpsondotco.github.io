#!/usr/bin/env python3
"""
Simple Pendleton price monitoring script
Based on the working argos.py approach
"""

import subprocess
import time
import random
import signal
import sys

def signal_handler(sig, frame):
    print('\n💥 Monitoring stopped by user')
    sys.exit(0)

def monitor_pendleton():
    print("🎯 Starting Pendleton price monitoring...")
    print("   Press Ctrl+C to stop")
    
    check_count = 0
    
    try:
        while True:
            check_count += 1
            print(f"\n🔍 Check #{check_count} - Running Pendleton scraper...")
            
            # Run the pendleton scraper
            result = subprocess.run(['python3', 'pendleton.py'], 
                                 capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Scrape completed successfully")
                # Extract product count from output
                for line in result.stdout.split('\n'):
                    if 'Monitoring' in line and 'items in Pendleton' in line:
                        print(f"   {line}")
                    elif 'Total records processed:' in line:
                        print(f"   {line}")
            else:
                print(f"❌ Scrape failed: {result.stderr}")
            
            # Random delay between 5-15 minutes
            delay_minutes = random.randint(5, 15)
            delay_seconds = delay_minutes * 60
            print(f"😴 Sleeping for {delay_minutes} minutes...")
            time.sleep(delay_seconds)
            
    except KeyboardInterrupt:
        print(f"\n💥 Monitoring stopped by user after {check_count} checks")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    monitor_pendleton()
