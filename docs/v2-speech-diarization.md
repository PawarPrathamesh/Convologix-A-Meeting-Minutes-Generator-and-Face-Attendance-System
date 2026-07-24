# ConvoLogix v2 Speech Diarization

## Goal

The meeting output should answer "who said what" instead of returning one anonymous summary.

The v2 backend now has a speech intelligence service that:

- extracts mono 16 kHz WAV audio from uploaded meeting videos with FFmpeg
- transcribes timestamped speech segments with `faster-whisper`
- optionally runs PyAnnote speaker diarization when a Hugging Face token is configured
- aligns transcript segments to speaker turns by timestamp overlap
- generates a per-speaker summary and a speaker-turn transcript

## Endpoints

Upload a meeting:

```bash
POST /api/meetings
```

Process speech and diarization:

```bash
POST /api/meetings/{meeting_id}/process
```

Read meeting details and saved result:

```bash
GET /api/meetings/{meeting_id}
```

Check pipeline readiness:

```bash
GET /api/health
```

The health response includes `speech.ready_for_transcription` and `speech.ready_for_diarization`. This is a fast runtime check only.

Verify gated PyAnnote model access:

```bash
GET /api/speech/diarization-check
```

This endpoint requires an admin bearer token when auth is enabled. The frontend System screen handles that automatically after admin login.

Run the full beta gate:

```bash
CONVOLOGIX_BETA_EMAIL=admin@example.com CONVOLOGIX_BETA_PASSWORD=your-password python scripts/beta-readiness.py http://127.0.0.1:8000
```

## Configuration

Docker Compose includes these environment variables:

```bash
CONVOLOGIX_INSTALL_DIARIZATION=false
CONVOLOGIX_ASR_MODEL=small.en
CONVOLOGIX_ASR_DEVICE=cpu
CONVOLOGIX_ASR_COMPUTE_TYPE=int8
CONVOLOGIX_DIARIZATION_MODEL=pyannote/speaker-diarization-3.1
HUGGINGFACE_TOKEN=
```

For real diarization, set `CONVOLOGIX_INSTALL_DIARIZATION=true` before building and set `HUGGINGFACE_TOKEN` to a token that has read access to the selected PyAnnote model. The Hugging Face user must also accept the gated model conditions for `pyannote/speaker-diarization-3.1`. Without that package and token, ConvoLogix still transcribes the meeting, but speaker labels remain unassigned and the API returns `processed_without_diarization`.

Optional speaker-count hints:

```bash
CONVOLOGIX_DIARIZATION_MIN_SPEAKERS=2
CONVOLOGIX_DIARIZATION_MAX_SPEAKERS=6
```

## Output Shape

`MeetingProcessResponse` contains:

- `transcript`: timestamped ASR segments
- `speaker_turns`: merged consecutive segments by speaker
- `summary_by_speaker`: concise "who said what" summary
- `diarization_enabled`: whether real diarization was used

## Next Steps

1. Accept gated PyAnnote model access and rerun `scripts/beta-readiness.py`.
2. Run a real multi-speaker meeting through the frontend and inspect speaker turns.
3. Replace the simple extractive per-speaker summary with a stronger summarizer once the transcript data path is stable.
