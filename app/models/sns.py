from enum import StrEnum, auto


class ExpenseEventType(StrEnum):
    EXPENSE_CREATED = auto()
    EXPENSE_DELETED = auto()
