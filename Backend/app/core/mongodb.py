from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    settings = get_settings()

    if not settings.mongodb_uri:
        raise RuntimeError(
            "MONGODB_URI is not configured"
        )

    return MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5000,
    )


def get_database() -> Database:
    settings = get_settings()

    return get_mongo_client()[
        settings.mongodb_database
    ]


def close_mongo_connection() -> None:
    get_mongo_client().close()


def create_indexes() -> None:
    db = get_database()

    # Workers
    db.workers.create_index(
        "username",
        unique=True,
    )

    db.workers.create_index(
        "role",
    )

    # Machines
    db.machines.create_index(
        "name",
    )

    db.machines.create_index(
        "manufacturer",
    )

    db.machines.create_index(
        "model",
    )

    # Issues
    db.issues.create_index(
        "worker_reported_id",
    )

    db.issues.create_index(
        "machine_id",
    )

    db.issues.create_index(
        "technician_id",
    )

    db.issues.create_index(
        "status",
    )

    db.issues.create_index(
        "created_at",
    )