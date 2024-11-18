from fastapi import APIRouter, HTTPException, Header, status
from typing import List
from data.models import Tournament, PlayerProfile
from services import tournament_service
from services.user_service import is_admin
from datetime import datetime

tournaments_router = APIRouter(prefix='/api/tournaments', tags=['tournaments'])

@tournaments_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_tournament(
    tournament_data: Tournament,
    participants: List[str],
    token: str = Header(None)
):
    if not token or not await is_admin(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    if len(participants) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament must have at least 2 participants"
        )

    tournament = await tournament_service.create(tournament_data, participants)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create tournament"
        )
    return tournament