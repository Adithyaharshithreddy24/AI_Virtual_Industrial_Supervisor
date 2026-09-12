from fastapi import APIRouter, HTTPException, status

from app.auth.password import verify_password
from app.auth.security import create_access_token
from app.core.mongodb import get_database


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post("/login")
def login(
    username: str,
    password: str,
):
    db = get_database()

    username = username.strip().lower()

    # =====================================================
    # CHECK WORKERS / TECHNICIANS
    # =====================================================

    worker = db.workers.find_one(
        {
            "username": username
        }
    )

    if worker:

        password_hash = worker.get(
            "password_hash"
        )

        if not password_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account password is not configured.",
            )

        if not verify_password(
            password,
            password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        user_id = str(
            worker["_id"]
        )

        role = worker.get(
            "role",
            "worker",
        )

        token = create_access_token(
            user_id=user_id,
            username=worker["username"],
            role=role,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": worker["username"],
                "name": worker.get(
                    "name",
                    "",
                ),
                "role": role,
                "phone_number": worker.get(
                    "phone_number",
                    "",
                ),
                "language": worker.get(
                    "language",
                    "en-IN",
                ),
            },
        }


    # =====================================================
    # CHECK MANAGERS
    # =====================================================

    manager = db.managers.find_one(
        {
            "username": username
        }
    )

    if manager:

        password_hash = manager.get(
            "password_hash"
        )

        if not password_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Manager password is not configured.",
            )

        if not verify_password(
            password,
            password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        user_id = str(
            manager["_id"]
        )

        token = create_access_token(
            user_id=user_id,
            username=manager["username"],
            role="manager",
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": manager["username"],
                "name": manager.get(
                    "name",
                    "",
                ),
                "role": "manager",
                "phone_number": manager.get(
                    "phone_number",
                    "",
                ),
                "language": manager.get(
                    "language",
                    "en-IN",
                ),
            },
        }


    # =====================================================
    # USER NOT FOUND
    # =====================================================

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password.",
    )