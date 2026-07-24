# ConvoLogix v2 Face Recognition

## Direction

V2 should not train a custom CNN classifier from scratch. The new backend uses a pretrained face pipeline:

- YuNet detects faces in uploaded images.
- SFace converts aligned faces into embeddings.
- ConvoLogix stores one averaged embedding per enrolled attendee.
- Recognition compares new face embeddings with the gallery using cosine similarity.

This is cleaner than the old LBPH/custom-CNN path because enrollment can work with fewer images, model quality is not tied to our small dataset, and Docker can mount model files separately from source code.

## Model Files

Put these ONNX files in `models/` before enabling recognition:

- `face_detection_yunet_2023mar.onnx`
- `face_recognition_sface_2021dec.onnx`

They are intentionally not committed. Docker Compose mounts `./models` as read-only into `/app/models`.

## API Flow

1. `POST /api/faces/enroll`
   - form field `person_name`
   - one or more image files in `files`
   - stores images under `data/faces/<person-id>/`
   - rebuilds `data/face_gallery.npz` when the ONNX models are available

2. `POST /api/faces/recognize`
   - one image file in `file`
   - returns detected faces, bounding boxes, identity, and similarity score

3. `GET /api/faces/gallery`
   - shows enrolled people and model readiness

## Docker

Run the v2 stack after placing the model files:

```bash
docker compose up --build
```

Frontend: `http://localhost:5180`

Backend: `http://127.0.0.1:8000/api/health`

## Next Development Steps

1. Add video frame sampling and call the same SFace service for attendance.
2. Add ASR/transcription as a separate meeting processing service.
3. Store meeting processing jobs in SQLite/Postgres instead of JSON files.
4. Move email credentials to environment variables or an email provider integration.
5. Add automated tests for enrollment, recognition error states, and upload validation.
