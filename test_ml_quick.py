import requests
import time

print("Testing ml-explain endpoint...")
start = time.time()
try:
    r = requests.get('http://localhost:8000/api/ml-explain/20000433', timeout=30)
    elapsed = time.time() - start
    print(f'Status: {r.status_code}')
    print(f'Time: {elapsed:.2f}s')
    if r.status_code == 200:
        print('SUCCESS!')
    else:
        print(f'Response: {r.text[:300]}')
except requests.exceptions.Timeout:
    print('TIMEOUT after 30 seconds')
except Exception as e:
    print(f'ERROR: {e}')
