from datetime import datetime, timezone, timedelta
import os
from passlib.context import CryptContext
from jose import jwt

ACCESS_TOKEN_EXPIRE_MINUTES = 60
ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hash: str):
    return pwd_context.verify(password, hash)

def create_access_token(username: str):
    to_encode = { 
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) 
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)