from fastapi import APIRouter
from .endpoints import auth_routes, analysis_routes, file_routes, settings_routes  # Add settings_routes import

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
api_router.include_router(analysis_routes.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(file_routes.router, prefix="", tags=["files"])
api_router.include_router(settings_routes.router, prefix="/portfolio", tags=["settings"])