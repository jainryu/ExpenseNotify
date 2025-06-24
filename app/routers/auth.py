from fastapi import APIRouter, Depends

from app.api.dependencies import get_user_db
from app.service.user_db import UserDB


router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me")
async def get_all_transactions(db: UserDB = Depends(get_user_db)):
    user = await db.get_user_by_userid('1234')
    return user