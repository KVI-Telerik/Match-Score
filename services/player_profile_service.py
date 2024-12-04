from typing import Optional

from data.database import DatabaseConnection
from data.models import PlayerProfile, UpdateProfile
from routers.api.player_profile import players_profiles_router


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

async def check_linked_player_profile(player_profile_id: int):
    query = """
        SELECT id
        FROM users
        WHERE player_profile_id = $1
    """
    user_id = await DatabaseConnection.read_query(query, player_profile_id)
    return user_id[0][0] if user_id else None

async def delete_player_profile(player_profile_id: int):


    check_query = """
        SELECT id FROM player_profiles WHERE id = $1
    """
    profile = await DatabaseConnection.read_query(check_query, player_profile_id)
    if not profile:
        return None

    linked = await check_linked_player_profile(player_profile_id)
    if linked:
        return None

    try:

        await DatabaseConnection.update_query("""
            DELETE FROM match_participants 
            WHERE player_profile_id = $1
        """, player_profile_id)


        await DatabaseConnection.update_query("""
            DELETE FROM tournament_participants 
            WHERE player_profile_id = $1
        """, player_profile_id)


        await DatabaseConnection.update_query("""
            DELETE FROM requests 
            WHERE player_profile_id = $1
        """, player_profile_id)


        await DatabaseConnection.update_query("""
            UPDATE users 
            SET player_profile_id = NULL 
            WHERE player_profile_id = $1
        """, player_profile_id)


        success = await DatabaseConnection.update_query("""
            DELETE FROM player_profiles 
            WHERE id = $1
        """, player_profile_id)

        return success

    except Exception as e:
        print(f"Error during player profile deletion: {str(e)}")
        return False

async def get_all(search: str = None):
    query = """
        SELECT id, full_name, country, sports_club, wins, losses, draws
        FROM player_profiles
    """
    if search:
        query += f" WHERE full_name ILIKE '%{search}%'"

    results = await DatabaseConnection.read_query(query)
    return [PlayerProfile.from_query_result(*result) for result in results] if results else []

async def get_profile_by_id(player_profile_id: int):
    query = """
        SELECT pp.id, pp.full_name, pp.country, pp.sports_club, pp.wins, pp.losses, pp.draws, 
                t.title as tournament_name
        FROM player_profiles pp
        LEFT JOIN tournament_participants tp ON pp.id = tp.player_profile_id
        LEFT JOIN tournament t ON tp.tournament_id = t.id
        WHERE pp.id = $1
    """

    results = await DatabaseConnection.read_query(query, player_profile_id)
    if not results:
        return None

    profile_data = results[0]
    player_profile_result = {
        "id": profile_data[0],
        "full_name": profile_data[1],
        "country": profile_data[2],
        "sports_club": profile_data[3] if profile_data[3] else "N/A",
        "wins": profile_data[4],
        "losses": profile_data[5],
        "draws": profile_data[6],
        "tournaments": profile_data[7::] if  profile_data[7] else "N/A"
    }
    return player_profile_result