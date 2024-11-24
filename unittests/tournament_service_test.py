import re
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from services import tournament_service, player_profile_service, match_service
from data.models import Tournament, Match, PlayerProfile



@pytest.fixture
def mock_tournament_data():
    return Tournament(
        title="Test Tournament",
        format="Knockout",
        match_format="Score limited",
        prize=5000
    )


@pytest.fixture
def mock_participants():
    return ["John Doe", "Jane Smith", "Bob Johnson", "Alice Williams"]


@pytest.mark.asyncio
async def test_create_knockout_tournament(mock_tournament_data: Tournament, mock_participants: list[str]):
    with patch("data.database.DatabaseConnection.insert_query", new_callable=AsyncMock) as mock_insert_query, \
         patch("data.database.DatabaseConnection.read_query", new_callable=AsyncMock) as mock_read_query, \
         patch("services.match_service.create", new_callable=AsyncMock) as mock_create_match:
        
        mock_insert_query.return_value = 1 
        
        # Mock profile query return value (simulate a database row)
        mock_read_query.return_value = [
            [1, "John Doe", "USA", "", 0, 0, 0]  # Simulating a single row of query results
        ]

        mock_create_match.return_value = True


        result = await tournament_service.create(mock_tournament_data, mock_participants)

        assert result is True
        mock_insert_query.assert_called_once()
        mock_read_query.assert_called()
        mock_create_match.assert_called()



@pytest.mark.asyncio
async def test_create_league_tournament(mock_tournament_data: Tournament, mock_participants: list[str]):
    mock_tournament_data.format = "League"

    with patch("data.database.DatabaseConnection.insert_query", new_callable=AsyncMock) as mock_insert_query, \
         patch("services.player_profile_service.get_player_profile_by_name", new_callable=AsyncMock) as mock_get_profile, \
         patch("data.database.DatabaseConnection.update_query", new_callable=AsyncMock) as mock_update_query:

        # Use side_effect to simulate different behavior for different queries
        def insert_query_side_effect(query, *args):
            if query.startswith("INSERT INTO tournament"):
                return 1  # Simulate tournament ID
            elif query.startswith("INSERT INTO match"):
                return 2  # Simulate match ID
            return None

        mock_insert_query.side_effect = insert_query_side_effect

        # Mock profile query return value (simulate a database row)
        mock_get_profile.return_value = PlayerProfile(
            id=1, full_name="John Doe", country="USA", sports_club="", wins=0, losses=0, draws=0
        )
        mock_update_query.return_value = True

        
        result = await tournament_service.create(mock_tournament_data, mock_participants)

        assert result is True
        mock_insert_query.assert_any_call(
            "INSERT INTO tournament(title,format,match_format,prize)\n     VALUES ($1, $2, $3, $4)",
            mock_tournament_data.title,
            mock_tournament_data.format,
            mock_tournament_data.match_format,
            mock_tournament_data.prize,
        )
        mock_get_profile.assert_called()
        mock_update_query.assert_called()






@pytest.mark.asyncio
async def test_advance_knockout_tournament():
    tournament_id = 1

    with patch("data.database.DatabaseConnection.read_query", new_callable=AsyncMock) as mock_read_query, \
         patch("data.database.DatabaseConnection.update_query", new_callable=AsyncMock) as mock_update_query, \
         patch("services.match_service.get_match_with_scores", new_callable=AsyncMock) as mock_get_scores, \
         patch("services.match_service.create", new_callable=AsyncMock) as mock_create_match:

        # Simulate ongoing matches
        mock_read_query.return_value = [[1], [2]]
        # Simulate updating matches to finished
        mock_update_query.return_value = True
        # Simulate match scores
        mock_get_scores.return_value = {
            "participants": ["John Doe-10", "Jane Smith-5"],
            "date": (datetime.now() + timedelta(days=1)).isoformat(),
            "format": "Score limited"
        }
        # Simulate successful match creation
        mock_create_match.return_value = True

        # Call the service function
        result = await tournament_service.advance_knockout_tournament(tournament_id)

        # Function to normalize SQL queries by collapsing extra spaces and trimming
        def normalize_query(query):
            return re.sub(r"\s+", " ", query).strip()

        # Expected and actual queries after normalization
        expected_query = normalize_query("""
            SELECT id FROM match
            WHERE tournament_id = $1 AND finished = False AND tournament_type = 'Knockout'
        """)
        actual_query = normalize_query(mock_read_query.call_args[0][0])

        # Assertions
        assert result is True
        assert actual_query == expected_query  # Compare normalized queries
        mock_update_query.assert_called()
        mock_get_scores.assert_called()
        mock_create_match.assert_called()





@pytest.mark.asyncio
async def test_create_knockout_matches(mock_tournament_data: Tournament, mock_participants: list[str]):
    tournament_id = 1

    with patch("services.player_profile_service.get_player_profile_by_name", new_callable=AsyncMock) as mock_get_profile, \
         patch("data.database.DatabaseConnection.update_query", new_callable=AsyncMock) as mock_update_query, \
         patch("services.match_service.create", new_callable=AsyncMock) as mock_create_match:

        # Mock player profile retrieval
        mock_get_profile.return_value = PlayerProfile(
            id=1, full_name="John Doe", country="USA", sports_club="", wins=0, losses=0, draws=0
        )
        # Mock database updates
        mock_update_query.return_value = True
        # Mock match creation
        mock_create_match.return_value = True

        # Call the service function
        result = await tournament_service.create_knockout_matches(tournament_id, mock_participants, "Score limited")

        # Assertions
        assert result is True
        mock_get_profile.assert_called()
        mock_update_query.assert_called()
        mock_create_match.assert_called()



@pytest.mark.asyncio
async def test_create_league_matches(mock_tournament_data: Tournament, mock_participants: list[str]):
    tournament_id = 1

    with patch("services.player_profile_service.get_player_profile_by_name", new_callable=AsyncMock) as mock_get_profile, \
         patch("data.database.DatabaseConnection.update_query", new_callable=AsyncMock) as mock_update_query, \
         patch("data.database.DatabaseConnection.insert_query", new_callable=AsyncMock) as mock_insert_query:

        # Mock player profile retrieval
        mock_get_profile.return_value = PlayerProfile(
            id=1, full_name="John Doe", country="USA", sports_club="", wins=0, losses=0, draws=0
        )
        # Mock database updates
        mock_update_query.return_value = True
        # Mock match creation
        mock_insert_query.side_effect = lambda query, *args: 1 if query.startswith("INSERT INTO match") else None

        # Call the service function
        result = await tournament_service.create_league_matches(tournament_id, mock_participants, "Score limited")

        # Assertions
        assert result is True
        mock_get_profile.assert_called()
        mock_update_query.assert_called()
        mock_insert_query.assert_called()
