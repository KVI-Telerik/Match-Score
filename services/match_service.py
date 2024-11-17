from typing import Optional, List
from data.models import Match, PlayerProfile
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


async def get_match_participants(match_id: int) -> List[PlayerProfile]:
    query = """
        SELECT pp.id, full_name, country, sports_club, wins, losses, draws, user_id
        FROM player_profiles pp
        JOIN match_participants mp ON pp.id = mp.player_profile_id
        WHERE mp.match_id = $1
    """
    results = await DatabaseConnection.read_query(query, match_id)
    return [PlayerProfile.from_query_result(*row) for row in results]


async def get_by_id(match_id: int) -> Optional[Match]:
    query = """
        SELECT id, format, date, tournament_id, tournament_type
        FROM match
        WHERE id = $1
    """
    result = await DatabaseConnection.read_query(query, match_id)
    if not result:
        return None

    match_data = result[0]
    participants = await get_match_participants(match_id)
    return Match(
        id=match_data[0],
        format=match_data[1],
        date=match_data[2],
        participants=[p.full_name for p in participants],
        tournament_id=match_data[3],
        tournament_type=match_data[4]
    )

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