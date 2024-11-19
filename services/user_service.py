from fastapi import HTTPException, Header
from passlib.context import CryptContext
from starlette import status

# from common.auth_middleware import validate_token
from data.database import DatabaseConnection
from data.models import Requests, User
from passlib.hash import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Union

from services.player_profile_service import get_player_profile_by_name

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "6a631f3a77008d5586d9ecc2ca7bea47695d575b5e6195dd6ca200829a8ae40c"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

async def all_users() -> List[User]:
    query = "SELECT * FROM users"
    users = await DatabaseConnection.read_query(query)
    return [User.from_query_result(*user) for user in users]

async def get_user_by_id(user_id: int) -> Optional[User]:
    query = "SELECT * FROM users WHERE id = $1"
    user = await DatabaseConnection.read_query(query, user_id)
    if user:
        return User.from_query_result(*user[0])
    return None

async def create_user(user: User) -> Optional[User]:
    duplicate_query = "SELECT * FROM users WHERE username = $1 OR email = $2"
    duplicate_user = await DatabaseConnection.read_query(
        duplicate_query,
        user.username,
        user.email
    )
    if duplicate_user:
        return None

    user.password = bcrypt.hash(user.password)

    query = """
        INSERT INTO users (first_name, last_name, username, password, email)
        VALUES ($1, $2, $3, $4, $5)
    """
    user.id = await DatabaseConnection.insert_query(
        query,
        user.first_name,
        user.last_name,
        user.username,
        user.password,
        user.email
    )
    return user

async def login_user(email: str, password: str) -> Optional[Dict[str, str]]:
    query = "SELECT * FROM users WHERE email = $1"
    user_data = await DatabaseConnection.read_query(query, email)
    if not user_data:
        return None

    user = await get_user_by_id(user_data[0][0])
    if not user:
        return None

    if not bcrypt.verify(password, user.password):
        return None

    expire = datetime.now().astimezone() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "id": user.id,
        "email": user.email,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


async def is_admin(token: str) -> bool:

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            return False

        query = "SELECT is_admin FROM users WHERE id = $1"
        result = await DatabaseConnection.read_query(query, user_id)

        if result and result[0] and result[0][0]:
            return True
        return False

    except JWTError:
        return False

async def is_director(token: str) -> bool:

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            return False

        query = "SELECT is_director FROM users WHERE id = $1"
        result = await DatabaseConnection.read_query(query, user_id)

        if result and result[0] and result[0][0]:
            return True
        return False

    except JWTError:
        return False


async def claim_request(token):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("id")
    if user_id is None:
        return False
    user = await get_user_by_id(user_id)
    first_name = user.first_name
    last_name = user.last_name
    fullname = first_name + " " + last_name

    player_profile = await get_player_profile_by_name(fullname)
    if player_profile:
       query = """
       INSERT INTO requests (user_id, player_profile_id)
        VALUES ($1, $2)
       """

       result = await DatabaseConnection.insert_query(query, user_id, player_profile.id)
       return result
    

async def claim_director_request(token):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("id")
    if user_id is None:
        return False
    
    query = """
        INSERT INTO requests (user_id)
        VALUES ($1)
       """
    
    result = await DatabaseConnection.insert_query(query, user_id)
    return result


async def all_requests():
    query = """
     SELECT * FROM requests
    """
    result = await DatabaseConnection.read_query(query)
    return [Requests.from_query_result(*row) for row in result]

async def claim_type(id):
    query = """
     SELECT player_profile_id FROM requests
     WHERE id = $1
    """
    result = await DatabaseConnection.read_query(query, id)
    if result[0][0] is None:
        return 'director claim'
    else:
        return 'player claim'
    

async def approve_player_claim(id):
    query = """
    UPDATE requests
    SET approved_or_denied = True
    WHERE id = $1
    """
    status = await DatabaseConnection.update_query(query, id)
    if status:
        query = """
        UPDATE users
        SET player_profile_id = r.player_profile_id
        FROM requests r
        WHERE users.id = r.user_id
        AND r.id = $1
        """
        result = await DatabaseConnection.update_query(query, id)
        return result
    else:
        return status

async def approve_director_claim(id):
    query = """
    UPDATE requests
    SET approved_or_denied = True
    WHERE id = $1
    """
    status = await DatabaseConnection.update_query(query, id)
    if status:
        query = """
        UPDATE users
        SET is_director = True
        FROM requests r
        WHERE users.id = r.user_id
        AND r.id = $1
        """
        result = await DatabaseConnection.update_query(query, id)
        return result
    else:
        return status