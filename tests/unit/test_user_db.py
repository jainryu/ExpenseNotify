import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.auth import UserInDB
from app.service.user_db import UserDB


@pytest_asyncio.fixture
async def user_db():
    return UserDB()


@pytest.fixture
def mock_table():
    """Mock DynamoDB table"""
    return AsyncMock()


@pytest.fixture
def mock_dynamodb_resource(mock_table):
    mock_dynamodb = AsyncMock()
    mock_dynamodb.Table.return_value = mock_table
    return mock_dynamodb


@pytest.fixture
def mock_async_context_manager(mock_dynamodb_resource):
    mock_resource = AsyncMock()
    mock_resource.__aenter__.return_value = mock_dynamodb_resource
    mock_resource.__aexit__.return_value = None
    return mock_resource


@pytest.fixture
def mock_session_with_resource(mock_async_context_manager):
    mock_session = MagicMock()
    mock_session.resource.return_value = mock_async_context_manager
    return mock_session


@pytest.mark.asyncio
async def test_get_user_by_userid_found(mock_session_with_resource, mock_table):
    mock_table.get_item.return_value = {
        "Item": {"user_id": "123", "name": "Alice", "hashed_password": "hashed_pw"}
    }

    user_db = UserDB()
    user_db.session = mock_session_with_resource

    user = await user_db.get_user_by_userid("123")

    assert user == UserInDB(user_id="123", name="Alice",
                            hashed_password="hashed_pw")
    mock_table.get_item.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_userid_not_found(user_db, mock_async_context_manager, mock_table):
    mock_table.get_item.return_value = {}

    result = await user_db.get_user_by_userid("missing")

    assert result is None
    mock_table.get_item.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user_success(user_db, mock_async_context_manager, mock_table):
    user = UserInDB(user_id="alice", hashed_password="pw123")

    with patch.object(user_db.session, "resource", return_value=mock_async_context_manager):
        await user_db.create_user(user)

    mock_table.put_item.assert_awaited_once_with(
        Item=user.model_dump(),
        ConditionExpression="attribute_not_exists(user_id)"
    )


@pytest.mark.asyncio
async def test_update_user_credentials_success(user_db, mock_async_context_manager, mock_table):
    with patch.object(user_db.session, "resource", return_value=mock_async_context_manager):
        await user_db.update_user_credentials("bob", "secret-creds")

    mock_table.update_item.assert_awaited_once_with(
        Key={"user_id": "bob"},
        UpdateExpression="SET google_credentials = :val",
        ExpressionAttributeValues={":val": "secret-creds"}
    )
