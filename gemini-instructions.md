Act as a Senior Python Backend Architect. I want to refactor the existing `userprofile-api` codebase to adhere to "Clean Architecture" principles and industry best practices.

The current architecture calls PostgreSQL stored procedures directly within the Service layer using raw SQL strings. I want to improve separation of concerns, type safety, and testability.

Please execute the following refactoring plan step-by-step:

### 1. Implement the Repository Pattern
Create a new directory `app/repositories`.
* Move all database interaction logic (SQL queries and stored procedure calls) out of `app/services/*` and into dedicated repository classes (e.g., `ProfileRepository`, `SettingsRepository`, `SubscriptionRepository`).
* The Repositories should take the `Database` instance (from `app/core/database.py`) as a dependency in their `__init__`.
* **Crucial:** The Repositories must return Pydantic models (Domain models) instead of raw dictionaries. If a query returns `None`, return `None`. Do not handle HTTP exceptions in the Repository; simply return data.

### 2. Refactor the Service Layer
Update all files in `app/services/`:
* Remove all `db.fetch_*` calls.
* Inject the corresponding Repository into the Service class constructor (e.g., `def __init__(self, profile_repo: ProfileRepository):`).
* Update the Service methods to call Repository methods.
* Keep business logic (validations, external API calls, caching logic) inside the Service.
* Use FastAPI's `Depends` system in `app/routes` to inject these Services properly, rather than using global instances like `profile_service = ProfileService()`.

### 3. Enhance Type Safety
* Ensure every method in Services and Repositories has full type hinting (arguments and return types).
* Avoid using `dict` or `Any` wherever possible. Use the Pydantic schemas defined in `app/schemas`.

### 4. Setup Testing Infrastructure
Since the project currently lacks tests:
* Create a `tests/` directory.
* Create a `tests/conftest.py` file that sets up:
    * `pytest-asyncio` configuration.
    * A fixture for the FastAPI `app`.
    * A fixture that overrides `get_db` to use a test database or mocks.
* Create a sample test file `tests/test_routes/test_profile.py` demonstrating how to write an integration test for the `/users/me` endpoint.

### 5. Refine Error Handling
* Ensure that `ResourceNotFoundError` and other exceptions are raised in the Service layer (when a Repository returns None), not in the Repository layer itself.

**Constraint Checklist:**
* Do NOT change the underlying database schema or the stored procedures.
* Keep using `asyncpg` via the existing `Database` class.
* Maintain the existing Redis caching logic within the Service layer.
* Maintain the existing Pydantic V2 style.

Start by creating the base Repository structure and refactoring `ProfileService` as the primary example, then proceed to the other domains.
