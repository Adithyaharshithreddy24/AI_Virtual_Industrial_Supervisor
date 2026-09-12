from datetime import datetime
import logging
from xml.sax.saxutils import escape

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app.core.config import get_settings
from app.models.schemas import (
    CallRequest,
    HealthResponse,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SuperviseTextRequest,
)
from app.rag.ingestion import run_ingestion
from app.rag.retriever import get_collection_health
from app.services.audio import AudioService
from app.services.query import run_query
from app.services.supervisor import IndustrialSupervisor
from app.services.telephony import TechnicianCallService
from app.services.transcription import SarvamTranscriber
from app.repositories.mongodb_repository import (
    append_issue_message,
    create_issue,
    get_technician_for_machine,
    get_issue,
    update_issue,
)
from app.services.speech import SarvamSpeechService

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


def _persist_analysis(
    message: str,
    worker_id: str | None,
    machine_id: str | None,
    issue_id: str | None,
    domain_filter: str | None,
) -> dict:
    if not worker_id:
        raise HTTPException(
            status_code=400,
            detail="worker_id is required to save an issue",
        )

    try:
        issue = (
            get_issue(issue_id)
            if issue_id
            else create_issue(
                worker_reported_id=worker_id,
                machine_id=machine_id,
                raised_issue_message=message,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not issue:
        raise HTTPException(
            status_code=404,
            detail="Issue not found",
        )

    if str(issue["worker_reported_id"]) != worker_id:
        raise HTTPException(
            status_code=403,
            detail="Issue does not belong to this worker",
        )

    if issue_id:
        append_issue_message(
            issue_id,
            {
                "role": "user",
                "content": message,
                "created_at": datetime.utcnow(),
            },
        )

    technician = get_technician_for_machine(machine_id)
    technician_language = (
        technician.get("language", "en-IN")
        if technician
        else "en-IN"
    )
    technician_phone_number = (
        technician.get("phone_number", "")
        if technician
        else ""
    )

    try:
        decision = IndustrialSupervisor().analyze(
            message,
            domain_filter=domain_filter,
            technician_language=technician_language,
            technician_phone_number=technician_phone_number,
        )
    except Exception as exc:
        error_text = str(exc)
        if (
            "RESOURCE_EXHAUSTED" in error_text
            or "429" in error_text
            or "quota" in error_text.lower()
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "AI analysis quota is temporarily exhausted. "
                    "Your report was saved; please try again later "
                    "or configure a Google AI project with available quota."
                ),
            ) from exc

        raise HTTPException(
            status_code=502,
            detail=f"Supervisor analysis failed: {exc}",
        ) from exc

    if (
        not decision.worker_can_resolve
        and not decision.technician_alert_sent
        and technician
    ):
        try:
            call_result = TechnicianCallService().call_technician(
                message=decision.technician_message or message,
                technician=technician,
                language_code=technician_language,
            )
            decision.technician_alert_sent = bool(
                call_result.get("success")
                and call_result.get("call_sid")
            )
            decision.technician_call_sid = call_result.get(
                "call_sid"
            )
        except Exception as exc:
            logger.exception(
                "Assigned technician call could not be initiated"
            )

    if decision.worker_can_resolve:
        response_message = (
            decision.troubleshooting_message
            or "Follow the safe troubleshooting steps."
        )
    else:
        response_message = (
            decision.technician_message
            or decision.troubleshooting_message
            or "Technician intervention is required."
        )
        response_message += (
            " Technician call initiated."
            if decision.technician_alert_sent
            else " Technician call could not be initiated."
        )
    status = (
        "resolved"
        if decision.worker_can_resolve
        else "technician alerted"
        if decision.technician_alert_sent
        else "yet to resolve"
    )

    updated = update_issue(
        str(issue["_id"]),
        {
            "response_message": response_message,
            "status": status,
            "technician_id": (
                str(technician["_id"])
                if technician and not decision.worker_can_resolve
                else None
            ),
        },
    )
    updated = append_issue_message(
        str(issue["_id"]),
        {
            "role": "ai",
            "content": response_message,
            "decision": decision.model_dump(),
            "created_at": datetime.utcnow(),
        },
    ) or updated

    return {
        "issue_id": str(updated["_id"]),
        "decision": decision.model_dump(),
        "conversation": updated.get(
            "conversation",
            [],
        ),
    }


@router.get("/")
def root() -> dict:
    return {"message": "AI Industrial Virtual Supervisor API is running"}


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    try:
        rag = get_collection_health()
        return HealthResponse(
            status="healthy",
            collection=settings.collection_name,
            total_chunks=rag["total_chunks"],
            documents=rag["documents"],
        )
    except Exception as exc:
        return HealthResponse(
            status=f"degraded: {exc}",
            collection=settings.collection_name,
            total_chunks=0,
            documents=[],
        )


@router.get("/telephony/audio/{filename}")
def telephony_audio(filename: str) -> FileResponse:
    settings = get_settings()
    audio_path = settings.resolved_audio_dir / filename

    if (
        audio_path.parent != settings.resolved_audio_dir
        or not audio_path.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="Audio file not found",
        )

    return FileResponse(audio_path, media_type="audio/wav")


@router.post("/voice/transcribe")
async def transcribe_voice(file: UploadFile = File(...)) -> dict:
    audio_service = AudioService()
    chunks = await audio_service.prepare_upload(file)
    try:
        transcript = SarvamTranscriber().transcribe(chunks)
        return {"transcript": transcript}
    finally:
        audio_service.cleanup(chunks)


@router.get("/voice/synthesize")
def synthesize_voice(
    text: str,
    language_code: str = "en-IN",
) -> FileResponse:
    try:
        audio_path = SarvamSpeechService().synthesize_to_file(
            text,
            language_code=language_code,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Speech synthesis failed: {exc}",
        ) from exc

    return FileResponse(audio_path, media_type="audio/wav")


@router.post("/voice/analyze")
async def analyze_voice(
    file: UploadFile = File(...),
    domain_filter: str | None = None,
    worker_id: str | None = None,
    machine_id: str | None = None,
    issue_id: str | None = None,
) -> dict:
    audio_service = AudioService()
    try:
        chunks = await audio_service.prepare_upload(file)
    except Exception as exc:
        logger.exception("Voice upload preparation failed")
        raise HTTPException(
            status_code=422,
            detail=f"Audio preparation failed: {exc}",
        ) from exc

    try:
        try:
            transcript = SarvamTranscriber().transcribe(chunks)
        except Exception as exc:
            logger.exception("Voice transcription failed")
            raise HTTPException(
                status_code=502,
                detail=f"Voice transcription failed: {exc}",
            ) from exc

        result = _persist_analysis(
            transcript,
            worker_id=worker_id,
            machine_id=machine_id,
            issue_id=issue_id,
            domain_filter=domain_filter,
        )
        return {
            "transcript": transcript,
            **result,
        }
    finally:
        audio_service.cleanup(chunks)


@router.post("/issues/analyze")
def analyze_text(request: SuperviseTextRequest) -> dict:
    return _persist_analysis(
        request.message,
        worker_id=request.worker_id,
        machine_id=request.machine_id,
        issue_id=request.issue_id,
        domain_filter=request.domain_filter,
    )


@router.post("/manuals/query", response_model=QueryResponse)
def query_manuals(request: QueryRequest) -> QueryResponse:
    try:
        result = run_query(
            request.query,
            domain_filter=request.domain_filter,
            top_k=request.top_k,
        )
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            query_metadata={
                "domain_filter": request.domain_filter,
                "top_k": request.top_k,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/manuals/ingest", response_model=IngestResponse)
def ingest_manuals() -> IngestResponse:
    try:
        return IngestResponse(**run_ingestion())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/technicians/call")
def call_technician(request: CallRequest) -> dict:
    try:
        return TechnicianCallService().make_call(
            message=request.message,
            to_phone_number=request.to_phone_number,
            language_code=request.language_code,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/telephony/twiml")
@router.get("/telephony/twiml")
def twiml(
    message: str = "Technician alert from AI Industrial Supervisor",
    language_code: str = "en-IN",
    audio_filename: str | None = None,
) -> Response:
    safe_message = escape(message)
    if audio_filename:
        audio_path = get_settings().resolved_audio_dir / audio_filename
        if (
            audio_path.parent == get_settings().resolved_audio_dir
            and audio_path.is_file()
        ):
            audio_url = (
                f"{get_settings().public_backend_url.rstrip('/')}/"
                f"api/v1/telephony/audio/{audio_path.name}"
            )
            body = f"<Response><Play>{escape(audio_url)}</Play></Response>"
            return Response(content=body, media_type="application/xml")

    try:
        audio_path = SarvamSpeechService().synthesize_to_file(
            message,
            language_code=language_code,
        )
        audio_url = (
            f"{get_settings().public_backend_url.rstrip('/')}/"
            f"api/v1/telephony/audio/{audio_path.name}"
        )
        body = f"<Response><Play>{escape(audio_url)}</Play></Response>"
    except Exception:
        body = (
            f'<Response><Say language="{escape(language_code)}">'
            f"{safe_message}</Say></Response>"
        )
    return Response(content=body, media_type="application/xml")


@router.post("/telephony/status")
async def telephony_status(
    call_sid: str | None = Form(None),
    call_status: str | None = Form(None),
    error_code: str | None = Form(None),
    error_message: str | None = Form(None),
) -> Response:
    logger.info(
        "Twilio call status sid=%s status=%s error=%s message=%s",
        call_sid,
        call_status,
        error_code,
        error_message,
    )
    return Response(status_code=204)
