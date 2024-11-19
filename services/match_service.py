from typing import Optional, List, Dict
from data.models import Match, MatchParticipants, MatchParticipantsResponse, MatchResponseModel, PlayerProfile
from data.database import DatabaseConnection
from services import player_profile_service
from datetime import datetime





async def create_player_profile(name: str) -> Optional[PlayerProfile]:

    new_profile = PlayerProfile(
        full_name=name,
        country=None,
        sports_club=None,
        wins=0,
        losses=0,
        draws=0,
        user_id=None
    )

    profile_id = await player_profile_service.create(new_profile)
    if not profile_id:
        return None

    return await player_profile_service.get_player_profile_by_name(name)


async def create(match_data: Match) -> Optional[Match]:

    participant_profiles = []
    for participant_name in match_data.participants:
        profile = await player_profile_service.get_player_profile_by_name(participant_name)
        if not profile:
            profile = await create_player_profile(participant_name)
        if not profile:
            return None
        participant_profiles.append(profile)


    tournament_id = None if match_data.tournament_id in [0, None] else match_data.tournament_id
    tournament_type = None if not match_data.tournament_type else match_data.tournament_type

    match_query = """
        INSERT INTO match (format, date, tournament_id, tournament_type)
        VALUES ($1, $2, $3, $4)
    """
    match_id = await DatabaseConnection.insert_query(
        match_query,
        match_data.format,
        match_data.date,
        tournament_id,
        tournament_type
    )

    if not match_id:
        return None


    participant_query = """
        INSERT INTO match_participants (match_id, player_profile_id)
        VALUES ($1, $2)
    """

    for profile in participant_profiles:
        success = await DatabaseConnection.update_query(
            participant_query,
            match_id,
            profile.id
        )
        if not success:
            await DatabaseConnection.update_query(
                "DELETE FROM match WHERE id = $1",
                match_id
            )
            return None

    match_data.id = match_id
    return match_data




async def get_match_participants_profiles(match_id: int) -> List[PlayerProfile]:
    query = """
        SELECT pp.id, full_name, country, sports_club, wins, losses, draws
        FROM player_profiles pp
        JOIN match_participants mp ON pp.id = mp.player_profile_id
        WHERE mp.match_id = $1
    """
    results = await DatabaseConnection.read_query(query, match_id)
    return [PlayerProfile.from_query_result(*row) for row in results]


async def get_by_id(match_id: int) -> Optional[Match]:
    """
    Get detailed match information including players and scores.
    
    Args:
        match_id: The ID of the match to retrieve
        
    Returns:
        Match object with all details or None if not found
    """
    # Get match basic information
    match_query = """
        SELECT 
            m.id,
            m.format,
            m.date,
            m.tournament_id,
            m.tournament_type
        FROM match m
        WHERE m.id = $1
    """
    
    match_result = await DatabaseConnection.read_query(match_query, match_id)
    if not match_result:
        return None
        
    # Get players and scores
    players_query = """
        SELECT 
            pp.full_name
        FROM match_participants mp
        JOIN player_profiles pp ON pp.id = mp.player_profile_id
        WHERE mp.match_id = $1
        ORDER BY mp.player_profile_id
    """
    
    players_result = await DatabaseConnection.read_query(players_query, match_id)
    
    # Extract match data
    match_data = match_result[0]
    # Extract player names into a list
    participants = [row[0] for row in players_result]
    
    # Create Match object with all required fields
    return Match(
        id=match_data[0],
        format=match_data[1],
        date=match_data[2],
        tournament_id=match_data[3],
        tournament_type=match_data[4],
        participants=participants  # Include participants list
    )

async def get_match_with_scores(match_id: int) -> Optional[Dict]:
    """
    Get detailed match information including players and scores,
    with the 7th key being 'score' containing the player's name and score.
    """
    match = await get_by_id(match_id)
    if not match:
        return None

    # Get detailed player information with scores
    players_query = """
        SELECT 
            pp.full_name,
            mp.score
        FROM match_participants mp
        JOIN player_profiles pp ON pp.id = mp.player_profile_id
        WHERE mp.match_id = $1
        ORDER BY mp.player_profile_id
    """
    
    players_result = await DatabaseConnection.read_query(players_query, match_id)
    
    # Debugging log
    print(f"Players result: {players_result}")
    
    # Reformat player details
    players = [
        {
            "score": {
                "name": player[0],  # Player's full name
                "value": player[1]  # Player's score
            }
        }
        for player in players_result
    ]
    
    # Return both the basic match info and detailed player info
    return {
        "id": match.id,
        "format": match.format,
        "date": match.date.strftime("%Y-%m-%d %H:%M"),
        "tournament_id": match.tournament_id,
        "tournament_type": match.tournament_type,
        "participants": match.participants,
        "players_details": players  # Only include name and score
    }


async def update_score(match_id: int, player_id:int , score:int) -> Optional[Match]:
    match = await get_by_id(match_id)
    if not match:
        return None
    

    query = """
        UPDATE match_participants
        SET score = score + $1
        WHERE match_id = $2 AND player_profile_id = $3
    """
    success = await DatabaseConnection.update_query(query, score, match_id,player_id)
    if not success:
        return None

    
    return True

async def reschedule_match(match_id: int, new_date: datetime) -> Optional[Match]:
    if new_date.tzinfo is not None :
        new_date = new_date.replace(tzinfo=None)

    query = """
        UPDATE match
        SET date = $1
        WHERE id = $2
    """
    success = await DatabaseConnection.update_query(query, new_date, match_id)
    if not success:
        return None

    return await get_by_id(match_id)