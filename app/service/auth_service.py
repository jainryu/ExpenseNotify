from fastapi import Depends
from app.api.dependencies import get_user_db


class AuthService:

    def verify_password():
        pass
    
    def authenticate_user(self, username: str, password: str, userDB = Depends(get_user_db)) -> bool:
        user = userDB.get_user_by_username(username)
        if not user:
            return False
        # if not verify password - return False