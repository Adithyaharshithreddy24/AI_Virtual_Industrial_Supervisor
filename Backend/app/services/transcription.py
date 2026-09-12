from pathlib import Path

import requests
from pydub import AudioSegment

from app.core.config import get_settings


class SarvamTranscriber:
    """Converts operator speech into English text using Sarvam Saaras."""

    API_URL = "https://api.sarvam.ai/speech-to-text"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _send_piece(self, piece_path: Path) -> str:
        if not piece_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {piece_path}"
            )

        if piece_path.stat().st_size == 0:
            raise ValueError(
                f"Audio file is empty: {piece_path}"
            )

        headers = {
            "api-subscription-key": self.settings.sarvam_api_key,
        }

        data = {
            "model": self.settings.sarvam_stt_model,
            "mode": "translate",
            "language_code": "unknown",
        }

        with piece_path.open("rb") as audio_file:
            response = requests.post(
                self.API_URL,
                headers=headers,
                files={
                    "file": (
                        piece_path.name,
                        audio_file,
                        "audio/wav",
                    )
                },
                data=data,
                timeout=120,
            )

        # Important: expose Sarvam's actual error instead of
        # only returning "400 Bad Request".
        if not response.ok:
            try:
                error_body = response.json()
            except ValueError:
                error_body = response.text

            raise RuntimeError(
                "Sarvam STT request failed: "
                f"HTTP {response.status_code} - "
                f"{error_body}"
            )

        result = response.json()


        transcript = result.get("transcript", "")

        if not transcript:
            raise RuntimeError(
                f"Sarvam returned no transcript: {result}"
            )

        return transcript

    def transcribe_chunk(self, chunk_path: Path) -> str:
        audio = AudioSegment.from_wav(chunk_path)

        # Sarvam REST STT supports a maximum of 30 seconds
        # per request, so keep each piece below that limit.
        piece_ms = self.settings.sarvam_piece_seconds * 1000

        pieces: list[str] = []

        for index, start in enumerate(
            range(0, len(audio), piece_ms)
        ):
            piece = audio[start : start + piece_ms]

            piece_path = chunk_path.with_name(
                f"{chunk_path.stem}_sarvam_{index}.wav"
            )

            piece.export(
                piece_path,
                format="wav",
                parameters=[
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                ],
            )

            try:
                text = self._send_piece(
                    piece_path
                ).strip()

                if text:
                    pieces.append(text)

            finally:
                piece_path.unlink(
                    missing_ok=True
                )

        return " ".join(pieces)

    def transcribe(
        self,
        chunks: list[Path],
    ) -> str:

        if not self.settings.sarvam_api_key:
            raise RuntimeError(
                "SARVAM_API_KEY is not configured"
            )

        transcript_parts: list[str] = []

        for chunk in chunks:
            text = self.transcribe_chunk(chunk)

            if text:
                transcript_parts.append(text)

        transcript = " ".join(
            transcript_parts
        ).strip()

        return transcript