from __future__ import annotations

from collections.abc import Callable

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.schemas import (
    AuthStatusResponse,
    AuthTokenResponse,
    DiarizationCheckResponse,
    EnrollmentResponse,
    EmailReportRequest,
    EmailReportResponse,
    GalleryResponse,
    MeetingDetailResponse,
    MeetingProcessResponse,
    MeetingProcessStartResponse,
    MeetingUploadResponse,
    RecognitionResponse,
    LoginRequest,
    UserCreateRequest,
    UserResponse,
)
from app.services.auth import AuthService, AuthenticationError, AuthorizationError, CurrentUser
from app.services.face_recognition import FaceRecognitionNotReady, OpenCVSFaceService
from app.services.reporting import EmailNotConfigured, ReportNotReady, ReportService
from app.services.speech_intelligence import SpeechIntelligenceService, SpeechProcessingNotReady
from app.services.storage import (
    ensure_workspace,
    list_meetings,
    list_people,
    read_meeting_metadata,
    read_meeting_detail,
    save_meeting_video,
    save_person_image,
    slugify,
    update_meeting_status,
)
from app.services.video_attendance import VideoAttendanceService


settings = get_settings()
ensure_workspace(settings)
face_service = OpenCVSFaceService(settings)
attendance_service = VideoAttendanceService(settings, face_service)
speech_service = SpeechIntelligenceService(settings, attendance_service)
report_service = ReportService(settings)
auth_service = AuthService(settings)
bearer_scheme = HTTPBearer(auto_error=False)

app = FastAPI(title=settings.app_name, version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> CurrentUser:
    if not settings.auth_enabled:
        return auth_service.disabled_user()
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication is required.")
    try:
        return auth_service.verify_access_token(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_role(minimum_role: str) -> Callable[[CurrentUser], CurrentUser]:
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        try:
            auth_service.require_role(user, minimum_role)
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return user

    return dependency


def require_meeting_access(meeting_id: str, user: CurrentUser, minimum_role: str = "viewer") -> None:
    try:
        auth_service.require_role(user, minimum_role)
        metadata = read_meeting_metadata(settings, meeting_id)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    owner_id = metadata.get("owner_id")
    if user.role != "admin" and owner_id != user.id:
        raise HTTPException(status_code=403, detail="This meeting belongs to another user.")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "model": face_service.status().model_dump(),
        "speech": speech_service.status().model_dump(),
    }


@app.get("/api/auth/status", response_model=AuthStatusResponse)
def auth_status() -> AuthStatusResponse:
    return auth_service.status()


@app.post("/api/auth/setup", response_model=AuthTokenResponse)
def setup_first_admin(request: UserCreateRequest) -> AuthTokenResponse:
    try:
        return auth_service.setup_first_admin(request)
    except (ValueError, AuthorizationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/auth/login", response_model=AuthTokenResponse)
def login(request: LoginRequest) -> AuthTokenResponse:
    try:
        user = auth_service.authenticate(request.email, request.password)
    except (ValueError, AuthenticationError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return AuthTokenResponse(access_token=auth_service.create_access_token(user), user=user)


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: CurrentUser = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name, role=user.role)


@app.get("/api/auth/users", response_model=list[UserResponse])
def users(_: CurrentUser = Depends(require_role("admin"))) -> list[UserResponse]:
    return auth_service.list_users()


@app.post("/api/auth/users", response_model=UserResponse)
def create_user(request: UserCreateRequest, _: CurrentUser = Depends(require_role("admin"))) -> UserResponse:
    try:
        return auth_service.create_user(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/speech/diarization-check", response_model=DiarizationCheckResponse)
def diarization_check(
    load_model: bool = True,
    _: CurrentUser = Depends(require_role("admin")),
) -> DiarizationCheckResponse:
    return speech_service.check_diarization_model_access(load_model=load_model)


@app.get("/api/faces/gallery", response_model=GalleryResponse)
def gallery(_: CurrentUser = Depends(require_role("viewer"))) -> GalleryResponse:
    return GalleryResponse(people=list_people(settings), model=face_service.status())


@app.post("/api/faces/enroll", response_model=EnrollmentResponse)
async def enroll_faces(
    person_name: str = Form(...),
    files: list[UploadFile] = File(...),
    _: CurrentUser = Depends(require_role("admin")),
) -> EnrollmentResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one face image.")

    saved_images = 0
    for upload in files:
        data = await upload.read()
        if not data:
            continue
        try:
            save_person_image(settings, person_name, upload.filename or "face.jpg", data)
            saved_images += 1
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    people = list_people(settings)
    person_id = slugify(person_name)
    person = next((entry for entry in people if entry.id == person_id), None)
    if person is None:
        raise HTTPException(status_code=400, detail="No valid images were saved for this person.")

    try:
        build = face_service.rebuild_gallery()
        message = f"Enrolled images saved and face gallery rebuilt. Skipped {build.skipped_images} unusable images."
    except FaceRecognitionNotReady as exc:
        build = None
        message = f"Images saved. Recognition model is not ready yet: {exc}"

    return EnrollmentResponse(
        person=person,
        saved_images=saved_images,
        gallery_people=build.people if build else 0,
        gallery_embeddings=build.embeddings if build else 0,
        model=face_service.status(),
        message=message,
    )


@app.post("/api/faces/recognize", response_model=RecognitionResponse)
async def recognize_face(
    file: UploadFile = File(...),
    _: CurrentUser = Depends(require_role("member")),
) -> RecognitionResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Upload a non-empty image.")

    try:
        faces = face_service.recognize_image(data)
    except FaceRecognitionNotReady as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RecognitionResponse(file_name=file.filename or "image", faces=faces, model=face_service.status())


@app.post("/api/meetings", response_model=MeetingUploadResponse)
async def upload_meeting(
    title: str = Form(""),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role("member")),
) -> MeetingUploadResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Upload a non-empty meeting video.")

    try:
        metadata = save_meeting_video(
            settings,
            title,
            file.filename or "meeting.mp4",
            data,
            owner_id=user.id,
            owner_email=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MeetingUploadResponse(
        id=metadata["id"],
        title=metadata["title"],
        file_name=metadata["file_name"],
        status=metadata["status"],
        message="Meeting uploaded. Processing pipeline will attach transcription and attendance next.",
    )


@app.get("/api/meetings", response_model=list[MeetingDetailResponse])
def meetings(user: CurrentUser = Depends(require_role("viewer"))) -> list[MeetingDetailResponse]:
    return list_meetings(settings, owner_id=user.id, include_all=user.role == "admin")


@app.get("/api/meetings/{meeting_id}", response_model=MeetingDetailResponse)
def meeting_detail(meeting_id: str, user: CurrentUser = Depends(require_role("viewer"))) -> MeetingDetailResponse:
    require_meeting_access(meeting_id, user)
    try:
        return read_meeting_detail(settings, meeting_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _process_meeting_background(meeting_id: str) -> None:
    try:
        speech_service.process_meeting(meeting_id)
    except Exception:
        # The service already records failed state and error text in metadata.
        return


@app.post("/api/meetings/{meeting_id}/process", response_model=MeetingProcessStartResponse)
def process_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role("member")),
) -> MeetingProcessStartResponse:
    require_meeting_access(meeting_id, user, minimum_role="member")
    try:
        metadata = update_meeting_status(settings, meeting_id, "queued")
        background_tasks.add_task(_process_meeting_background, meeting_id)
        return MeetingProcessStartResponse(
            id=metadata["id"],
            title=metadata["title"],
            status=metadata["status"],
            message="Meeting processing started. Poll the meeting detail endpoint for progress.",
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/meetings/{meeting_id}/process-sync", response_model=MeetingProcessResponse)
def process_meeting_sync(
    meeting_id: str,
    user: CurrentUser = Depends(require_role("member")),
) -> MeetingProcessResponse:
    require_meeting_access(meeting_id, user, minimum_role="member")
    try:
        return speech_service.process_meeting(meeting_id)
    except SpeechProcessingNotReady as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/meetings/{meeting_id}/report.md")
def meeting_markdown_report(
    meeting_id: str,
    user: CurrentUser = Depends(require_role("viewer")),
) -> Response:
    require_meeting_access(meeting_id, user)
    try:
        report = report_service.build_markdown_report(meeting_id)
    except ReportNotReady as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=report,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="convologix-{meeting_id}.md"'},
    )


@app.get("/api/meetings/{meeting_id}/report.txt")
def meeting_text_report(
    meeting_id: str,
    user: CurrentUser = Depends(require_role("viewer")),
) -> Response:
    require_meeting_access(meeting_id, user)
    try:
        report = report_service.build_text_report(meeting_id)
    except ReportNotReady as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=report,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="convologix-{meeting_id}.txt"'},
    )


@app.post("/api/meetings/{meeting_id}/email-report", response_model=EmailReportResponse)
def email_meeting_report(
    meeting_id: str,
    request: EmailReportRequest,
    user: CurrentUser = Depends(require_role("member")),
) -> EmailReportResponse:
    require_meeting_access(meeting_id, user, minimum_role="member")
    try:
        return report_service.send_report(meeting_id, request)
    except EmailNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ReportNotReady as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
