"""
UniVR Chatbot - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import chat, admin
from app.config import APP_ENV, DEBUG

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    logger.info(f"🚀 UniVR Chatbot starting in {APP_ENV} mode")
    yield
    logger.info("👋 UniVR Chatbot shutting down")


# Create FastAPI app
app = FastAPI(
    title="UniVR Chatbot",
    description="RAG-based chatbot for University of Verona student services",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint for Heroku."""
    return {"status": "healthy", "app": "univr-chatbot"}
