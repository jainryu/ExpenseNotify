import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.utils.email_utils import decode_emails

load_dotenv()
CLIENT_SECRET_FILE = os.getenv('CLIENT_SECRET_FILE')
TOKEN_FILE = os.getenv('TOKEN_FILE')
SCOPES= ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:

    def get_expense_emails(self):
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

            results = service.users().messages().list(userId="me", labelIds=["Label_2311038950946628504"], maxResults=10).execute()
            messages = results.get("messages", [])
            
            decoded_body_list = decode_emails(service, messages)
            
            return decoded_body_list
        except Exception as e:
            return None