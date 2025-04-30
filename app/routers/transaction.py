from fastapi import APIRouter
from app.models.transaction import Transaction

router = APIRouter(
    prefix="/transactions",
)

@router.get("/", response_model=list[Transaction])
async def get_all_transactions():
    return [
        Transaction(id="1", amount=100.0, status=False),
        Transaction(id="2", amount=200.0, status=False),
    ]


@router.post("/create", response_model=Transaction)
async def create_transaction(transaction: Transaction):
    return transaction

@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(transaction_id: str, transaction: Transaction):
    transaction.id = transaction_id
    return transaction