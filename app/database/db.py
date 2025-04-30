import boto3

from app.models import Transaction

db = boto3.resource('dynamodb')
table = db.Table('Transactions')

async def get_transactions() -> list[Transaction]:
    response = table.scan()
    items = response.get('Items', [])
    
    return [Transaction.model_validate(item) for item in items]

async def create_transaction(transaction: Transaction) -> Transaction:
    table.create_item(
        Item=transaction.model_dump()
    )