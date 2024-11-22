import pytest
from fastapi.testclient import TestClient
from routers.api.player_profile import players_profiles_router
from data.models import PlayerProfile
from services import player_profile_service
from unittest.mock import AsyncMock, patch

client = TestClient(players_profiles_router)

@pytest.fixture
def mock_player_profile():
    return PlayerProfile(
        id=1,
        full_name="John Doe",
        country="USA",
        sports_club="Yankees",
        wins=10,
        losses=5,
        draws=2
    )

@pytest.mark.asyncio
async def test_get_player_profile_by_name_found(mock_player_profile):
    with patch("data.database.DatabaseConnection.read_query", new_callable=AsyncMock) as mock_read_query:
        mock_read_query.return_value = [[
            mock_player_profile.id,
            mock_player_profile.full_name,
            mock_player_profile.country,
            mock_player_profile.sports_club,
            mock_player_profile.wins,
            mock_player_profile.losses,
            mock_player_profile.draws
        ]]

        result = await player_profile_service.get_player_profile_by_name("John Doe")

        assert result is not None
        assert result.full_name == "John Doe"
        assert result.country == "USA"
        assert result.sports_club == "Yankees"
        assert result.wins == 10
        assert result.losses == 5
        assert result.draws == 2

@pytest.mark.asyncio
async def test_get_player_profile_by_name_not_found():
    with patch("data.database.DatabaseConnection.read_query", new_callable=AsyncMock) as mock_read_query:
        mock_read_query.return_value = []

        result = await player_profile_service.get_player_profile_by_name("Unknown Player")

        assert result is None

@pytest.mark.asyncio
async def test_create_new_player_profile(mock_player_profile):
    with patch("data.database.DatabaseConnection.read_query", new_callable=AsyncMock) as mock_read_query, \
        patch("data.database.DatabaseConnection.insert_query", new_callable=AsyncMock) as mock_insert_query:

        mock_read_query.return_value = []  # No duplicate player
        mock_insert_query.return_value = True

        result = await player_profile_service.create(mock_player_profile)

        assert result is True
        mock_insert_query.assert_called_once()

@pytest.mark.asyncio
async def test_create_duplicate_player_profile(mock_player_profile):
    with patch("data.database.DatabaseConnection.read_query", new_callable=AsyncMock) as mock_read_query:
        mock_read_query.return_value = [[
            mock_player_profile.id,
            mock_player_profile.full_name,
            mock_player_profile.country,
            mock_player_profile.sports_club,
            mock_player_profile.wins,
            mock_player_profile.losses,
            mock_player_profile.draws
        ]]

        result = await player_profile_service.create(mock_player_profile)

        assert result is None  # Duplicate player detected
