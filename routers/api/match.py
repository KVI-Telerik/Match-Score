from fastapi import APIRouter, HTTPException, Header, status
from typing import List
from data.models import Match, PlayerProfile
from services import match_service
from services.user_service import is_admin
from datetime import datetime

matches_router = APIRouter(prefix='/api/matches', tags=['matches'])

@matches_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_new_match(
    match_data: Match,
    token: str = Header(None)
):
    """Create a new match with automatic player profile creation"""
    if not token or not await is_admin(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    if len(match_data.participants) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match must have at least 2 participants"
        )

    match = await match_service.create(match_data)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create match. Check for duplicate player names or missing player data."
        )
    return match

@matches_router.patch('/{match_id}/player_profile/{player_id}', status_code=status.HTTP_200_OK)
async def update_match_score(
    match_id: int,
    player_id: int,
    score: int,
    token: str = Header(None)
):
    """Update match score for a player"""
    if not token or not await is_admin(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    match = await match_service.update_score(match_id, player_id, score)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update match score. Check for missing player or match data."
        )
    return {"message": "Match score updated successfully"}

@matches_router.patch('/{id}/date', status_code=status.HTTP_200_OK)
async def reschedule_match(
    match_id: int,
    new_date: datetime,
    token: str = Header(None)
):
    """Reschedule match date"""
    if not token or not await is_admin(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    match = await match_service.reschedule_match(match_id, new_date)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reschedule match. Check for missing match data."
        )
    return {"message": "Match rescheduled", "new_date": match.date}