from fastapi import Depends, FastAPI
from app.api.dependencies import get_db, get_gemini_client
from app.routers import auth, genai, home, transaction
from fastapi.middleware.cors import CORSMiddleware


from app.service.transaction_db import DB
from app.service.gemini import Gemini
from app.service.gmail_service import GmailService


app = FastAPI()
app.include_router(transaction.router)
app.include_router(home.router)
app.include_router(genai.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
