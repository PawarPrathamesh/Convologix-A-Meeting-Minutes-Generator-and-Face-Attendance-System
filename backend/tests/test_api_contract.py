from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient


TEST_DATA_DIR = tempfile.TemporaryDirectory()
os.environ["CONVOLOGIX_DATA_DIR"] = TEST_DATA_DIR.name
os.environ["CONVOLOGIX_AUTH_SECRET_KEY"] = "test-secret-key-for-api-contract"
os.environ["CONVOLOGIX_BOOTSTRAP_ADMIN_EMAIL"] = "admin@example.com"
os.environ["CONVOLOGIX_BOOTSTRAP_ADMIN_PASSWORD"] = "correct-horse-battery-staple"

from app.main import app


class ApiContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        response = self.client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "correct-horse-battery-staple"},
        )
        self.assertEqual(response.status_code, 200)
        self.auth_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_health_includes_face_and_speech_status(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("model", payload)
        self.assertIn("speech", payload)
        self.assertIn("ready_for_transcription", payload["speech"])

    def test_auth_status_and_me_contract(self) -> None:
        response = self.client.get("/api/auth/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["setup_required"], False)

        me_response = self.client.get("/api/auth/me", headers=self.auth_headers)

        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["email"], "admin@example.com")
        self.assertEqual(me_response.json()["role"], "admin")

    def test_protected_endpoints_require_authentication(self) -> None:
        response = self.client.get("/api/faces/gallery")

        self.assertEqual(response.status_code, 401)

    def test_gallery_contract(self) -> None:
        response = self.client.get("/api/faces/gallery", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("people", payload)
        self.assertIn("model", payload)
        self.assertIsInstance(payload["people"], list)

    def test_meetings_contract(self) -> None:
        response = self.client.get("/api/meetings", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_diarization_check_contract(self) -> None:
        response = self.client.get("/api/speech/diarization-check?load_model=false", headers=self.auth_headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("ok", payload)
        self.assertIn("pipeline_loaded", payload)
        self.assertIn("message", payload)

    def test_unknown_meeting_returns_404(self) -> None:
        response = self.client.get("/api/meetings/000000000000", headers=self.auth_headers)

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
