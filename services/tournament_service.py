import itertools
from random import random
from typing import List, Optional, Dict
from data.models import Tournament, Match, PlayerProfile
from data.database import DatabaseConnection
from services import match_service, player_profile_service
from datetime import datetime, timedelta
import random
from services.match_service import create_player_profile


async def create(tournament_data: Tournament, participants: List[str]) -> Optional[Tournament]:
    query = """INSERT INTO tournament(title,format,match_format,prize)
     VALUES ($1, $2, $3, $4)"""

    tournament_id = await DatabaseConnection.insert_query(query,
                                                          tournament_data.title,
                                                          tournament_data.format,
                                                          tournament_data.match_format,
                                                          tournament_data.prize)
    if not tournament_id:
        return None

    if tournament_data.format == "Knockout":
        matches_created = await create_knockout_matches(tournament_id,participants,tournament_data.match_format)
    elif tournament_data.format == "League":
        matches_created = await create_league_matches(tournament_id,participants,tournament_data.match_format)
    


    if not matches_created:
        return None

    return True
    
    # if not matches_created:
    #     await DatabaseConnection.update_query("DELETE FROM tournament WHERE id=$1", tournament_id)


async def get_all(search: Optional[str] = None) -> List[dict]:
    query = '''
    SELECT t.id, t.title, t.format, t.match_format, t.prize, p.full_name
    FROM tournament t
    LEFT JOIN tournament_participants tp ON t.id = tp.tournament_id
    LEFT JOIN player_profiles p ON tp.player_profile_id = p.id
    '''


    if search:
        query += '''
        WHERE LOWER(t.title) LIKE LOWER($1)
        '''
        search_pattern = f'%{search}%'
        result = await DatabaseConnection.read_query(query, search_pattern)
    else:
        result = await DatabaseConnection.read_query(query)

    if not result:
        return None

    result_dict = {}
    for row in result:
        if row[0] not in result_dict:
            result_dict[row[0]] = {
                "id": row[0],
                "title": row[1],
                "format": row[2],
                "match_format": row[3],
                "prize": row[4],
                "participants": []
            }
        if row[5]:
            result_dict[row[0]]["participants"].append(row[5])

    return list(result_dict.values())

async def get_by_id(tournament_id: int) -> Optional[Dict]:
    query = '''
        SELECT 
            t.id, 
            t.title, 
            t.format, 
            t.match_format, 
            t.prize, 
            m.id AS match_id, 
            m.format AS match_format, 
            m.date AS match_date, 
            m.tournament_type, 
            pp.full_name AS participant_name, 
            COALESCE(mp.score, 0) AS participant_score
        FROM tournament t
        LEFT JOIN match m ON t.id = m.tournament_id
        LEFT JOIN match_participants mp ON m.id = mp.match_id
        LEFT JOIN player_profiles pp ON mp.player_profile_id = pp.id
        WHERE t.id = $1
        ORDER BY m.date
    '''
    result = await DatabaseConnection.read_query(query, tournament_id)
    if not result:
        return None

    tournament_info = {
        "id": result[0][0],
        "title": result[0][1],
        "format": result[0][2],
        "match_format": result[0][3],
        "prize": result[0][4],
        "matches": []
    }

    matches = {}
    for row in result:
        match_id = row[5]
        if match_id:
            if match_id not in matches:
                matches[match_id] = {
                    "id": match_id,
                    "format": row[6],
                    "date": row[7].strftime("%Y-%m-%d %H:%M"),
                    "tournament_type": row[8],
                    "participants": []
                }
            participant_info = f"{row[9]} {row[10]}"
            matches[match_id]["participants"].append(participant_info)

    tournament_info["matches"] = list(matches.values())

    return tournament_info


async def create_knockout_matches(tournament_id, participants: List[str], match_format:str):

    participant_profiles = []
    for participant_name in participants:
        profile = await player_profile_service.get_player_profile_by_name(participant_name)
        if not profile:
            profile = await create_player_profile(participant_name)
        if not profile:
            return None
        participant_profiles.append(profile)

    for participant in participant_profiles:
        query = """INSERT INTO tournament_participants 
        (tournament_id, player_profile_id)
        VALUES ($1, $2)"""
        await DatabaseConnection.update_query(query, tournament_id,participant.id)

    random.shuffle(participant_profiles)

    days = 1
    for i in range(0, len(participant_profiles),2):
        match_data= Match(
            format=match_format,
            date= datetime.now() + timedelta(days=days),
            participants=[participant_profiles[i].full_name,participant_profiles[i + 1].full_name],
            tournament_id=tournament_id,
            tournament_type="Knockout"
        )
        match = await match_service.create(match_data)
        if not match:
            return False
        days += 1.1
    return True


async def create_league_matches(tournament_id, participants: List[str], match_format: str):

    participant_profiles = []
    for participant_name in participants:
        profile = await player_profile_service.get_player_profile_by_name(participant_name)
        if not profile:
            profile = await create_player_profile(participant_name)
        if not profile:
            return None
        participant_profiles.append(profile)


    for participant in participant_profiles:
        query = """INSERT INTO tournament_participants 
        (tournament_id, player_profile_id)
        VALUES ($1, $2)"""
        await DatabaseConnection.update_query(query, tournament_id, participant.id)


    matches = []
    for participant1, participant2 in itertools.combinations(participant_profiles, 2):
        matches.append({
            "format": match_format,
            "date": datetime.now(),
            "tournament_id": tournament_id,
            "tournament_type": "League",
            "participants": [(participant1.id, participant1.full_name),
                             (participant2.id, participant2.full_name)]
        })


    days = 1
    for match in matches:

        query = """INSERT INTO match (format, date, tournament_id, tournament_type)
        VALUES ($1, $2, $3, $4)"""
        match_id = await DatabaseConnection.insert_query(
            query,
            match["format"],
            match["date"] + timedelta(days=days),
            match["tournament_id"],
            match["tournament_type"]
        )
        if not match_id:
            return False


        participant_query = """
        INSERT INTO match_participants (match_id, player_profile_id)
        VALUES ($1, $2)
        """

        for player_id, _ in match["participants"]:
            success = await DatabaseConnection.update_query(
                participant_query,
                match_id,
                player_id
            )
            if not success:
                return False

        days += 0.1

    return True
# async def create_league_matches(tournament_id, participants: List[str], match_format:str):
#
#     participant_profiles = []
#     for participant_name in participants:
#         profile = await player_profile_service.get_player_profile_by_name(participant_name)
#         if not profile:
#             profile = await create_player_profile(participant_name)
#         if not profile:
#             return None
#         participant_profiles.append(profile)
#
#     for participant in participant_profiles:
#         query = """INSERT INTO tournament_participants
#         (tournament_id, player_profile_id)
#         VALUES ($1, $2)"""
#         await DatabaseConnection.update_query(query, tournament_id,participant.id)
#
#
#
#     matches = []
#     for participant1, participant2 in itertools.combinations(participant_profiles, 2):
#         matches.append({
#             "format": match_format,
#             "date": datetime.now(),
#             "tournament_id": tournament_id,
#             "tournament_type": "League",
#             "participants": [participant1.full_name, participant2.full_name]
#         })
#
#
#     days = 1
#     for match in matches:
#         query = """INSERT INTO match (format, date, tournament_id, tournament_type)
#         VALUES ($1, $2, $3, $4)"""
#         match_id = await DatabaseConnection.insert_query(query, match["format"], match["date"] + timedelta(days=days), match["tournament_id"], match["tournament_type"])
#         if not match_id:
#             return False
#         participant_profiles = []
#         for participant_name in match["participants"]:
#             profile = await player_profile_service.get_player_profile_by_name(participant_name)
#             if not profile:
#                 profile = await create_player_profile(participant_name)
#             if not profile:
#                 return None
#             participant_profiles.append(profile)
#             participant_query = """
#             INSERT INTO match_participants (match_id, player_profile_id)
#             VALUES ($1, $2)
#             """
#
#             for profile in participant_profiles:
#                 await DatabaseConnection.update_query(
#                     participant_query,
#                     match_id,
#                     profile.id
#                 )
#
#         days = 0.1
#
#     return True


async def advance_knockout_tournament(tournament_id: int):
    query = """
        SELECT id FROM match 
        WHERE tournament_id = $1 AND finished = False AND tournament_type = 'Knockout'
    """
    matches = await DatabaseConnection.read_query(query, tournament_id)

    if not matches:
        print(f"No ongoing matches for tournament {tournament_id}.")
        return False

    update_query = """
        UPDATE match 
        SET finished = True 
        WHERE tournament_id = $1 AND tournament_type = 'Knockout' AND finished = False
    """
    await DatabaseConnection.update_query(update_query, tournament_id)

    winners = []
    match_format = None

    for match in matches:
        match_data = await match_service.get_match_with_scores(match[0])
        if not match_data:
            continue


        if match_format is None:
            match_format = match_data['format']

        participant_scores = [p.split('-') for p in match_data["participants"]]
        winner = max(participant_scores, key=lambda x: int(x[1]))[0]
        winners.append(winner)

    if len(winners) == 1:
        return f"Tournament {tournament_id} has concluded. Winner: {winners[0]}, Score: {participant_scores[0][1]}:{participant_scores[1][1]}"

    if len(winners) < 2:
        return f"Tournament {tournament_id} cannot proceed with fewer than 2 participants."

    date_string = match_data["date"]
    date = datetime.fromisoformat(date_string)
    days = 1

    for i in range(0, len(winners), 2):
        if i + 1 >= len(winners):
            break


        new_match = Match(
            format=match_format,
            date=date + timedelta(days=days),
            participants=[winners[i], winners[i + 1]],
            tournament_id=tournament_id,
            tournament_type="Knockout"
        )

        if not await match_service.create(new_match):
            print(f"Failed to create a match for participants {winners[i]} and {winners[i + 1]}")
            return False

        days += 1

    return True

# async def finsh_league_tournament(tournament_id: int):
#     query = """
#         SELECT id FROM match 
#         WHERE tournament_id = $1 AND finished = False AND tournament_type = 'League'
#     """
#     matches = await DatabaseConnection.read_query(query, tournament_id)

#     if not matches:
#         return f"No ongoing matches for tournament {tournament_id}."
    
#     update_query = """
#         UPDATE match 
#         SET finished = True 
#         WHERE tournament_id = $1 AND tournament_type = 'League' AND finished = False
#     """
#     await DatabaseConnection.update_query(update_query, tournament_id)


async def get_league_standings(tournament_id: int):
    query = """
    SELECT player_profile_id, wins, losses, draws, points
    FROM tournament_participants
    WHERE tournament_id = $1
    ORDER BY points DESC
    """
    result = await DatabaseConnection.read_query(query, tournament_id)
    if not result:
        return None

    standings = []
    for row in result:
        standings.append({
            "Player": await get_names_by_id(row[0]),
            "Points": row[4],
            "Wins": row[1],
            "Losses": row[2],
            "Draws": row[3]
        })
    
    return standings
    


async def get_names_by_id(player_profile_id: int):
    query = """
    SELECT full_name
    FROM player_profiles
    WHERE id = $1
    """
    result = await DatabaseConnection.read_query(query, player_profile_id)
    return str(result[0][0])