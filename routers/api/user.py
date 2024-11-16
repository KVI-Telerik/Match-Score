from fastapi import APIRouter, HTTPException, status
from data.models import User, UserLogin
from services.user_service import create_user, login_user

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