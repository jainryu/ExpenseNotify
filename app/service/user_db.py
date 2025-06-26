import aioboto3
from aiohttp import ClientError
from app.models.auth import UserInDB

DYNAMODB_REGION = "us-west-1"
USER_TABLE_NAME = "User"


class UserDB:
    def __init__(self):
        self.session = aioboto3.Session()

    async def get_user_by_userid(self, user_id: str) -> UserInDB | None:
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(USER_TABLE_NAME)
            response = await table.get_item(Key={"user_id": user_id})
            user = response.get("Item")
            return UserInDB.model_validate(user) if user else None

    async def create_user(self, user: UserInDB):
        async with self.session.resource("dynamodb", region_name=DYNAMODB_REGION) as dynamodb:
            table = await dynamodb.Table(USER_TABLE_NAME)
            try:
                await table.put_item(
                    Item=user.model_dump(),
                    ConditionExpression="attribute_not_exists(user_id)"
                )
            except ClientError as e:
                print("Error creating user:", e)
                raise e