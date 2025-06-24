import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from app.models.auth import UserInDB

db = boto3.resource('dynamodb', region_name='us-west-1')

class UserDB:

    def __init__(self):
        self.table = db.Table('User')

    async def get_user_by_userid(self, user_id: str) -> UserInDB | None:

        response = self.table.get_item(Key={'user_id': user_id})
        user = response.get('Item')
        return UserInDB.model_validate(user) if user else None
    
    async def create_user(self, user: UserInDB):
        try:
            self.table.put_item(
                Item=user.model_dump(),
                ConditionExpression="attribute_not_exists(PK)"
            )
            
        except ClientError as e:
            print("Error creating user:", e)
            raise e