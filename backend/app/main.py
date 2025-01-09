from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import analysis_routes, auth_routes, file_routes
from .core.db import init_db

app = FastAPI(title="Portfolio Visualizer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(
    auth_routes.router,
    prefix="/api/auth",
    tags=["auth"]
)

app.include_router(
    analysis_routes.router,
    prefix="/api/portfolio",
    tags=["portfolio"]
)

app.include_router(
    file_routes.router,
    prefix="/api",
    tags=["files"]
) 