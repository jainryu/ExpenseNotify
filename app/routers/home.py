from fastapi import APIRouter, Depends

from app.api.dependencies import get_db, get_gemini_client
from app.models.Transaction import Transaction
from app.service.db import DB
from app.service.gemini import Gemini
from app.service.gmail_service import GmailService


router = APIRouter()

@router.get("/")
async def root():
    return "welcome to Expense Notify!"