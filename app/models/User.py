from pydantic import BaseModel


class UserDB(BaseModel):
    username: str
    email: str
    hashed_password: str

class UserSignUp(BaseModel):
    username: str
    email: str
    password: str