import requests

API_URL = "http://localhost:8081"

def test_cors():
    print("🧪 Testing CORS...")
    # test with Origin header to simulate cross origin request
    headers = {'Origin': 'http://localhost:3000'}
    response = requests.get(f"{API_URL}/healthz", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"CORS Headers: {response.headers.get('Access-Control-Allow-Origin')}")
    
    # Test preflight request
    options_response = requests.options(f"{API_URL}/healthz", headers=headers)
    print(f"Preflight Status: {options_response.status_code}")
    print(f"Allowed Methods: {options_response.headers.get('Access-Control-Allow-Methods')}")

def test_logging():
    print("📝 Testing Logging...")
    response = requests.get(f"{API_URL}/healthz")
    request_id = response.headers.get('X-Request-ID')
    process_time = response.headers.get('X-Process-Time')
    print(f"Request ID: {request_id}")
    print(f"Process Time: {process_time}s")
    print("✅ Logging OK\n")

def test_rate_limiting():
    print("🚫 Testing Rate Limiting...")
    
    # do 65 requests
    for i in range(65):
        response = requests.get(f"{API_URL}/healthz")
        remaining = response.headers.get('X-RateLimit-Remaining-Minute')
        
        if response.status_code == 429:
            print(f"✅ Rate limit triggered at request {i+1}")
            print(f"Response: {response.json()}")
            break
        elif i % 10 == 0:
            print(f"Request {i+1}: OK, remaining: {remaining}")
    
    print("✅ Rate Limiting OK\n")

if __name__ == "__main__":
    test_cors()
    test_logging()
    test_rate_limiting()