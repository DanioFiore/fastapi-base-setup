# JWT Authentication Guide - Money Wizardry
This guide explains how to implement and use JWT authentication in the Money Wizardry project.
## 📋 Table of Contents
1. [Overview](#overview)
2. [Configuration](#configuration)
3. [Available Endpoints](#available-endpoints)
4. [How to Use Authentication](#how-to-use-authentication)
5. [Testing](#testing)
6. [Practical Examples](#practical-examples)
7. [Security](#security)
8. [Troubleshooting](#troubleshooting)
## 🔍 Overview
The implemented JWT (JSON Web Token) authentication system provides:
- **Access Token**: Short-lived token for accessing protected APIs
- **Refresh Token**: Long-lived token for renewing the access token
- **Stateless Authentication**: No server-side sessions
- **Security**: Password hashing with bcrypt
- **Rate Limiting Middleware**: Protection against brute force attacks
- **Security**: Password hashing with bcrypt
- **Rate Limiting Middleware**: Protection against brute force attacks

### Authentication Flow

```
1. User → POST /api/auth/login (email + password)
2. Server → Verify credentials
3. Server → Generate Access Token + Refresh Token
4. Client → Store tokens
5. Client → Use Access Token for protected requests
6. When Access Token expires → Use Refresh Token to obtain a new one
```

## ⚙️ Configuration

### Environment Variables

Make sure your `.env` file contains:

```env
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Security
PASSWORD_MIN_LENGTH=8
PASSWORD_SPECIAL_CHARS=!@#$%^&*()_+-=[]{}|;:,.<>?
```

### Required Dependencies

The system uses the following libraries (already included in `requirements.txt`):

```
python-jose[cryptography]  # Per JWT
passlib[bcrypt]           # Per hash delle password
fastapi                   # Framework web
sqlmodel                  # ORM
```

## 🛠️ Available Endpoints

### 1. Login
**POST** `/api/auth/login`

```json
// Request
{
  "email": "user@example.com",
  "password": "password123"
}

// Response
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1N...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1N...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "testuser",
      "email": "user@example.com",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

### 2. Refresh Token
**POST** `/api/auth/refresh`

```json
// Request
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1N..."
}

// Response
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1N...",
    "token_type": "bearer"
  }
}
```

### 3. Current user info
**GET** `/api/auth/me`

```bash
# Headers mandatory
Authorization: Bearer <access_token>
```

```json
// Response
{
  "success": true,
  "data": {
    "id": 1,
    "username": "testuser",
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 4. Logout
**POST** `/api/auth/logout`

```bash
# Headers mandatory
Authorization: Bearer <access_token>
```

```json
// Response
{
  "success": true,
  "data": {
    "message": "Successfully logged out"
  }
}
```

## 🔐 How to Use Authentication

### 1. Protecting an Endpoint

```python
from fastapi import APIRouter, Depends
from api.auth import get_current_user
from api.users.models import User

router = APIRouter()

@router.get("/protected-endpoint")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}!"}
```

### 2. Optional Authentication

```python
from api.auth import get_current_user_optional
from typing import Optional

@router.get("/optional-auth")
def optional_auth_route(current_user: Optional[User] = Depends(get_current_user_optional)):
    if current_user:
        return {"message": f"Hello {current_user.username}!"}
    else:
        return {"message": "Hello anonymous user!"}
```

### 3. Client-Side (JavaScript)

```javascript
class AuthClient {
    constructor(baseUrl = 'http://localhost:8081') {
        this.baseUrl = baseUrl;
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    }

    async login(email, password) {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.data.access_token;
            this.refreshToken = data.data.refresh_token;
            
            localStorage.setItem('access_token', this.accessToken);
            localStorage.setItem('refresh_token', this.refreshToken);
            
            return data.data.user;
        } else {
            throw new Error('Login failed');
        }
    }

    async makeAuthenticatedRequest(url, options = {}) {
        const headers = {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        let response = await fetch(url, {
            ...options,
            headers
        });

        // Se il token è scaduto, prova a rinnovarlo
        if (response.status === 401) {
            await this.refreshAccessToken();
            
            // Riprova la richiesta con il nuovo token
            headers['Authorization'] = `Bearer ${this.accessToken}`;
            response = await fetch(url, {
                ...options,
                headers
            });
        }

        return response;
    }

    async refreshAccessToken() {
        const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: this.refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.data.access_token;
            localStorage.setItem('access_token', this.accessToken);
        } else {
            // Refresh token scaduto, reindirizza al login
            this.logout();
            window.location.href = '/login';
        }
    }

    logout() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }
}

// Using the client
const auth = new AuthClient();

// Login
try {
    const user = await auth.login('user@example.com', 'password123');
    console.log('Logged in as:', user.username);
} catch (error) {
    console.error('Login failed:', error);
}

// Authenticated request
const response = await auth.makeAuthenticatedRequest('/api/auth/me');
const userData = await response.json();
```

## 🧪 Testing


### 1. Test Manuale con curl

```bash
# 1. Create a user
curl -X POST "http://localhost:8081/api/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "confirm_password": "TestPass123!"
  }'

# 2. Login
curl -X POST "http://localhost:8081/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# 3. Use the token to have access to protected routes
curl -X GET "http://localhost:8081/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# 4. Refresh token
curl -X POST "http://localhost:8081/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

## 🔒 Security

### Implemented Best Practices

1. **Password Hashing**: Using bcrypt with automatic salt
2. **Token Expiration**: Short-lived access token (30 min)
3. **Refresh Token**: Separate token for renewal
4. **Rate Limiting**: Protection against brute force attacks
5. **HTTPS**: Recommended for production
6. **Input Validation**: Email and password checks

### Security Configurations

```python
# password needs (.env)
PASSWORD_MIN_LENGTH = 8
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

# Automatic validations:
# - At least one uppercase letter
# - At least one lowercase letter
# - At least one number 
# - At least one special character
```

### Production Recommendations

1. **Use HTTPS**: Never send tokens over HTTP
2. **Secure Storage**: Store tokens in httpOnly cookies or secure storage
3. **Token Blacklist**: Implement blacklist for secure logout
4. **Monitoring**: Log failed login attempts
5. **Backup Keys**: Maintain backups of JWT keys

## 🔧 Troubleshooting

### Errori Comuni

#### 1. "Could not validate credentials"
```
Cause: Invalid or expired JWT token
Solution:
- Verify that the token is correct
- Check if it has expired  
- Use refresh token to obtain a new one
```

#### 2. "Incorrect email or password"
```
Cause: Invalid login credentials
Solution:
- Verify email and password
- Check if user exists in database
- Verify user is active (is_active=True)
```

#### 3. "Invalid refresh token"
```
Cause: Expired or invalid refresh token
Solution:
- User needs to login again
- Check JWT_REFRESH_TOKEN_EXPIRE_DAYS configuration
```

#### 4. "User not found"
```
Cause: User in token no longer exists in database
Solution:
- Verify that the user has not been deleted
- Log out and log in again
```

### Debug

```python
# add logging for debug
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# in the authentication code
logger.debug(f"Token payload: {payload}")
logger.debug(f"User ID from token: {user_id}")
```

### Check Configuration

```python
# Script to check configuration
from core.config import get_settings

settings = get_settings()
print(f"JWT Algorithm: {settings.JWT_ALGORITHM}")
print(f"Access Token Expire: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
print(f"Refresh Token Expire: {settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS} days")
print(f"Secret Key Length: {len(settings.JWT_SECRET_KEY)} characters")
```