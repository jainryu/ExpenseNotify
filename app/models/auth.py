from pydantic import BaseModel


class UserInDB(BaseModel):
    user_id: str
    email: str
