from fastapi import APIRouter, HTTPException, status, Header
from data.models import User, UserLogin
from services.user_service import all_requests, approve_director_claim, approve_player_claim, claim_director_request, claim_request, claim_type, create_user, is_admin, login_user

users_router = APIRouter(prefix='/api/users', tags=['users'])

@users_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: User):
    """
    Register a new user.
    """
    user = await create_user(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )
    return {"message": "User registered successfully", "user_id": user.id}

@users_router.post("/login")
async def login_user_endpoint(login_data: UserLogin):
    """
    Log in a user and return a JWT token.
    """
    token = await login_user(login_data.email, login_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    return token

@users_router.post("/player_profile",status_code=status.HTTP_200_OK)
async def claim_player_profile(token: str = Header(None)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing"
        )

    awaiting_approval = await claim_request(token)
    if not awaiting_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player profile with such name can`t be claimed or does not exist"
        )    
    return {"message": "awaiting approval"}


@users_router.post("/director_profile",status_code=status.HTTP_200_OK)
async def claim_director_profile(token: str = Header(None)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing"
        )

    awaiting_approval = await claim_director_request(token)
    if not awaiting_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player profile with such name can`t be claimed or does not exist"
        )
    return {"message": "awaiting approval"}

@users_router.get("/requests",status_code=status.HTTP_200_OK)
async def get_all_requests(token: str = Header(None)):
    if not token or not await is_admin(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    result = await all_requests()
    return result


@users_router.put("/player_request/{id}",status_code=status.HTTP_200_OK)
async def approve_player_request(id:int ,token: str = Header(None)):
    if not token or not await is_admin(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    claim = await claim_type(id)
    
    if claim != 'player claim':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Wrong claim.")
    approved = await approve_player_claim(id)
    if approved:
        return {"message": "approved!"}
    else: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to approve request.")
    


@users_router.put("/director_request/{id}",status_code=status.HTTP_200_OK)
async def approve_player_request(id:int ,token: str = Header(None)):
    if not token or not await is_admin(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    claim = await claim_type(id)
    if claim != 'director claim':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Wrong claim.")
    approved = await approve_director_claim(id)
    if approved:
        return {"message": "approved!"}
    else: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to approve request.")
    