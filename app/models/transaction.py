import datetime
from typing import Optional
from pydantic import BaseModel


class Transaction(BaseModel):
    id: str
    title: str
    date: str
    amount: str
    description: Optional[str] = None
    status: bool