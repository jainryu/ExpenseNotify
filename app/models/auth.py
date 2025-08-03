from typing import Optional
from pydantic import BaseModel


class UserInDB(BaseModel):
    user_id: str
    hashed_password: str
    google_credentials: Optional[str] = None
