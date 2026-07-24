from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings
from app.schemas import FaceMatch, ModelStatus
from app.services.storage import IMAGE_SUFFIXES


class FaceRecognitionNotReady(RuntimeError):
    """Raised when the pretrained detector or recognizer cannot be used yet."""


@dataclass(frozen=True)
class GalleryBuildResult:
    people: int
    embeddings: int
    skipped_images: int


class OpenCVSFaceService:
    """Face recognition using pretrained OpenCV YuNet and SFace ONNX models.

    YuNet detects faces. SFace converts aligned faces into embeddings. Recognition
    is nearest-neighbor matching in embedding space, not training a custom CNN.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cv2: Any | None = None
        self._np: Any | None = None
        self._detector: Any | None = None
        self._recognizer: Any | None = None

    def status(self) -> ModelStatus:
        detector_exists = bool(self.settings.face_detector_model and self.settings.face_detector_model.exists())
        recognizer_exists = bool(
            self.settings.face_recognition_model and self.settings.face_recognition_model.exists()
        )
        ready = detector_exists and recognizer_exists and self.settings.gallery_file.exists()
        if ready:
            message = "Pretrained face recognition is ready."
        elif not detector_exists or not recognizer_exists:
            message = "Configure YuNet and SFace ONNX model files to enable recognition."
        else:
            message = "Enroll at least one person to build the face gallery."

        return ModelStatus(
            detector_configured=self.settings.face_detector_model is not None,
            detector_exists=detector_exists,
            recognizer_configured=self.settings.face_recognition_model is not None,
            recognizer_exists=recognizer_exists,
            gallery_exists=self.settings.gallery_file.exists(),
            threshold=self.settings.face_match_threshold,
            ready=ready,
            message=message,
        )

    def rebuild_gallery(self, enrollment_dir: Path | None = None) -> GalleryBuildResult:
        self._ensure_backend()
        np = self._np
        assert np is not None

        source_dir = enrollment_dir or self.settings.enrollment_dir
        labels: list[str] = []
        embeddings: list[Any] = []
        skipped_images = 0

        for person_dir in sorted(path for path in source_dir.iterdir() if path.is_dir()):
            person_embeddings: list[Any] = []
            for image_path in sorted(person_dir.iterdir()):
                if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                    continue
                image = self._read_image(image_path)
                if image is None:
                    skipped_images += 1
                    continue
                face = self._largest_face(image)
                if face is None:
                    skipped_images += 1
                    continue
                person_embeddings.append(self._feature(image, face))

            if person_embeddings:
                labels.append(person_dir.name)
                embeddings.append(np.mean(np.vstack(person_embeddings), axis=0))

        if embeddings:
            matrix = np.vstack(embeddings).astype("float32")
            labels_array = np.array(labels, dtype=str)
            self.settings.gallery_file.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(self.settings.gallery_file, labels=labels_array, embeddings=matrix)
            return GalleryBuildResult(people=len(labels), embeddings=len(embeddings), skipped_images=skipped_images)

        if self.settings.gallery_file.exists():
            self.settings.gallery_file.unlink()
        return GalleryBuildResult(people=0, embeddings=0, skipped_images=skipped_images)

    def recognize_image(self, image_bytes: bytes) -> list[FaceMatch]:
        self._ensure_backend()
        labels, embeddings = self._load_gallery()
        image = self._decode_image(image_bytes)
        return self._recognize_image_with_gallery(image, labels, embeddings)

    def recognize_image_array(self, image: Any) -> list[FaceMatch]:
        self._ensure_backend()
        labels, embeddings = self._load_gallery()
        return self._recognize_image_with_gallery(image, labels, embeddings)

    def _recognize_image_with_gallery(self, image: Any, labels: Any, embeddings: Any) -> list[FaceMatch]:
        faces = self._detect(image)
        if not faces:
            return []

        np = self._np
        assert np is not None

        matches: list[FaceMatch] = []
        for face in faces:
            feature = self._feature(image, face)
            scores = embeddings @ feature.reshape(-1)
            best_index = int(np.argmax(scores))
            confidence = float(scores[best_index])
            identity = str(labels[best_index]) if confidence >= self.settings.face_match_threshold else "Unknown"
            x, y, w, h = [int(round(value)) for value in face[:4]]
            matches.append(FaceMatch(identity=identity, confidence=confidence, bbox=[x, y, w, h]))
        return matches

    def _ensure_backend(self) -> None:
        if self._detector is not None and self._recognizer is not None:
            return

        if not self.settings.face_detector_model or not self.settings.face_detector_model.exists():
            raise FaceRecognitionNotReady("YuNet detector model is not configured or does not exist.")
        if not self.settings.face_recognition_model or not self.settings.face_recognition_model.exists():
            raise FaceRecognitionNotReady("SFace recognition model is not configured or does not exist.")

        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise FaceRecognitionNotReady("Install OpenCV and NumPy to enable face recognition.") from exc

        if not hasattr(cv2, "FaceDetectorYN_create") or not hasattr(cv2, "FaceRecognizerSF_create"):
            raise FaceRecognitionNotReady("opencv-contrib-python-headless 4.10+ is required for YuNet/SFace.")

        self._cv2 = cv2
        self._np = np
        self._detector = cv2.FaceDetectorYN_create(str(self.settings.face_detector_model), "", (320, 320))
        self._recognizer = cv2.FaceRecognizerSF_create(str(self.settings.face_recognition_model), "")

    def _load_gallery(self) -> tuple[Any, Any]:
        if not self.settings.gallery_file.exists():
            raise FaceRecognitionNotReady("Face gallery is empty. Enroll people first.")

        np = self._np
        assert np is not None
        gallery = np.load(self.settings.gallery_file, allow_pickle=False)
        labels = gallery["labels"]
        embeddings = gallery["embeddings"].astype("float32")
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / np.clip(norms, 1e-12, None)
        return labels, embeddings

    def _decode_image(self, image_bytes: bytes) -> Any:
        cv2 = self._cv2
        np = self._np
        assert cv2 is not None
        assert np is not None
        buffer = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Uploaded file is not a readable image.")
        return image

    def _read_image(self, image_path: Path) -> Any | None:
        cv2 = self._cv2
        assert cv2 is not None
        return cv2.imread(str(image_path), cv2.IMREAD_COLOR)

    def _detect(self, image: Any) -> list[Any]:
        height, width = image.shape[:2]
        assert self._detector is not None
        self._detector.setInputSize((width, height))
        _, faces = self._detector.detect(image)
        if faces is None:
            return []
        return [face for face in faces]

    def _largest_face(self, image: Any) -> Any | None:
        faces = self._detect(image)
        if not faces:
            return None
        return max(faces, key=lambda face: float(face[2] * face[3]))

    def _feature(self, image: Any, face: Any) -> Any:
        np = self._np
        assert np is not None
        assert self._recognizer is not None
        aligned = self._recognizer.alignCrop(image, face)
        feature = self._recognizer.feature(aligned).reshape(-1).astype("float32")
        norm = np.linalg.norm(feature)
        if norm <= 1e-12:
            return feature
        return feature / norm
