from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.schemas import AttendanceObservation, AttendanceSummary
from app.services.face_recognition import FaceRecognitionNotReady, OpenCVSFaceService


@dataclass(frozen=True)
class AttendanceAnalysis:
    enabled: bool
    message: str
    attendance: list[AttendanceSummary]
    observations: list[AttendanceObservation]


class VideoAttendanceService:
    def __init__(self, settings: Settings, face_service: OpenCVSFaceService) -> None:
        self.settings = settings
        self.face_service = face_service

    def analyze_video(self, video_path: Path) -> AttendanceAnalysis:
        status = self.face_service.status()
        if not status.ready:
            return AttendanceAnalysis(
                enabled=False,
                message=status.message,
                attendance=[],
                observations=[],
            )

        try:
            import cv2
        except ImportError as exc:
            raise FaceRecognitionNotReady("Install OpenCV to analyze video attendance.") from exc

        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            return AttendanceAnalysis(
                enabled=False,
                message="Could not open meeting video for attendance analysis.",
                attendance=[],
                observations=[],
            )

        try:
            fps = capture.get(cv2.CAP_PROP_FPS) or 0
            frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            duration = frame_count / fps if fps > 0 and frame_count > 0 else 0
            timestamps = self._sample_timestamps(duration)
            observations: list[AttendanceObservation] = []

            for timestamp in timestamps:
                capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                ok, frame = capture.read()
                if not ok:
                    continue

                for match in self.face_service.recognize_image_array(frame):
                    if match.identity == "Unknown":
                        continue
                    observations.append(
                        AttendanceObservation(
                            person=match.identity,
                            timestamp=round(timestamp, 2),
                            confidence=match.confidence,
                            bbox=match.bbox,
                        )
                    )

            attendance = self._summarize(observations)
            return AttendanceAnalysis(
                enabled=True,
                message=(
                    f"Attendance analyzed from {len(timestamps)} sampled frames."
                    if attendance
                    else f"No enrolled attendees were detected in {len(timestamps)} sampled frames."
                ),
                attendance=attendance,
                observations=observations,
            )
        finally:
            capture.release()

    def _sample_timestamps(self, duration: float) -> list[float]:
        max_frames = max(1, self.settings.attendance_max_frames)
        interval = max(1.0, self.settings.attendance_sample_interval_seconds)
        if duration <= 0:
            return [0.0]

        timestamps: list[float] = []
        current = 0.0
        while current <= duration and len(timestamps) < max_frames:
            timestamps.append(round(current, 2))
            current += interval

        if timestamps[-1] < duration and len(timestamps) < max_frames:
            timestamps.append(round(duration, 2))
        return timestamps

    def _summarize(self, observations: list[AttendanceObservation]) -> list[AttendanceSummary]:
        grouped: dict[str, list[AttendanceObservation]] = {}
        for observation in observations:
            grouped.setdefault(observation.person, []).append(observation)

        summaries: list[AttendanceSummary] = []
        for person, entries in grouped.items():
            summaries.append(
                AttendanceSummary(
                    person=person,
                    first_seen=min(entry.timestamp for entry in entries),
                    last_seen=max(entry.timestamp for entry in entries),
                    detections=len(entries),
                    best_confidence=max(entry.confidence for entry in entries),
                )
            )

        return sorted(summaries, key=lambda item: (-item.detections, item.person))
