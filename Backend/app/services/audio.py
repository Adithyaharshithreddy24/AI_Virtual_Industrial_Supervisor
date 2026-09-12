from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from pydub import AudioSegment

from app.core.config import get_settings


class AudioService:
    """Stores, normalizes, and chunks operator audio."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def save_upload(self, file: UploadFile) -> Path:
        suffix = Path(file.filename or "audio").suffix or ".bin"
        output = self.settings.resolved_audio_dir / f"{uuid4().hex}{suffix}"
        content = await file.read()
        output.write_bytes(content)
        return output

    def convert_to_wav(self, input_path: Path) -> Path:
        output_path = input_path.with_name(f"{input_path.stem}_converted.wav")
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(output_path, format="wav")
        return output_path

    def chunk_audio(self, wav_path: Path) -> list[Path]:
        audio = AudioSegment.from_wav(wav_path)
        chunk_ms = self.settings.audio_chunk_minutes * 60 * 1000
        chunks: list[Path] = []

        for index, start in enumerate(range(0, len(audio), chunk_ms)):
            chunk = audio[start : start + chunk_ms]
            chunk_path = wav_path.with_name(f"{wav_path.stem}_chunk_{index}.wav")
            chunk.export(chunk_path, format="wav")
            chunks.append(chunk_path)

        return chunks

    async def prepare_upload(self, file: UploadFile) -> list[Path]:
        original = await self.save_upload(file)
        wav = self.convert_to_wav(original)
        return self.chunk_audio(wav)

    @staticmethod
    def cleanup(paths: list[Path]) -> None:
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
