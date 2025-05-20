import base64
import os
import boto3
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from fastapi import FastAPI, HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.models.DBResponse import DBResponse
from app.models.Transaction import Transaction
from app.routers import transaction
from google import genai

from app.service.gemini import Gemini
from app.service.gmail_service import GmailService


app = FastAPI()
app.include_router(transaction.router)

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

gemini_client = Gemini(
    client=genai.Client(api_key =  GEMINI_API_KEY))
gmail_service = GmailService()

db = boto3.resource('dynamodb', region_name='us-west-1')
table = db.Table('Transactions')

@app.get("/addTransaction")
async def root():
    try:
        decoded_body_list = gmail_service.get_expense_emails()

        if decoded_body_list is None:
            return {"message": "No emails found or an error occurred."}
            
        # ask gemini to create transaction 
        transaction_list = gemini_client.get_transaction_from_gemini(decoded_body_list)

        created_transaction_list = []

        for transaction in transaction_list:
            response = table.put_item(
                Item=transaction.model_dump()
            )

            response_model = DBResponse.model_validate(response)
            if response_model.ResponseMetadata.HTTPStatusCode != 200:
                raise HTTPException(
                    status_code=response_model.ResponseMetadata.HTTPStatusCode,
                    detail="Failed to create transaction"
                )
            created_transaction_list.append(Transaction.model_validate(transaction.model_dump()))
            
        return created_transaction_list 
    
    except Exception as error:
        print(f"An error occurred: {error}")
        return {"error": str(error)}