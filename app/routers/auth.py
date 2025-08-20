import base64
import os
from typing import Annotated
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import jwt
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from google_auth_oauthlib.flow import Flow


from app.api.dependencies import get_db, get_user_db
from app.models.auth import UserInDB
from app.service.transaction_db import DB
from app.service.user_db import UserDB
from app.utils.encrytion_utils import encrypt_credentials

router = APIRouter(prefix="/auth", tags=["auth"])
load_dotenv()
b64_creds = os.getenv("GOOGLE_CREDENTIALS_B64")
decoded = base64.b64decode(b64_creds)

with open("temp_credentials.json", "wb") as f:
    f.write(decoded)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REDIRECT_URI = "https://expensenotify.onrender.com/auth/google-callback"


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


async def get_current_user_from_token(token: str, db: UserDB) -> UserInDB:
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
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.user_id}, expires_delta=access_token_expires)
    return Token(access_token=token, token_type="bearer")


@router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
):
    return current_user.user_id


@router.get("/google-login")
async def google_login(request: Request, db: UserDB = Depends(get_user_db)):
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token missing")

    user = await get_current_user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    flow = Flow.from_client_secrets_file(
        "temp_credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=token
    )
    return RedirectResponse(auth_url)


@router.get("/google-callback")
async def google_callback(request: Request, db: UserDB = Depends(get_user_db)):
    code = request.query_params.get("code")
    token = request.query_params.get("state")

    user = await get_current_user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    flow = Flow.from_client_secrets_file(
        "temp_credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials

    await db.update_user_credentials(
        user_id=user.user_id,
        google_credentials=encrypt_credentials(credentials.to_json())
    )

    frontend_url = "https://expense-notify-fe-f3uc.vercel.app//google-link-success?status=success"
    return RedirectResponse(frontend_url)
