from fastapi import APIRouter
from app.database import db
from app.models.Transaction import Transaction

router = APIRouter(
    prefix="/transactions",
)

@router.get("/", response_model=list[Transaction])
async def get_all_transactions():
    transaction_list = await db.get_all_transactions()
    return transaction_list


@router.post("/create", response_model=Transaction, status_code=201)
async def create_transaction(transaction: Transaction):
    created_transaction = await db.create_transaction(transaction=transaction)
    return created_transaction

@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str):
    transaction = await db.get_transaction(transaction_id=transaction_id)
    return transaction

# @router.put("/{transaction_id}", response_model=Transaction)
# async def update_transaction(transaction_id: str, transaction: Transaction):
#     updated_transaction = await db.update_transaction(transaction_id=transaction_id, transaction=transaction)
#     return updated_transaction