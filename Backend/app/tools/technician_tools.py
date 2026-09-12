import json
from langchain.tools import tool

from app.services.telephony import TechnicianCallService


@tool
def alert_technician(
    message: str,
    language_code: str = "en-IN",
    technician_phone_number: str = "",
) -> str:
    """Call the configured maintenance technician when operator-level resolution is unsafe or insufficient.

    This tool performs a real phone call. Use it only when specialized maintenance
    or technician intervention is required.
    """
    service = TechnicianCallService()
    result = (
        service.make_call(
            message,
            technician_phone_number,
            language_code=language_code,
        )
        if technician_phone_number
        else service.call_default_technician(
            message,
            language_code=language_code,
        )
    )
    return json.dumps(result, ensure_ascii=False)
