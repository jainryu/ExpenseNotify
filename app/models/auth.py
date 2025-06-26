from pydantic import BaseModel


class UserInDB(BaseModel):
    user_id: str
    hashed_password: str
