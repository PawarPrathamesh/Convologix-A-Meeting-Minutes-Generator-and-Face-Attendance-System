from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import Settings
from app.schemas import EmailReportRequest, EmailReportResponse, MeetingDetailResponse, MeetingProcessResponse
from app.services.storage import meeting_dir, read_meeting_detail


class ReportNotReady(RuntimeError):
    """Raised when a meeting report cannot be generated yet."""


class EmailNotConfigured(RuntimeError):
    """Raised when SMTP settings are incomplete."""


class ReportService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_markdown_report(self, meeting_id: str) -> str:
        detail = read_meeting_detail(self.settings, meeting_id)
        if detail.result is None:
            raise ReportNotReady("Process this meeting before downloading a report.")

        report = self._markdown(detail, detail.result)
        self._write_report_file(meeting_id, "md", report)
        return report

    def build_text_report(self, meeting_id: str) -> str:
        markdown = self.build_markdown_report(meeting_id)
        lines = []
        for line in markdown.splitlines():
            if line.startswith("#"):
                lines.append(line.lstrip("#").strip().upper())
            elif line.startswith("- "):
                lines.append(line)
            else:
                lines.append(line.replace("**", ""))
        report = "\n".join(lines)
        self._write_report_file(meeting_id, "txt", report)
        return report

    def send_report(self, meeting_id: str, request: EmailReportRequest) -> EmailReportResponse:
        if not self._smtp_ready():
            raise EmailNotConfigured("SMTP is not configured. Set CONVOLOGIX_SMTP_* environment variables.")

        detail = read_meeting_detail(self.settings, meeting_id)
        report = self.build_markdown_report(meeting_id)
        message = EmailMessage()
        message["From"] = self.settings.smtp_from_email or ""
        message["To"] = request.receiver_email
        message["Subject"] = request.subject or f"Meeting report: {detail.title}"
        message.set_content(request.body or "Attached is the ConvoLogix meeting report.")
        message.add_attachment(
            report.encode("utf-8"),
            maintype="text",
            subtype="markdown",
            filename=f"convologix-{meeting_id}.md",
        )

        with smtplib.SMTP(self.settings.smtp_host or "", self.settings.smtp_port, timeout=30) as server:
            if self.settings.smtp_use_tls:
                server.starttls()
            if self.settings.smtp_username and self.settings.smtp_password:
                server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(message)

        return EmailReportResponse(sent=True, message="Meeting report sent.")

    def _smtp_ready(self) -> bool:
        return bool(self.settings.smtp_host and self.settings.smtp_from_email)

    def _write_report_file(self, meeting_id: str, suffix: str, content: str) -> None:
        reports_dir = meeting_dir(self.settings, meeting_id) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / f"convologix-{meeting_id}.{suffix}").write_text(content, encoding="utf-8")

    def _markdown(self, detail: MeetingDetailResponse, result: MeetingProcessResponse) -> str:
        lines = [
            f"# {detail.title}",
            "",
            f"- Meeting ID: `{detail.id}`",
            f"- File: `{detail.file_name}`",
            f"- Status: `{detail.status}`",
            f"- Speaker diarization: {'enabled' if result.diarization_enabled else 'not used'}",
            f"- Attendance analysis: {result.attendance_message}",
            f"- Processing note: {result.message}",
            "",
            "## Who Said What",
            "",
        ]

        if result.summary_by_speaker:
            for item in result.summary_by_speaker:
                lines.append(f"### {item.speaker}")
                lines.append("")
                lines.append(item.summary or "No summary available.")
                lines.append("")
        else:
            lines.extend(["No speaker summary was generated.", ""])

        lines.extend(["## Attendance", ""])
        if result.attendance:
            for attendee in result.attendance:
                lines.append(
                    "- "
                    f"**{attendee.person}**: {attendee.detections} detections, "
                    f"first seen {self._format_time(attendee.first_seen)}, "
                    f"last seen {self._format_time(attendee.last_seen)}, "
                    f"best confidence {attendee.best_confidence:.2f}"
                )
        else:
            lines.append("No enrolled attendees were detected or attendance analysis is not configured.")
        lines.append("")

        lines.extend(["## Speaker Turns", ""])
        if result.speaker_turns:
            for turn in result.speaker_turns:
                lines.append(
                    f"- `{self._format_time(turn.start)} - {self._format_time(turn.end)}` "
                    f"**{turn.speaker}:** {turn.text}"
                )
        else:
            lines.append("No speaker turns were generated.")
        lines.append("")

        lines.extend(["## Transcript", ""])
        for segment in result.transcript:
            speaker = segment.speaker or "Unassigned speaker"
            lines.append(
                f"- `{self._format_time(segment.start)} - {self._format_time(segment.end)}` "
                f"**{speaker}:** {segment.text}"
            )

        return "\n".join(lines).strip() + "\n"

    def _format_time(self, seconds: float) -> str:
        total_seconds = max(0, round(seconds))
        minutes, remainder = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{remainder:02d}"
        return f"{minutes}:{remainder:02d}"
