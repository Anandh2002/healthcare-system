# app/main.py

# This is the entry point of our entire application.
# FastAPI() creates the app instance.
# We attach routers to it (in later phases).
# We configure middleware (CORS, logging) here.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Import the auth router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.admin import router as admin_router

'''
Request
   ↓
main.py         → knows WHICH router handles this URL
   ↓
endpoints/      → knows WHAT to call, validates input/output
   ↓
deps.py         → opens DB session, validates token
   ↓
services/       → knows HOW to handle the business logic
   ↓
repositories/   → knows HOW to talk to the database
   ↓
core/security   → knows HOW to hash passwords and make tokens
   ↓
Response
'''

def create_application() -> FastAPI:
    """
    App factory pattern — instead of creating the app at module level,
    we wrap it in a function. This makes testing easier because we can
    create fresh app instances for each test.
    """

    application=FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        
    )

    # Include the auth router — all its routes are now active
    # prefix="/api/v1" means routes become /api/v1/auth/login etc.
    application.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    application.include_router(users_router, prefix=settings.API_V1_PREFIX)
    application.include_router(admin_router, prefix=settings.API_V1_PREFIX)


    # Runs when the server starts up
    @application.on_event("startup")
    async def startup():
        print("✅ Server started successfully")
        print(f"✅ Environment: {settings.ENVIRONMENT}")
        print(f"✅ Docs available at: http://localhost:8000/docs")

    # Runs when the server shuts down
    @application.on_event("shutdown")
    async def shutdown():
        print("Server shutting down...")

    # Health check endpoint — a simple way to verify the server is running.
    # Load balancers and monitoring tools ping this route.

    @application.get("/health",tags=["health"])

    async def health_check():
        return {
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    return application

app=create_application()