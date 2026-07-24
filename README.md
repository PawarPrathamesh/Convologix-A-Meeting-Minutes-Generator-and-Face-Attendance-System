# ConvoLogix v2

ConvoLogix v2 is a Dockerized meeting-intelligence web app. It replaces the old local Tkinter prototype path with a FastAPI backend, browser dashboard, pretrained face-recognition models, authenticated meeting access, and speaker-aware meeting reports.

## What v2 Includes

- Secure login with `viewer`, `member`, and `admin` roles
- Protected meeting uploads, meeting history, processing, reports, and email delivery
- First-admin setup from the browser or bootstrap environment variables
- Meeting transcription with `faster-whisper`
- Optional PyAnnote speaker diarization for "who said what"
- Pretrained OpenCV YuNet/SFace face recognition instead of training a CNN from scratch
- Face enrollment, recognition checks, and video-frame attendance sampling
- Markdown/text report downloads and optional SMTP email reports
- Docker Compose deployment for API and frontend
- GitHub Actions for security checks, syntax checks, Docker builds, and image publishing

## Architecture

```text
frontend/   Static browser dashboard served by Nginx
backend/    FastAPI API, auth, speech processing, reports, face recognition
scripts/    Smoke, beta-readiness, and security checks
models/     Local ONNX model mount point, not tracked by Git
data/       Local runtime data mount point, not tracked by Git
docs/       v2 implementation notes and roadmap
```

The legacy academic prototype remains in `Code/` for reference. New v2 development lives in `backend/`, `frontend/`, `scripts/`, and `docs/`.

## Quick Start

1. Copy the sample environment file:

```bash
cp .env.example .env
```

2. Set a long random `CONVOLOGIX_AUTH_SECRET_KEY` in `.env`.

3. Place these files in `models/`:

```text
face_detection_yunet_2023mar.onnx
face_recognition_sface_2021dec.onnx
```

4. Start the stack:

```bash
docker compose up -d --build
```

5. Open the dashboard:

```text
http://localhost:5180
```

On first launch, create the first admin account in the browser. After that, admins can add users from the System screen.

## Roles

| Role | Access |
| --- | --- |
| `viewer` | View own meetings, gallery, completed reports |
| `member` | Viewer access plus upload, process, recognition checks, email reports |
| `admin` | Member access plus face enrollment, diarization checks, user management, all meetings |

## Checks

Smoke test:

```bash
python scripts/smoke-test.py http://127.0.0.1:8000
```

Authenticated beta readiness:

```bash
CONVOLOGIX_BETA_EMAIL=admin@example.com \
CONVOLOGIX_BETA_PASSWORD=your-password \
python scripts/beta-readiness.py http://127.0.0.1:8000
```

For a fresh local beta instance, add `CONVOLOGIX_BETA_CREATE_ADMIN=true` to let the script create the first admin from those credentials.

Security gate:

```bash
python scripts/security-check.py
```

## Speaker Diarization

Diarization is optional because PyAnnote is a heavier dependency and uses a gated Hugging Face model.

```bash
CONVOLOGIX_INSTALL_DIARIZATION=true
HUGGINGFACE_TOKEN=your-token
docker compose up -d --build
```

The Hugging Face account must have accepted the terms for `pyannote/speaker-diarization-3.1`. Without this, ConvoLogix still transcribes and summarizes meetings, but speaker labels remain unassigned.

## Public Release Warning

The v2 release tree is configured to avoid tracking `.env`, runtime data, ONNX models, generated reports, bytecode, and biometric samples. For a public repository, also purge old sensitive files from Git history or publish from a clean/orphan release branch. A normal branch can still expose private files that existed in older commits.

See [INSTALL.md](INSTALL.md) for detailed installation, run, beta-test, and deployment steps.
