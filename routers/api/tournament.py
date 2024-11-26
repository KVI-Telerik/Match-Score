from fastapi import APIRouter, HTTPException, Header, status
from typing import List
from data.models import Tournament, PlayerProfile
from services import tournament_service
from services.user_service import is_admin, is_director
from datetime import datetime

tournaments_router = APIRouter(prefix='/api/tournaments', tags=['tournaments'])

@tournaments_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_tournament(
    tournament_data: Tournament,
    participants: List[str],
    token: str = Header(None)
):
    if not token or not await is_admin(token):
        if not await is_director(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or director access required"
            )

    if len(participants) < 2 or len(participants) % 2 != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament must have at least 2 participants and the total number of participants has to be even"
        )

    tournament = await tournament_service.create(tournament_data, participants)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create tournament"
        )
    return tournament

@tournaments_router.post('/{id}/next_round',status_code=status.HTTP_201_CREATED)
async def next_round_knockout(tournament_id:int,token: str = Header(None)):
    if not token or not await is_admin(token):
        if not await is_director(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or director access required"
            )
    success = await tournament_service.advance_knockout_tournament(tournament_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to advance tournament"
        )
    
    if success != True:
        return success
    return {"message": "Tournament is proceeding to next stage!"}




@tournaments_router.get('/league/{tournament_id}/standings', status_code=status.HTTP_200_OK)
async def get_standings(tournament_id: int):
    tournament = await tournament_service.get_league_standings(tournament_id)

    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    return tournament

@tournaments_router.get('/')
async def get_tournaments():
    tournaments = await tournament_service.get_all()
    if not tournaments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tournaments found"
        )
    return tournaments

@tournaments_router.get('/{id}')
async def get_tournament(id: int):
    tournament = await tournament_service.get_by_id(id)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found"
        )
    return tournament

    
    