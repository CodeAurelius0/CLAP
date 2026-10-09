"""
test_auth.py — Comprehensive tests for CLAP GitHub authentication & credential store.
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.services import credential_store
from app.services import github_auth


class TestCredentialStore(unittest.TestCase):
    """Test OS keyring and in-memory credential storage."""

    def setUp(self):
        credential_store.delete_credential("test_token")

    def tearDown(self):
        credential_store.delete_credential("test_token")

    def test_save_get_delete_credential(self):
        self.assertFalse(credential_store.has_credential("test_token"))
        self.assertIsNone(credential_store.get_credential("test_token"))

        credential_store.save_credential("secret_val_xyz", "test_token")
        self.assertTrue(credential_store.has_credential("test_token"))
        self.assertEqual(credential_store.get_credential("test_token"), "secret_val_xyz")

        credential_store.delete_credential("test_token")
        self.assertFalse(credential_store.has_credential("test_token"))
        self.assertIsNone(credential_store.get_credential("test_token"))

    def test_memory_fallback(self):
        # Force memory store path
        original_avail = credential_store._keyring_available
        try:
            credential_store._keyring_available = False
            credential_store.save_credential("mem_val", "test_mem")
            self.assertEqual(credential_store.get_credential("test_mem"), "mem_val")
            self.assertTrue(credential_store.has_credential("test_mem"))
            credential_store.delete_credential("test_mem")
            self.assertIsNone(credential_store.get_credential("test_mem"))
        finally:
            credential_store._keyring_available = original_avail


class TestGitHubAuthService(unittest.TestCase):
    """Test GitHub auth orchestration and OAuth/PKCE logic."""

    def setUp(self):
        github_auth.disconnect()
        self.orig_client_id = settings.GITHUB_CLIENT_ID

    def tearDown(self):
        github_auth.disconnect()
        settings.GITHUB_CLIENT_ID = self.orig_client_id

    def test_auth_status_unauthenticated(self):
        status = github_auth.get_auth_status()
        self.assertFalse(status["authenticated"])
        self.assertIsNone(status["provider"])
        self.assertIsNone(status["username"])
        self.assertIsNone(status["user"])

    def test_start_oauth_missing_client_id(self):
        settings.GITHUB_CLIENT_ID = ""
        with self.assertRaises(ValueError) as ctx:
            github_auth.start_oauth_flow()
        self.assertIn("GitHub Client ID is not configured", str(ctx.exception))

    def test_start_oauth_flow_success(self):
        settings.GITHUB_CLIENT_ID = "test_client_id_123"
        result = github_auth.start_oauth_flow()
        self.assertIn("auth_url", result)
        self.assertIn("state", result)
        auth_url = result["auth_url"]
        self.assertIn("client_id=test_client_id_123", auth_url)
        self.assertIn("code_challenge=", auth_url)
        self.assertIn("code_challenge_method=S256", auth_url)
        self.assertIn("state=", auth_url)
        self.assertIn("scope=repo+read%3Auser+user%3Aemail", auth_url)

    def test_handle_oauth_callback_invalid_state(self):
        with self.assertRaises(ValueError) as ctx:
            github_auth.handle_oauth_callback("dummy_code", "invalid_state_123")
        self.assertIn("Invalid or expired OAuth state", str(ctx.exception))

    @patch("httpx.get")
    def test_validate_and_store_pat_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "login": "octocat",
            "name": "The Octocat",
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "email": "octocat@github.com",
            "html_url": "https://github.com/octocat",
        }
        mock_get.return_value = mock_response

        res = github_auth.validate_and_store_pat("ghp_validtoken123")
        self.assertTrue(res["authenticated"])
        self.assertEqual(res["user"]["login"], "octocat")
        self.assertEqual(github_auth.get_token(), "ghp_validtoken123")

        # Status check
        status = github_auth.get_auth_status()
        self.assertTrue(status["authenticated"])
        self.assertEqual(status["username"], "octocat")

    @patch("httpx.get")
    def test_validate_and_store_pat_invalid(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            github_auth.validate_and_store_pat("ghp_invalidtoken")
        self.assertIn("Could not authenticate with this token", str(ctx.exception))
        self.assertIsNone(github_auth.get_token())


class TestAuthRoutes(unittest.TestCase):
    """Test FastAPI authentication endpoints."""

    def setUp(self):
        self.client = TestClient(app)
        github_auth.disconnect()
        self.orig_client_id = settings.GITHUB_CLIENT_ID

    def tearDown(self):
        github_auth.disconnect()
        settings.GITHUB_CLIENT_ID = self.orig_client_id

    def test_get_status_unauthenticated(self):
        response = self.client.get("/api/auth/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["data"]["authenticated"])

    def test_get_user_unauthenticated_returns_401(self):
        response = self.client.get("/api/auth/user")
        self.assertEqual(response.status_code, 401)

    def test_start_oauth_endpoint_json(self):
        settings.GITHUB_CLIENT_ID = "test_id"
        response = self.client.get("/api/auth/github/start?json=true")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("auth_url", data["data"])

    def test_callback_cancelled_by_user(self):
        response = self.client.get("/api/auth/github/callback?error=access_denied")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Authorization Cancelled", response.text)
        self.assertIn("CLAP_AUTH_ERROR", response.text)

    def test_disconnect_endpoint(self):
        response = self.client.post("/api/auth/disconnect")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["data"]["authenticated"])


if __name__ == "__main__":
    unittest.main()
