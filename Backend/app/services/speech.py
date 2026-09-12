import base64
from pathlib import Path
from uuid import uuid4

import requests

from app.core.config import get_settings


SUPPORTED_LANGUAGES = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "od-IN": "Odia",
    "pa-IN": "Punjabi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
}


class SarvamSpeechService:
    """Synthesizes localized replies with Sarvam Bulbul."""

    API_URL = "https://api.sarvam.ai/text-to-speech"
    TRANSLATE_URL = "https://api.sarvam.ai/translate"

    def __init__(self) -> None:
        self.settings = get_settings()

    def synthesize_to_file(
        self,
        text: str,
        language_code: str = "en-IN",
        sample_rate: int = 22050,
    ) -> Path:
        if not text.strip():
            raise ValueError("Speech text cannot be empty")

        if language_code not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {language_code}"
            )

        if not self.settings.sarvam_api_key:
            raise RuntimeError(
                "SARVAM_API_KEY is not configured"
            )

        localized_text = self.translate(
            text,
            language_code,
        )

        response = requests.post(
            self.API_URL,
            headers={
                "api-subscription-key": self.settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            json={
                "inputs": [localized_text],
                "target_language_code": language_code,
                "speaker": self.settings.sarvam_tts_speaker,
                "model": self.settings.sarvam_tts_model,
                "enable_preprocessing": True,
                "speech_sample_rate": sample_rate,
            },
            timeout=120,
        )

        if not response.ok:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise RuntimeError(
                "Sarvam TTS request failed: "
                f"HTTP {response.status_code} - {detail}"
            )

        payload = response.json()
        audios = payload.get("audios") or []
        if not audios:
            raise RuntimeError(
                f"Sarvam returned no audio: {payload}"
            )

        output = (
            self.settings.resolved_audio_dir
            / f"tts_{uuid4().hex}.wav"
        )
        output.write_bytes(base64.b64decode(audios[0]))
        return output

    def translate(
        self,
        text: str,
        language_code: str,
    ) -> str:
        if language_code == "en-IN":
            return text

        response = requests.post(
            self.TRANSLATE_URL,
            headers={
                "api-subscription-key": self.settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            json={
                "input": text,
                "source_language_code": "en-IN",
                "target_language_code": language_code,
                "model": self.settings.sarvam_translate_model,
                "enable_preprocessing": True,
            },
            timeout=120,
        )

        if not response.ok:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise RuntimeError(
                "Sarvam translation request failed: "
                f"HTTP {response.status_code} - {detail}"
            )

        translated = response.json().get("translated_text")
        if not translated:
            raise RuntimeError(
                "Sarvam returned no translated text"
            )

        return translated
