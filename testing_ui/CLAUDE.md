# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Testing UI** is a standalone web-based testing interface for the Auth API. It provides visual, interactive testing of all authentication flows without requiring curl/Postman.

**Core Purpose**: Manual QA testing, development feedback, API demonstration, and debugging support.

**Key Technologies**: FastAPI, Jinja2 templates, Tailwind CSS (CDN), Vanilla JavaScript

## Critical Development Patterns

### 🔴 Always Rebuild After Code Changes

**CRITICAL**: Code changes require rebuild to take effect:

```bash
# Wrong (restart uses old cached image)
docker compose restart auth-testing-ui

# Right (rebuild picks up new code)
docker compose build && docker compose restart auth-testing-ui

# Force rebuild without cache (use after significant changes)
docker compose build --no-cache && docker compose restart auth-testing-ui
```

**When to rebuild:**
- After ANY Python code changes (standalone.py, router.py)
- After template changes (auth_test.html)
- After requirements.txt updates
- After Dockerfile modifications

### API Communication Pattern

The testing UI is a **client-side application** that communicates with auth-api via JavaScript Fetch:

```javascript
// JavaScript in auth_test.html makes HTTP calls to auth-api
const API_BASE = 'http://localhost:8000';  // Auth API endpoint

async function registerAccount() {
    const response = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });
}
```

**Key Points:**
- Testing UI runs on port 8099
- Auth API runs on port 8000
- All API calls go from browser → auth-api:8000
- CORS is configured to allow localhost:8000

### Standalone Architecture

The testing UI is **completely independent** from auth-api:

```
┌─────────────────────┐        ┌─────────────────────┐
│  Testing UI (8099)  │        │   Auth API (8000)   │
│  ─────────────────  │        │  ─────────────────  │
│  • Serves HTML page │        │  • JWT tokens       │
│  • No API logic     │───────▶│  • Authentication   │
│  • Client-side only │        │  • Database         │
└─────────────────────┘        └─────────────────────┘
        ↑                              ↑
        │                              │
        └──────── Browser ─────────────┘
```

**Benefits:**
- Zero coupling with auth-api code
- Can be started/stopped independently
- Easy to deploy/test in isolation
- No impact on auth-api performance

## Common Commands

### Quick Start

```bash
# 1. Ensure auth-api is running (required)
cd /mnt/d/activity && ./scripts/start-infra.sh
cd /mnt/d/activity/auth-api && docker compose up -d

# 2. Start testing UI
cd /mnt/d/activity/testing_ui
./start.sh

# Access the testing page
open http://localhost:8099/test/auth
```

### Development Workflow

```bash
# View logs
docker logs -f auth-testing-ui

# Stop
docker compose down

# Rebuild after changes (CRITICAL!)
docker compose build && docker compose restart

# Check health
curl http://localhost:8099/health

# Access API docs
open http://localhost:8099/docs
```

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run standalone
python standalone.py

# Access
open http://localhost:8099/test/auth
```

### Docker Network Management

```bash
# Check if network exists
docker network ls | grep activity-network

# Create network manually (if needed)
docker network create activity-network

# Inspect network connections
docker network inspect activity-network
```

## Architecture

### Directory Structure

```
testing_ui/
├── standalone.py         # FastAPI app (port 8099)
├── router.py             # Route handler for /test/auth
├── start.sh              # Quick start script (Docker)
├── Dockerfile            # Lightweight Python 3.12-slim image
├── docker-compose.yml    # Docker Compose config
├── requirements.txt      # Minimal dependencies (FastAPI, Jinja2)
├── .dockerignore         # Docker ignore patterns
├── templates/
│   └── auth_test.html    # Full testing interface (Tailwind CSS)
└── README.md            # Complete documentation
```

### Component Roles

**standalone.py**:
- Creates FastAPI app on port 8099
- Includes testing router
- Adds CORS for localhost:8000 (auth-api)
- Health check endpoint: `/health`
- Root redirect: `/` → `/test/auth`

**router.py**:
- Single route: `GET /test/auth`
- Serves Jinja2 template (auth_test.html)
- Tags: "testing-ui"

**auth_test.html**:
- Complete client-side testing interface
- Vanilla JavaScript (no frameworks)
- Tailwind CSS via CDN
- localStorage for session persistence
- Fetch API for HTTP calls to auth-api

### Technology Stack

**Backend (Minimal)**:
- FastAPI 0.115.5
- Uvicorn 0.32.1 (ASGI server)
- Jinja2 3.1.4 (templating)

**Frontend (Client-side)**:
- Vanilla JavaScript (ES6+)
- Tailwind CSS 3.x (CDN)
- Fetch API (async/await)
- localStorage (session persistence)

### Service Dependencies

**Required:**
- Auth API (localhost:8000) - Must be running for testing
- Docker network: `activity-network` - Enables container communication

**Optional:**
- None (fully standalone)

## Testing Flows Supported

### 1. Registration Flow (2 Steps)

```javascript
// Step 1: Create account
POST /api/auth/register
{ email, password }
→ Returns: { verification_token }

// Step 2: Verify email
POST /api/auth/register/verify
{ verification_token, code }
→ Returns: Success message
```

### 2. Login Flow (2-3 Steps)

```javascript
// Step 1: Send login code
POST /api/auth/login
{ email, password }
→ Returns: { requires_code: true, user_id }

// Step 2: Complete login with code
POST /api/auth/login
{ email, password, code }
→ Returns: { access_token, refresh_token } OR { requires_org_selection, organizations }

// Step 3: Select organization (multi-org users only)
POST /api/auth/login
{ email, password, code, org_id }
→ Returns: { access_token, refresh_token, org_id }
```

### 3. Password Reset Flow (2 Steps)

```javascript
// Step 1: Request reset
POST /api/auth/password/reset
{ email }
→ Returns: { reset_token }

// Step 2: Complete reset
POST /api/auth/password/reset/complete
{ reset_token, code, new_password }
→ Returns: Success message
```

### 4. Token Management

```javascript
// Refresh access token
POST /api/auth/token/refresh
{ refresh_token }
→ Returns: { access_token, refresh_token } (rotation)

// Logout
POST /api/auth/logout
{ refresh_token }
→ Returns: Success message
```

## Configuration

### Environment Variables

The testing UI has **minimal configuration**:

```bash
# Port (default: 8099)
PORT=8099

# Log level
LOG_LEVEL=INFO

# Python unbuffered output (Docker)
PYTHONUNBUFFERED=1
```

**No .env file needed** - all config via docker-compose.yml environment section.

### Port Allocation

- **8099**: Testing UI HTTP (exposed to host)
- **8000**: Auth API HTTP (target for API calls)

### CORS Configuration

Configured in `standalone.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Auth API only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Development Patterns

### Adding New Test Flows

To add a new authentication flow to the UI:

**1. Add HTML section** in `auth_test.html`:

```html
<section id="new-flow" class="flow-section bg-white rounded-lg shadow-lg p-6">
    <h2 class="text-2xl font-bold mb-4">🆕 New Flow</h2>

    <div class="space-y-4">
        <input type="text" id="new_input" placeholder="Input value" />
        <button onclick="newFlow()" class="btn-primary">Execute</button>
    </div>

    <div id="new_flow_response" class="response-container"></div>
</section>
```

**2. Add JavaScript function**:

```javascript
async function newFlow() {
    const input = document.getElementById('new_input').value;

    const result = await apiCall('/api/auth/new-endpoint', 'POST', {
        field: input
    });

    displayResponse('new_flow_response', result.data);

    // Auto-fill next form if needed
    if (result.data?.token) {
        document.getElementById('next_token').value = result.data.token;
    }
}
```

**3. Add navigation link**:

```html
<nav class="sticky top-0 z-10 bg-white shadow-md">
    <div class="nav-links">
        <!-- Existing links -->
        <a href="#new-flow">🆕 New Flow</a>
    </div>
</nav>
```

### Customizing API Base URL

For testing against different environments:

**Edit `auth_test.html`**:

```javascript
// Current (default)
const API_BASE = 'http://localhost:8000';

// Change to staging
const API_BASE = 'https://auth-api-staging.example.com';

// Change to production (NOT RECOMMENDED - use with caution)
const API_BASE = 'https://auth-api.example.com';
```

### Modifying Styles

The UI uses **Tailwind CSS via CDN**:

**Option 1: Modify Tailwind classes** (recommended):
```html
<button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
    Click Me
</button>
```

**Option 2: Add custom CSS**:
```html
<style>
.custom-button {
    background: linear-gradient(to right, #667eea, #764ba2);
    border-radius: 8px;
}
</style>
```

**Option 3: Local Tailwind build** (advanced):
- Replace CDN with local build
- Add `tailwind.config.js`
- Build: `npx tailwindcss -i input.css -o output.css`

## Troubleshooting

### "Testing UI not responding"

```bash
# Check container status
docker ps | grep auth-testing-ui

# Check health
curl http://localhost:8099/health

# View logs
docker logs auth-testing-ui

# Restart
docker compose restart auth-testing-ui
```

### "API calls failing with CORS errors"

**Symptom**: Browser console shows "CORS policy" errors

**Solution**:
```bash
# Ensure auth-api is running
curl http://localhost:8000/health

# Check CORS config in standalone.py
# Ensure allow_origins includes auth-api URL

# Rebuild after CORS changes
docker compose build && docker compose restart
```

### "Container won't start"

```bash
# Check network exists
docker network ls | grep activity-network

# Create network if missing
docker network create activity-network

# Rebuild without cache
docker compose build --no-cache && docker compose up -d

# Check logs for errors
docker logs auth-testing-ui
```

### "Changes to HTML/Python not reflected"

```bash
# ALWAYS rebuild after code changes
docker compose build && docker compose restart

# Force rebuild without cache
docker compose build --no-cache && docker compose restart

# Verify new code is running
docker logs auth-testing-ui | head -20
```

### "Port 8099 already in use"

```bash
# Check what's using the port
lsof -i :8099

# Stop existing container
docker compose down

# Or change port in docker-compose.yml
ports:
  - "9099:8099"  # Use 9099 instead
```

## Security Considerations

### Development Only

This testing UI is **NEVER for production**:

⚠️ **Security Issues:**
- Stores tokens in browser localStorage (visible to XSS)
- Displays full JWT tokens in clear text
- No authentication required to access the page
- No rate limiting on the testing UI itself
- Credentials stored in localStorage

⚠️ **Intended Use:**
- Local development testing only
- QA environments (non-production)
- Demo/documentation purposes

### Production Deployment

**NEVER deploy testing UI to production environments.**

If accidentally deployed:
1. Stop container immediately: `docker compose down`
2. Remove from production infrastructure
3. Rotate all exposed tokens/credentials
4. Review access logs for unauthorized access

### Safe Development Practices

**DO:**
- Use test accounts only (e.g., `test@example.com`)
- Clear localStorage after testing
- Use SKIP_LOGIN_CODE=true in auth-api for faster testing
- Test in isolated environments

**DON'T:**
- Use real user credentials
- Test against production auth-api
- Share testing UI URLs publicly
- Store sensitive data in localStorage

## Additional Documentation

- `README.md` - Complete feature documentation and usage examples
- `start.sh` - Bash script with health checks and network validation
- Auth API docs: http://localhost:8000/docs (auth-api must be running)

## Need Help?

**Check Status:**
```bash
# Testing UI health
curl http://localhost:8099/health

# Auth API health (required)
curl http://localhost:8000/health

# View logs
docker logs -f auth-testing-ui
```

**Common Issues:**
1. Auth API not running → Start with `cd /mnt/d/activity/auth-api && docker compose up -d`
2. Network missing → Run `docker network create activity-network`
3. Code changes not reflected → Rebuild with `docker compose build && docker compose restart`
4. CORS errors → Ensure auth-api is on port 8000 and CORS is configured
