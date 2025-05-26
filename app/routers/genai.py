from fastapi import APIRouter, Depends

from app.api.dependencies import get_db, get_gemini_client
from app.models.Transaction import Transaction
from app.service.transaction_db import DB
from app.service.gemini import Gemini
from app.service.gmail_service import GmailService


router = APIRouter(prefix="/genai", tags=["genai"])

@router.get("/extract", response_model=list[Transaction] | dict)
async def addTransaction(db: DB = Depends(get_db), gmail_service: GmailService = Depends(GmailService), gemini_client: Gemini = Depends(get_gemini_client)):
    try:
        decoded_body_list = gmail_service.get_expense_emails()

        if decoded_body_list is None:
            return {"message": "No emails found or an error occurred."}
        
        existing_transactions = await db.get_all_transactions()
        existing_transaction_ids = [transaction.transaction_id for transaction in existing_transactions]
        transactions_to_add = [transaction.id for transaction in decoded_body_list if transaction.id not in existing_transaction_ids]
            
        # ask gemini to create transaction 
        if not transactions_to_add: 
            return {"message": "No new transactions to add."}
        
        print("new transactions found")
        transaction_list = gemini_client.get_transaction_from_gemini(decoded_body_list)
        return await db.create_transaction_from_gmail(transaction_list)
    
    except Exception as error:
        print(f"An error occurred: {error}")
        return {"error": str(error)}