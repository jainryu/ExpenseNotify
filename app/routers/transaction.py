from fastapi import APIRouter, Depends
from app.api.dependencies import get_db
from app.models.Transaction import Transaction
from app.models.auth import UserInDB
from app.routers.auth import get_current_user
from app.service.transaction_db import DB

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
)


@router.get("/me", response_model=list[Transaction])
async def get_transaction_by_user_id(user: UserInDB = Depends(get_current_user), db: DB = Depends(get_db)):
    transaction = await db.get_transaction_by_user_id(user_id=user.user_id)
    return transaction


@router.post("/create", response_model=list[Transaction], status_code=201)
async def create_transaction(transactions: list[Transaction], user: UserInDB = Depends(get_current_user), db: DB = Depends(get_db)):
    created_transaction = await db.create_transaction(transactions=transactions)
    return created_transaction


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str, user: UserInDB = Depends(get_current_user),  db: DB = Depends(get_db)):
    transaction = await db.get_transaction(transaction_id=transaction_id)
    return transaction


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: str, user: UserInDB = Depends(get_current_user), db: DB = Depends(get_db)):
    await db.delete_transaction(user_id=user.user_id, transaction_id=transaction_id)
    return transaction_id
