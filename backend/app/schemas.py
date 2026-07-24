from __future__ import annotations

from pydantic import BaseModel, Field


class ModelStatus(BaseModel):
    detector_configured: bool
    detector_exists: bool
    recognizer_configured: bool
    recognizer_exists: bool
    gallery_exists: bool
    threshold: float
    ready: bool
    message: str


class PersonSummary(BaseModel):
    id: str
    display_name: str
    image_count: int


class GalleryResponse(BaseModel):
    people: list[PersonSummary]
    model: ModelStatus


class EnrollmentResponse(BaseModel):
    person: PersonSummary
    saved_images: int
    gallery_people: int
    gallery_embeddings: int
    model: ModelStatus
    message: str


class FaceMatch(BaseModel):
    identity: str
    confidence: float = Field(ge=-1.0, le=1.0)
    bbox: list[int] = Field(min_length=4, max_length=4)


class RecognitionResponse(BaseModel):
    file_name: str
    faces: list[FaceMatch]
    model: ModelStatus


class AuthStatusResponse(BaseModel):
    enabled: bool
    setup_required: bool
    user_count: int


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    created_at: str | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserCreateRequest(BaseModel):
    email: str
    password: str = Field(min_length=10)
    display_name: str | None = None
    role: str = "viewer"


class MeetingUploadResponse(BaseModel):
    id: str
    title: str
    file_name: str
    status: str
    message: str


class SpeechPipelineStatus(BaseModel):
    ffmpeg_available: bool
    asr_package_available: bool
    asr_model: str
    diarization_package_available: bool
    diarization_model: str
    diarization_token_configured: bool
    diarization_model_access: str = "not_checked"
    diarization_model_message: str | None = None
    ready_for_transcription: bool
    ready_for_diarization: bool
    message: str


class DiarizationCheckResponse(BaseModel):
    ok: bool
    model: str
    package_available: bool
    token_configured: bool
    pipeline_loaded: bool
    message: str


class MeetingSummary(BaseModel):
    speaker: str
    summary: str


class TranscriptSegment(BaseModel):
    start: float
    end: float
    speaker: str | None
    text: str


class SpeakerTurn(BaseModel):
    speaker: str
    start: float
    end: float
    text: str


class AttendanceObservation(BaseModel):
    person: str
    timestamp: float
    confidence: float = Field(ge=-1.0, le=1.0)
    bbox: list[int] = Field(min_length=4, max_length=4)


class AttendanceSummary(BaseModel):
    person: str
    first_seen: float
    last_seen: float
    detections: int
    best_confidence: float = Field(ge=-1.0, le=1.0)


class MeetingProcessResponse(BaseModel):
    id: str
    title: str
    status: str
    diarization_enabled: bool
    attendance_enabled: bool
    attendance_message: str
    transcript: list[TranscriptSegment]
    speaker_turns: list[SpeakerTurn]
    summary_by_speaker: list[MeetingSummary]
    attendance: list[AttendanceSummary]
    attendance_observations: list[AttendanceObservation]
    speech: SpeechPipelineStatus
    message: str


class MeetingProcessStartResponse(BaseModel):
    id: str
    title: str
    status: str
    message: str


class MeetingDetailResponse(BaseModel):
    id: str
    title: str
    file_name: str
    status: str
    owner_id: str | None = None
    owner_email: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    error_message: str | None = None
    result: MeetingProcessResponse | None = None


class EmailReportRequest(BaseModel):
    receiver_email: str
    subject: str | None = None
    body: str | None = None


class EmailReportResponse(BaseModel):
    sent: bool
    message: str
