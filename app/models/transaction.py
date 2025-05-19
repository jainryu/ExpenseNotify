import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    id: str
    title: str
    date: str
    amount: str
    description: Optional[str] = Field(max_length = 50)
    status: bool