import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import ClientError
from fastapi import HTTPException

from app.models.transaction import Transaction, TransactionDB
from app.models.DBResponse import DBResponse
from app.models.sns import ExpenseEventType
from app.service.transaction_db import DB


@pytest.fixture
def mock_table():
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
def mock_event_bus():
    return AsyncMock()


@pytest_asyncio.fixture
async def db_instance(mock_event_bus):
    with patch('app.service.transaction_db.EventBus', return_value=mock_event_bus):
        return DB()


@pytest.fixture
def sample_transaction():
    return Transaction(
        amount="100.50",
        description="Test transaction",
        date="2024-01-15"
    )


@pytest.fixture
def sample_transaction_db():
    return TransactionDB(
        title="Test Transaction",
        user_id="user123",
        transaction_id="txn_user123_2024-01-15_abc123",
        amount="100.50",
        description="Test transaction",
        date="2024-01-15",
        status=True
    )


@pytest.fixture
def mock_db_response():
    """Mock successful DB response"""
    return DBResponse(
        ResponseMetadata={'HTTPStatusCode': 200}
    )


@pytest.mark.asyncio
async def test_get_all_transactions_success(db_instance, mock_async_context_manager, mock_table, sample_transaction_db):
    mock_table.scan.return_value = {
        'Items': [sample_transaction_db.model_dump()]
    }

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        result = await db_instance.get_all_transactions("user123")

    assert result == [TransactionDB(
        title="Test Transaction",
        user_id="user123",
        transaction_id="txn_user123_2024-01-15_abc123",
        amount="100.50",
        description="Test transaction",
        date="2024-01-15",
        status=True
    )]
    mock_table.scan.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_transactions_empty(db_instance, mock_async_context_manager, mock_table):
    mock_table.scan.return_value = {'Items': []}

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        result = await db_instance.get_all_transactions("user123")

    assert result == []
    mock_table.scan.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_transactions_client_error(db_instance, mock_async_context_manager, mock_table):
    mock_table.scan.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException', 'Message': 'Validation error'}},
        'ScanItem'
    )

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        with pytest.raises(HTTPException) as exc_info:
            await db_instance.get_all_transactions("user123")

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_create_transaction_success(db_instance, mock_async_context_manager, mock_table, mock_event_bus, sample_transaction, mock_db_response):
    mock_table.put_item.return_value = mock_db_response.model_dump()

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        with patch('app.service.transaction_db.generate_transaction_id', return_value='txn_user123_2024-01-15_abc123'):
            result = await db_instance.create_transaction("user123", sample_transaction)

    assert result.user_id == "user123"
    assert result.transaction_id == "txn_user123_2024-01-15_abc123"
    mock_table.put_item.assert_awaited_once()
    mock_event_bus.publish_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_transaction_failed_response(db_instance, mock_async_context_manager, mock_table, sample_transaction):
    failed_response = DBResponse(ResponseMetadata={'HTTPStatusCode': 400})
    mock_table.put_item.return_value = failed_response.model_dump()

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        with patch('app.service.transaction_db.generate_transaction_id', return_value='txn_user123_2024-01-15_abc123'):
            with pytest.raises(HTTPException) as exc_info:
                await db_instance.create_transaction("user123", sample_transaction)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_create_transaction_from_gmail_success(db_instance, mock_async_context_manager, mock_table, sample_transaction_db, mock_db_response):
    transaction_list = [sample_transaction_db]
    mock_table.put_item.return_value = mock_db_response.model_dump()

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        result = await db_instance.create_transaction_from_gmail(transaction_list)

    assert len(result) == 1
    assert result[0].user_id == "user123"
    mock_table.put_item.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_transaction_from_gmail_partial_failure(db_instance, mock_async_context_manager, mock_table, sample_transaction_db):
    transaction_list = [sample_transaction_db, sample_transaction_db]
    success_response = DBResponse(ResponseMetadata={'HTTPStatusCode': 200})
    failed_response = DBResponse(ResponseMetadata={'HTTPStatusCode': 400})

    mock_table.put_item.side_effect = [
        success_response.model_dump(),
        failed_response.model_dump()
    ]

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        with pytest.raises(HTTPException) as exc_info:
            await db_instance.create_transaction_from_gmail(transaction_list)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_transaction_success(db_instance, mock_async_context_manager, mock_table, sample_transaction_db):
    mock_table.get_item.return_value = {
        'Item': sample_transaction_db.model_dump()
    }

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        result = await db_instance.get_transaction("txn_123", "user123")

    assert result.user_id == "user123"
    mock_table.get_item.assert_awaited_once_with(
        Key={'user_id': 'user123', 'transaction_id': 'txn_123'}
    )


@pytest.mark.asyncio
async def test_get_transaction_not_found(db_instance, mock_async_context_manager, mock_table):
    mock_table.get_item.return_value = {}

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        with pytest.raises(HTTPException) as exc_info:
            await db_instance.get_transaction("txn_123", "user123")

    assert exc_info.value.status_code == 404
    assert "Transaction not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_transaction_by_user_id_success(db_instance, mock_async_context_manager, mock_table, sample_transaction_db):
    mock_table.query.return_value = {
        'Items': [sample_transaction_db.model_dump()]
    }

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        result = await db_instance.get_transaction_by_user_id("user123")

    assert len(result) == 1
    assert result[0].user_id == "user123"
    mock_table.query.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_transaction_by_user_id_empty(db_instance, mock_async_context_manager, mock_table):
    mock_table.query.return_value = {'Items': []}

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        result = await db_instance.get_transaction_by_user_id("user123")

    assert result == []


@pytest.mark.asyncio
async def test_delete_transaction_success(db_instance, mock_async_context_manager, mock_table, mock_event_bus):
    mock_table.delete_item.return_value = {
        'ResponseMetadata': {'HTTPStatusCode': 200}
    }

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        await db_instance.delete_transaction("txn_123", "user123")

    mock_table.delete_item.assert_awaited_once_with(
        Key={'user_id': 'user123', 'transaction_id': 'txn_123'}
    )
    mock_event_bus.publish_event.assert_awaited_once_with(
        "txn_123", ExpenseEventType.EXPENSE_DELETED
    )


@pytest.mark.asyncio
async def test_delete_transaction_not_found(db_instance, mock_async_context_manager, mock_table):
    mock_table.delete_item.return_value = {
        'ResponseMetadata': {'HTTPStatusCode': 404}
    }

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        with pytest.raises(HTTPException) as exc_info:
            await db_instance.delete_transaction("txn_123", "user123")

    assert exc_info.value.status_code == 404
    assert "Transaction not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_transaction_success(db_instance, mock_async_context_manager, mock_table, sample_transaction, sample_transaction_db):
    # Setup
    mock_table.update_item.return_value = {
        'Attributes': sample_transaction_db.model_dump()
    }

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        result = await db_instance.update_transaction("txn_123", "user123", sample_transaction)

    assert result.user_id == "user123"
    mock_table.update_item.assert_awaited_once()

    call_args = mock_table.update_item.await_args
    assert call_args.kwargs['Key'] == {
        'user_id': 'user123', 'transaction_id': 'txn_123'}
    assert 'UpdateExpression' in call_args.kwargs
    assert 'ExpressionAttributeValues' in call_args.kwargs
    assert 'ExpressionAttributeNames' in call_args.kwargs
    assert call_args.kwargs['ReturnValues'] == "ALL_NEW"


@pytest.mark.asyncio
async def test_update_transaction_not_found(db_instance, mock_async_context_manager, mock_table, sample_transaction):
    mock_table.update_item.return_value = {}

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        with pytest.raises(HTTPException) as exc_info:
            await db_instance.update_transaction("txn_123", "user123", sample_transaction)

    assert exc_info.value.status_code == 404
    assert "Transaction not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_transaction_client_error(db_instance, mock_async_context_manager, mock_table, sample_transaction):
    mock_table.update_item.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException', 'Message': 'Validation error'}},
        'UpdateItem'
    )

    with patch.object(db_instance.session, "resource", return_value=mock_async_context_manager):
        with pytest.raises(HTTPException) as exc_info:
            await db_instance.update_transaction("txn_123", "user123", sample_transaction)

    assert exc_info.value.status_code == 500


def test_generate_transaction_id():
    from app.service.transaction_db import generate_transaction_id

    user_id = "testuser"
    transaction_id = generate_transaction_id(user_id)

    assert transaction_id.startswith(f"txn_{user_id}_")
    assert len(transaction_id.split("_")) == 4
