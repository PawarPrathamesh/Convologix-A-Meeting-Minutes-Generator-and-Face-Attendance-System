# ConvoLogix v2 Install And Run Guide

This guide takes a fresh machine from clone to beta-ready ConvoLogix v2. The recommended deployment path is Docker Compose because it keeps Python, FFmpeg, OpenCV, Nginx, and optional diarization dependencies isolated.

## 1. Prerequisites

Install:

- Docker Desktop with Docker Compose
- Git
- A terminal: PowerShell on Windows, Terminal on macOS/Linux

Required local model files:

- `face_detection_yunet_2023mar.onnx`
- `face_recognition_sface_2021dec.onnx`

Optional for speaker diarization:

- Hugging Face account
- Hugging Face access token
- Accepted model terms for `pyannote/speaker-diarization-3.1`

## 2. Clone And Choose The Release Branch

Clone the repository:

```bash
git clone <repository-url>
cd <repository-folder>
```

For the public v2 release branch:

```bash
git checkout codex/v2-release
```

If you are developing locally before push, use the current local release branch created by Codex.

## 3. Configure Environment

Create your private environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set at minimum:

```text
CONVOLOGIX_AUTH_ENABLED=true
CONVOLOGIX_AUTH_SECRET_KEY=<long-random-secret>
```

Generate a strong secret with Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Optional first-admin bootstrap:

```text
CONVOLOGIX_BOOTSTRAP_ADMIN_EMAIL=admin@example.com
CONVOLOGIX_BOOTSTRAP_ADMIN_PASSWORD=<strong-password>
CONVOLOGIX_BOOTSTRAP_ADMIN_NAME=ConvoLogix Admin
```

If bootstrap values are empty, the frontend shows a first-admin setup form.

## 4. Add Face Recognition Models

Create the model folder:

```bash
mkdir models
```

Place the files here:

```text
models/
  face_detection_yunet_2023mar.onnx
  face_recognition_sface_2021dec.onnx
```

These models are mounted read-only into the API container. They are intentionally ignored by Git.

## 5. Start ConvoLogix

Build and start:

```bash
docker compose up -d --build
```

Check containers:

```bash
docker compose ps
```

Open the app:

```text
http://localhost:5180
```

Backend health:

```text
http://127.0.0.1:8000/api/health
```

Stop:

```bash
docker compose down
```

Stop and remove local runtime data only when you intentionally want a fresh instance:

```bash
docker compose down
```

Then delete `data/` manually if needed.

## 6. Create Users

On the first browser launch, create the first admin account if setup is required.

After admin login:

1. Open the System screen.
2. Use User Access to add users.
3. Assign one of these roles:

| Role | Best For | Permissions |
| --- | --- | --- |
| `viewer` | Stakeholders | View owned meetings and reports |
| `member` | Meeting operators | Upload/process meetings and send reports |
| `admin` | Maintainers | Manage users, enrollment, diarization checks, all meetings |

## 7. Enroll Attendees

Admin users can enroll attendees:

1. Open Enrollment.
2. Enter a person name.
3. Upload multiple clear face images.
4. Submit the form.

The backend stores images under local runtime data and rebuilds the face embedding gallery. Use well-lit, consented images for best results.

## 8. Upload And Process A Meeting

Member or admin users can:

1. Open Meetings.
2. Upload a meeting video.
3. Select the uploaded meeting.
4. Click Process Speech.
5. Wait for processing to finish.
6. Review speaker summaries, speaker turns, attendance, and report downloads.

Long recordings can take several minutes depending on CPU speed and selected ASR model.

## 9. Enable Speaker Diarization

Transcription is available by default. For real speaker labels, enable PyAnnote:

```text
CONVOLOGIX_INSTALL_DIARIZATION=true
HUGGINGFACE_TOKEN=<hf-token>
```

Optional speaker-count hints:

```text
CONVOLOGIX_DIARIZATION_MIN_SPEAKERS=2
CONVOLOGIX_DIARIZATION_MAX_SPEAKERS=6
```

Rebuild:

```bash
docker compose up -d --build
```

Verify in the frontend:

1. Log in as admin.
2. Open System.
3. Click Check Diarization Access.

Or use the beta script:

```bash
CONVOLOGIX_BETA_EMAIL=admin@example.com CONVOLOGIX_BETA_PASSWORD=<password> python scripts/beta-readiness.py http://127.0.0.1:8000
```

For a fresh local beta instance:

```bash
CONVOLOGIX_BETA_EMAIL=admin@example.com CONVOLOGIX_BETA_PASSWORD=<password> CONVOLOGIX_BETA_CREATE_ADMIN=true python scripts/beta-readiness.py http://127.0.0.1:8000
```

If PyAnnote reports gated access failure, visit the Hugging Face page for `pyannote/speaker-diarization-3.1`, accept the conditions, confirm the token has read access, and rerun the check.

## 10. Configure Email Reports

Set SMTP values in `.env`:

```text
CONVOLOGIX_SMTP_HOST=smtp.example.com
CONVOLOGIX_SMTP_PORT=587
CONVOLOGIX_SMTP_USERNAME=user@example.com
CONVOLOGIX_SMTP_PASSWORD=<smtp-password>
CONVOLOGIX_SMTP_FROM_EMAIL=user@example.com
CONVOLOGIX_SMTP_USE_TLS=true
```

Restart the API:

```bash
docker compose up -d
```

Email delivery is optional. Report downloads work without SMTP.

## 11. Run Local Verification

Syntax checks:

```bash
python -m compileall backend/app scripts
node --check frontend/app.js
```

Security gate:

```bash
python scripts/security-check.py
```

Backend tests in Docker:

```bash
docker compose exec api python -m unittest discover -s tests
```

Smoke test:

```bash
python scripts/smoke-test.py http://127.0.0.1:8000
```

Authenticated smoke test:

```bash
CONVOLOGIX_SMOKE_EMAIL=admin@example.com CONVOLOGIX_SMOKE_PASSWORD=<password> python scripts/smoke-test.py http://127.0.0.1:8000
```

Fresh-instance smoke test with first-admin creation:

```bash
CONVOLOGIX_SMOKE_EMAIL=admin@example.com CONVOLOGIX_SMOKE_PASSWORD=<password> CONVOLOGIX_SMOKE_CREATE_ADMIN=true python scripts/smoke-test.py http://127.0.0.1:8000
```

## 12. CI/CD

The release includes two GitHub Actions workflows:

- `.github/workflows/ci.yml`
  - tracked-file security check
  - Python compile
  - frontend JavaScript syntax check
  - Docker Compose config validation
  - Docker image build
  - API tests in the image

- `.github/workflows/publish-images.yml`
  - manual or tag-triggered publish to GitHub Container Registry
  - API image
  - frontend image

Use repository or environment secrets for production values. Never commit `.env`.

## 13. Public Release Checklist

Before pushing publicly:

- Confirm you are on a clean root-history release branch.
- Run `python scripts/security-check.py`.
- Confirm `.env` is not tracked.
- Confirm `data/` is not tracked.
- Confirm `models/*.onnx` are not tracked.
- Confirm face images, meeting videos, generated reports, and bytecode are not tracked.
- Confirm old Git history is not being pushed if it contains private artifacts.

The safe public branch created by Codex is intended for this exact reason.

## 14. Troubleshooting

### API Is Offline

```bash
docker compose ps
docker compose logs api
```

### Frontend Loads But API Calls Fail

Open System and confirm the API base URL is:

```text
http://127.0.0.1:8000
```

### Face Recognition Is Not Ready

Confirm the ONNX files exist in `models/` and restart:

```bash
docker compose up -d --build
```

### Diarization Fails

Confirm:

- `CONVOLOGIX_INSTALL_DIARIZATION=true`
- token is present in `.env`
- Hugging Face terms are accepted
- Docker image was rebuilt after changing the install flag

### Protected Endpoints Return 401

Log in again. Tokens expire according to `CONVOLOGIX_AUTH_TOKEN_MINUTES`.

### Need A Clean Local Beta Reset

Stop the stack, remove `data/`, then start again:

```bash
docker compose down
```

Delete `data/` manually, then:

```bash
docker compose up -d
```
