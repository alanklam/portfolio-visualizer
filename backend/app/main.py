from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .database import engine
from .models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Portfolio Visualizer",
    description="API for visualizing and analyzing investment portfolio data",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # FastAPI server
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from .routers import upload, portfolio, user_settings

# Include routers with prefixes
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(user_settings.router, prefix="/api/settings", tags=["settings"])

# Create database tables
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {
        "status": "ok",
        "message": "Portfolio Visualizer API is running"
    }

# Log startup
logger.info("Starting Portfolio Visualizer API") 