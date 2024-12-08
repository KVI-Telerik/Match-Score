from typing import Optional, List, Dict
from data.models import Match, MatchParticipants, PlayerProfile
from data.database import DatabaseConnection
from services import player_profile_service
from datetime import datetime

from services.notification_service import notify_user_added_to_event


async def get_tournament_by_match_id(match_id: int):

    query = """
    SELECT tournament_id 
    FROM match
    WHERE id = $1
    """
    result = await DatabaseConnection.read_query(query, match_id)

    if not result or result[0][0] is None:
        return None

    return int(result[0][0])


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
    for profile in participant_profiles:
        user_data = await DatabaseConnection.read_query("SELECT id, last_name,email FROM users WHERE player_profile_id = $1", profile.id)  
        if user_data:
            await notify_user_added_to_event(user_data, "match", match_data.date)

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
        
   
    players_query = """
        SELECT 
            pp.full_name
        FROM match_participants mp
        JOIN player_profiles pp ON pp.id = mp.player_profile_id
        WHERE mp.match_id = $1
        ORDER BY mp.player_profile_id
    """
    
    players_result = await DatabaseConnection.read_query(players_query, match_id)
    
    
    match_data = match_result[0]
    
    participants = [row[0] for row in players_result]
    
   
    return Match(
        id=match_data[0],
        format=match_data[1],
        date=match_data[2],
        tournament_id=match_data[3],
        tournament_type=match_data[4],
        participants=participants  
    )


async def get_all(tournament_search: Optional[str] = None) -> List[Dict]:
    query = """
            SELECT 
                m.id,
                m.format,
                m.date,
                m.tournament_id,
                m.tournament_type,
                m.finished,
                pp.full_name,
                COALESCE(mp.score, 0) as score,
                t.title as tournament_name
            FROM match m
            JOIN match_participants mp ON m.id = mp.match_id
            JOIN player_profiles pp ON mp.player_profile_id = pp.id
            LEFT JOIN tournament t ON m.tournament_id = t.id
    """

    params = []
    if tournament_search:
        query += " WHERE LOWER(t.title) LIKE LOWER($1)"
        params.append(f"%{tournament_search}%")

    query += " ORDER BY m.date DESC"

    results = await DatabaseConnection.read_query(query, *params)
    if not results:
        return []

    matches_dict = {}
    for row in results:
        match_id = row[0]
        if match_id not in matches_dict:
            matches_dict[match_id] = {
                "id": row[0],
                "format": row[1],
                "date": row[2],
                "tournament_id": row[3],
                "tournament_type": row[4],
                "finished": row[5],
                "tournament_name": row[8],
                "participants": []
            }
        matches_dict[match_id]["participants"].append(f"{row[6]}-{row[7]}")

    return list(matches_dict.values())
async def get_match_with_scores(match_id: int) -> Optional[Dict]:
    query = """
            SELECT 
                m.id,
                m.format,
                m.date,
                m.tournament_id,
                m.tournament_type,
                m.finished,
                pp.id AS player_profile_id,
                pp.full_name,
                COALESCE(mp.score, 0) as score,
                t.title as tournament_name
            FROM match m
            JOIN match_participants mp ON m.id = mp.match_id
            JOIN player_profiles pp ON mp.player_profile_id = pp.id
            LEFT JOIN tournament t ON m.tournament_id = t.id
            WHERE m.id = $1
        """

    results = await DatabaseConnection.read_query(query, match_id)

    if not results:
        return None

    match = {
        "id": results[0][0],
        "format": results[0][1],
        "date": results[0][2].strftime("%Y-%m-%d %H:%M"),
        "tournament_id": results[0][3],
        "tournament_type": results[0][4],
        "finished": results[0][5],
        "participants": [f"{row[7]}-{row[8]}-{row[6]}" for row in results],  # format: name-score-player_id
        "tournament_name": results[0][9]
    }

    return match



async def update_score(match_id: int, player_id: int, score: int) -> Optional[bool]:
    match = await get_by_id(match_id)
    if not match:
        return None

    query = """
        UPDATE match_participants
        SET score = score + $1
        WHERE match_id = $2 AND player_profile_id = $3
    """
    success = await DatabaseConnection.update_query(query, score, match_id, player_id)
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


async def match_end_league(match_id: int, tournament_id: int):
    query = """
        UPDATE match
        SET finished = True
        WHERE id = $1
    """
    success = await DatabaseConnection.update_query(query, match_id)
    if not success:
        return None

    match_data = await get_match_with_scores(match_id)
    participant_scores = [p.split('-') for p in match_data["participants"]]

    if participant_scores[0][1] == participant_scores[1][1]:
        # Handle draw case
        draws = [participant_scores[0][0], participant_scores[1][0]]

        # Update tournament_participants for draw
        tournament_draw_query = """
        UPDATE tournament_participants
        SET draws = draws + 1, 
        points = points + 1
        WHERE player_profile_id IN ($1, $2) AND tournament_id = $3
        """

        # Update player_profiles for draw
        player_draw_query = """
        UPDATE player_profiles
        SET draws = draws + 1
        WHERE id = $1
        """

        p1_obj = str(await player_profile_service.get_player_profile_by_name(draws[0]))
        p2_obj = str(await player_profile_service.get_player_profile_by_name(draws[1]))
        p1_id = int(p1_obj.split('id=')[1].split()[0])
        p2_id = int(p2_obj.split('id=')[1].split()[0])

        # Execute tournament participants update
        await DatabaseConnection.update_query(tournament_draw_query, p1_id, p2_id, tournament_id)

        # Execute player profiles updates
        await DatabaseConnection.update_query(player_draw_query, p1_id)
        await DatabaseConnection.update_query(player_draw_query, p2_id)

        return f'Match ended at a draw between {draws[0]} and {draws[1]}'

    else:
        # Handle win/loss case
        winner = max(participant_scores, key=lambda x: int(x[1]))[0]
        loser = min(participant_scores, key=lambda x: int(x[1]))[0]

        winner_obj = str(await player_profile_service.get_player_profile_by_name(winner))
        loser_obj = str(await player_profile_service.get_player_profile_by_name(loser))
        winner_id = int(winner_obj.split('id=')[1].split()[0])
        loser_id = int(loser_obj.split('id=')[1].split()[0])

        # Update tournament_participants for winner
        tournament_winner_query = """
        UPDATE tournament_participants
        SET wins = wins + 1,
        points = points + 3
        WHERE player_profile_id = $1 AND tournament_id = $2
        """

        # Update tournament_participants for loser
        tournament_loser_query = """
        UPDATE tournament_participants
        SET losses = losses + 1
        WHERE player_profile_id = $1 AND tournament_id = $2
        """

        # Update player_profiles for winner
        player_winner_query = """
        UPDATE player_profiles
        SET wins = wins + 1
        WHERE id = $1
        """

        # Update player_profiles for loser
        player_loser_query = """
        UPDATE player_profiles
        SET losses = losses + 1
        WHERE id = $1
        """

        # Execute tournament participants updates
        await DatabaseConnection.update_query(tournament_winner_query, winner_id, tournament_id)
        await DatabaseConnection.update_query(tournament_loser_query, loser_id, tournament_id)

        # Execute player profiles updates
        await DatabaseConnection.update_query(player_winner_query, winner_id)
        await DatabaseConnection.update_query(player_loser_query, loser_id)

        return f'Match ended. Winner: {winner}'

async def end_single_match(match_id: int) -> bool:
    match_data = await get_match_with_scores(match_id)
    if not match_data:
        return False

    update_query = """
        UPDATE match
        SET finished = True
        WHERE id = $1
    """
    success = await DatabaseConnection.update_query(update_query, match_id)
    if not success:
        return False

    participant_scores = [p.split('-') for p in match_data["participants"]]


    if participant_scores[0][1] == participant_scores[1][1]:
        # Update both players' draw counts
        draw_query = """
            UPDATE player_profiles
            SET draws = draws + 1
            WHERE id = $1
        """
        for participant in participant_scores:
            player_obj = await player_profile_service.get_player_profile_by_name(participant[0])
            if player_obj:
                await DatabaseConnection.update_query(draw_query, player_obj.id)
        return True


    winner = max(participant_scores, key=lambda x: int(x[1]))[0]
    loser = min(participant_scores, key=lambda x: int(x[1]))[0]


    winner_obj = await player_profile_service.get_player_profile_by_name(winner)
    loser_obj = await player_profile_service.get_player_profile_by_name(loser)

    if not winner_obj or not loser_obj:
        return False

    winner_query = """
        UPDATE player_profiles
        SET wins = wins + 1
        WHERE id = $1
    """
    await DatabaseConnection.update_query(winner_query, winner_obj.id)


    loser_query = """
        UPDATE player_profiles
        SET losses = losses + 1
        WHERE id = $1
    """
    await DatabaseConnection.update_query(loser_query, loser_obj.id)

    return True


