import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime
from data.models import Match, PlayerProfile
from services import match_service
import re

@pytest.fixture
def mock_match_data():
    return Match(
        id=1,
        format="Time limited",
        date=datetime.now(),
        tournament_id=None,
        tournament_type=None,
        participants=["John Doe", "Jane Smith"]
    )

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
async def test_get_tournament_by_match_id():
    with patch("data.database.DatabaseConnection.read_query", new_callable=AsyncMock) as mock_read_query:
        mock_read_query.return_value = [[1]]
        tournament_id = await match_service.get_tournament_by_match_id(1)
        assert tournament_id == 1
        mock_read_query.assert_called_once()

@pytest.mark.asyncio
async def test_create_player_profile():
    with patch("services.player_profile_service.create", new_callable=AsyncMock) as mock_create, \
         patch("services.player_profile_service.get_player_profile_by_name", new_callable=AsyncMock) as mock_get:
        mock_create.return_value = 1
        mock_get.return_value = PlayerProfile(id=1, full_name="John Doe", country=None, sports_club=None, wins=0, losses=0, draws=0)
        
        profile = await match_service.create_player_profile("John Doe")
        assert profile is not None
        assert profile.full_name == "John Doe"
        mock_create.assert_called_once()
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_create_match(mock_match_data, mock_player_profile):
    with patch("services.player_profile_service.get_player_profile_by_name", new_callable=AsyncMock) as mock_get_profile, \
         patch("services.match_service.create_player_profile", new_callable=AsyncMock) as mock_create_profile, \
         patch("data.database.DatabaseConnection.insert_query", new_callable=AsyncMock) as mock_insert_query, \
         patch("data.database.DatabaseConnection.update_query", new_callable=AsyncMock) as mock_update_query:
        mock_get_profile.return_value = mock_player_profile
        mock_create_profile.return_value = mock_player_profile
        mock_insert_query.return_value = 1
        mock_update_query.return_value = True

        match = await match_service.create(mock_match_data)
        assert match is not None
        assert match.id == 1
        mock_insert_query.assert_called_once()
        mock_update_query.assert_called()




@pytest.mark.asyncio
async def test_update_score():
    mock_match = Match(
        id=1,
        format="Time limited",
        date=datetime.now(),
        tournament_id=None,
        tournament_type=None,
        participants=["John Doe", "Jane Smith"]
    )
    with patch("services.match_service.get_by_id", new_callable=AsyncMock) as mock_get_by_id, \
         patch("data.database.DatabaseConnection.update_query", new_callable=AsyncMock) as mock_update_query:
        
        mock_get_by_id.return_value = mock_match
        
        mock_update_query.return_value = True
        
  
        result = await match_service.update_score(1, 1, 10)
        
        
        assert result is True
        mock_get_by_id.assert_called_once_with(1)
        
        # Normalize query strings to prevent formatting issues
        def normalize_whitespace(query):
            return re.sub(r"\s+", " ", query).strip()
        
        expected_query = """
            UPDATE match_participants
            SET score = score + $1
            WHERE match_id = $2 AND player_profile_id = $3
        """
        actual_query = mock_update_query.call_args[0][0]
        
        
        assert normalize_whitespace(actual_query) == normalize_whitespace(expected_query)
        
        
        assert mock_update_query.call_args[0][1:] == (10, 1, 1)


@pytest.mark.asyncio
async def test_get_match_with_scores():
    with patch("data.database.DatabaseConnection.read_query", new_callable=AsyncMock) as mock_read_query:
        mock_read_query.return_value = [
            (1, "Round Robin", datetime.now(), None, None, False, "John Doe", 10),
            (1, "Round Robin", datetime.now(), None, None, False, "Jane Smith", 5)
        ]

        match = await match_service.get_match_with_scores(1)
        assert match is not None
        assert match["id"] == 1
        assert len(match["participants"]) == 2
        assert match["participants"][0].startswith("John Doe-")
        mock_read_query.assert_called_once()

@pytest.mark.asyncio
async def test_match_end_league_draw():
    with patch("services.match_service.get_match_with_scores", new_callable=AsyncMock) as mock_get_scores, \
         patch("services.player_profile_service.get_player_profile_by_name", new_callable=AsyncMock) as mock_get_player, \
         patch("data.database.DatabaseConnection.update_query", new_callable=AsyncMock) as mock_update_query:

        mock_get_scores.return_value = {
            "participants": ["John Doe-5", "Jane Smith-5"]
        }

        mock_get_player.side_effect = [
            PlayerProfile(id=1, full_name="John Doe", country="USA", sports_club=None, wins=0, losses=0, draws=0),
            PlayerProfile(id=2, full_name="Jane Smith", country="Canada", sports_club=None, wins=0, losses=0, draws=0)
        ]

        mock_update_query.return_value = True

        result = await match_service.match_end_league(1, 1)

        assert "Match ended at a draw" in result
        mock_get_scores.assert_called_once_with(1)
        assert mock_get_player.call_count == 2
        mock_update_query.assert_called()

@pytest.mark.asyncio
async def test_match_end_league_winner():
    with patch("services.match_service.get_match_with_scores", new_callable=AsyncMock) as mock_get_scores, \
         patch("services.player_profile_service.get_player_profile_by_name", new_callable=AsyncMock) as mock_get_player, \
         patch("data.database.DatabaseConnection.update_query", new_callable=AsyncMock) as mock_update_query:

        mock_get_scores.return_value = {
            "participants": ["John Doe-10", "Jane Smith-5"]
        }

        mock_get_player.side_effect = [
            PlayerProfile(id=1, full_name="John Doe", country="USA", sports_club=None, wins=0, losses=0, draws=0),
            PlayerProfile(id=2, full_name="Jane Smith", country="Canada", sports_club=None, wins=0, losses=0, draws=0)
        ]


        mock_update_query.return_value = True

        result = await match_service.match_end_league(1, 1)

        assert "Winner: John Doe" in result
        mock_get_scores.assert_called_once_with(1)
        assert mock_get_player.call_count == 2
        mock_update_query.assert_called()

