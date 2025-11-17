"""
Standalone launcher for the Authentication Testing UI.

This runs the testing UI as a completely separate FastAPI application
on port 8099, independent from the main auth-api.

Usage:
    python testing_ui/standalone.py

    Or with custom port:
    PORT=9000 python testing_ui/standalone.py
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router

# Create standalone FastAPI app
app = FastAPI(
    title="Auth API Testing UI",
    description="Standalone testing interface for Authentication API",
    version="1.0.0",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Auth API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include testing router
app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    """Landing page with links to all test interfaces"""
    from fastapi.responses import HTMLResponse

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API Testing Suite</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-4xl w-full">
            <div class="text-center mb-8">
                <h1 class="text-5xl font-bold text-white mb-4">🧪 API Testing Suite</h1>
                <p class="text-xl text-white/90">Comprehensive testing interfaces for all microservices</p>
                <p class="text-sm text-white/75 mt-2">Development & Testing Environment</p>
            </div>

            <div class="grid md:grid-cols-2 gap-6">
                <!-- Auth API Test -->
                <a href="/test/auth" class="group">
                    <div class="bg-white rounded-2xl shadow-2xl p-8 hover:scale-105 transition-all duration-300 hover:shadow-blue-500/50">
                        <div class="text-6xl mb-4 group-hover:scale-110 transition-transform">🔐</div>
                        <h2 class="text-2xl font-bold text-gray-800 mb-3">Auth API</h2>
                        <p class="text-gray-600 mb-4">Test authentication flows, registration, login, and password reset</p>
                        <div class="flex flex-wrap gap-2 text-xs">
                            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded">Registration</span>
                            <span class="bg-green-100 text-green-800 px-2 py-1 rounded">Login</span>
                            <span class="bg-purple-100 text-purple-800 px-2 py-1 rounded">Password Reset</span>
                            <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded">Tokens</span>
                        </div>
                        <div class="mt-4 text-blue-600 font-semibold group-hover:translate-x-2 transition-transform inline-flex items-center">
                            Open Test Interface →
                        </div>
                    </div>
                </a>

                <!-- User Profile API Test -->
                <a href="/test/userprofile" class="group">
                    <div class="bg-white rounded-2xl shadow-2xl p-8 hover:scale-105 transition-all duration-300 hover:shadow-purple-500/50">
                        <div class="text-6xl mb-4 group-hover:scale-110 transition-transform">👤</div>
                        <h2 class="text-2xl font-bold text-gray-800 mb-3">User Profile API</h2>
                        <p class="text-gray-600 mb-4">Test all 28 profile endpoints including photos, interests, and settings</p>
                        <div class="flex flex-wrap gap-2 text-xs">
                            <span class="bg-pink-100 text-pink-800 px-2 py-1 rounded">Profiles</span>
                            <span class="bg-rose-100 text-rose-800 px-2 py-1 rounded">Photos</span>
                            <span class="bg-emerald-100 text-emerald-800 px-2 py-1 rounded">Interests</span>
                            <span class="bg-indigo-100 text-indigo-800 px-2 py-1 rounded">Settings</span>
                        </div>
                        <div class="mt-4 text-purple-600 font-semibold group-hover:translate-x-2 transition-transform inline-flex items-center">
                            Open Test Interface →
                        </div>
                    </div>
                </a>
            </div>

            <div class="mt-8 bg-white/10 backdrop-blur-lg rounded-xl p-6 text-white">
                <h3 class="font-bold mb-2 text-lg">📋 Quick Info</h3>
                <ul class="space-y-1 text-sm text-white/90">
                    <li>• <strong>Auth API:</strong> http://localhost:8000</li>
                    <li>• <strong>User Profile API:</strong> http://localhost:8008</li>
                    <li>• <strong>Testing UI:</strong> http://localhost:8099 (this server)</li>
                </ul>
            </div>

            <div class="text-center mt-6">
                <p class="text-white/75 text-sm">Built with FastAPI • Tailwind CSS • Jinja2</p>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-testing-ui",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8099"))

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║  🧪 API Testing Suite - Standalone Mode                       ║
╟────────────────────────────────────────────────────────────────╢
║  Landing:  http://localhost:{port}/                          ║
║  Auth:     http://localhost:{port}/test/auth                 ║
║  Profile:  http://localhost:{port}/test/userprofile          ║
║  Health:   http://localhost:{port}/health                    ║
║  Docs:     http://localhost:{port}/docs                      ║
╟────────────────────────────────────────────────────────────────╢
║  Targets:  Auth API (8000) • User Profile API (8008)         ║
╚════════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "testing_ui.standalone:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
