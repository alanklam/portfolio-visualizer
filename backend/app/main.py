from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routers import portfolio, upload, auth
from .database import init_db
from .dependencies import get_current_user

app = FastAPI()

# Initialize database tables
init_db()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(
    portfolio.router,
    prefix="/api/portfolio",
    tags=["portfolio"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    upload.router,
    prefix="/api/upload",
    tags=["upload"],
    dependencies=[Depends(get_current_user)]
) 