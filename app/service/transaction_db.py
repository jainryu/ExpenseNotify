from datetime import datetime
import random
import string
from aiohttp import ClientError
from boto3.dynamodb.conditions import Key
import aioboto3
from fastapi import HTTPException

from app.models.DBResponse import DBResponse
from app.models.Transaction import Transaction, TransactionDB

DYNAMODB_REGION = 'us-west-1'
TRANSACTION_TABLE = 'Transaction'


def generate_transaction_id(user_id: str) -> str:
    timestamp = datetime.now()  # milliseconds since epoch
    random_part = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=6))
    return f"txn_{user_id}_{timestamp}_{random_part}"


class DB:
    def __init__(self):
        self.session = aioboto3.Session()

    async def get_all_transactions(self, user_id: str) -> list[TransactionDB]:
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                response = await table.scan()
                items = response.get('Items', [])
                return [TransactionDB.model_validate(item) for item in items]
            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def create_transaction(self, user_id: str, transaction: Transaction):
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                tx_db = TransactionDB(
                    user_id=user_id,
                    transaction_id=generate_transaction_id(user_id),
                    **transaction.model_dump()
                )
                response = await table.put_item(Item=tx_db.model_dump())
                response_model = DBResponse.model_validate(response)

                if response_model.ResponseMetadata.HTTPStatusCode != 200:
                    raise HTTPException(
                        status_code=response_model.ResponseMetadata.HTTPStatusCode,
                        detail="Failed to create transaction"
                    )

                return TransactionDB.model_validate(tx_db.model_dump())

            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def create_transaction_from_gmail(self, transaction_list: list[TransactionDB]):
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
                        TransactionDB.model_validate(transaction.model_dump()))

                except ClientError as e:
                    raise HTTPException(status_code=500, detail=str(e))

        return created_transaction_list

    async def get_transaction(self, transaction_id: str, user_id: str) -> TransactionDB:
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

                return TransactionDB.model_validate(item)

            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def get_transaction_by_user_id(self, user_id: str) -> list[TransactionDB]:
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                filtering_exp = Key('user_id').eq(user_id)
                response = await table.query(KeyConditionExpression=filtering_exp)
                items = response.get('Items', [])
                return [TransactionDB.model_validate(item) for item in items]

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

    async def update_transaction(self, transaction_id: str, user_id: str, transaction: Transaction) -> TransactionDB:
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(TRANSACTION_TABLE)
            try:
                update_expression = "SET "
                expression_attribute_values = {}
                expression_attribute_names = {}

                for key, value in transaction.model_dump().items():
                    if value is not None:
                        placeholder = f"#{key}"  # attribute name placeholder
                        value_placeholder = f":{key}"

                        update_expression += f"{placeholder} = {value_placeholder}, "
                        expression_attribute_values[value_placeholder] = value
                        # map placeholder to actual name
                        expression_attribute_names[placeholder] = key

                update_expression = update_expression.rstrip(", ")

                response = await table.update_item(
                    Key={'user_id': user_id, 'transaction_id': transaction_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ExpressionAttributeNames=expression_attribute_names,
                    ReturnValues="ALL_NEW"
                )

                updated_item = response.get('Attributes')
                if not updated_item:
                    raise HTTPException(
                        status_code=404, detail="Transaction not found or could not be updated"
                    )

                return TransactionDB.model_validate(updated_item)

            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))
