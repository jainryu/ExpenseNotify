import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[str] = None
    description: Optional[str] = Field(max_length=50, default=None)
    status: Optional[bool] = None


class TransactionDB(Transaction):
    user_id: str
    transaction_id: str
