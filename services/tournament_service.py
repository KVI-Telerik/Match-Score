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

    if tournament_data.format == "knockout":
        matches_created = await create_knockout_matches(tournament_id,participants,tournament_data.match_format)
    elif tournament_data.format == "league":
        pass


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
        ($1, $2)"""
        await DatabaseConnection.update_query(query, tournament_id,participant.id)

    random.shuffle(participant_profiles)

    for i in range(0, len(participant_profiles),2):
        match_data= Match(
            format=match_format,
            date= datetime.now() + timedelta(days=1),
            participants=[participant_profiles[i].full_name,participant_profiles[i + 1].full_name],
            tournament_id=tournament_id,
        )
        match = await match_service.create(match_data)
        if not match:
            return False
    return True




