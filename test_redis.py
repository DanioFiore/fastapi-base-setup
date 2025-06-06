#!/usr/bin/env python3
"""
Script to test Redis connection, operations, and rate limiting.
"""

import redis
import requests
import time
from typing import Optional
from src.core.config import settings

API_URL = f"http://localhost:{settings.APP_PORT}"
REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_PASSWORD = settings.REDIS_PASSWORD
REDIS_DB = settings.REDIS_DB

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
            socket_connect_timeout=2
        )
        client.ping()
        print("✅ Redis connection successful (Docker)")
        return client
    except Exception as e:
        print(f"❌ Docker Redis connection failed: {e}")
        
    try:
        # Try with localhost
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2
        )
        client.ping()
        print("✅ Redis connection successful (localhost)")
        return client
    except Exception as e:
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
            print(f"❌ SET/GET failed: expected '{test_value}', got '{retrieved_value}'")
        
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
        
    except Exception as e:
        print(f"❌ Redis operations failed: {e}")

def test_rate_limiting_keys(client: redis.Redis):
    """
    Test rate limiting keys.
    
    Args:
        client: Client Redis
    """
    print("\n🚫 Testing Rate Limiting Keys...")
    
    try:
        # search rate limiting keys
        rate_limit_keys = client.keys("rate_limit:*")
        print(f"Found {len(rate_limit_keys)} rate limiting keys:")
        
        for key in rate_limit_keys[:5]:  # show only the first 5
            value = client.get(key)
            ttl = client.ttl(key)
            print(f"  {key}: {value} (TTL: {ttl}s)")
        
        if len(rate_limit_keys) > 5:
            print(f"  ... and {len(rate_limit_keys) - 5} more keys")
            
    except Exception as e:
        print(f"❌ Rate limiting keys check failed: {e}")

def test_api_rate_limiting():
    """
    Test rate limiting for api call.
    """
    print("\n🚀 Testing API Rate Limiting...")
    
    success_count = 0
    rate_limited_count = 0
    
    print("Making 70 requests to trigger rate limiting...")
    
    for i in range(70):
        try:
            response = requests.get(f"{API_URL}/healthz", timeout=5)
            
            if response.status_code == 200:
                success_count += 1
                remaining = response.headers.get('X-RateLimit-Remaining-Minute', 'N/A')
                if i % 10 == 0 or int(remaining) < 10 if remaining != 'N/A' else False:
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
    
    print(f"\nResults:")
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
        info = client.info()
        
        print(f"Redis version: {info.get('redis_version', 'N/A')}")
        print(f"Connected clients: {info.get('connected_clients', 'N/A')}")
        print(f"Used memory: {info.get('used_memory_human', 'N/A')}")
        print(f"Total keys: {info.get('db0', {}).get('keys', 0) if 'db0' in info else 0}")
        
        # Statistiche sui comandi
        commands_processed = info.get('total_commands_processed', 0)
        print(f"Total commands processed: {commands_processed}")
        
    except Exception as e:
        print(f"❌ Redis monitoring failed: {e}")

def main():

    print("🧪 Redis Test Suite")
    print("=" * 50)
    
    redis_client = test_redis_connection()
    
    if redis_client:
        test_redis_operations(redis_client)
        
        test_rate_limiting_keys(redis_client)
        
        test_redis_monitoring(redis_client)
    else:
        print("\n⚠️  Skipping Redis-specific tests due to connection failure")
    
    # Test rate limiting via API (works even without Redis)
    test_api_rate_limiting()
    
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