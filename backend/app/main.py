from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import async_session_maker
from app.services.seed import seed_stocks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting {settings.app_name}...")

    # Seed stocks
    async with async_session_maker() as db:
        count = await seed_stocks(db)
        if count > 0:
            print(f"Seeded {count} stocks from B3")
        else:
            print("Stocks already seeded")

    yield
    # Shutdown
    print(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Sistema pessoal de acompanhamento de ações da B3",
    lifespan=lifespan,
)

# CORS - permitir frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
