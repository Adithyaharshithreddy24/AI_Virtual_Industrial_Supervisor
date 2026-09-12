from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.models.mongodb_models import MachineResponse
from app.repositories.mongodb_repository import (
    create_machine,
    get_worker,
    get_machine,
    list_machines,
    update_machine_manual,
)
from app.services.manual_storage import ManualStorage


router = APIRouter(
    prefix="/api/v1/machines",
    tags=["Machines"],
)

@router.post(
    "",
    response_model=MachineResponse,
)
async def add_machine(
    name: str = Form(...),
    manufacturer: str = Form(...),
    model: str = Form(...),
    technician_id: str = Form(...),
    user_manual: UploadFile | None = File(None),
):

    try:
        technician = get_worker(technician_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not technician or technician.get("role") != "technician":
        raise HTTPException(
            status_code=400,
            detail="Selected account is not a technician",
        )

    file_id = None

    if user_manual:

        if user_manual.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="User manual must be a PDF",
            )

        content = await user_manual.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="PDF file is empty",
            )

    machine = create_machine(
        name=name,
        manufacturer=manufacturer,
        model=model,
        technician_id=technician_id,
    )

    machine_id = str(machine["_id"])

    if user_manual:

        file_id = ManualStorage().save_pdf(
            filename=user_manual.filename
            or "manual.pdf",
            content=content,
            machine_id=machine_id,
        )

        update_machine_manual(
            machine_id,
            file_id,
        )

        machine["user_manual_file_id"] = file_id

    return MachineResponse(
        id=machine_id,
        name=machine["name"],
        manufacturer=machine["manufacturer"],
        model=machine["model"],
        user_manual_file_id=file_id,
        technician_id=(
            str(machine["technician_id"])
            if machine.get("technician_id")
            else None
        ),
    )


@router.get(
    "",
    response_model=list[MachineResponse],
)
def get_machines():

    machines = list_machines()

    return [
        MachineResponse(
            id=str(machine["_id"]),
            name=machine["name"],
            manufacturer=machine["manufacturer"],
            model=machine["model"],
            user_manual_file_id=machine.get(
                "user_manual_file_id"
            ),
            technician_id=(
                str(machine["technician_id"])
                if machine.get("technician_id")
                else None
            ),
        )
        for machine in machines
    ]


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
)
def get_machine_by_id(
    machine_id: str,
):

    machine = get_machine(machine_id)

    if not machine:

        raise HTTPException(
            status_code=404,
            detail="Machine not found",
        )

    return MachineResponse(
        id=str(machine["_id"]),
        name=machine["name"],
        manufacturer=machine["manufacturer"],
        model=machine["model"],
        user_manual_file_id=machine.get(
            "user_manual_file_id"
        ),
        technician_id=(
            str(machine["technician_id"])
            if machine.get("technician_id")
            else None
        ),
    )