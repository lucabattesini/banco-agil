from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL
from app.routers.chat_router import router as chat_router

app = FastAPI(title="Banco Ágil")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
