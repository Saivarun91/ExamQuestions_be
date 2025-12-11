import jwt
from datetime import datetime, timedelta
from django.conf import settings
SECRET_KEY = "kG5hQ8wZ7vLx2p9R6aT3sB4nE1mY0fJ2qW8vC5xZ9rU6oP7l"  # Change this


def generate_jwt(payload, expire_minutes=60):
    payload['exp'] = datetime.utcnow() + timedelta(minutes=expire_minutes)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token
    
def decode_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
