from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.api import api_router
from .core.db import init_db
# from .api.endpoints import settings_routes

app = FastAPI(title="Portfolio Visualizer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Updated to match React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and include router
init_db()
app.include_router(api_router, prefix="/api")
# app.include_router(settings_routes.router, prefix="/api/portfolio", tags=["settings"])