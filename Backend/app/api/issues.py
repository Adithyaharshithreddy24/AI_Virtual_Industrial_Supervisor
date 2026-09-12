from fastapi import APIRouter, HTTPException

from app.models.mongodb_models import (
    IssueCreate,
    IssueResponse,
    IssueUpdate,
)
from app.repositories.mongodb_repository import (
    create_issue,
    get_issue,
    list_issues,
    update_issue,
)


router = APIRouter(
    prefix="/api/v1/issues",
    tags=["Issues"],
)


def serialize_issue(
    issue: dict,
) -> IssueResponse:

    technician_id = issue.get(
        "technician_id"
    )

    return IssueResponse(
        id=str(issue["_id"]),
        worker_reported_id=str(
            issue["worker_reported_id"]
        ),
        machine_id=(
            str(issue["machine_id"])
            if issue.get("machine_id")
            else None
        ),
        raised_issue_message=issue[
            "raised_issue_message"
        ],
        response_message=issue.get(
            "response_message"
        ),
        technician_id=(
            str(technician_id)
            if technician_id
            else None
        ),
        status=issue.get(
            "status",
            "yet to resolve",
        ),
        created_at=issue[
            "created_at"
        ],
        conversation=issue.get(
            "conversation",
            [],
        ),
    )


@router.post(
    "",
    response_model=IssueResponse,
)
def add_issue(
    request: IssueCreate,
):

    try:

        issue = create_issue(
            worker_reported_id=request.worker_reported_id,
            machine_id=request.machine_id,
            raised_issue_message=request.raised_issue_message,
        )

        return serialize_issue(issue)

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[IssueResponse],
)
def get_issues(
    status: str | None = None,
    worker_id: str | None = None,
    technician_id: str | None = None,
):

    try:
        issues = list_issues(
            status,
            worker_reported_id=worker_id,
            technician_id=technician_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return [
        serialize_issue(issue)
        for issue in issues
    ]


@router.get(
    "/{issue_id}",
    response_model=IssueResponse,
)
def get_issue_by_id(
    issue_id: str,
):

    issue = get_issue(issue_id)

    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found",
        )

    return serialize_issue(issue)


@router.patch(
    "/{issue_id}",
    response_model=IssueResponse,
)
def modify_issue(
    issue_id: str,
    request: IssueUpdate,
    technician_id: str | None = None,
):

    try:
        existing_issue = get_issue(issue_id)

        if not existing_issue:
            raise HTTPException(
                status_code=404,
                detail="Issue not found",
            )

        if technician_id and str(
            existing_issue.get("technician_id")
        ) != technician_id:
            raise HTTPException(
                status_code=403,
                detail="Issue is not assigned to this technician",
            )

        issue = update_issue(
            issue_id,
            request.model_dump(
                exclude_none=True
            ),
        )

        if not issue:

            raise HTTPException(
                status_code=404,
                detail="Issue not found",
            )

        return serialize_issue(issue)

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc