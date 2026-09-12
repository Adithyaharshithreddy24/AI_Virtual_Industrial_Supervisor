from datetime import datetime
from typing import Any

from bson import ObjectId

from app.core.mongodb import get_database


def _id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise ValueError(
            f"Invalid MongoDB ObjectId: {value}"
        ) from exc


# =========================================================
# WORKERS
# =========================================================

def create_worker(
    name: str,
    phone_number: str,
    role: str,
    username: str,
    password_hash: str,
    language: str = "en-IN",
) -> dict[str, Any]:

    db = get_database()

    if role not in {"worker", "technician"}:
        raise ValueError(
            "Role must be worker or technician"
        )

    if db.workers.find_one(
        {"username": username}
    ):
        raise ValueError(
            "Username already exists"
        )

    document = {
        "name": name,
        "phone_number": phone_number,
        "role": role,
        "username": username,
        "password_hash": password_hash,
        "language": language,
        "created_at": datetime.utcnow(),
    }

    result = db.workers.insert_one(document)

    document["_id"] = result.inserted_id

    return document


def get_worker_by_username(
    username: str,
) -> dict[str, Any] | None:

    return get_database().workers.find_one(
        {"username": username}
    )


def get_worker(
    worker_id: str,
) -> dict[str, Any] | None:

    return get_database().workers.find_one(
        {"_id": _id(worker_id)}
    )


def get_default_technician() -> dict[str, Any] | None:

    return get_database().workers.find_one(
        {"role": "technician"},
        sort=[("created_at", -1)],
    )


def get_technician_for_machine(
    machine_id: str | None,
) -> dict[str, Any] | None:
    if not machine_id:
        return get_default_technician()

    try:
        machine = get_machine(machine_id)
    except ValueError:
        return get_default_technician()
    if not machine or not machine.get("technician_id"):
        return get_default_technician()

    return get_database().workers.find_one(
        {
            "_id": machine["technician_id"],
            "role": "technician",
        }
    ) or get_default_technician()


def list_workers(
    role: str | None = None,
) -> list[dict[str, Any]]:

    query = {}

    if role:
        query["role"] = role

    return list(
        get_database()
        .workers
        .find(query)
        .sort("created_at", -1)
    )


# =========================================================
# MACHINES
# =========================================================

def create_machine(
    name: str,
    manufacturer: str,
    model: str,
    user_manual_file_id: str | None = None,
    technician_id: str | None = None,
) -> dict[str, Any]:

    document = {
        "name": name,
        "manufacturer": manufacturer,
        "model": model,
        "user_manual_file_id": user_manual_file_id,
        "technician_id": (
            _id(technician_id)
            if technician_id
            else None
        ),
        "created_at": datetime.utcnow(),
    }

    result = get_database().machines.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return document


def get_machine(
    machine_id: str,
) -> dict[str, Any] | None:

    return get_database().machines.find_one(
        {"_id": _id(machine_id)}
    )


def list_machines() -> list[dict[str, Any]]:

    return list(
        get_database()
        .machines
        .find()
        .sort("created_at", -1)
    )


def update_machine_manual(
    machine_id: str,
    file_id: str,
) -> None:

    get_database().machines.update_one(
        {"_id": _id(machine_id)},
        {
            "$set": {
                "user_manual_file_id": file_id,
            }
        },
    )


# =========================================================
# ISSUES
# =========================================================

def create_issue(
    worker_reported_id: str,
    machine_id: str | None,
    raised_issue_message: str,
) -> dict[str, Any]:

    document = {
        "worker_reported_id": _id(
            worker_reported_id
        ),
        "machine_id": (
            _id(machine_id)
            if machine_id
            else None
        ),
        "raised_issue_message": raised_issue_message,
        "response_message": None,
        "technician_id": None,
        "status": "yet to resolve",
        "created_at": datetime.utcnow(),
        "conversation": [
            {
                "role": "user",
                "content": raised_issue_message,
                "created_at": datetime.utcnow(),
            }
        ],
    }

    result = get_database().issues.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return document


def get_issue(
    issue_id: str,
) -> dict[str, Any] | None:

    return get_database().issues.find_one(
        {"_id": _id(issue_id)}
    )


def list_issues(
    status: str | None = None,
    worker_reported_id: str | None = None,
) -> list[dict[str, Any]]:

    query = {}

    if status:
        query["status"] = status

    if worker_reported_id:
        query["worker_reported_id"] = _id(
            worker_reported_id
        )

    return list(
        get_database()
        .issues
        .find(query)
        .sort("created_at", -1)
    )


def update_issue(
    issue_id: str,
    updates: dict[str, Any],
) -> dict[str, Any] | None:

    clean_updates = {
        key: value
        for key, value in updates.items()
        if value is not None
    }

    if not clean_updates:
        return get_issue(issue_id)

    if "technician_id" in clean_updates:
        clean_updates["technician_id"] = _id(
            clean_updates["technician_id"]
        )

    get_database().issues.update_one(
        {"_id": _id(issue_id)},
        {"$set": clean_updates},
    )

    return get_issue(issue_id)


def append_issue_message(
    issue_id: str,
    message: dict[str, Any],
) -> dict[str, Any] | None:

    get_database().issues.update_one(
        {"_id": _id(issue_id)},
        {"$push": {"conversation": message}},
    )

    return get_issue(issue_id)