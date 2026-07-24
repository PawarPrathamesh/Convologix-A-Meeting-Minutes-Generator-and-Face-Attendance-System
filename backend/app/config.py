from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _path_from_env(name: str, default: Path) -> Path:
    return Path(os.getenv(name, str(default))).expanduser().resolve()


def _optional_path_from_env(name: str) -> Path | None:
    value = os.getenv(name)
    if not value:
        return None
    return Path(value).expanduser().resolve()


def _float_from_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _int_from_env(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _bool_from_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    data_dir: Path
    uploads_dir: Path
    enrollment_dir: Path
    gallery_file: Path
    users_file: Path
    auth_enabled: bool
    auth_secret_key: str
    auth_token_minutes: int
    bootstrap_admin_email: str | None
    bootstrap_admin_password: str | None
    bootstrap_admin_name: str | None
    face_detector_model: Path | None
    face_recognition_model: Path | None
    face_match_threshold: float
    ffmpeg_binary: str
    asr_model: str
    asr_device: str
    asr_compute_type: str
    diarization_model: str
    huggingface_token: str | None
    diarization_min_speakers: int | None
    diarization_max_speakers: int | None
    attendance_sample_interval_seconds: float
    attendance_max_frames: int
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from_email: str | None
    smtp_use_tls: bool
    cors_origins: tuple[str, ...]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    root = _backend_root()
    data_dir = _path_from_env("CONVOLOGIX_DATA_DIR", root / "data")
    origins = os.getenv(
        "CONVOLOGIX_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:3000,http://localhost:3000",
    )

    return Settings(
        app_name=os.getenv("CONVOLOGIX_APP_NAME", "ConvoLogix v2"),
        data_dir=data_dir,
        uploads_dir=_path_from_env("CONVOLOGIX_UPLOADS_DIR", data_dir / "uploads"),
        enrollment_dir=_path_from_env("CONVOLOGIX_ENROLLMENT_DIR", data_dir / "faces"),
        gallery_file=_path_from_env("CONVOLOGIX_FACE_GALLERY_FILE", data_dir / "face_gallery.npz"),
        users_file=_path_from_env("CONVOLOGIX_USERS_FILE", data_dir / "users.json"),
        auth_enabled=_bool_from_env("CONVOLOGIX_AUTH_ENABLED", True),
        auth_secret_key=os.getenv("CONVOLOGIX_AUTH_SECRET_KEY") or secrets.token_urlsafe(32),
        auth_token_minutes=_int_from_env("CONVOLOGIX_AUTH_TOKEN_MINUTES") or 720,
        bootstrap_admin_email=os.getenv("CONVOLOGIX_BOOTSTRAP_ADMIN_EMAIL"),
        bootstrap_admin_password=os.getenv("CONVOLOGIX_BOOTSTRAP_ADMIN_PASSWORD"),
        bootstrap_admin_name=os.getenv("CONVOLOGIX_BOOTSTRAP_ADMIN_NAME"),
        face_detector_model=_optional_path_from_env("CONVOLOGIX_FACE_DETECTOR_MODEL"),
        face_recognition_model=_optional_path_from_env("CONVOLOGIX_FACE_RECOGNITION_MODEL"),
        face_match_threshold=_float_from_env("CONVOLOGIX_FACE_MATCH_THRESHOLD", 0.62),
        ffmpeg_binary=os.getenv("CONVOLOGIX_FFMPEG_BINARY", "ffmpeg"),
        asr_model=os.getenv("CONVOLOGIX_ASR_MODEL", "small.en"),
        asr_device=os.getenv("CONVOLOGIX_ASR_DEVICE", "cpu"),
        asr_compute_type=os.getenv("CONVOLOGIX_ASR_COMPUTE_TYPE", "int8"),
        diarization_model=os.getenv("CONVOLOGIX_DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1"),
        huggingface_token=os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN"),
        diarization_min_speakers=_int_from_env("CONVOLOGIX_DIARIZATION_MIN_SPEAKERS"),
        diarization_max_speakers=_int_from_env("CONVOLOGIX_DIARIZATION_MAX_SPEAKERS"),
        attendance_sample_interval_seconds=_float_from_env("CONVOLOGIX_ATTENDANCE_SAMPLE_INTERVAL_SECONDS", 20.0),
        attendance_max_frames=_int_from_env("CONVOLOGIX_ATTENDANCE_MAX_FRAMES") or 30,
        smtp_host=os.getenv("CONVOLOGIX_SMTP_HOST"),
        smtp_port=_int_from_env("CONVOLOGIX_SMTP_PORT") or 587,
        smtp_username=os.getenv("CONVOLOGIX_SMTP_USERNAME"),
        smtp_password=os.getenv("CONVOLOGIX_SMTP_PASSWORD"),
        smtp_from_email=os.getenv("CONVOLOGIX_SMTP_FROM_EMAIL") or os.getenv("CONVOLOGIX_SMTP_USERNAME"),
        smtp_use_tls=_bool_from_env("CONVOLOGIX_SMTP_USE_TLS", True),
        cors_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
    )
