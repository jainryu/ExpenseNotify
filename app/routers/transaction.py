from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user, get_db
from app.models.Transaction import Transaction
from app.models.auth import UserInDB
from app.service.transaction_db import DB

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
)

@router.get("/", response_model=list[Transaction])
async def get_all_transactions(user: UserInDB = Depends(get_current_user), db: DB = Depends(get_db)):
    transaction_list = await db.get_all_transactions(userid = user.userid)
    return transaction_list

@router.get("/me", response_model=list[Transaction])
async def get_transaction_by_user_id(user: UserInDB = Depends(get_current_user), db: DB = Depends(get_db)):
    transaction = await db.get_transaction_by_user_id(user_id=user.user_id)
    return transaction

@router.post("/create", response_model=Transaction, status_code=201)
async def create_transaction(transaction: Transaction, db: DB = Depends(get_db)):
    created_transaction = await db.create_transaction(transaction=transaction)
    return created_transaction

@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str, db: DB = Depends(get_db)):
    transaction = await db.get_transaction(transaction_id=transaction_id)
    return transaction