# FastAPI Base Setup

A comprehensive FastAPI base setup with authentication, database integration, middleware, and containerization.

## 🚀 Features

### Core Features
- **FastAPI Framework**: High-performance, modern Python web framework
- **JWT Authentication**: Secure token-based authentication with access and refresh tokens
- **Database Integration**: PostgreSQL with SQLModel/SQLAlchemy ORM
- **Redis Caching**: Redis integration for caching and session management
- **Database Migrations**: Alembic for database schema versioning
- **Docker Support**: Full containerization with Docker Compose
- **Environment-based Configuration**: Flexible settings management

### Middleware & Security
- **CORS Middleware**: Cross-origin resource sharing configuration
- **Rate Limiting**: Redis-backed rate limiting for API protection
- **Request Logging**: Comprehensive request/response logging
- **Password Security**: Bcrypt hashing with configurable requirements
- **Environment-specific Middleware**: Different configurations for dev/staging/prod

### Development Tools
- **Auto-formatting**: Black code formatter integration
- **API Documentation**: Automatic OpenAPI/Swagger documentation
- **Development Scripts**: Convenient run scripts for local development

## 📁 Project Structure

```
fastapi-base-setup/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── auth/              # Authentication endpoints
│   │   └── users/             # User management endpoints
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   ├── security.py        # JWT and security utilities
│   │   └── utility/           # Common utilities
│   ├── db/
│   │   ├── config.py          # Database configuration
│   │   └── session.py         # Database session management
│   └── middleware/
│       ├── cors.py            # CORS middleware
│       ├── logging.py         # Logging middleware
│       ├── rate_limiting.py   # Rate limiting middleware
│       └── setup.py           # Middleware orchestration
├── alembic/                   # Database migrations
├── docker-compose.yaml        # Docker services configuration
├── Dockerfile                 # Application container
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── run.sh                    # Development script
```

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (if running locally)
- Redis (if running locally)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fastapi-base-setup

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
vim .env
```

### 2. Environment Configuration

Update your `.env` file with appropriate values:

```env
# Application
APP_NAME=FastAPI Base Setup
APP_VERSION=0.1.0
APP_ENV=dev
APP_PORT=8081

# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@db_postgres:5432/postgres

# Redis
REDIS_URL=redis://redis:6379

# JWT Security
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
```

### 3. Running with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Access the application
open http://localhost:8081
```

### 4. Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn src.main:app --host 0.0.0.0 --port 8081 --reload
```

### 5. Using the Convenience Script

```bash
# Make script executable
chmod +x run.sh

# Start development environment
./run.sh

# Or with specific options
./run.sh --build  # Rebuild containers
./run.sh --logs   # Show logs
```

## 🔐 Authentication System

The project includes a complete JWT authentication system:

### Available Endpoints

- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update user profile

### Usage Example

```python
# Login
response = requests.post(
    "http://localhost:8081/api/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
tokens = response.json()

# Use access token for protected endpoints
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
profile = requests.get(
    "http://localhost:8081/api/users/me",
    headers=headers
)
```

For detailed authentication documentation, see [JWT_AUTH_GUIDE.md](JWT_AUTH_GUIDE.md).

## 🗄️ Database Management

### Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

### Database Access

- **PostgreSQL**: `localhost:5432` (postgres/postgres)
- **pgAdmin**: `http://localhost:5050` (admin@example.com/admin)

## 🔧 Configuration

### Environment-based Settings

The application supports different configurations based on `APP_ENV`:

- **dev**: Development mode with permissive CORS and detailed logging
- **staging**: Staging environment with moderate security
- **prod**: Production mode with strict security and minimal logging


## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8081/docs`
- **ReDoc**: `http://localhost:8081/redoc`
- **OpenAPI JSON**: `http://localhost:8081/openapi.json`

## 🧪 Testing

### Health Check

```bash
curl http://localhost:8081/healthz
# Response: {"status": "ok"}
```

### Authentication Flow Test

```bash
# Test login (replace with actual user credentials)
curl -X POST "http://localhost:8081/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Test protected endpoint
curl -X GET "http://localhost:8081/api/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🐳 Docker Services

The Docker Compose setup includes:

- **app**: Main FastAPI application
- **db_postgres**: PostgreSQL database
- **redis**: Redis cache/session store
- **pgadmin**: Database administration interface

### Service Management

```bash
# Start specific service
docker-compose up -d db_postgres

# View service logs
docker-compose logs -f app

# Restart service
docker-compose restart app

# Stop all services
docker-compose down
```

## 🔒 Security Features

- **JWT Tokens**: Secure, stateless authentication
- **Password Hashing**: Bcrypt with configurable rounds
- **Rate Limiting**: Redis-backed request throttling
- **CORS Protection**: Configurable cross-origin policies
- **Environment Isolation**: Separate configs for different environments
- **Input Validation**: Pydantic models for request/response validation

## 🚀 Deployment

### Production Deployment

1. Set `APP_ENV=prod` in your environment
2. Use strong `JWT_SECRET_KEY`
3. Configure production database and Redis instances
4. Set up reverse proxy (nginx/traefik)
5. Enable HTTPS
6. Configure monitoring and logging

### Environment Variables for Production

```env
APP_ENV=prod
APP_DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-db:5432/dbname
REDIS_URL=redis://prod-redis:6379
JWT_SECRET_KEY=your-production-secret-key
CORS_ORIGINS=https://yourdomain.com
```

## 🛠️ Development

### Code Formatting

```bash
# Format code with Black
black .

# Check formatting
black --check .
```

### Adding New Features

1. Create new API modules in `src/api/`
2. Add database models in appropriate modules
3. Create Alembic migrations for schema changes
4. Update middleware configuration if needed
5. Add tests for new functionality

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and formatting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.