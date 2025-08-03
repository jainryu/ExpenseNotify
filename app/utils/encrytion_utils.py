import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY.encode())


def encrypt_credentials(raw_json: str) -> str:
    return fernet.encrypt(raw_json.encode()).decode()


def decrypt_credentials(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()
