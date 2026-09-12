from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import get_settings


ALGORITHM = "HS256"


def create_access_token(
    user_id: str,
    username: str,
    role: str,
) -> str:

    settings = get_settings()

    if not settings.jwt_secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured"
        )

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=settings.jwt_expire_minutes
    )

    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )