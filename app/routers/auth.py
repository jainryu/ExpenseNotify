import os
from typing import Annotated
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import jwt
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from app.api.dependencies import get_user_db
from app.models.auth import UserInDB
from app.service.user_db import UserDB

router = APIRouter(prefix="/auth", tags=["auth"])


load_dotenv()
TOKEN_KEY = os.getenv("TOKEN_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class User(BaseModel):
    user_id: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, TOKEN_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme), db: UserDB = Depends(get_user_db)) -> UserInDB:
    try:
        payload = jwt.decode(token, TOKEN_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.get_user_by_userid(user_id=user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/signup", status_code=201)
async def signup(user_in: User,  db: UserDB = Depends(get_user_db)):
    user = await db.get_user_by_userid(user_id=user_in.user_id)
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = hash_password(user_in.password)
    await db.create_user(UserInDB(
        user_id=user_in.user_id,
        hashed_password=hashed
    ))
    return {"message": "User created successfully"}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: UserDB = Depends(get_user_db)):
    user = await db.get_user_by_userid(user_id=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": user.user_id})
    return Token(access_token=token, token_type="bearer")


@router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
):
    return current_user.user_id
