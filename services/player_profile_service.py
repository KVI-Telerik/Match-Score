from typing import Optional

from data.database import DatabaseConnection
from data.models import PlayerProfile, UpdateProfile


async def get_player_profile_by_name(full_name: str) -> Optional[PlayerProfile]:

    query = """
        SELECT id, full_name, country, sports_club, wins, losses, draws
        FROM player_profiles 
        WHERE LOWER(TRIM(full_name)) = LOWER(TRIM($1))
    """
    results = await DatabaseConnection.read_query(query, full_name)
    return PlayerProfile.from_query_result(*results[0]) if results else None



async def create(player_profile: PlayerProfile):
    duplicate_query = """
        SELECT * FROM player_profiles 
        WHERE LOWER(TRIM(full_name)) = LOWER(TRIM($1))
    """
    duplicate_player = await DatabaseConnection.read_query(
        duplicate_query,
        player_profile.full_name
    )

    if duplicate_player:
        return None

    query = """
        INSERT INTO player_profiles (
            full_name,
            country,
            sports_club,
            wins,
            losses,
            draws
            
        ) VALUES ($1, $2, $3, $4, $5, $6)
    """

    return await DatabaseConnection.insert_query(
        query,
        player_profile.full_name,
        player_profile.country,
        player_profile.sports_club,
        player_profile.wins,
        player_profile.losses,
        player_profile.draws

    )

async def update(id: int, player_profile: UpdateProfile):
    existing_profile = await DatabaseConnection.read_query(
        "SELECT country, sports_club FROM player_profiles WHERE id = $1",
        id
    )
    if not existing_profile:
        return None

    current_country, current_sports_club = existing_profile[0]
    country = player_profile.country if player_profile.country is not None else current_country
    sports_club = player_profile.sports_club if player_profile.sports_club is not None else current_sports_club

    query = """
        UPDATE player_profiles
        SET country = $1, sports_club = $2 
        WHERE id = $3
    """
    await DatabaseConnection.update_query(query, country, sports_club, id)

    return {"id": id, "country": country, "sports_club": sports_club}


async def get_by_id(player_profile_id: int) -> Optional[PlayerProfile]:
    query = """
        SELECT id, full_name, country, sports_club, wins, losses, draws
        FROM player_profiles
        WHERE id = $1
    """
    results = await DatabaseConnection.read_query(query, player_profile_id)
    return PlayerProfile.from_query_result(*results[0]) if results else None

async def get_user_id(player_profile_id: int):
    query = """
        SELECT id
        FROM users
        WHERE player_profile_id = $1
    """
    results = await DatabaseConnection.read_query(query, player_profile_id)
    return results[0][0] if results else None