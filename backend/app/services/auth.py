from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Settings
from app.schemas import AuthStatusResponse, AuthTokenResponse, UserCreateRequest, UserResponse


ROLE_RANKS = {"viewer": 10, "member": 20, "admin": 30}
PASSWORD_ITERATIONS = 210_000


class AuthenticationError(RuntimeError):
    """Raised when credentials or bearer tokens are invalid."""


class AuthorizationError(RuntimeError):
    """Raised when a user does not have the required role."""


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    display_name: str
    role: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _normal_email(email: str) -> str:
    cleaned = email.strip().lower()
    if "@" not in cleaned or len(cleaned) > 254:
        raise ValueError("Enter a valid email address.")
    return cleaned


def _validated_role(role: str) -> str:
    cleaned = role.strip().lower()
    if cleaned not in ROLE_RANKS:
        raise ValueError("Role must be one of: viewer, member, admin.")
    return cleaned


def _user_response(record: dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=record["id"],
        email=record["email"],
        display_name=record["display_name"],
        role=record["role"],
        created_at=record.get("created_at"),
    )


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._bootstrap_admin()

    def status(self) -> AuthStatusResponse:
        users = self._read_users()
        return AuthStatusResponse(
            enabled=self.settings.auth_enabled,
            setup_required=self.settings.auth_enabled and not users,
            user_count=len(users),
        )

    def disabled_user(self) -> CurrentUser:
        return CurrentUser(
            id="auth-disabled",
            email="auth-disabled@local",
            display_name="Auth Disabled",
            role="admin",
        )

    def list_users(self) -> list[UserResponse]:
        return [_user_response(record) for record in self._read_users()]

    def setup_first_admin(self, request: UserCreateRequest) -> AuthTokenResponse:
        if self._read_users():
            raise AuthorizationError("Initial setup is already complete.")
        user = self.create_user(
            UserCreateRequest(
                email=request.email,
                password=request.password,
                display_name=request.display_name,
                role="admin",
            )
        )
        token = self.create_access_token(CurrentUser(**user.model_dump(exclude={"created_at"})))
        return AuthTokenResponse(access_token=token, user=user)

    def create_user(self, request: UserCreateRequest) -> UserResponse:
        email = _normal_email(request.email)
        role = _validated_role(request.role)
        if len(request.password) < 10:
            raise ValueError("Password must be at least 10 characters.")

        users = self._read_users()
        if any(record["email"] == email for record in users):
            raise ValueError("A user with this email already exists.")

        display_name = (request.display_name or email.split("@", 1)[0]).strip()[:100] or email
        record = {
            "id": uuid.uuid4().hex,
            "email": email,
            "display_name": display_name,
            "role": role,
            "password_hash": self._hash_password(request.password),
            "created_at": _utc_now(),
        }
        users.append(record)
        self._write_users(users)
        return _user_response(record)

    def authenticate(self, email: str, password: str) -> UserResponse:
        normalized = _normal_email(email)
        for record in self._read_users():
            if record["email"] == normalized and self._verify_password(password, record["password_hash"]):
                return _user_response(record)
        raise AuthenticationError("Invalid email or password.")

    def create_access_token(self, user: CurrentUser | UserResponse) -> str:
        now = int(time.time())
        payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.display_name,
            "role": user.role,
            "iat": now,
            "exp": now + self.settings.auth_token_minutes * 60,
        }
        header = {"alg": "HS256", "typ": "JWT"}
        signing_input = ".".join(
            [
                _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
                _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
            ]
        )
        signature = hmac.new(
            self.settings.auth_secret_key.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        return f"{signing_input}.{_b64url_encode(signature)}"

    def verify_access_token(self, token: str) -> CurrentUser:
        try:
            header_value, payload_value, signature_value = token.split(".", 2)
            signing_input = f"{header_value}.{payload_value}"
            expected_signature = hmac.new(
                self.settings.auth_secret_key.encode("utf-8"),
                signing_input.encode("ascii"),
                hashlib.sha256,
            ).digest()
            actual_signature = _b64url_decode(signature_value)
            if not hmac.compare_digest(expected_signature, actual_signature):
                raise AuthenticationError("Invalid bearer token.")
            payload = json.loads(_b64url_decode(payload_value).decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as exc:
            raise AuthenticationError("Invalid bearer token.") from exc

        if int(payload.get("exp", 0)) < int(time.time()):
            raise AuthenticationError("Bearer token has expired.")

        user_id = str(payload.get("sub", ""))
        for record in self._read_users():
            if record["id"] == user_id:
                return CurrentUser(
                    id=record["id"],
                    email=record["email"],
                    display_name=record["display_name"],
                    role=record["role"],
                )
        raise AuthenticationError("Bearer token user no longer exists.")

    def require_role(self, user: CurrentUser, minimum_role: str) -> None:
        required = ROLE_RANKS[_validated_role(minimum_role)]
        actual = ROLE_RANKS.get(user.role, 0)
        if actual < required:
            raise AuthorizationError(f"{minimum_role.title()} access is required.")

    def _bootstrap_admin(self) -> None:
        if not self.settings.auth_enabled or self._read_users():
            return
        email = self.settings.bootstrap_admin_email
        password = self.settings.bootstrap_admin_password
        if not email or not password:
            return
        self.create_user(
            UserCreateRequest(
                email=email,
                password=password,
                display_name=self.settings.bootstrap_admin_name or "ConvoLogix Admin",
                role="admin",
            )
        )

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
        return "pbkdf2_sha256${}${}${}".format(
            PASSWORD_ITERATIONS,
            _b64url_encode(salt),
            _b64url_encode(digest),
        )

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            algorithm, iterations_value, salt_value, digest_value = stored_hash.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                _b64url_decode(salt_value),
                int(iterations_value),
            )
            return hmac.compare_digest(_b64url_encode(digest), digest_value)
        except (ValueError, TypeError):
            return False

    def _read_users(self) -> list[dict[str, Any]]:
        path = self.settings.users_file
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("User store is invalid.")
        return data

    def _write_users(self, users: list[dict[str, Any]]) -> None:
        path = self.settings.users_file
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(f"{path}.tmp")
        temporary.write_text(json.dumps(users, indent=2), encoding="utf-8")
        temporary.replace(path)
