# ConvoLogix v2

ConvoLogix v2 is a secure, Dockerized meeting-intelligence application. It turns meeting recordings into structured reports with transcription, speaker-aware summaries, optional face-attendance detection, and protected multi-user access.

The original project started as a local academic prototype for meeting minutes and face attendance. Version 2 moves the active product into a web architecture with a FastAPI backend, browser dashboard, pretrained computer-vision models, role-based authentication, CI/CD, and release hygiene suitable for beta testing.

## Why This Project Exists

Meetings often produce useful decisions, follow-ups, and attendance records, but those details are easy to lose. Manual note taking is inconsistent, attendance tracking can be unreliable, and post-meeting reporting takes time. ConvoLogix automates that workflow:

1. Upload a meeting recording.
2. Extract and transcribe the audio.
3. Optionally identify "who said what" with speaker diarization.
4. Sample video frames for attendee face recognition.
5. Generate a structured report with speaker summaries, transcript turns, and attendance observations.
6. Download or email the report.

## Version 2 Highlights

- Secure login with `viewer`, `member`, and `admin` roles.
- Protected meeting uploads, processing, meeting details, downloads, and email report delivery.
- First-admin setup from the browser or from bootstrap environment variables.
- Admin user management from the frontend.
- Meeting transcription with `faster-whisper`.
- Optional PyAnnote speaker diarization for "who said what".
- Pretrained OpenCV YuNet and SFace face recognition, avoiding custom CNN training from scratch.
- Face enrollment, image recognition checks, and video-frame attendance sampling.
- Markdown and text report generation.
- Optional SMTP report email delivery.
- Docker Compose deployment for backend and frontend.
- GitHub Actions workflows for checks, Docker builds, and image publishing.
- Security cleanup for public release: runtime data, biometric samples, model binaries, `.env`, bytecode, generated reports, and editor metadata are not tracked.

## Architecture

```text
                 Browser Dashboard
                frontend/ + Nginx
                         |
                         v
                  FastAPI Backend
                  backend/app/main.py
                         |
        +----------------+----------------+
        |                |                |
   Auth + Roles     Speech Service    Face Service
   users.json       faster-whisper     YuNet/SFace ONNX
   bearer tokens    PyAnnote optional  face gallery
        |                |                |
        +----------------+----------------+
                         |
                    Local runtime data
                    data/ and models/
```

### Main Directories

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI app, auth, storage, speech intelligence, face recognition, reporting, API tests |
| `frontend/` | Static web dashboard served by Nginx |
| `scripts/` | Smoke test, beta-readiness gate, tracked-file security gate |
| `docs/` | v2 roadmap and implementation notes |
| `models/` | Local model mount point; contains only `README.md` in Git |
| `data/` | Local runtime data mount point; ignored by Git |
| `Code/`, `CNN and other/` | Legacy prototype code kept for reference |

## User Roles

| Role | Access |
| --- | --- |
| `viewer` | View own meetings, gallery status, completed reports |
| `member` | Viewer access plus upload meetings, process meetings, run recognition checks, send email reports |
| `admin` | Member access plus face enrollment, diarization access checks, user management, and all meetings |

Meeting ownership is enforced in the backend. Admins can see all meetings; non-admin users only see meetings they own.

## Core Workflow

### 1. Admin Setup

On first launch, ConvoLogix has no users. Open the frontend and create the first admin account. You can also bootstrap the first admin with environment variables if you prefer non-interactive deployment.

### 2. Face Enrollment

Admins upload face images for expected attendees. The backend stores those images locally and rebuilds the SFace embedding gallery. The ONNX models are mounted from `models/` and are not committed.

### 3. Meeting Upload

Members and admins upload a meeting video. The file is stored under local runtime data and receives an owner id. The recording is never committed to Git.

### 4. Processing

The backend extracts audio with FFmpeg, transcribes with `faster-whisper`, optionally diarizes speakers with PyAnnote, samples video frames for face attendance, and stores the result.

### 5. Report Review

The frontend displays:

- per-speaker summaries
- speaker turns with timestamps
- attendance summaries
- raw processing status
- Markdown/text report download buttons
- optional email report form

## Quick Start

Copy the environment template:

```bash
cp .env.example .env
```

Set a long random secret:

```text
CONVOLOGIX_AUTH_SECRET_KEY=replace-with-a-long-random-secret
```

Place these files in `models/`:

```text
face_detection_yunet_2023mar.onnx
face_recognition_sface_2021dec.onnx
```

Start the stack:

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:5180
```

Backend health:

```text
http://127.0.0.1:8000/api/health
```

Detailed setup steps are in [INSTALL.md](INSTALL.md).

## Speaker Diarization

Transcription works in the default app image. Real diarization is optional because PyAnnote is large and requires Hugging Face gated model access.

Enable diarization:

```text
CONVOLOGIX_INSTALL_DIARIZATION=true
HUGGINGFACE_TOKEN=<your-hugging-face-token>
```

Then rebuild:

```bash
docker compose up -d --build
```

The Hugging Face account behind the token must accept the terms for `pyannote/speaker-diarization-3.1`. If access is not accepted, meetings still transcribe and summarize, but speaker labels remain unassigned.

## Release Checks

Run syntax checks:

```bash
python -m compileall backend/app scripts
node --check frontend/app.js
```

Run the tracked-file security gate:

```bash
python scripts/security-check.py
```

Run API tests in Docker:

```bash
docker compose exec api python -m unittest discover -s tests
```

Run smoke checks:

```bash
python scripts/smoke-test.py http://127.0.0.1:8000
```

Run authenticated beta readiness:

```bash
CONVOLOGIX_BETA_EMAIL=admin@example.com \
CONVOLOGIX_BETA_PASSWORD=your-password \
python scripts/beta-readiness.py http://127.0.0.1:8000
```

For a fresh local beta instance, add:

```bash
CONVOLOGIX_BETA_CREATE_ADMIN=true
```

This lets the beta script create the first admin from the provided beta credentials.

## CI/CD

The repository includes:

- `.github/workflows/ci.yml`: security check, Python compile, frontend syntax check, Docker Compose validation, Docker image build, API tests.
- `.github/workflows/publish-images.yml`: manual or tag-triggered Docker image publishing to GitHub Container Registry.

Production deployments should provide secrets through the deployment platform or GitHub Actions secrets. Do not commit `.env`.

## Security And Privacy

ConvoLogix deals with sensitive material: meeting recordings, transcripts, face images, user accounts, and optional third-party tokens. The v2 release is designed to keep those out of Git:

- `.env` is ignored.
- `data/` is ignored.
- `models/*` is ignored except `models/README.md`.
- biometric sample folders are ignored.
- generated reports/audio/video outputs are ignored.
- Python bytecode and editor metadata are ignored.
- `scripts/security-check.py` blocks common private artifacts and known legacy credential patterns from being tracked.

For public release, publish from a clean root-history branch like `codex/v2-release` or another orphan branch. A normal branch from old history can expose files that existed in older commits, even if the current tree deletes them.

## Current Beta Notes

- Create the first admin before testing protected workflows.
- Confirm both ONNX face models are mounted.
- Confirm Hugging Face gated model access if diarization is required.
- Run `scripts/beta-readiness.py` after admin setup.
- Upload a real multi-speaker meeting and inspect "Who Said What", attendance, report downloads, and email delivery.

## Study Guide

For interview preparation or onboarding a new developer, read [docs/interview-study-guide.md](docs/interview-study-guide.md). It explains the full system design, backend services, frontend flow, Docker/CI setup, security decisions, limitations, roadmap, and interview talking points.

## License And Use

This project began as an academic/educational system. Review repository licensing and privacy obligations before using it with real participants or in production. Always get consent before processing face images, voice recordings, or meeting transcripts.
