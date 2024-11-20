import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from jose import jwt
from data.models import User, Requests
from services.user_service import approve_player_claim, claim_type, all_requests, claim_director_request, claim_request, \
    is_director, is_admin, login_user, create_user, get_user_by_id, all_users, approve_director_claim

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_user():
    return User(
        id=1,
        first_name="John",
        last_name="Doe",
        username="johndoe",
        email="john@example.com",
        password="password123"
    )


@pytest.fixture
def mock_token():
    expire = datetime.now().astimezone() + timedelta(minutes=60)
    payload = {"id": 1, "email": "john@example.com", "exp": expire}
    return jwt.encode(payload, "6a631f3a77008d5586d9ecc2ca7bea47695d575b5e6195dd6ca200829a8ae40c", "HS256")


@pytest.mark.asyncio
async def test_all_users():
    mock_users = [(1, "John", "Doe", "johndoe", "hashedpassword123", "john@example.com", False, False, None)]
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = mock_users
        users = await all_users()
        assert len(users) == 1
        assert users[0].id == 1
        assert users[0].username == "johndoe"

@pytest.mark.asyncio
async def test_get_user_by_id_exists():
    mock_user_data = [(1, "John", "Doe", "johndoe", "hashedpassword123", "john@example.com", False, False, None)]
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = mock_user_data
        user = await get_user_by_id(1)
        assert user is not None
        assert user.id == 1


@pytest.mark.asyncio
async def test_get_user_by_id_not_exists():
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = []
        user = await get_user_by_id(999)
        assert user is None


@pytest.mark.asyncio
async def test_create_user_success(mock_user):
    with (
        patch('data.database.DatabaseConnection.read_query') as mock_query,
        patch('data.database.DatabaseConnection.insert_query') as mock_insert
    ):
        mock_query.return_value = []
        mock_insert.return_value = 1

        result = await create_user(mock_user)
        assert result is not None
        assert result.id == 1
        assert bcrypt.verify("password123", result.password)


@pytest.mark.asyncio
async def test_create_user_duplicate(mock_user):
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = [(1,)]
        result = await create_user(mock_user)
        assert result is None


@pytest.mark.asyncio
async def test_login_user_success(mock_user):
    hashed_password = bcrypt.hash("password123")
    mock_user.password = hashed_password

    with (
        patch('data.database.DatabaseConnection.read_query') as mock_query,
        patch('services.user_service.get_user_by_id') as mock_get_user
    ):
        mock_query.return_value = [(1,)]
        mock_get_user.return_value = mock_user

        result = await login_user("john@example.com", "password123")
        assert result is not None
        assert "access_token" in result
        assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user_invalid_password(mock_user):
    hashed_password = bcrypt.hash("password123")
    mock_user.password = hashed_password

    with (
        patch('data.database.DatabaseConnection.read_query') as mock_query,
        patch('services.user_service.get_user_by_id') as mock_get_user
    ):
        mock_query.return_value = [(1,)]
        mock_get_user.return_value = mock_user

        result = await login_user("john@example.com", "wrongpassword")
        assert result is None


@pytest.mark.asyncio
async def test_is_admin_success(mock_token):
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = [(True,)]
        result = await is_admin(mock_token)
        assert result is True


@pytest.mark.asyncio
async def test_is_admin_not_admin(mock_token):
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = [(False,)]
        result = await is_admin(mock_token)
        assert result is False


@pytest.mark.asyncio
async def test_is_director_success(mock_token):
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = [(True,)]
        result = await is_director(mock_token)
        assert result is True

@pytest.mark.asyncio
async def test_claim_director_request_success(mock_token):
    with patch('data.database.DatabaseConnection.insert_query') as mock_insert:
        mock_insert.return_value = 1
        result = await claim_director_request(mock_token)
        assert result == 1


@pytest.mark.asyncio
async def test_all_requests():
    mock_requests = [(1, 1, 1, False), (2, 2, None, False)]
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = mock_requests
        requests = await all_requests()
        assert len(requests) == 2


@pytest.mark.asyncio
async def test_claim_type_player():
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = [(1,)]
        result = await claim_type(1)
        assert result == 'player claim'


@pytest.mark.asyncio
async def test_claim_type_director():
    with patch('data.database.DatabaseConnection.read_query') as mock_query:
        mock_query.return_value = [(None,)]
        result = await claim_type(1)
        assert result == 'director claim'


@pytest.mark.asyncio
async def test_approve_player_claim_success():
    with (
        patch('data.database.DatabaseConnection.update_query') as mock_update
    ):
        mock_update.return_value = True
        result = await approve_player_claim(1)
        assert result is True
        assert mock_update.call_count == 2


@pytest.mark.asyncio
async def test_approve_director_claim_success():
    with (
        patch('data.database.DatabaseConnection.update_query') as mock_update
    ):
        mock_update.return_value = True
        result = await approve_director_claim(1)
        assert result is True
        assert mock_update.call_count == 2