import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request
from app.models.auth import UserInDB
from app.service.transaction_db import DB
from app.service.gemini import Gemini
from app.service.gmail_service import GmailService
from google import genai
from google.oauth2 import id_token
from google.auth.transport import requests

from app.service.user_db import UserDB

load_dotenv()

def get_db() -> DB:
    return DB()

def get_user_db() -> UserDB:
    return UserDB()

def get_gmail_service() -> GmailService:
    return GmailService()

def get_gemini_client() -> Gemini:

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    gemini_client = Gemini(
        client=genai.Client(api_key =  GEMINI_API_KEY))
    
    return gemini_client


async def get_current_user(request: Request, db: UserDB = Depends(get_user_db)) -> UserInDB:
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]

        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID")
        )

        user_id = idinfo.get("sub")
        email = idinfo.get("email")
        user = await db.get_user_by_userid(user_id=user_id)
        if not user:
            user = await db.create_user(UserInDB(
                user_id=user_id,
                email=email,
            ))
        return user

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")