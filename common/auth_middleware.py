from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from data.database import DatabaseConnection
from services.user_service import SECRET_KEY, ALGORITHM, get_user_by_id
from jose import jwt

security = HTTPBearer()

def validate_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def auth_middleware(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    request.state.user = validate_token(token)

# async def is_admin(token: str) -> bool:
#     """
#     Check if a user is an admin based on their JWT token.
#
#     Args:
#         token (str): JWT token from the request
#
#     Returns:
#         bool: True if user is admin, False otherwise
#     """
#     try:
#         payload = validate_token(token)
#         user_id = payload["id"]
#
#         query = "SELECT is_admin FROM users WHERE id = $1"
#         result = await DatabaseConnection.read_query(query, user_id)
#
#         # Check if we got a result and if is_admin is True
#         return bool(result and result[0][0])
#
#     except Exception as e:
#         print(f"Error checking admin status: {e}")
#         return False

def get_user_if_token(request: Request):
    token = request.cookies.get("access_token")
    if token:
       payload = validate_token(token)
       user = get_user_by_id(payload["id"])
       print(payload["id"])
       print('-------------')
       print(user)
       return user
    else:
        return None
    







