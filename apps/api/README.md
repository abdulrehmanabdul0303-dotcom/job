# JobPilot AI - Backend API

FastAPI backend for JobPilot AI platform.

## Features

- ✅ JWT Authentication (access + refresh tokens)
- ✅ Async PostgreSQL with SQLAlchemy
- ✅ Redis integration
- ✅ Alembic migrations
- ✅ Comprehensive testing with pytest
- ✅ Rate limiting
- ✅ Audit logging
- ✅ OpenAPI documentation

## Development

### Setup

```bash
# Install dependencies
pip install -e .
pip install -e ".[dev]"

# Set environment variables
cp ../../.env.example ../../.env
# Edit .env with your settings
```

### Run Locally

```bash
# Start database and Redis
docker compose -f ../../infra/docker-compose.yml up postgres redis -d

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View history
alembic history
```

## API Endpoints

### Health
- `GET /health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health with dependencies

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout (invalidate refresh token)

## Project Structure

```
app/
├── api/v1/          # API endpoints
│   ├── auth.py      # Authentication routes
│   ├── health.py    # Health check routes
│   └── router.py    # Main router
├── core/            # Core functionality
│   ├── config.py    # Configuration
│   ├── database.py  # Database connection
│   └── security.py  # Security utilities
├── models/          # SQLAlchemy models
│   └── user.py      # User models
├── schemas/         # Pydantic schemas
│   └── auth.py      # Auth schemas
├── services/        # Business logic
│   └── auth.py      # Auth service
└── main.py          # FastAPI app
```

## Environment Variables

```bash
# API
API_PORT=8000
JWT_SECRET=your-secret-key
JWT_ACCESS_TTL_MIN=15
JWT_REFRESH_TTL_DAYS=7

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/jobpilot

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Security

- Passwords hashed with bcrypt
- JWT tokens with expiration
- Rate limiting on auth endpoints
- Audit logging for security events
- SQL injection protection via SQLAlchemy
- Input validation via Pydantic
