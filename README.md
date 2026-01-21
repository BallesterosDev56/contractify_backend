# Contractify Backend

FastAPI Modular Monolith backend for contract generation, signing, and management.

## Architecture

This backend implements a **Modular Monolith** architecture where each domain is isolated into its own module, but runs in a single process. This allows for:

- Single deployment on Render Free Tier
- Easy refactoring to microservices in the future
- Clear domain boundaries
- No cross-module dependencies

### Modules

| Module | Endpoints | Description |
|--------|-----------|-------------|
| users | 6 | User management and sessions |
| contracts | 19 | Contract lifecycle management |
| templates | 4 | Contract templates and types |
| ai | 4 | AI-powered generation |
| documents | 4 | PDF generation and download |
| signatures | 7 | Digital signature workflows |
| notifications | 5 | Email and reminders |
| audit | 2 | Audit trail and compliance |

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Firebase project (for authentication)

### Installation

```bash
# Clone and navigate to backend
cd contractify_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Database Setup

```bash
# Create PostgreSQL database
createdb contractify

# Create schemas (run in psql)
psql -d contractify -c "CREATE SCHEMA IF NOT EXISTS users;"
psql -d contractify -c "CREATE SCHEMA IF NOT EXISTS contracts;"
psql -d contractify -c "CREATE SCHEMA IF NOT EXISTS ai;"
psql -d contractify -c "CREATE SCHEMA IF NOT EXISTS signatures;"
psql -d contractify -c "CREATE SCHEMA IF NOT EXISTS notifications;"
psql -d contractify -c "CREATE SCHEMA IF NOT EXISTS audit;"
```

### Environment Variables

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contractify

# Firebase (optional for development)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789

# API Settings
API_PREFIX=/api
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=true
```

### Run the Server

```bash
# Development with hot reload
uvicorn app.main:app --reload --port 3000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

The API will be available at:
- API Base: http://localhost:3000/api
- Swagger UI: http://localhost:3000/api/docs
- ReDoc: http://localhost:3000/api/redoc

## Development

### Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Settings (pydantic-settings)
│   ├── db.py              # SQLAlchemy 2.0 async setup
│   └── auth.py            # Firebase JWT validation
├── shared/
│   ├── exceptions.py      # Custom exception handlers
│   └── schemas.py         # Shared Pydantic models
└── modules/
    ├── users/             # User management
    ├── contracts/         # Contract CRUD & lifecycle
    ├── templates/         # Template management
    ├── ai/                # AI generation
    ├── documents/         # PDF generation
    ├── signatures/        # Digital signatures
    ├── notifications/     # Email & reminders
    └── audit/             # Audit trail
```

### Module Structure

Each module follows the same pattern:

```
module/
├── __init__.py           # Exports router
├── api.py                # FastAPI routes
├── service.py            # Business logic
├── repository.py         # Database operations
├── models.py             # SQLAlchemy models
└── schemas.py            # Pydantic schemas
```

### Authentication

The backend validates Firebase JWT tokens. For development, you can use mock tokens:

```bash
# Dev token format: dev_userId_email
curl -H "Authorization: Bearer dev_123_test@example.com" http://localhost:3000/api/users/me
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:3000/health

# Get user profile (with auth)
curl -H "Authorization: Bearer dev_123_test@example.com" \
  http://localhost:3000/api/users/me

# Create contract
curl -X POST http://localhost:3000/api/contracts \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Contract","templateId":"tpl_arrendamiento_v1","contractType":"ARRENDAMIENTO_VIVIENDA"}'

# Generate contract with AI
curl -X POST http://localhost:3000/api/ai/generate-contract \
  -H "Authorization: Bearer dev_123_test@example.com" \
  -H "Content-Type: application/json" \
  -d '{"contractId":"<id>","templateId":"tpl_arrendamiento_v1","contractType":"ARRENDAMIENTO_VIVIENDA","inputs":{"arrendador_nombre":"Juan","arrendatario_nombre":"María"}}'
```

## Deployment (Render)

### render.yaml

```yaml
services:
  - type: web
    name: contractify-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: contractify-db
          property: connectionString
      - key: FIREBASE_PROJECT_ID
        sync: false
      - key: DEBUG
        value: false

databases:
  - name: contractify-db
    plan: free
```

## API Documentation

The API follows the OpenAPI 3.0 specification defined in `docu.yaml`. All endpoints are prefixed with `/api`.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/users/me | Get current user |
| GET | /api/contracts | List contracts |
| POST | /api/contracts | Create contract |
| POST | /api/ai/generate-contract | Generate with AI |
| POST | /api/signatures/sign | Sign contract |
| GET | /api/audit/contracts/{id}/trail | Get audit trail |

See `/api/docs` for complete API documentation.

## License

Private - All rights reserved.
