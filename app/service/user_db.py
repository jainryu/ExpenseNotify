import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from app.models.auth import UserInDB

db = boto3.resource('dynamodb', region_name='us-west-1')

class UserDB:

    def __init__(self):
        self.table = db.Table('User')

    async def get_user_by_username(self, username: str) -> UserInDB | None:

        response = await self.talbe.query(
            IndexName='username-index',
            KeyConditionExpression=Key('username').eq(username) & Key('SK').eq('RESERVED')
        )
        user = response.get('Items', [])
        return UserInDB.model_validate(user[0]) if user else None
    
    async def create_user(self, user: UserInDB):
        try:
            await self.table.put_item(
                Item={"PK": f"USERNAME#{user.username}", "SK": "RESERVED"},
                ConditionExpression="attribute_not_exists(PK)"
            )
            
            # 2. Reserve email
            await self.table.put_item(
                Item={"PK": f"EMAIL#{user.email}", "SK": "RESERVED"},
                ConditionExpression="attribute_not_exists(PK)"
            )

            await self.table.put_item(
                Item = {
                    "PK": f"USER#{user.user_id}",
                    "SK": "RESERVED",
                    "username": user.username,
                    "email": user.email,
                    "hashed_password": user.hashed_password
                }
            )

        except ClientError as e:
            print("Error creating user:", e)
            raise e