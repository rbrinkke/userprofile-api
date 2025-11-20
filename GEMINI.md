# User Profile API - Project Overview

The **User Profile API** is a robust, production-ready microservice built with **FastAPI** (Python 3.11) designed to manage the complete user lifecycle. It handles profiles, photos, interests, settings, subscriptions, verification, and moderation.

## Key Technologies

*   **Framework:** FastAPI (Python 3.11)
*   **Database:** PostgreSQL (managed via `app.core.database`)
*   **Caching & Rate Limiting:** Redis
*   **Monitoring:** Prometheus (via `prometheus-fastapi-instrumentator`)
*   **Containerization:** Docker & Docker Compose

## Architecture

The project follows a clean, layered architecture:

*   **`app/routes/`**: API Endpoints (Controllers). Handles HTTP requests, validation, and routing.
*   **`app/schemas/`**: Pydantic models for Request/Response validation.
*   **`app/services/`**: Business logic layer. Orchestrates data operations and external service calls.
*   **`app/models/`**: Database models (likely SQLModel or SQLAlchemy, or just raw SQL wrappers).
*   **`app/core/`**: Core infrastructure (Config, Database, Cache, Logging, Security).
*   **`app/middleware/`**: Cross-cutting concerns (Correlation IDs, Error Handling).

## Getting Started

### Prerequisites

*   Docker & Docker Compose
*   Python 3.11+ (for local development)

### Building and Running

The easiest way to run the application and its dependencies (Postgres, Redis) is via Docker Compose:

```bash
# Start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

The API will be available at `http://localhost:8008`.
Documentation (Swagger UI) is available at `http://localhost:8008/docs` (in development mode).

### Local Development

If running locally (without Docker for the app itself):

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set Environment Variables:**
    Copy `.env.example` to `.env` and configure accordingly.
3.  **Run Application:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

## Database & Schema

*   **Schema Definition:** `sqlschema.sql` contains the initial database schema.
*   **Migrations:** (Check if Alembic or manual SQL is used. Currently relies on `sqlschema.sql` or `app.core.database` initialization).

## Testing

Tests are located in the `tests/` directory.

```bash
# Run tests (example)
pytest
```

## Contribution Guidelines

*   **Code Style:** Follows PEP 8.
*   **Logging:** Use structured logging via `app.core.logging_config`.
*   **Error Handling:** Use `app.core.exceptions.APIException` for consistent error responses.
