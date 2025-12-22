from datetime import datetime, timedelta
from jose import jwt
from core.config import SECRET_KEY, ALGORITHM

def create_access_token(data: dict, minutes: int = 60):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=minutes)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)