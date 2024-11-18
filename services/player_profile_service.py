from typing import Optional

from data.database import DatabaseConnection
from data.models import PlayerProfile


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
