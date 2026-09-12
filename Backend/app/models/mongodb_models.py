from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# =========================================================
# Worker
# =========================================================

class WorkerCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    phone_number: str = Field(
        min_length=5,
        max_length=30,
    )

    role: str

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=6,
    )

    language: str = Field(
        default="en-IN",
        min_length=2,
        max_length=20,
    )


class WorkerResponse(BaseModel):

    id: str

    name: str

    phone_number: str

    role: str

    username: str

    language: str = "en-IN"


# =========================================================
# Machine
# =========================================================

class MachineResponse(BaseModel):

    id: str

    name: str

    manufacturer: str

    model: str

    user_manual_file_id: str | None = None

    technician_id: str | None = None


# =========================================================
# Issue
# =========================================================

class IssueCreate(BaseModel):

    worker_reported_id: str

    machine_id: str | None = None

    raised_issue_message: str


class IssueUpdate(BaseModel):

    response_message: str | None = None

    technician_id: str | None = None

    status: str | None = None


class IssueResponse(BaseModel):

    id: str

    worker_reported_id: str

    machine_id: str | None = None

    raised_issue_message: str

    response_message: str | None = None

    technician_id: str | None = None

    status: str

    created_at: datetime

    conversation: list[dict[str, Any]] = Field(
        default_factory=list
    )