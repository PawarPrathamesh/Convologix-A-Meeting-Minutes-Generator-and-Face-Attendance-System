# ConvoLogix v2 Notes

ConvoLogix v2 is the deployable web version of the project. The canonical release README is now [README.md](README.md), and detailed install/run steps are in [INSTALL.md](INSTALL.md).

## What Works

- Meeting video upload
- Background meeting processing
- FFmpeg audio extraction
- Whisper-compatible transcription with `faster-whisper`
- Optional PyAnnote speaker diarization for "who said what"
- Pretrained YuNet/SFace face recognition path
- Login, roles, protected meeting access, and admin user management
- Face enrollment and image recognition APIs
- Video-frame attendance sampling during meeting processing
- Markdown and text report downloads
- SMTP email-report hook through environment variables
- Docker Compose deployment
- GitHub Actions CI/CD workflows

## Run

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

Smoke test:

```bash
python scripts/smoke-test.py http://127.0.0.1:8000
```

Beta readiness test:

```bash
python scripts/beta-readiness.py http://127.0.0.1:8000
```

## Face Recognition Models

Place these model files in `models/`:

- `face_detection_yunet_2023mar.onnx`
- `face_recognition_sface_2021dec.onnx`

The app will run without them, but face enrollment/recognition and attendance detection will report that the model is not ready.

## Speaker Diarization

Transcription is included in the default backend image. Real speaker diarization is optional because PyAnnote is heavy and requires gated model access.

Enable diarization before rebuilding:

```bash
CONVOLOGIX_INSTALL_DIARIZATION=true
HUGGINGFACE_TOKEN=your_token
docker compose up -d --build
```

The token must have read access and the gated model conditions must be accepted for `pyannote/speaker-diarization-3.1`. Use `GET /api/speech/diarization-check` or `python scripts/beta-readiness.py` to verify model access after rebuilding.

Without that setup, meetings still transcribe and summarize, but speaker labels remain unassigned.

## SMTP Report Email

Configure these variables when email delivery is needed:

```bash
CONVOLOGIX_SMTP_HOST=smtp.example.com
CONVOLOGIX_SMTP_PORT=587
CONVOLOGIX_SMTP_USERNAME=user@example.com
CONVOLOGIX_SMTP_PASSWORD=secret
CONVOLOGIX_SMTP_FROM_EMAIL=user@example.com
CONVOLOGIX_SMTP_USE_TLS=true
```

Never commit real SMTP passwords or biometric data.
