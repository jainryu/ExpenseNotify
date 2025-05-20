import os
from dotenv import load_dotenv
from app.service.db import DB
from app.service.gemini import Gemini
from app.service.gmail_service import GmailService
from google import genai


load_dotenv()

def get_db() -> DB:
    return DB()

def get_gmail_service() -> GmailService:
    return GmailService()

def get_gemini_client() -> Gemini:

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    gemini_client = Gemini(
        client=genai.Client(api_key =  GEMINI_API_KEY))
    
    return gemini_client