from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


def fetch_json(
    base_url: str,
    path: str,
    token: str | None = None,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 900,
) -> dict | list:
    url = f"{base_url.rstrip('/')}{path}"
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(f"{path} returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{path} returned HTTP {exc.code}: {detail}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def beta_login(base_url: str) -> str | None:
    status = fetch_json(base_url, "/api/auth/status", timeout=20)
    require(isinstance(status, dict), "Auth status response must be a JSON object.")
    if not status.get("enabled"):
        return None

    email = (
        os.getenv("CONVOLOGIX_BETA_EMAIL")
        or os.getenv("CONVOLOGIX_SMOKE_EMAIL")
        or os.getenv("CONVOLOGIX_BOOTSTRAP_ADMIN_EMAIL")
    )
    password = (
        os.getenv("CONVOLOGIX_BETA_PASSWORD")
        or os.getenv("CONVOLOGIX_SMOKE_PASSWORD")
        or os.getenv("CONVOLOGIX_BOOTSTRAP_ADMIN_PASSWORD")
    )
    if status.get("setup_required"):
        if os.getenv("CONVOLOGIX_BETA_CREATE_ADMIN", "").strip().lower() not in {"1", "true", "yes", "on"}:
            raise RuntimeError("Initial admin setup is required before beta readiness can run.")
        if not email or not password:
            raise RuntimeError(
                "Set CONVOLOGIX_BETA_EMAIL and CONVOLOGIX_BETA_PASSWORD to create the first admin."
            )
        setup_response = fetch_json(
            base_url,
            "/api/auth/setup",
            method="POST",
            payload={
                "email": email,
                "password": password,
                "display_name": os.getenv("CONVOLOGIX_BETA_NAME", "ConvoLogix Beta Admin"),
                "role": "admin",
            },
            timeout=20,
        )
        require(isinstance(setup_response, dict), "Setup response must be a JSON object.")
        token = setup_response.get("access_token")
        require(isinstance(token, str) and bool(token), "Setup response must include access_token.")
        return token

    if not email or not password:
        raise RuntimeError(
            "Set CONVOLOGIX_BETA_EMAIL and CONVOLOGIX_BETA_PASSWORD for authenticated beta readiness checks."
        )

    token_response = fetch_json(
        base_url,
        "/api/auth/login",
        method="POST",
        payload={"email": email, "password": password},
        timeout=20,
    )
    require(isinstance(token_response, dict), "Login response must be a JSON object.")
    token = token_response.get("access_token")
    require(isinstance(token, str) and bool(token), "Login response must include access_token.")
    return token


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    failures: list[str] = []
    passes: list[str] = []

    def check(condition: bool, passed: str, failed: str) -> None:
        if condition:
            passes.append(passed)
        else:
            failures.append(failed)

    token = beta_login(base_url)
    passes.append("Authenticated beta check session is ready")

    health = fetch_json(base_url, "/api/health", timeout=20)
    if not isinstance(health, dict):
        raise RuntimeError("Health response must be a JSON object.")

    model = health.get("model", {})
    speech = health.get("speech", {})
    check(health.get("status") == "ok", "API health is ok", "API health is not ok")
    check(bool(model.get("ready")), "Face recognition model is ready", str(model.get("message")))
    check(
        bool(speech.get("ready_for_transcription")),
        "Transcription runtime is ready",
        "Transcription runtime is not ready",
    )
    check(
        bool(speech.get("ready_for_diarization")),
        "Diarization dependencies and token are configured",
        str(speech.get("message")),
    )

    gallery = fetch_json(base_url, "/api/faces/gallery", token=token, timeout=20)
    if not isinstance(gallery, dict):
        raise RuntimeError("Gallery response must be a JSON object.")
    people = gallery.get("people", [])
    check(bool(people), f"Face gallery has {len(people)} enrolled person(s)", "Face gallery has no enrolled people")

    diarization = fetch_json(base_url, "/api/speech/diarization-check", token=token)
    if not isinstance(diarization, dict):
        raise RuntimeError("Diarization check response must be a JSON object.")
    check(
        bool(diarization.get("ok")) and bool(diarization.get("pipeline_loaded")),
        "PyAnnote gated model access is verified",
        str(diarization.get("message")),
    )

    meetings = fetch_json(base_url, "/api/meetings", token=token, timeout=20)
    check(isinstance(meetings, list), "Meeting list endpoint is ready", "Meeting list endpoint did not return a list")

    for item in passes:
        print(f"PASS: {item}")

    if failures:
        for item in failures:
            print(f"FAIL: {item}", file=sys.stderr)
        print(f"ConvoLogix beta readiness failed: {len(failures)} issue(s)", file=sys.stderr)
        return 1

    print("ConvoLogix beta readiness passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"Beta readiness failed: could not reach API: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"Beta readiness failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
