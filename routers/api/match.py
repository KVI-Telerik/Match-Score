from fastapi import APIRouter, HTTPException, Header, status
from typing import List
from data.models import Match, PlayerProfile
from services import match_service
from services.match_service import create
from services.user_service import is_admin, is_director

matches_router = APIRouter(prefix='/api/matches', tags=['matches'])

@matches_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_new_match(
    match_data: Match,
    token: str = Header(None)
):

    if not token or not await is_admin(token):
        if not await is_director(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or director access required"
            )

    if len(match_data.participants) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match must have at least 2 participants"
        )

    match = await create(match_data)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create match. Check for duplicate player names or missing player data."
        )
    return match

# @matches_router.get('/', response_model=Match)
# async def get_matches(sort: str | None = None, sort_by: str | None = None):

@matches_router.get('/{match_id}', response_model=Match)
async def get_match_by_id(match_id: int):
    match = await match_service.get_match_with_scores(match_id)

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    return match