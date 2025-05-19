from typing import List
import boto3
from fastapi import HTTPException

from app.models.Transaction import Transaction
from app.models.DBResponse import DBResponse



db = boto3.resource('dynamodb', region_name='us-west-1')
table = db.Table('Transactions')

async def get_all_transactions() -> list[Transaction]:
    response = table.scan()
    items = response.get('Items', [])
    
    return [Transaction.model_validate(item) for item in items]

async def create_transaction(transaction: Transaction) -> Transaction:
    response = table.put_item(
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

async def create_transaction_from_gmail(transaction_list: List[Transaction]):
    created_transaction_list = []
    for transaction in transaction_list:
        response = table.put_item(
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

async def get_transaction(transaction_id: str) -> Transaction:
    response = table.get_item(
        Key={'id': transaction_id}
    )
    
    item = response.get('Item')
    if not item:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return Transaction.model_validate(item)


# async def update_transaction(transaction_id: str, transaction: Transaction) -> Transaction:
#     transaction_dict = transaction.model_dump()
#     transaction_dict['id'] = transaction_id
    
#     table.update_item(
#         Key={'id': transaction_id},
#         UpdateExpression="set title=:t, date=:d, amount=:a, description=:desc, status=:s",
#         ExpressionAttributeValues={
#             ':t': transaction_dict['title'],
#             ':d': transaction_dict['date'].isoformat(),
#             ':a': transaction_dict['amount'],
#             ':desc': transaction_dict.get('description', None),
#             ':s': transaction_dict['status']
#         },
#         ReturnValues="UPDATED_NEW"
#     )
    
#     return Transaction.model_validate(transaction_dict)