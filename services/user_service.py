from jose import jwt, JWTError
from passlib.hash import bcrypt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from data.database import DatabaseConnection
from data.models import Requests, User
from passlib.hash import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from services.player_profile_service import get_player_profile_by_name
from services.notification_service import notify_user_request_handled


load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY","6a631f3a77008d5586d9ecc2ca7bea47695d575b5e6195dd6ca200829a8ae40c")
ALGORITHM = os.getenv("ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60



async def create_access_token(user_id: int, email: str) -> str:
    """
    Creates an access token and initializes a user session.
    The token has a 7-day maximum lifetime, but the session requires activity within 1 hour.
    """
    expire = datetime.now() + timedelta(days=7)  
    payload = {
        "id": user_id,
        "email": email,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
   
    SessionManager.update_session(user_id, email)
    
    return token

class SessionManager:
    """Manages user sessions and activity tracking"""
    _sessions = {}  

    @classmethod
    def update_session(cls, user_id: int, email: str):
        """Updates or creates a session for a user"""
        cls._sessions[user_id] = {
            'last_activity': datetime.now(),
            'email': email
        }
        

    @classmethod
    def is_session_active(cls, user_id: int) -> bool:
        """Checks if a user's session is still active"""
        if user_id not in cls._sessions:
           
            return False
        
        session = cls._sessions[user_id]
        last_activity = session['last_activity']
        current_time = datetime.now()
        time_diff = current_time - last_activity
        is_active = time_diff < timedelta(hours=1)
        
        
        
        return is_active

    @classmethod
    def get_user_session(cls, user_id: int) -> Optional[Dict]:
        """Retrieves session information for a user"""
        return cls._sessions.get(user_id)

    @classmethod
    def clear_session(cls, user_id: int):
        """Removes a user's session"""
        if user_id in cls._sessions:
            email = cls._sessions[user_id]['email']
            
            del cls._sessions[user_id]

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
    """
    Authenticates a user and creates both a token and an active session.
    Returns None if authentication fails.
    """
    query = "SELECT * FROM users WHERE email = $1"
    user_data = await DatabaseConnection.read_query(query, email)
    if not user_data:
        return None

    user = await get_user_by_id(user_data[0][0])
    if not user:
        return None

    if not bcrypt.verify(password, user.password):
        return None

    token = await create_access_token(user.id, user.email)
    return {"access_token": token, "token_type": "bearer"}

async def validate_token_with_session(token: str) -> Optional[Dict]:
    """
    Validates a token and checks if the associated session is active.
    Returns the token payload if valid and session is active, None otherwise.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        email = payload.get("email")
        
        if user_id and SessionManager.is_session_active(user_id):
            SessionManager.update_session(user_id, email)
            return payload
            
        return None
    except JWTError:
        return None

async def is_admin(token: str) -> bool:
    """Check if user is admin while validating their session"""
    try:
        payload = await validate_token_with_session(token)
        if not payload:
            return False

        user_id = payload.get("id")
        query = "SELECT is_admin FROM users WHERE id = $1"
        result = await DatabaseConnection.read_query(query, user_id)

        return bool(result and result[0] and result[0][0])

    except JWTError:
        return False

async def is_director(token: str) -> bool:
    """Check if user is director while validating their session"""
    try:
        payload = await validate_token_with_session(token)
        if not payload:
            return False

        user_id = payload.get("id")
        query = "SELECT is_director FROM users WHERE id = $1"
        result = await DatabaseConnection.read_query(query, user_id)

        return bool(result and result[0] and result[0][0])

    except JWTError:
        return False
    
async def logout_user(token: str) -> bool:
    """Properly logout user by clearing their session"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id:
            SessionManager.clear_session(user_id)
            return True
        return False
    except JWTError:
        return False


async def claim_request(token):
    """Claim a player profile while validating session"""
    payload = await validate_token_with_session(token)
    if not payload:
        return False
    
    user_id = payload.get("id")
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
    return False

async def claim_director_request(token):
    """Claim director status while validating session"""
    payload = await validate_token_with_session(token)
    if not payload:
        return False
    
    user_id = payload.get("id")
    query = """
        INSERT INTO requests (user_id)
        VALUES ($1)
    """
    
    result = await DatabaseConnection.insert_query(query, user_id)
    return result

async def cleanup_expired_sessions():
    """Periodically clean up expired sessions"""
    current_time = datetime.now()
    expired_users = []
    
    for user_id in SessionManager._sessions:
        if not SessionManager.is_session_active(user_id):
            expired_users.append(user_id)
    
    for user_id in expired_users:
        SessionManager.clear_session(user_id)
        
   


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

        
        if result:
            user_data = await DatabaseConnection.read_query(
                "SELECT u.id, u.last_name, u.email FROM users u JOIN requests r ON u.id = r.user_id WHERE r.id = $1",
                id
            )
            if user_data:
                await notify_user_request_handled(user_data, "player claim", approved=True)

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

        # Send notification
        if result:
            user_data = await DatabaseConnection.read_query(
                "SELECT u.id, u.last_name, u.email FROM users u JOIN requests r ON u.id = r.user_id WHERE r.id = $1",
                id
            )
            if user_data:
                await notify_user_request_handled(user_data, "director claim", approved=True)

        return result
    else:
        return status

    
async def deny_claim(id):
    query = """
    UPDATE requests
    SET approved_or_denied = False
    WHERE id = $1
    """
    status = await DatabaseConnection.update_query(query, id)

    if status:
        query = """
        DELETE FROM requests
        WHERE id = $1
        """
        result = await DatabaseConnection.update_query(query, id)

        # Send notification
        if result:
            user_data = await DatabaseConnection.read_query(
                "SELECT u.id, u.last_name, u.email FROM users u JOIN requests r ON u.id = r.user_id WHERE r.id = $1",
                id
            )
            if user_data:
                await notify_user_request_handled(user_data, "claim", approved=False)

            return True
    else:
        return False

    


