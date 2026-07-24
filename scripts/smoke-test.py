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
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise RuntimeError(f"{path} returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{path} returned HTTP {exc.code}: {detail}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def login_for_checks(base_url: str) -> tuple[str | None, dict]:
    status = fetch_json(base_url, "/api/auth/status")
    require(isinstance(status, dict), "Auth status response must be a JSON object.")
    if not status.get("enabled"):
        return None, status

    email = os.getenv("CONVOLOGIX_SMOKE_EMAIL") or os.getenv("CONVOLOGIX_BOOTSTRAP_ADMIN_EMAIL")
    password = os.getenv("CONVOLOGIX_SMOKE_PASSWORD") or os.getenv("CONVOLOGIX_BOOTSTRAP_ADMIN_PASSWORD")
    if status.get("setup_required"):
        if os.getenv("CONVOLOGIX_SMOKE_CREATE_ADMIN", "").strip().lower() not in {"1", "true", "yes", "on"}:
            return None, status
        if not email or not password:
            raise RuntimeError(
                "Set CONVOLOGIX_SMOKE_EMAIL and CONVOLOGIX_SMOKE_PASSWORD to create the first admin."
            )
        token_response = fetch_json(
            base_url,
            "/api/auth/setup",
            method="POST",
            payload={
                "email": email,
                "password": password,
                "display_name": os.getenv("CONVOLOGIX_SMOKE_NAME", "ConvoLogix Smoke Admin"),
                "role": "admin",
            },
        )
        require(isinstance(token_response, dict), "Setup response must be a JSON object.")
        token = token_response.get("access_token")
        require(isinstance(token, str) and bool(token), "Setup response must include access_token.")
        return token, {**status, "setup_required": False, "user_count": 1}

    if not email or not password:
        raise RuntimeError(
            "Auth is enabled. Set CONVOLOGIX_SMOKE_EMAIL and CONVOLOGIX_SMOKE_PASSWORD for protected checks."
        )

    token_response = fetch_json(
        base_url,
        "/api/auth/login",
        method="POST",
        payload={"email": email, "password": password},
    )
    require(isinstance(token_response, dict), "Login response must be a JSON object.")
    token = token_response.get("access_token")
    require(isinstance(token, str) and bool(token), "Login response must include access_token.")
    return token, status


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    checks: list[str] = []

    health = fetch_json(base_url, "/api/health")
    require(isinstance(health, dict), "Health response must be a JSON object.")
    require(health.get("status") == "ok", "Health status must be ok.")
    require("model" in health, "Health response must include face model status.")
    require("speech" in health, "Health response must include speech pipeline status.")
    checks.append("health")

    token, auth_status = login_for_checks(base_url)
    checks.append("auth-status")
    if auth_status.get("setup_required"):
        print("ConvoLogix smoke checks passed:", ", ".join(checks))
        print("Initial admin setup is required before protected endpoint checks can run.")
        return 0

    gallery = fetch_json(base_url, "/api/faces/gallery", token=token)
    require(isinstance(gallery, dict), "Gallery response must be a JSON object.")
    require("people" in gallery, "Gallery response must include people.")
    checks.append("faces-gallery")

    meetings = fetch_json(base_url, "/api/meetings", token=token)
    require(isinstance(meetings, list), "Meetings response must be a list.")
    checks.append("meetings-list")

    print("ConvoLogix smoke checks passed:", ", ".join(checks))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"Smoke check failed: could not reach API: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"Smoke check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
