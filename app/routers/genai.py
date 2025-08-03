from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from google.oauth2.credentials import Credentials

from app.api.dependencies import get_db, get_gemini_client, get_user_db
from app.models.transaction import TransactionDB
from app.models.auth import UserInDB
from app.routers.auth import SCOPES, get_current_user
from app.service.transaction_db import DB
from app.service.gemini import Gemini
from app.service.gmail_service import GmailService
from app.service.user_db import UserDB
from app.utils.encrytion_utils import decrypt_credentials, encrypt_credentials
from dateutil.parser import parse as parse_date


router = APIRouter(prefix="/genai", tags=["genai"])


async def get_gmail_service(user: UserInDB = Depends(get_current_user), db: UserDB = Depends(get_user_db)) -> GmailService:
    try:
        creds_data = json.loads(decrypt_credentials(user.google_credentials))

        expiry_str = creds_data.get("expiry")
        expiry_dt = parse_date(expiry_str) if expiry_str else None
        if expiry_dt and expiry_dt.tzinfo is None:
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)

        creds = Credentials(
            token=creds_data.get("token"),
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=creds_data.get("scopes"),
        )

        now = datetime.now(timezone.utc)
        if expiry_dt and now >= expiry_dt:
            if creds.refresh_token:
                try:
                    creds.refresh(Request())
                    await db.update_user_credentials(
                        user_id=user.user_id,
                        google_credentials=encrypt_credentials(creds.to_json())
                    )
                except Exception as e:
                    print(f"Failed to refresh credentials: {e}")
                    raise HTTPException(
                        status_code=401, detail="Google credentials expired or invalid. Please re-link your account.")
            else:
                raise HTTPException(
                    status_code=500, detail="Failed")

        return GmailService(creds)

    except Exception as e:
        print(f"Failed to load credentials: {e}")
        raise HTTPException(
            status_code=401, detail="Invalid or missing Google credentials.")


@router.get("/extract", response_model=list[TransactionDB] | dict)
async def addTransaction(user: UserInDB = Depends(get_current_user), db: DB = Depends(get_db), gmail_service: GmailService = Depends(get_gmail_service), gemini_client: Gemini = Depends(get_gemini_client)):
    try:
        decoded_body_list = gmail_service.get_expense_emails()

        if decoded_body_list is None:
            return {"message": "No emails found or an error occurred."}

        existing_transactions = await db.get_all_transactions(user_id=user.user_id)
        existing_transaction_ids = [
            transaction.transaction_id for transaction in existing_transactions]
        transactions_to_add = [
            transaction.id for transaction in decoded_body_list if transaction.id not in existing_transaction_ids]

        # ask gemini to create transaction
        if not transactions_to_add:
            return {"message": "No new transactions to add."}

        print("new transactions found")
        transaction_list = gemini_client.get_transaction_from_gemini(
            user=user, emails=[body for body in decoded_body_list if body.id in transactions_to_add])
        return await db.create_transaction_from_gmail(transaction_list)

    except Exception as error:
        print(f"An error occurred: {error}")
        return {"error": str(error)}
