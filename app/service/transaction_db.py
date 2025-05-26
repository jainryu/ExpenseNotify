import boto3
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException

from app.models.DBResponse import DBResponse
from app.models.Transaction import Transaction

db = boto3.resource('dynamodb', region_name='us-west-1')


class DB:

    def __init__(self):
        self.table = db.Table('Transaction')

    async def get_all_transactions(self) -> list[Transaction]:
        response = self.table.scan()
        items = response.get('Items', [])
        
        return [Transaction.model_validate(item) for item in items]

    async def create_transaction(self, transaction: Transaction) -> Transaction:
        response = self.table.put_item(
            Item=transaction.model_dump()
        )

        print("Response Metadata:", response)

        response_model = DBResponse.model_validate(response)
        if response_model.ResponseMetadata.HTTPStatusCode != 200:
            raise HTTPException(
                status_code=response_model.ResponseMetadata.HTTPStatusCode,
                detail="Failed to create transaction"
            )

        return Transaction.model_validate(transaction.model_dump())

    async def create_transaction_from_gmail(self, transaction_list: list[Transaction]):
        created_transaction_list = []
        for transaction in transaction_list:
            response = self.table.put_item(
                Item=transaction.model_dump()
            )

            response_model = DBResponse.model_validate(response)
            if response_model.ResponseMetadata.HTTPStatusCode != 200:
                raise HTTPException(
                    status_code=response_model.ResponseMetadata.HTTPStatusCode,
                    detail="Failed to create transaction"
                )
            created_transaction_list.append(Transaction.model_validate(transaction.model_dump()))
            
        return created_transaction_list 

    async def get_transaction(self, transaction_id: str) -> Transaction:
        response = self.table.get_item(
            Key={'id': transaction_id}
        )
        
        item = response.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return Transaction.model_validate(item)
    
    async def get_transaction_by_user_id(self, user_id: str) -> list[Transaction]:
        filtering_exp = Key('user_id').eq(user_id)
        response = self.table.query(
            KeyConditionExpression=filtering_exp
        )
        
        items = response.get('Items', [])
        return [Transaction.model_validate(item) for item in items]
