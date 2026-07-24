# ConvoLogix v2 Install And Run Guide

## Prerequisites

- Docker Desktop with Docker Compose
- Git
- Two OpenCV ONNX face models:
  - `face_detection_yunet_2023mar.onnx`
  - `face_recognition_sface_2021dec.onnx`
- Optional: Hugging Face token with accepted access to `pyannote/speaker-diarization-3.1`

## 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:

```text
CONVOLOGIX_AUTH_SECRET_KEY=<long-random-secret>
CONVOLOGIX_AUTH_ENABLED=true
```

Optional bootstrap admin:

```text
CONVOLOGIX_BOOTSTRAP_ADMIN_EMAIL=admin@example.com
CONVOLOGIX_BOOTSTRAP_ADMIN_PASSWORD=<strong-password>
CONVOLOGIX_BOOTSTRAP_ADMIN_NAME=ConvoLogix Admin
```

If bootstrap variables are empty, the first browser visit shows the admin setup form.

## 2. Add Face Models

Create `models/` and place the ONNX files there:

```text
models/
  face_detection_yunet_2023mar.onnx
  face_recognition_sface_2021dec.onnx
```

These files stay local and are mounted into Docker. They are intentionally ignored by Git.

## 3. Start The App

```bash
docker compose up -d --build
```

Frontend:

```text
http://localhost:5180
```

Backend health:

```text
http://127.0.0.1:8000/api/health
```

Stop the stack:

```bash
docker compose down
```

## 4. Create Users

Open the frontend and create the first admin if setup is required. Admin users can add:

- `viewer`: view meetings/reports they own
- `member`: upload and process meetings
- `admin`: manage users, enrollment, and all meetings

## 5. Enable Speaker Diarization

Set these values before rebuilding:

```text
CONVOLOGIX_INSTALL_DIARIZATION=true
HUGGINGFACE_TOKEN=<hf-token>
```

Then rebuild:

```bash
docker compose up -d --build
```

Check access from the frontend System screen or with:

```bash
CONVOLOGIX_BETA_EMAIL=admin@example.com CONVOLOGIX_BETA_PASSWORD=<password> python scripts/beta-readiness.py http://127.0.0.1:8000
```

## 6. Run Release Checks

Syntax and security checks:

```bash
python -m compileall backend/app scripts
node --check frontend/app.js
python scripts/security-check.py
```

Smoke test:

```bash
CONVOLOGIX_SMOKE_EMAIL=admin@example.com CONVOLOGIX_SMOKE_PASSWORD=<password> python scripts/smoke-test.py http://127.0.0.1:8000
```

For a fresh local instance, add `CONVOLOGIX_SMOKE_CREATE_ADMIN=true` to create the first admin during smoke testing.

Beta readiness:

```bash
CONVOLOGIX_BETA_EMAIL=admin@example.com CONVOLOGIX_BETA_PASSWORD=<password> python scripts/beta-readiness.py http://127.0.0.1:8000
```

For a fresh local beta instance, add `CONVOLOGIX_BETA_CREATE_ADMIN=true` to create the first admin during the beta gate.

## 7. CI/CD

The repository includes:

- `.github/workflows/ci.yml`: security check, Python compile, frontend syntax check, Docker Compose validation, image build, API tests
- `.github/workflows/publish-images.yml`: manual/tagged publish of API and frontend images to GitHub Container Registry

For production, set environment variables through your deployment platform or GitHub Actions secrets. Do not commit `.env`, meeting videos, face images, report outputs, or model binaries.

## 8. Public Git Release

Before pushing to a public repository, use a clean release branch or purge old Git history. The current tree is cleaned, but old commits may still contain biometric samples or credentials if they existed before v2 cleanup.
