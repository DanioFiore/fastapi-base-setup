# Middleware Documentation

This folder contains custom middleware components for the FastAPI application. Each middleware serves a specific purpose in enhancing security, monitoring, and functionality.

## Overview

The middleware stack includes:

- **CORS Middleware** (`cors.py`) - Handles Cross-Origin Resource Sharing
- **Logging Middleware** (`logging.py`) - Request/response logging and monitoring
- **Rate Limiting Middleware** (`rate_limiting.py`) - API rate limiting and abuse prevention
- **Setup Module** (`setup.py`) - Centralized middleware configuration

## Quick Start

The middleware is automatically configured in `main.py` based on your environment:

```python
from middleware.setup import setup_middleware

# This is already done in main.py
setup_middleware(app)
```

## CORS Middleware

### Purpose
Handles Cross-Origin Resource Sharing (CORS) to allow web applications from different origins to access your API.

### Configuration
Configure CORS settings in your `.env` file:

```env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS
CORS_ALLOW_HEADERS=*
CORS_EXPOSE_HEADERS=X-Total-Count,X-Page-Count
CORS_MAX_AGE=86400
```

### Usage Examples

```python
from middleware.cors import add_cors_middleware, configure_cors_for_development

# Basic setup
add_cors_middleware(app)

# Development setup (more permissive)
configure_cors_for_development(app)

# Production setup (strict)
configure_cors_for_production(app)
```

## Logging Middleware

### Purpose
Provides comprehensive request/response logging, performance monitoring, and error tracking.

### Features
- Unique request ID generation
- Request/response timing
- Error logging and tracking
- User action auditing
- Configurable log levels

### Configuration
```env
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

### Usage Examples

```python
from middleware.logging import get_request_logger, log_user_action

# In your route handlers
@app.post("/api/users/")
async def create_user(request: Request, user_data: UserCreate):
    logger = get_request_logger(request)
    logger.info("Creating new user")
    
    # ... create user logic ...
    
    log_user_action(request, "user_created", {"user_id": new_user.id})
    return new_user
```

### Log Format
```
2024-01-15 10:30:45 - Request abc123 started | Method: POST | URL: /api/users/ | Client IP: 192.168.1.1
2024-01-15 10:30:45 - Request abc123 completed | Status: 201 | Process time: 0.1234s
```

## Rate Limiting Middleware

### Purpose
Protects your API from abuse by limiting the number of requests per client within specified time windows.

### Features
- Redis-based distributed rate limiting
- Per-IP and per-user limits
- Endpoint-specific rate limits
- Token bucket algorithm
- Rate limit headers in responses

### Configuration
```env
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
```

### Default Rate Limits

| Endpoint | Per Minute | Per Hour |
|----------|------------|----------|
| `/api/auth/login` | 5 | 20 |
| `/api/auth/register` | 3 | 10 |
| `/api/auth/forgot-password` | 2 | 5 |
| `/api/users/` | 30 | 1000 |
| Default | 60 | 1000 |

### Customizing Rate Limits

```python
from middleware.rate_limiting import RateLimitMiddleware

# Custom rate limits
custom_limits = {
    "/api/payments/": {"requests_per_minute": 10, "requests_per_hour": 100},
    "/api/reports/": {"requests_per_minute": 5, "requests_per_hour": 50},
}

# Apply to middleware (modify rate_limiting.py)
middleware = RateLimitMiddleware(app)
middleware.endpoint_limits.update(custom_limits)
```

### Rate Limit Headers

The middleware adds these headers to responses:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Reset-Minute: 1642248000
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 950
X-RateLimit-Reset-Hour: 1642251600
Retry-After: 15
```

### Rate Limit Response

When rate limit is exceeded:

```json
{
  "detail": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 15
}
```

## Environment-Specific Setup

### Development
- Permissive CORS (allows all origins)
- Detailed logging
- Rate limiting disabled or in-memory

### Staging
- Moderate CORS settings
- Full logging
- Redis-based rate limiting

### Production
- Strict CORS (specific origins only)
- Optimized logging
- Full Redis-based rate limiting
- Enhanced security headers

## Dependencies

Make sure these packages are installed:

```bash
pip install redis fastapi
```

## Redis Setup

For rate limiting to work properly, you need Redis running:

```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu
```

## Monitoring and Debugging

### Check Middleware Status

```python
# Add this endpoint to check middleware status
@app.get("/middleware/status")
async def middleware_status():
    return {
        "cors": "enabled",
        "logging": "enabled",
        "rate_limiting": "enabled" if redis_client else "disabled",
        "environment": settings.APP_ENV
    }
```

### Log Analysis

```bash
# View recent logs
tail -f app.log

# Filter by request ID
grep "abc123" app.log

# Monitor rate limiting
grep "Rate limit" app.log
```

### Redis Monitoring

```bash
# Connect to Redis CLI
redis-cli

# View rate limit keys
KEYS rate_limit:*

# Check specific rate limit
GET rate_limit:ip:192.168.1.1:/api/users/:minute:1642248
```

## Troubleshooting

### Common Issues

1. **CORS errors in browser**
   - Check `CORS_ORIGINS` in `.env`
   - Ensure your frontend URL is included
   - Verify `CORS_ALLOW_CREDENTIALS` setting

2. **Rate limiting not working**
   - Check Redis connection
   - Verify Redis credentials in `.env`
   - Check Redis logs for errors

3. **Missing logs**
   - Check `LOG_LEVEL` setting
   - Verify file permissions for log file
   - Ensure `LOG_TO_FILE` is enabled

4. **Performance issues**
   - Monitor Redis memory usage
   - Adjust log levels in production
   - Consider log rotation settings

### Debug Mode

Enable debug logging to see detailed middleware activity:

```env
LOG_LEVEL=DEBUG
```

This will show:
- Request headers and body
- Response headers
- Rate limiting decisions
- Redis operations

## Security Considerations

1. **Never log sensitive data**
   - Passwords are automatically filtered
   - Authorization headers are excluded
   - Consider custom filtering for sensitive fields

2. **Rate limiting bypass**
   - Monitor for unusual patterns
   - Consider IP whitelisting for trusted sources
   - Implement additional security layers

3. **Redis security**
   - Use Redis AUTH (password)
   - Restrict Redis network access
   - Consider Redis SSL/TLS in production

## Performance Tips

1. **Logging optimization**
   - Use appropriate log levels
   - Implement log rotation
   - Consider structured logging for analysis

2. **Rate limiting optimization**
   - Use Redis clustering for high traffic
   - Implement sliding window for smoother limits
   - Cache rate limit decisions

3. **CORS optimization**
   - Use specific origins instead of wildcards
   - Cache preflight responses
   - Minimize exposed headers