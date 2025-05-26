from pydantic import BaseModel


class UserInDB(BaseModel):
    user_id: str
    username: str
    email: str
    hashed_password: str

class UserSignUp(BaseModel):
    username: str
    email: str
    password: str
