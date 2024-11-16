from data.database import read_query, insert_query
from data.models import User
from passlib.hash import bcrypt
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "6a631f3a77008d5586d9ecc2ca7bea47695d575b5e6195dd6ca200829a8ae40c"  
ALGORITHM = "HS256"  
ACCESS_TOKEN_EXPIRE_MINUTES = 60  


def all_users():
    query = "SELECT * FROM users"
    users = read_query(query)
    return [User.from_query_result(*user) for user in users]


def get_user_by_id(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    user = read_query(query, (user_id,))
    if user:
        return User.from_query_result(*user[0])
    return None

def create_user(user: User):
    duplicate_query = "SELECT * FROM users WHERE username = %s OR email = %s"
    duplicate_user = read_query(duplicate_query, (user.username, user.email))
    if duplicate_user:
        return None  

    user.password = bcrypt.hash(user.password)

    query = """
        INSERT INTO users (first_name, last_name, username, password, email)
        VALUES (%s, %s, %s, %s, %s)
    """
    user.id = insert_query(query, (
        user.first_name, user.last_name, user.username, user.password, user.email,
    ))
    return user

def login_user(email: str, password: str):
    query = "SELECT * FROM users WHERE email = %s"
    user_data = read_query(query, (email,))
    if not user_data:
        return None  

    user = get_user_by_id(user_data[0][0])

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

