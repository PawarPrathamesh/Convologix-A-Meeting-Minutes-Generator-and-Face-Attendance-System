# ConvoLogix v2 Roadmap

## Vision

ConvoLogix v2 is a deployable web application for meeting intelligence:

- upload meeting recordings
- transcribe speech
- identify who said what with speaker diarization
- detect attendees from meeting video frames
- generate a structured meeting report
- run locally or in Docker without machine-specific paths or committed private data

## Milestones

### 1. Deployable Foundation

- [x] Create FastAPI backend.
- [x] Create web frontend.
- [x] Add Dockerfiles and Docker Compose.
- [x] Remove v2 hard-coded local paths and secrets.
- [x] Mount data and model artifacts instead of committing them.

### 2. Pretrained Face Recognition

- [x] Add pretrained YuNet and SFace integration.
- [x] Add face enrollment API.
- [x] Add image recognition API.
- [x] Add video-frame attendance recognition.
- [x] Add attendance output to meeting reports.

### 3. Speech Intelligence

- [x] Add FFmpeg audio extraction.
- [x] Add Whisper-compatible transcription.
- [x] Add optional PyAnnote diarization.
- [x] Add "who said what" speaker summaries.
- [x] Run meeting processing as a background job.
- [x] Add resilient processing status and polling.

### 4. Reports and Delivery

- [x] Generate Markdown and text meeting reports.
- [x] Add report download endpoints.
- [x] Add SMTP email hook using environment variables.
- [x] Keep generated reports in mounted runtime storage.

### 5. Frontend Workflow

- [x] Upload meeting recordings.
- [x] Enroll attendee images.
- [x] Test face recognition.
- [x] Show speaker turns and summaries.
- [x] Show meeting history.
- [x] Poll background processing status.
- [x] Show attendance and report downloads.

### 6. Production Readiness

- [x] Add API smoke-test script.
- [x] Add Docker health checks.
- [x] Add automated backend tests.
- [x] Add login, roles, and protected meeting access.
- [x] Add admin user management in the frontend.
- [x] Add CI/CD workflows for checks, Docker builds, and image publishing.
- [x] Add tracked-file security gate.
- [x] Document model and token setup.
- [x] Document v2 install, run, beta test, and deployment flow.
- [x] Remove old biometric/generated artifacts from current repository tracking.
- [ ] Purge sensitive artifacts from Git history before public release.

## Current Priority

Prepare beta testing:

1. Create the first admin account.
2. Confirm face models are mounted.
3. Confirm Hugging Face gated model access for diarization.
4. Run `scripts/smoke-test.py`.
5. Run `scripts/beta-readiness.py`.
6. Upload a real meeting and inspect speaker turns, summaries, attendance, and reports.
