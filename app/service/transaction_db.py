from aiohttp import ClientError
from boto3.dynamodb.conditions import Key
import aioboto3
from fastapi import HTTPException

from app.models.DBResponse import DBResponse
from app.models.Transaction import Transaction

DYNAMODB_REGION = 'us-west-1'
TRANSACTION_TABLE = 'Transaction'


class DB:
    def __init__(self):
        self.session = aioboto3.Session()

    async def get_all_transactions(self, user_id: str) -> list[Transaction]:
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                response = await table.scan()
                items = response.get('Items', [])
                return [Transaction.model_validate(item) for item in items]
            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def create_transaction(self, transactions: list[Transaction]):
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                async with table.batch_writer() as batch:
                    for tx in transactions:
                        await batch.put_item(Item=tx.model_dump())

                return [Transaction.model_validate(tx.model_dump()) for tx in transactions]

            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def create_transaction_from_gmail(self, transaction_list: list[Transaction]):
        created_transaction_list = []

        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            for transaction in transaction_list:
                try:
                    response = await table.put_item(Item=transaction.model_dump())
                    response_model = DBResponse.model_validate(response)

                    if response_model.ResponseMetadata.HTTPStatusCode != 200:
                        raise HTTPException(
                            status_code=response_model.ResponseMetadata.HTTPStatusCode,
                            detail="Failed to create transaction"
                        )

                    created_transaction_list.append(
                        Transaction.model_validate(transaction.model_dump()))

                except ClientError as e:
                    raise HTTPException(status_code=500, detail=str(e))

        return created_transaction_list

    async def get_transaction(self, transaction_id: str, user_id: str) -> Transaction:
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                response = await table.get_item(
                    Key={'user_id': user_id, 'transaction_id': transaction_id}
                )
                item = response.get('Item')
                if not item:
                    raise HTTPException(
                        status_code=404, detail="Transaction not found")

                return Transaction.model_validate(item)

            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def get_transaction_by_user_id(self, user_id: str) -> list[Transaction]:
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                filtering_exp = Key('user_id').eq(user_id)
                response = await table.query(KeyConditionExpression=filtering_exp)
                items = response.get('Items', [])
                return [Transaction.model_validate(item) for item in items]

            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def delete_transaction(self, transaction_id: str, user_id: str):
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                response = await table.delete_item(
                    Key={'user_id': user_id, 'transaction_id': transaction_id}
                )
                if response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
                    raise HTTPException(
                        status_code=404, detail="Transaction not found or could not be deleted"
                    )

            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))
