from fastapi import Depends, FastAPI
from googleapiclient.discovery import build
from app.api.dependencies import get_db, get_gemini_client
from app.models.Transaction import Transaction
from app.routers import genai, home, transaction

from app.service.db import DB
from app.service.gemini import Gemini
from app.service.gmail_service import GmailService


app = FastAPI()
app.include_router(transaction.router)
app.include_router(home.router)
app.include_router(genai.router)
