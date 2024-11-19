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

async def create_league_matches(tournament_id, participants: List[str], match_format:str):

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


    
    matches = []
    for participant1, participant2 in itertools.combinations(participant_profiles, 2):
        matches.append({
            "format": match_format,
            "date": datetime.now(),
            "tournament_id": tournament_id,
            "tournament_type": "League",
            "participants": [participant1.full_name, participant2.full_name]
        })
    
   
    days = 1
    for match in matches:
        query = """INSERT INTO match (format, date, tournament_id, tournament_type)
        VALUES ($1, $2, $3, $4)"""
        match_id = await DatabaseConnection.insert_query(query, match["format"], match["date"] + timedelta(days=days), match["tournament_id"], match["tournament_type"])
        if not match_id:
            return False
        participant_profiles = []
        for participant_name in match["participants"]:
            profile = await player_profile_service.get_player_profile_by_name(participant_name)
            if not profile:
                profile = await create_player_profile(participant_name)
            if not profile:
                return None
            participant_profiles.append(profile)
            participant_query = """
            INSERT INTO match_participants (match_id, player_profile_id)
            VALUES ($1, $2)
            """

            for profile in participant_profiles:
                await DatabaseConnection.update_query(
                    participant_query,
                    match_id,
                    profile.id
                )

        days = 0.1
        
    return True
        
        
    




