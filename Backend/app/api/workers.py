from fastapi import APIRouter, HTTPException

from app.auth.password import hash_password
from app.models.mongodb_models import (
    WorkerCreate,
    WorkerResponse,
)
from app.repositories.mongodb_repository import (
    create_worker,
    list_workers,
)
router = APIRouter(
    prefix="/api/v1/workers",
    tags=["Workers"],
)

@router.post(
    "",
    response_model=WorkerResponse,
)
def add_worker(
    request: WorkerCreate,
):

    try:

        worker = create_worker(
            name=request.name,
            phone_number=request.phone_number,
            role=request.role,
            username=request.username,
            password_hash=hash_password(
                request.password
            ),
            language=request.language,
        )

        return WorkerResponse(
            id=str(worker["_id"]),
            name=worker["name"],
            phone_number=worker["phone_number"],
            role=worker["role"],
            username=worker["username"],
            language=worker.get(
                "language",
                "en-IN",
            ),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[WorkerResponse],
)
def get_workers():

    workers = list_workers()

    return [
        WorkerResponse(
            id=str(worker["_id"]),
            name=worker["name"],
            phone_number=worker["phone_number"],
            role=worker["role"],
            username=worker["username"],
            language=worker.get(
                "language",
                "en-IN",
            ),
        )
        for worker in workers
    ]