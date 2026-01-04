import subprocess
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import async_session_maker
from app.services.seed import seed_stocks


def run_migrations():
    """Run alembic migrations before app starts."""
    print("Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"Migration output: {result.stdout}")
        if result.stderr:
            print(f"Migration stderr: {result.stderr}")
        print("Migrations completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Migration failed with code {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting {settings.app_name}...")

    # Run migrations first
    run_migrations()

    # Seed stocks
    try:
        async with async_session_maker() as db:
            count = await seed_stocks(db)
            if count > 0:
                print(f"Seeded {count} stocks from B3")
            else:
                print("Stocks already seeded")
    except Exception as e:
        print(f"Warning: Could not seed stocks: {e}")

    yield
    # Shutdown
    print(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Sistema pessoal de acompanhamento de ações da B3",
    lifespan=lifespan,
)

# CORS - permitir frontend local e produção
cors_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:4173",  # Vite preview
    "http://localhost:3000",
]

# Em produção, permitir qualquer subdomínio do Vercel
if settings.app_env == "production":
    cors_origins.extend([
        "https://*.vercel.app",
        "https://stock-tracker-frontend.vercel.app",  # Ajuste conforme seu domínio
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "production" else cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
