from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.schemas import MeetingDetailResponse, MeetingProcessResponse, PersonSummary


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
SAFE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


def slugify(value: str) -> str:
    slug = SAFE_NAME_PATTERN.sub("-", value.strip()).strip("-._").lower()
    if not slug:
        raise ValueError("Name must contain at least one letter or number.")
    return slug[:80]


def ensure_workspace(settings: Settings) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.enrollment_dir.mkdir(parents=True, exist_ok=True)
    settings.gallery_file.parent.mkdir(parents=True, exist_ok=True)
    settings.users_file.parent.mkdir(parents=True, exist_ok=True)


def safe_filename(file_name: str, fallback: str) -> str:
    name = Path(file_name or fallback).name
    sanitized = SAFE_NAME_PATTERN.sub("-", name).strip("-._")
    return sanitized or fallback


def save_person_image(settings: Settings, person_name: str, file_name: str, data: bytes) -> Path:
    person_id = slugify(person_name)
    saved_name = safe_filename(file_name, f"{uuid.uuid4().hex}.jpg")
    suffix = Path(saved_name).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        raise ValueError(f"Unsupported image type: {suffix or 'unknown'}")

    person_dir = settings.enrollment_dir / person_id
    person_dir.mkdir(parents=True, exist_ok=True)
    target = person_dir / f"{uuid.uuid4().hex}_{saved_name}"
    target.write_bytes(data)
    return target


def list_people(settings: Settings) -> list[PersonSummary]:
    if not settings.enrollment_dir.exists():
        return []

    people: list[PersonSummary] = []
    for person_dir in sorted(path for path in settings.enrollment_dir.iterdir() if path.is_dir()):
        image_count = sum(
            1
            for image_path in person_dir.iterdir()
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_SUFFIXES
        )
        people.append(
            PersonSummary(
                id=person_dir.name,
                display_name=person_dir.name.replace("-", " ").title(),
                image_count=image_count,
            )
        )
    return people


def save_meeting_video(
    settings: Settings,
    title: str,
    file_name: str,
    data: bytes,
    owner_id: str | None = None,
    owner_email: str | None = None,
) -> dict[str, str]:
    saved_name = safe_filename(file_name, f"{uuid.uuid4().hex}.mp4")
    suffix = Path(saved_name).suffix.lower()
    if suffix not in VIDEO_SUFFIXES:
        raise ValueError(f"Unsupported video type: {suffix or 'unknown'}")

    meeting_id = uuid.uuid4().hex[:12]
    meeting_dir = settings.uploads_dir / "meetings" / meeting_id
    meeting_dir.mkdir(parents=True, exist_ok=True)
    video_path = meeting_dir / saved_name
    video_path.write_bytes(data)

    metadata = {
        "id": meeting_id,
        "title": title.strip() or Path(saved_name).stem,
        "file_name": saved_name,
        "status": "uploaded",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if owner_id:
        metadata["owner_id"] = owner_id
    if owner_email:
        metadata["owner_email"] = owner_email
    (meeting_dir / "meeting.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def meetings_root(settings: Settings) -> Path:
    return settings.uploads_dir / "meetings"


def meeting_dir(settings: Settings, meeting_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{12}", meeting_id):
        raise ValueError("Invalid meeting id.")
    return meetings_root(settings) / meeting_id


def meeting_metadata_path(settings: Settings, meeting_id: str) -> Path:
    return meeting_dir(settings, meeting_id) / "meeting.json"


def meeting_result_path(settings: Settings, meeting_id: str) -> Path:
    return meeting_dir(settings, meeting_id) / "result.json"


def read_meeting_metadata(settings: Settings, meeting_id: str) -> dict[str, str]:
    path = meeting_metadata_path(settings, meeting_id)
    if not path.exists():
        raise FileNotFoundError(f"Meeting {meeting_id} was not found.")
    return json.loads(path.read_text(encoding="utf-8"))


def write_meeting_metadata(settings: Settings, meeting_id: str, metadata: dict[str, str]) -> None:
    meeting_metadata_path(settings, meeting_id).write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def update_meeting_status(
    settings: Settings,
    meeting_id: str,
    status: str,
    error_message: str | None = None,
) -> dict[str, str]:
    metadata = read_meeting_metadata(settings, meeting_id)
    metadata["status"] = status
    metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
    if error_message:
        metadata["error_message"] = error_message
    elif "error_message" in metadata:
        del metadata["error_message"]
    write_meeting_metadata(settings, meeting_id, metadata)
    return metadata


def meeting_video_path(settings: Settings, meeting_id: str) -> Path:
    metadata = read_meeting_metadata(settings, meeting_id)
    return meeting_dir(settings, meeting_id) / metadata["file_name"]


def save_meeting_result(settings: Settings, meeting_id: str, result: MeetingProcessResponse) -> None:
    meeting_result_path(settings, meeting_id).write_text(result.model_dump_json(indent=2), encoding="utf-8")


def read_meeting_result(settings: Settings, meeting_id: str) -> MeetingProcessResponse | None:
    path = meeting_result_path(settings, meeting_id)
    if not path.exists():
        return None
    return MeetingProcessResponse.model_validate_json(path.read_text(encoding="utf-8"))


def list_meetings(settings: Settings, owner_id: str | None = None, include_all: bool = False) -> list[MeetingDetailResponse]:
    root = meetings_root(settings)
    if not root.exists():
        return []

    meetings: list[MeetingDetailResponse] = []
    for metadata_path in sorted(root.glob("*/meeting.json"), reverse=True):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        meeting_id = metadata["id"]
        if not include_all and metadata.get("owner_id") != owner_id:
            continue
        meetings.append(
            MeetingDetailResponse(
                id=meeting_id,
                title=metadata["title"],
                file_name=metadata["file_name"],
                status=metadata["status"],
                owner_id=metadata.get("owner_id"),
                owner_email=metadata.get("owner_email"),
                created_at=metadata.get("created_at"),
                updated_at=metadata.get("updated_at"),
                error_message=metadata.get("error_message"),
                result=read_meeting_result(settings, meeting_id),
            )
        )
    return meetings


def read_meeting_detail(settings: Settings, meeting_id: str) -> MeetingDetailResponse:
    metadata = read_meeting_metadata(settings, meeting_id)
    return MeetingDetailResponse(
        id=metadata["id"],
        title=metadata["title"],
        file_name=metadata["file_name"],
        status=metadata["status"],
        owner_id=metadata.get("owner_id"),
        owner_email=metadata.get("owner_email"),
        created_at=metadata.get("created_at"),
        updated_at=metadata.get("updated_at"),
        error_message=metadata.get("error_message"),
        result=read_meeting_result(settings, meeting_id),
    )
