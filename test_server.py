import requests
import time

time.sleep(3)

# Try port 10000
try:
    r = requests.get('http://localhost:10000/status', timeout=5)
    print(f"✓ Server running on port 10000")
    print(f"Status: {r.status_code}")
    print(r.json())
except Exception as e:
    print(f"Port 10000 not responding: {e}")
    
    # Try port 8001
    try:
        r = requests.get('http://localhost:8001/status', timeout=5)
        print(f"\n✓ Server running on port 8001")
        print(f"Status: {r.status_code}")
        print(r.json())
    except Exception as e2:
        print(f"Port 8001 not responding: {e2}")
        print("\n✗ No server detected on any port!")
