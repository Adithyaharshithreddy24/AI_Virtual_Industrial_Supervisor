import logging
from urllib.parse import quote

from twilio.rest import Client

from app.core.config import get_settings
from app.services.speech import SarvamSpeechService


logger = logging.getLogger(__name__)


class TechnicianCallService:
    """Twilio integration used by the technician-alert tool."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _client(self) -> Client:
        if not all(
            [
                self.settings.twilio_account_sid,
                self.settings.twilio_auth_token,
                self.settings.twilio_from_number,
            ]
        ):
            raise RuntimeError("Twilio configuration is incomplete")
        return Client(
            self.settings.twilio_account_sid,
            self.settings.twilio_auth_token,
        )

    def make_call(
        self,
        message: str,
        to_phone_number: str,
        language_code: str = "en-IN",
    ) -> dict:
        if not message.strip():
            raise ValueError("Technician message cannot be empty")
        if not to_phone_number.strip():
            raise ValueError("Technician phone number cannot be empty")

        if self.settings.twilio_trial_mode:
            verified_number = (
                self.settings.twilio_trial_verified_number
                or self.settings.technician_phone_number
            )
            if not verified_number:
                raise RuntimeError(
                    "Twilio trial mode requires "
                    "TWILIO_TRIAL_VERIFIED_NUMBER"
                )

            normalized_target = "".join(
                character
                for character in to_phone_number
                if character.isdigit() or character == "+"
            )
            normalized_verified = "".join(
                character
                for character in verified_number
                if character.isdigit() or character == "+"
            )
            if normalized_target != normalized_verified:
                raise RuntimeError(
                    "Twilio trial mode can call only the verified "
                    f"number {verified_number}. Verify {to_phone_number} "
                    "in Twilio or update the trial number setting."
                )

        client = self._client()

        if self.settings.twilio_call_url:
            call_url = self.settings.twilio_call_url
        else:
            audio_filename = ""
            try:
                audio_path = SarvamSpeechService().synthesize_to_file(
                    message,
                    language_code=language_code,
                    sample_rate=8000,
                )
                audio_filename = audio_path.name
            except Exception:
                logger.exception(
                    "Technician audio generation failed; using TwiML fallback"
                )

            call_url = (
                f"{self.settings.public_backend_url.rstrip('/')}/"
                "api/v1/telephony/twiml"
                f"?message={quote(message)}"
                f"&language_code={quote(language_code)}"
            )
            if audio_filename:
                call_url += f"&audio_filename={quote(audio_filename)}"

        call_options = {
            "to": to_phone_number,
            "from_": self.settings.twilio_from_number,
            "url": call_url,
        }

        if (
            self.settings.public_backend_url
            and not self.settings.twilio_trial_mode
        ):
            call_options.update({
                "status_callback": (
                    f"{self.settings.public_backend_url.rstrip('/')}/"
                    "api/v1/telephony/status"
                ),
                "status_callback_event": [
                    "initiated",
                    "ringing",
                    "answered",
                    "completed",
                ],
                "status_callback_method": "POST",
            })

        call = client.calls.create(**call_options)

        return {
            "success": True,
            "message": "Technician call initiated successfully",
            "call_sid": call.sid,
            "status": call.status,
        }

    def call_default_technician(
        self,
        message: str,
        language_code: str = "en-IN",
    ) -> dict:
        if not self.settings.technician_phone_number:
            raise RuntimeError("TECHNICIAN_PHONE_NUMBER is not configured")
        return self.make_call(
            message,
            self.settings.technician_phone_number,
            language_code=language_code,
        )

    def call_technician(
        self,
        message: str,
        technician: dict,
        language_code: str = "en-IN",
    ) -> dict:
        phone_number = technician.get("phone_number", "")
        if not phone_number:
            raise RuntimeError(
                "Assigned technician has no phone number"
            )

        return self.make_call(
            message,
            phone_number,
            language_code=language_code,
        )
