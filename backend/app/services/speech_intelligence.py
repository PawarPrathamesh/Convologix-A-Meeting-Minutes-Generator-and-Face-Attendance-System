from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings
from app.schemas import (
    AttendanceObservation,
    AttendanceSummary,
    DiarizationCheckResponse,
    MeetingProcessResponse,
    MeetingSummary,
    SpeakerTurn,
    SpeechPipelineStatus,
    TranscriptSegment,
)
from app.services.storage import (
    meeting_dir,
    meeting_video_path,
    read_meeting_metadata,
    save_meeting_result,
    update_meeting_status,
)


class SpeechProcessingNotReady(RuntimeError):
    """Raised when transcription or diarization cannot run in the current environment."""


@dataclass(frozen=True)
class DiarizationTurn:
    start: float
    end: float
    speaker: str


class SpeechIntelligenceService:
    def __init__(self, settings: Settings, attendance_service: Any | None = None) -> None:
        self.settings = settings
        self.attendance_service = attendance_service
        self._asr_model: Any | None = None
        self._diarization_pipeline: Any | None = None

    def status(self) -> SpeechPipelineStatus:
        ffmpeg_available = self._ffmpeg_available()
        asr_available = self._package_available("faster_whisper")
        diarization_available = self._package_available("pyannote.audio")
        ready_for_transcription = ffmpeg_available and asr_available
        ready_for_diarization = ready_for_transcription and diarization_available and bool(self.settings.huggingface_token)
        diarization_model_access = "verified" if self._diarization_pipeline is not None else "not_checked"

        if not ready_for_transcription:
            message = "Install FFmpeg and faster-whisper to process meeting audio."
        elif not ready_for_diarization:
            message = "Transcription is ready. Configure PyAnnote and HUGGINGFACE_TOKEN for speaker diarization."
        else:
            message = "Transcription and diarization dependencies are configured. Verify gated model access before beta testing."

        return SpeechPipelineStatus(
            ffmpeg_available=ffmpeg_available,
            asr_package_available=asr_available,
            asr_model=self.settings.asr_model,
            diarization_package_available=diarization_available,
            diarization_model=self.settings.diarization_model,
            diarization_token_configured=bool(self.settings.huggingface_token),
            diarization_model_access=diarization_model_access,
            diarization_model_message=(
                "PyAnnote pipeline has loaded successfully."
                if diarization_model_access == "verified"
                else "Run /api/speech/diarization-check to verify Hugging Face gated model access."
            ),
            ready_for_transcription=ready_for_transcription,
            ready_for_diarization=ready_for_diarization,
            message=message,
        )

    def check_diarization_model_access(self, load_model: bool = True) -> DiarizationCheckResponse:
        status = self.status()
        if not status.ready_for_diarization:
            return DiarizationCheckResponse(
                ok=False,
                model=self.settings.diarization_model,
                package_available=status.diarization_package_available,
                token_configured=status.diarization_token_configured,
                pipeline_loaded=False,
                message=status.message,
            )

        if not load_model:
            return DiarizationCheckResponse(
                ok=True,
                model=self.settings.diarization_model,
                package_available=True,
                token_configured=True,
                pipeline_loaded=False,
                message="Diarization dependencies and token are configured. Model load check was skipped.",
            )

        try:
            pipeline = self._load_diarization_pipeline()
        except Exception as exc:
            return DiarizationCheckResponse(
                ok=False,
                model=self.settings.diarization_model,
                package_available=True,
                token_configured=True,
                pipeline_loaded=False,
                message=str(exc),
            )

        return DiarizationCheckResponse(
            ok=True,
            model=self.settings.diarization_model,
            package_available=True,
            token_configured=True,
            pipeline_loaded=pipeline is not None,
            message="PyAnnote diarization pipeline loaded successfully.",
        )

    def process_meeting(self, meeting_id: str) -> MeetingProcessResponse:
        metadata = read_meeting_metadata(self.settings, meeting_id)
        update_meeting_status(self.settings, meeting_id, "processing")

        try:
            video_path = meeting_video_path(self.settings, meeting_id)
            audio_path = self._extract_audio(meeting_id, video_path)
            transcript = self._transcribe(audio_path)
            diarization_error = None
            diarization_turns: list[DiarizationTurn] = []
            if self.status().ready_for_diarization:
                try:
                    diarization_turns = self._diarize(audio_path)
                except SpeechProcessingNotReady as exc:
                    diarization_error = str(exc)
            diarization_enabled = bool(diarization_turns)
            transcript = self._assign_speakers(transcript, diarization_turns)
            speaker_turns = self._build_speaker_turns(transcript)
            summary = self._summarize_by_speaker(speaker_turns)
            attendance_enabled, attendance_message, attendance, observations = self._analyze_attendance(video_path)
            status = "processed" if diarization_enabled else "processed_without_diarization"

            result = MeetingProcessResponse(
                id=meeting_id,
                title=metadata["title"],
                status=status,
                diarization_enabled=diarization_enabled,
                attendance_enabled=attendance_enabled,
                attendance_message=attendance_message,
                transcript=transcript,
                speaker_turns=speaker_turns,
                summary_by_speaker=summary,
                attendance=attendance,
                attendance_observations=observations,
                speech=self.status(),
                message=(
                    "Meeting processed with speaker diarization."
                    if diarization_enabled
                    else (
                        f"Meeting transcribed. Speaker diarization skipped: {diarization_error}"
                        if diarization_error
                        else "Meeting transcribed. Speaker diarization is not configured yet."
                    )
                ),
            )
            save_meeting_result(self.settings, meeting_id, result)
            update_meeting_status(self.settings, meeting_id, status)
            return result
        except Exception as exc:
            update_meeting_status(self.settings, meeting_id, "failed", str(exc))
            raise

    def _analyze_attendance(
        self,
        video_path: Path,
    ) -> tuple[bool, str, list[AttendanceSummary], list[AttendanceObservation]]:
        if self.attendance_service is None:
            return False, "Attendance service is not configured.", [], []

        try:
            analysis = self.attendance_service.analyze_video(video_path)
        except Exception as exc:
            return False, f"Attendance analysis failed: {exc}", [], []

        return analysis.enabled, analysis.message, analysis.attendance, analysis.observations

    def _ffmpeg_available(self) -> bool:
        binary = self.settings.ffmpeg_binary
        return bool(shutil.which(binary) or Path(binary).exists())

    def _package_available(self, package_name: str) -> bool:
        try:
            return importlib.util.find_spec(package_name) is not None
        except (ModuleNotFoundError, ValueError):
            return False

    def _extract_audio(self, meeting_id: str, video_path: Path) -> Path:
        if not self._ffmpeg_available():
            raise SpeechProcessingNotReady("FFmpeg is required to extract meeting audio.")
        if not video_path.exists():
            raise FileNotFoundError(f"Meeting video does not exist: {video_path}")

        output_path = meeting_dir(self.settings, meeting_id) / "audio.wav"
        command = [
            self.settings.ffmpeg_binary,
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            str(output_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(f"Audio extraction failed: {detail[-800:]}")
        return output_path

    def _transcribe(self, audio_path: Path) -> list[TranscriptSegment]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise SpeechProcessingNotReady("Install faster-whisper to enable transcription.") from exc

        if self._asr_model is None:
            self._asr_model = WhisperModel(
                self.settings.asr_model,
                device=self.settings.asr_device,
                compute_type=self.settings.asr_compute_type,
            )

        raw_segments, _ = self._asr_model.transcribe(
            str(audio_path),
            vad_filter=True,
            word_timestamps=False,
        )
        segments = [
            TranscriptSegment(
                start=round(float(segment.start), 2),
                end=round(float(segment.end), 2),
                speaker=None,
                text=segment.text.strip(),
            )
            for segment in raw_segments
            if segment.text.strip()
        ]
        if not segments:
            raise RuntimeError("No speech was detected in the meeting audio.")
        return segments

    def _diarize(self, audio_path: Path) -> list[DiarizationTurn]:
        if not self.settings.huggingface_token:
            return []
        pipeline = self._load_diarization_pipeline()

        kwargs: dict[str, int] = {}
        if self.settings.diarization_min_speakers is not None:
            kwargs["min_speakers"] = self.settings.diarization_min_speakers
        if self.settings.diarization_max_speakers is not None:
            kwargs["max_speakers"] = self.settings.diarization_max_speakers

        annotation = pipeline(str(audio_path), **kwargs)
        turns: list[DiarizationTurn] = []
        speaker_map: dict[str, str] = {}
        for turn, _, raw_speaker in annotation.itertracks(yield_label=True):
            speaker = speaker_map.setdefault(raw_speaker, f"Speaker {len(speaker_map) + 1}")
            turns.append(DiarizationTurn(start=float(turn.start), end=float(turn.end), speaker=speaker))
        return turns

    def _load_diarization_pipeline(self) -> Any:
        try:
            from pyannote.audio import Pipeline
        except ImportError as exc:
            raise SpeechProcessingNotReady("Install pyannote.audio to enable speaker diarization.") from exc

        if self._diarization_pipeline is None:
            self._diarization_pipeline = Pipeline.from_pretrained(
                self.settings.diarization_model,
                use_auth_token=self.settings.huggingface_token,
            )
            if self._diarization_pipeline is None:
                raise SpeechProcessingNotReady(
                    "Could not download PyAnnote diarization model. Confirm the token has read access and "
                    "accept the gated model conditions for pyannote/speaker-diarization-3.1 on Hugging Face."
                )
        return self._diarization_pipeline

    def _assign_speakers(
        self,
        transcript: list[TranscriptSegment],
        diarization_turns: list[DiarizationTurn],
    ) -> list[TranscriptSegment]:
        if not diarization_turns:
            return transcript

        assigned: list[TranscriptSegment] = []
        for segment in transcript:
            best_speaker = None
            best_overlap = 0.0
            for turn in diarization_turns:
                overlap = max(0.0, min(segment.end, turn.end) - max(segment.start, turn.start))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = turn.speaker

            assigned.append(
                TranscriptSegment(
                    start=segment.start,
                    end=segment.end,
                    speaker=best_speaker or "Unknown speaker",
                    text=segment.text,
                )
            )
        return assigned

    def _build_speaker_turns(self, transcript: list[TranscriptSegment]) -> list[SpeakerTurn]:
        turns: list[SpeakerTurn] = []
        for segment in transcript:
            speaker = segment.speaker or "Unassigned speaker"
            if turns and turns[-1].speaker == speaker and segment.start - turns[-1].end <= 2.5:
                previous = turns[-1]
                turns[-1] = SpeakerTurn(
                    speaker=previous.speaker,
                    start=previous.start,
                    end=segment.end,
                    text=f"{previous.text} {segment.text}".strip(),
                )
            else:
                turns.append(
                    SpeakerTurn(
                        speaker=speaker,
                        start=segment.start,
                        end=segment.end,
                        text=segment.text,
                    )
                )
        return turns

    def _summarize_by_speaker(self, turns: list[SpeakerTurn]) -> list[MeetingSummary]:
        grouped: dict[str, list[str]] = {}
        for turn in turns:
            grouped.setdefault(turn.speaker, []).append(turn.text)

        summaries: list[MeetingSummary] = []
        for speaker, chunks in grouped.items():
            text = " ".join(chunks)
            sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
            selected = self._select_summary_sentences(sentences)
            summaries.append(MeetingSummary(speaker=speaker, summary=" ".join(selected)))
        return summaries

    def _select_summary_sentences(self, sentences: list[str]) -> list[str]:
        if not sentences:
            return []
        if len(sentences) <= 2:
            return sentences

        scored = sorted(
            enumerate(sentences),
            key=lambda item: (self._sentence_score(item[1]), -item[0]),
            reverse=True,
        )
        selected_indexes = sorted(index for index, _ in scored[:2])
        return [sentences[index] for index in selected_indexes]

    def _sentence_score(self, sentence: str) -> int:
        words = re.findall(r"[a-zA-Z0-9]+", sentence.lower())
        signal_words = {
            "decide",
            "decided",
            "action",
            "deadline",
            "risk",
            "issue",
            "blocker",
            "next",
            "plan",
            "owner",
            "deliver",
            "complete",
            "important",
        }
        return len(words) + sum(8 for word in words if word in signal_words)
