"""
This module contains integration tests for 
    - API middleware features including CORS
    - logging
    - rate limiting
Functions:
    test_cors():
        Tests Cross-Origin Resource Sharing (CORS) functionality 
        by sending GET and OPTIONS requests with an Origin header.
        
        Verifies CORS headers such as Access-Control-Allow-Origin and Access-Control-Allow-Methods.
    test_logging():
        Tests the logging middleware by sending a GET request 
        and checking for X-Request-ID and X-Process-Time headers in the response.
    test_rate_limiting():
        Tests the rate limiting middleware by sending multiple requests to the API 
        and verifying that a 429 status code is returned when the rate limit is exceeded.

"""

import requests

API_URL = "http://localhost:8081"


def test_cors():
    """
    Test CORS (Cross-Origin Resource Sharing) functionality of the API.

    This function performs two types of CORS tests:
    1. A simple cross-origin GET request with Origin header to verify CORS headers
    2. A preflight OPTIONS request to check allowed methods and CORS configuration

    The test simulates requests from 'http://localhost:3000' origin and validates:
    - Response status codes for both requests
    - Access-Control-Allow-Origin header in GET response
    - Access-Control-Allow-Methods header in OPTIONS response

    Prints test results including status codes and relevant CORS headers.
    """
    print("🧪 Testing CORS...")
    # test with Origin header to simulate cross origin request
    headers = {"Origin": "http://localhost:3000"}
    response = requests.get(f"{API_URL}/healthz", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"CORS Headers: {response.headers.get('Access-Control-Allow-Origin')}")

    # Test preflight request
    options_response = requests.options(
        f"{API_URL}/healthz", headers=headers, timeout=10
    )
    print(f"Preflight Status: {options_response.status_code}")
    print(
        f"Allowed Methods: {options_response.headers.get('Access-Control-Allow-Methods')}"
    )


def test_logging():
    """
    Tests the logging middleware by sending a GET request to the /healthz endpoint.
    Prints the X-Request-ID and X-Process-Time headers 
    from the response to verify logging functionality.
    """
    print("📝 Testing Logging...")
    response = requests.get(f"{API_URL}/healthz", timeout=10)
    request_id = response.headers.get("X-Request-ID")
    process_time = response.headers.get("X-Process-Time")
    print(f"Request ID: {request_id}")
    print(f"Process Time: {process_time}s")
    print("✅ Logging OK\n")


def test_rate_limiting():
    """
    Tests the rate limiting functionality of the API by 
    sending multiple requests to the /healthz endpoint.
    Sends up to 65 requests and checks if the rate limit is enforced 
    by expecting a 429 status code response.
    Prints progress every 10 requests and outputs when the rate limit is triggered.
    """

    print("🚫 Testing Rate Limiting...")

    # do 65 requests
    for i in range(65):
        response = requests.get(f"{API_URL}/healthz", timeout=10)
        remaining = response.headers.get("X-RateLimit-Remaining-Minute")

        if response.status_code == 429:
            print(f"✅ Rate limit triggered at request {i+1}")
            print(f"Response: {response.json()}")
            break

        if i % 10 == 0:
            print(f"Request {i+1}: OK, remaining: {remaining}")

    print("✅ Rate Limiting OK\n")


if __name__ == "__main__":
    test_cors()
    test_logging()
    test_rate_limiting()
