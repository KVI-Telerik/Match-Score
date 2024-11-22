
from fastapi import APIRouter, HTTPException, status, Header
from data.models import User, UserLogin, PlayerProfile
from services import player_profile_service, user_service
from services.user_service import ALGORITHM, SECRET_KEY, create_user, login_user, is_admin
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


@players_profiles_router.patch('/{id}', status_code=status.HTTP_200_OK)
async def update_profile(
    id: int,  # The ID of the profile to update
    player_profile_data: PlayerProfile,
    token: str = Header(None)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing"
        )

    # Decode and validate the token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Fetch the user making the request
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    # Fetch the player profile to update
    player_profile = await player_profile_service.get_by_id(id)
    if not player_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player profile not found"
        )

    # Use check_linked_user to determine if the player profile is linked to a user
    linked_player_profile_id = await user_service.check_linked_user(user.id)

    if linked_player_profile_id:
        # If the profile is linked, only the linked user can update it
        if linked_player_profile_id != id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to edit this profile"
            )
    else:
        # If the profile is not linked, only directors can update it
        if not user.is_director:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only directors can edit unlinked profiles"
            )

    # Perform the update
    updated_player_profile = await player_profile_service.update(id,player_profile_data)
    if not updated_player_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player profile update failed (e.g., duplicate full name)"
        )

    return {"message": "Player profile updated successfully"}
