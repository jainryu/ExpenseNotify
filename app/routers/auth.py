from fastapi import APIRouter

from app.models.auth import UserSignUp


router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def login(username: str, email: str, password: str):
    pass

@router.get("/signup")
async def signup(user: UserSignUp):
    
    pass