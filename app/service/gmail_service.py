import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.models.email import Email
from app.utils.email_utils import decode_emails

load_dotenv()
CLIENT_SECRET_FILE = os.getenv('CLIENT_SECRET_FILE')
TOKEN_FILE = os.getenv('TOKEN_FILE')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailService:

    def __init__(self, creds: Credentials):
        self.creds = creds

    def get_expense_emails(self) -> list[Email] | None:
        try:
            service = build("gmail", "v1", credentials=self.creds)

            results = service.users().messages().list(userId="me", labelIds=[
                "Label_2311038950946628504"], maxResults=10).execute()
            messages = results.get("messages", [])

            decoded_body_list = decode_emails(service, messages)

            return decoded_body_list
        except Exception as e:
            return None

    def logout(self):
        if os.path.exists("token.json"):
            os.remove("token.json")
        print("Logged out successfully. Token file removed.")
