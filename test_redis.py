#!/usr/bin/env python3
"""
Script to test Redis connection, operations, and rate limiting.
"""

import time
import os
from typing import Any, Dict, List, Optional

import redis
import requests
from redis.exceptions import RedisError

from src.core.config import settings

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_PASSWORD = settings.REDIS_PASSWORD
REDIS_DB = settings.REDIS_DB

# Detect if we're running inside Docker container
if os.path.exists('/.dockerenv'):
    # Inside container - use internal endpoint
    API_URL = f"http://127.0.0.1:{settings.APP_PORT}"
    print("🐳 Running inside Docker container")
else:
    # Outside container - use external endpoint
    API_URL = f"http://localhost:{settings.APP_PORT}"
    print("💻 Running on host machine")


def test_redis_connection() -> Optional[redis.Redis]:
    """
    Test Redis connection

    Returns:
        Redis client if successful, None otherwise
    """
    print("🔌 Testing Redis Connection...")

    try:
        # First try with Docker
        client = redis.Redis(
            host="redis",
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        client.ping()
        print("✅ Redis connection successful (Docker)")
        return client
    except RedisError as e:
        print(f"❌ Docker Redis connection failed: {e}")

    try:
        # Try with localhost
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        client.ping()
        print("✅ Redis connection successful (localhost)")
        return client
    except RedisError as e:
        print(f"❌ Localhost Redis connection failed: {e}")
        return None


def test_redis_operations(client: redis.Redis):
    """
    Testing Redis operations.

    Args:
        client: Client Redis
    """
    print("\n🧪 Testing Redis Operations...")

    try:
        # Test SET/GET
        test_key = "test:redis:operations"
        test_value = "Hello Redis!"

        client.set(test_key, test_value, ex=60)  # expire after 60 seconds
        retrieved_value = client.get(test_key)

        if retrieved_value == test_value:
            print("✅ SET/GET operations working")
        else:
            print(
                f"❌ SET/GET failed: expected '{test_value}', got '{retrieved_value}'"
            )

        # Test INCR (used for rate limiting)
        counter_key = "test:counter"
        client.delete(counter_key)

        count1 = client.incr(counter_key)
        count2 = client.incr(counter_key)

        if count1 == 1 and count2 == 2:
            print("✅ INCR operations working")
        else:
            print(f"❌ INCR failed: got {count1}, {count2}")

        # Test EXPIRE
        client.expire(counter_key, 1)
        time.sleep(1.1)
        expired_value = client.get(counter_key)

        if expired_value is None:
            print("✅ EXPIRE operations working")
        else:
            print(f"❌ EXPIRE failed: key should be expired but got '{expired_value}'")

        # Cleanup
        client.delete(test_key, counter_key)
    except RedisError as e:
        print(f"❌ Redis operations failed: {e}")
    except (TypeError, ValueError) as e:
        print(f"❌ Redis operations data processing failed: {e}")


def test_rate_limiting_keys(client: redis.Redis):
    """
    Test rate limiting keys.

    Args:
        client: Client Redis
    """
    print("\n🚫 Testing Rate Limiting Keys...")

    try:
        # search rate limiting keys
        rate_limit_keys_response = client.keys("rate_limit:*")

        # Handle the response properly - cast to list to satisfy type checker
        # Redis keys() returns a list of bytes/strings depending on decode_responses
        keys_list: List[str] = []
        if rate_limit_keys_response:
            # Type ignore for redis response that can be complex
            keys_list = list(rate_limit_keys_response)  # type: ignore

        print(f"Found {len(keys_list)} rate limiting keys:")

        for key in keys_list[:5]:  # show only the first 5
            value = client.get(key)
            ttl = client.ttl(key)
            print(f"  {key}: {value} (TTL: {ttl}s)")

        if len(keys_list) > 5:
            print(f"  ... and {len(keys_list) - 5} more keys")

    except RedisError as e:
        print(f"❌ Rate limiting keys check failed: {e}")
    except (TypeError, ValueError) as e:
        print(f"❌ Rate limiting keys processing failed: {e}")


def test_api_rate_limiting():
    """
    Test rate limiting for api call.
    """
    print("\n🚀 Testing API Rate Limiting...")

    success_count = 0
    rate_limited_count = 0

    print("Making 40 requests to trigger rate limiting...")

    for i in range(40):
        try:
            response = requests.get(f"{API_URL}/healthz", timeout=5)

            if response.status_code == 200:
                success_count += 1
                remaining = response.headers.get("X-RateLimit-Remaining-Minute", "N/A")
                if i % 5 == 0 or int(remaining) < 5 if remaining != "N/A" else False:
                    print(f"  Request {i+1}: OK (remaining: {remaining})")
            elif response.status_code == 429:
                rate_limited_count += 1
                if rate_limited_count == 1:
                    print(f"  ✅ Rate limit triggered at request {i+1}")
                    print(f"  Response: {response.json()}")
                    print(f"  Headers: {dict(response.headers)}")
                    break
            else:
                print(f"  ❌ Unexpected status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request {i+1} failed: {e}")
            break

    print("\nResults:")
    print(f"  Successful requests: {success_count}")
    print(f"  Rate limited requests: {rate_limited_count}")

    if rate_limited_count > 0:
        print("  ✅ Rate limiting is working!")
    else:
        print("  ⚠️  Rate limiting might not be working or limit is very high")


def test_redis_monitoring(client: redis.Redis):
    """
    Show monitoring info.

    Args:
        client: Client Redis
    """
    print("\n📊 Redis Monitoring Info...")

    try:
        # Get Redis info - cast to dict for type checking
        info_response = client.info()
        info: Dict[str, Any] = dict(info_response)  # type: ignore

        print(f"Redis version: {info.get('redis_version', 'N/A')}")
        print(f"Connected clients: {info.get('connected_clients', 'N/A')}")
        print(f"Used memory: {info.get('used_memory_human', 'N/A')}")

        # Handle db0 info safely
        total_keys = 0
        if "db0" in info and isinstance(info["db0"], dict):
            total_keys = info["db0"].get("keys", 0)
        print(f"Total keys: {total_keys}")

        # Statistics on commands
        commands_processed = info.get("total_commands_processed", 0)
        print(f"Total commands processed: {commands_processed}")

    except RedisError as e:
        print(f"❌ Redis monitoring failed: {e}")
    except (TypeError, ValueError) as e:
        print(f"❌ Redis monitoring data processing failed: {e}")


def show_rate_limit_info():
    """
    Show current rate limit configuration and settings.
    """
    print("\n⚙️  Rate Limit Configuration...")
    
    try:
        from src.core.config import settings
        
        print(f"Rate limit per minute: {getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 'Not set')}")
        print(f"Rate limit per hour: {getattr(settings, 'RATE_LIMIT_REQUESTS_PER_HOUR', 'Not set')}")
        print(f"API URL for testing: {API_URL}")
        
    except ImportError as e:
        print(f"❌ Could not import settings: {e}")
    except Exception as e:
        print(f"❌ Error getting rate limit info: {e}")


def main():
    """
    Main function to run redis tests.
    """
    print("🧪 Redis Test Suite")
    print("=" * 50)

    # Show rate limit configuration first
    show_rate_limit_info()

    redis_client = test_redis_connection()

    if redis_client:
        test_redis_operations(redis_client)

        test_rate_limiting_keys(redis_client)

        test_redis_monitoring(redis_client)
    else:
        print("\n⚠️  Skipping Redis-specific tests due to connection failure")

    # Test rate limiting via API (works even without Redis)
    test_api_rate_limiting()

    # Show rate limit configuration
    show_rate_limit_info()

    print("\n" + "=" * 50)
    print("🏁 Test completed!")

    if not redis_client:
        print("\n💡 Tips:")
        print("   - Make sure Redis is running")
        print("   - Verify credentials in .env")
        print("   - If using Docker: docker-compose up -d")
        print("   - If using local Redis: brew services start redis")


if __name__ == "__main__":
    main()
