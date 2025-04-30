from typing import Optional
from pydantic import BaseModel


class Transaction(BaseModel):
    id: int
    amount: float
    description: Optional[str] = None
    status: bool