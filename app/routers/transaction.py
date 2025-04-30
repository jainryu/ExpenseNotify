from fastapi import APIRouter


router = APIRouter(
    prefix="/transactions",
)

@router.get("/")
async def get_transaction():
    return {"message": "Transaction data"}