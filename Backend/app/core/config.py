from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------

    app_name: str = "AI Industrial Virtual Supervisor"
    app_version: str = "1.0.0"
    environment: str = "development"

    host: str = "0.0.0.0"
    port: int = 5000

    cors_origins: str = "*"

    # ---------------------------------------------------------
    # Gemini
    # ---------------------------------------------------------

    google_api_key: str = ""

    llm_provider: str = "gemini"

    llm_model: str = "gemini-3.6-flash"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2048

    ollama_base_url: str = "http://127.0.0.1:11434"

    ollama_model: str = "qwen3:4b"

    # ---------------------------------------------------------
    # MongoDB Atlas
    # ---------------------------------------------------------

    mongodb_uri: str = ""
    mongodb_database: str = "ai_industrial_supervisor"

    # ---------------------------------------------------------
    # Embeddings / RAG
    # ---------------------------------------------------------

    embedding_model: str = "models/gemini-embedding-2"

    collection_name: str = "industrial_manuals"

    chunk_size_general: int = 800
    chunk_overlap_general: int = 150

    chunk_size_oem: int = 600
    chunk_overlap_oem: int = 100

    rag_top_k: int = 5

    # ---------------------------------------------------------
    # Local storage
    # ---------------------------------------------------------

    base_dir: Path = Path(__file__).resolve().parents[2]

    pdf_dir: Path = Path("data/pdfs")
    audio_dir: Path = Path("data/audio")
    chroma_db_dir: Path = Path("storage/chroma")

    # ---------------------------------------------------------
    # Sarvam
    # ---------------------------------------------------------

    sarvam_api_key: str = ""

    sarvam_stt_model: str = "saaras:v3"

    sarvam_tts_model: str = "bulbul:v3"

    sarvam_tts_speaker: str = "aditya"

    sarvam_translate_model: str = "mayura:v1"

    sarvam_piece_seconds: int = 25

    audio_chunk_minutes: int = 10

    # ---------------------------------------------------------
    # Twilio
    # ---------------------------------------------------------

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""

    twilio_from_number: str = ""

    technician_phone_number: str = ""

    twilio_trial_mode: bool = False

    twilio_trial_verified_number: str = ""

    public_backend_url: str = ""

    twilio_call_url: str = ""

    # Authentication
    jwt_secret_key: str = ""
    jwt_expire_minutes: int = 480   
    # ---------------------------------------------------------
    # Paths
    # ---------------------------------------------------------

    @property
    def resolved_pdf_dir(self) -> Path:
        return self._resolve_path(self.pdf_dir)

    @property
    def resolved_audio_dir(self) -> Path:
        return self._resolve_path(self.audio_dir)

    @property
    def resolved_chroma_dir(self) -> Path:
        return self._resolve_path(self.chroma_db_dir)

    def _resolve_path(self, value: Path) -> Path:
        if value.is_absolute():
            return value

        return self.base_dir / value

    # ---------------------------------------------------------
    # CORS
    # ---------------------------------------------------------

    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]

        return [
            item.strip()
            for item in self.cors_origins.split(",")
            if item.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:

    settings = Settings()

    settings.resolved_pdf_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.resolved_audio_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.resolved_chroma_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return settings