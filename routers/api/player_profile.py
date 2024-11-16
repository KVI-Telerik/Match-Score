
from fastapi import APIRouter, HTTPException, status, Header
from data.models import User, UserLogin, PlayerProfile
from services import player_profile_service
from services.user_service import create_user, login_user, is_admin

players_profiles_router = APIRouter(prefix='/api/player_profiles', tags=['player_profiles'])


@players_profiles_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_profile(
        player_profile_data: PlayerProfile,
        token: str = Header(None)
):


    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing"
        )


    is_admin_user = await is_admin(token)
    if not is_admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    player_profile = await player_profile_service.create(player_profile_data)
    if not player_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="player with this fullname already exists"
        )

    return {"message": "player registered successfully"}
