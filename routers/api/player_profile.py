
from fastapi import APIRouter, HTTPException, status, Header


from data.models import PlayerProfile,UpdateProfile
from services import player_profile_service,user_service

# from services.user_service import ALGORITHM, SECRET_KEY, create_user, login_user, is_admin
from jose import jwt

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


    is_admin_user = await user_service.is_admin(token)
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


@players_profiles_router.patch('/{player_profile_id}', status_code=status.HTTP_200_OK)
async def update_profile(
    player_profile_id: int,  # The ID of the profile to update
    player_profile_data: UpdateProfile,
    token: str = Header(None)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing"
        )

    payload = jwt.decode(token, user_service.SECRET_KEY, algorithms=[user_service.ALGORITHM])

    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )


    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )


    player_profile = await player_profile_service.get_by_id(player_profile_id)
    if not player_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player profile not found"
        )


    profile_linked_user_id = await player_profile_service.get_user_id(player_profile_id)

    if profile_linked_user_id:

        if profile_linked_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to edit this profile"
            )
    else:

        if not user.is_director:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only directors can edit unlinked profiles"
            )


    updated_player_profile = await player_profile_service.update(player_profile_id, player_profile_data)
    if not updated_player_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player profile update failed (e.g., duplicate full name)"
        )

    return {"message": "Player profile updated successfully"}

@players_profiles_router.delete('/{player_profile_id}', status_code=status.HTTP_200_OK)
async def delete_profile(
    player_profile_id: int,
    token: str = Header(None)
):
    """Delete a player profile"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing"
        )

    is_admin_user = await user_service.is_admin(token)
    if not is_admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    success = await player_profile_service.delete_player_profile(player_profile_id)
    if success is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player profile not found"
        )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion unsuccessful"
        )

    return {"message": "Player deleted successfully"}

@players_profiles_router.get('/', status_code=status.HTTP_200_OK)
async def get_all_profiles(search: str = None):
    """Get all player profiles"""
    if search:
        profiles = await player_profile_service.get_all(search)
    else:
        profiles = await player_profile_service.get_all()
    
    return profiles

@players_profiles_router.get('/{player_profile_id}', status_code=status.HTTP_200_OK)
async def get_profile(player_profile_id: int):
    """Get a player profile by ID"""
    profile = await player_profile_service.get_profile_by_id(player_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player profile not found"
        )

    return profile