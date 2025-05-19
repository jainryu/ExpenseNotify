import base64
import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from fastapi import FastAPI
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.routers import transaction
from google import genai

from app.service.gemini import Gemini


app = FastAPI()

app.include_router(transaction.router)


CLIENT_SECRET_FILE = "/Users/jainryu/Desktop/projects/ExpenseNotify/credentials.json"
TOKEN_FILE = "/Users/jainryu/Desktop/projects/ExpenseNotify/token.json"
SCOPES= ['https://www.googleapis.com/auth/gmail.readonly']

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

gemini_client = Gemini(
    client=genai.Client(api_key =  GEMINI_API_KEY))

@app.get("/addTransaction")
async def root():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        # results = service.users().messages().list(userId="me", labelIds=["CATEGORY_EXPENSE"]).execute()
        results = service.users().messages().list(userId="me", labelIds=["Label_2311038950946628504"], maxResults=10).execute()
        messages = results.get("messages", [])
        
        decoded_body_list = []

        for message in messages:
            msg_id = message['id']
            msg = service.users().messages().get(userId="me", id=msg_id, format='full').execute()
            parts = msg['payload']['parts']
            
            for part in parts:
                nested_parts = part.get('parts')
                if not nested_parts:
                    if part['mimeType'] == 'text/plain':
                        decoded_body_list.append(_decode_body(part))
                else:
                    # If there are nested parts, iterate through them
                    for part in nested_parts:
                        if part['mimeType'] == 'text/plain':
                            decoded_body_list.append(_decode_body(part))
                            break
            
        # ask gemini to create transaction 
        transaction_list = gemini_client.get_transaction_from_gemini(decoded_body_list)
        print(transaction_list)
        return transaction_list
    
    except Exception as error:
        print(f"An error occurred: {error}")


def _decode_body(part) -> str:
    data = part['body']['data']
    byte_code = base64.urlsafe_b64decode(data)
    text = byte_code.decode("utf-8")
    print(text)
    return text