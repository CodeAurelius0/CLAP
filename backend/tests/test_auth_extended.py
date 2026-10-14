"""
test_auth_extended.py — Extended auth tests covering PKCE fix, XSS escaping,
path-safety regression, and OAuth callback edge cases.
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.services import github_auth


class TestPKCECodeExchange(unittest.TestCase):
    """Test that the correct auth flow is chosen based on whether a client_secret is set."""

    def setUp(self):
        github_auth.disconnect()
        self.orig_client_id = settings.GITHUB_CLIENT_ID
        self.orig_client_secret = settings.GITHUB_CLIENT_SECRET

    def tearDown(self):
        github_auth.disconnect()
        settings.GITHUB_CLIENT_ID = self.orig_client_id
        settings.GITHUB_CLIENT_SECRET = self.orig_client_secret

    @patch("httpx.get")
    @patch("httpx.post")
    def test_confidential_client_uses_secret_not_verifier(self, mock_post, mock_get):
        """When client_secret is set, code exchange must use it and NOT send code_verifier."""
        settings.GITHUB_CLIENT_ID = "test_id"
        settings.GITHUB_CLIENT_SECRET = "test_secret"

        # Create a valid session
        result = github_auth.start_oauth_flow()
        state = result["state"]

        # Mock token exchange
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {"access_token": "gho_secret_token"}
        mock_post.return_value = mock_post_resp

        # Mock /user
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "login": "octocat",
            "name": "Octocat",
            "avatar_url": "https://avatars.githubusercontent.com/u/583231",
            "email": "octocat@github.com",
            "html_url": "https://github.com/octocat",
        }
        mock_get.return_value = mock_get_resp

        github_auth.handle_oauth_callback("test_code", state)

        # Verify the POST body
        call_kwargs = mock_post.call_args[1] if mock_post.call_args[1] else {}
        call_data = mock_post.call_args[0][0] if mock_post.call_args[0] else {}
        # Use keyword args
        posted_data = mock_post.call_args.kwargs.get("data") or mock_post.call_args[1].get("data") or {}
        self.assertIn("client_secret", posted_data)
        self.assertNotIn("code_verifier", posted_data)

    @patch("httpx.get")
    @patch("httpx.post")
    def test_public_client_uses_verifier_not_secret(self, mock_post, mock_get):
        """When no client_secret is set, code exchange must use code_verifier."""
        settings.GITHUB_CLIENT_ID = "test_id"
        settings.GITHUB_CLIENT_SECRET = ""

        result = github_auth.start_oauth_flow()
        state = result["state"]

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {"access_token": "gho_public_token"}
        mock_post.return_value = mock_post_resp

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "login": "bob",
            "name": "Bob",
            "avatar_url": "",
            "email": None,
            "html_url": "https://github.com/bob",
        }
        mock_get.return_value = mock_get_resp

        github_auth.handle_oauth_callback("test_code", state)

        posted_data = mock_post.call_args.kwargs.get("data") or {}
        self.assertIn("code_verifier", posted_data)
        self.assertNotIn("client_secret", posted_data)


class TestCallbackXSSEscape(unittest.TestCase):
    """Test that the OAuth callback page properly escapes user-controlled values."""

    def setUp(self):
        self.client = TestClient(app)
        settings.GITHUB_CLIENT_ID = "test_id"
        self.orig_client_id = settings.GITHUB_CLIENT_ID

    def tearDown(self):
        github_auth.disconnect()
        settings.GITHUB_CLIENT_ID = self.orig_client_id

    def test_error_description_is_escaped(self):
        """error_description from GitHub must not appear raw as HTML/JS."""
        xss_payload = "<script>alert('xss')</script>"
        response = self.client.get(
            f"/api/auth/github/callback?error=bad_error&error_description={xss_payload}"
        )
        self.assertEqual(response.status_code, 200)
        # The raw <script> tag must not appear in the response
        self.assertNotIn("<script>alert", response.text)
        # The escaped version should be present
        self.assertIn("&lt;script&gt;", response.text)

    def test_error_state_triggers_error_page(self):
        response = self.client.get("/api/auth/github/callback?error=access_denied")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Authorization Cancelled", response.text)
        self.assertIn("CLAP_AUTH_ERROR", response.text)

    def test_postmessage_uses_specific_origin(self):
        """The postMessage call must use the configured FRONTEND_URL, not '*'."""
        response = self.client.get("/api/auth/github/callback?error=access_denied")
        # Should NOT have the wildcard
        self.assertNotIn("}, '*')", response.text)
        # Should have the configured frontend URL
        from app.config import settings as cfg
        self.assertIn(cfg.FRONTEND_URL, response.text)

    def test_missing_code_returns_400(self):
        response = self.client.get("/api/auth/github/callback?state=somestate")
        self.assertEqual(response.status_code, 400)
        self.assertIn("incomplete", response.text)

    def test_invalid_state_returns_400(self):
        """Valid code + invalid state → token exchange raises ValueError → 400."""
        response = self.client.get(
            "/api/auth/github/callback?code=abc&state=invalid_state_xyz"
        )
        self.assertEqual(response.status_code, 400)


class TestPathSafety(unittest.TestCase):
    """Regression tests for path traversal protection."""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_path_blocked(self):
        response = self.client.post("/api/project/select", json={"path": "/"})
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertIn("not allowed", detail["error"]["message"])

    def test_etc_blocked(self):
        response = self.client.post("/api/project/select", json={"path": "/etc"})
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_path_blocked(self):
        response = self.client.post("/api/project/select", json={
            "path": "/tmp/clap_does_not_exist_abc123"
        })
        self.assertEqual(response.status_code, 400)


class TestOAuthSessionExpiry(unittest.TestCase):
    """Test OAuth state session TTL and cleanup."""

    def setUp(self):
        github_auth.disconnect()
        github_auth._oauth_sessions.clear()
        self.orig_client_id = settings.GITHUB_CLIENT_ID

    def tearDown(self):
        github_auth.disconnect()
        github_auth._oauth_sessions.clear()
        settings.GITHUB_CLIENT_ID = self.orig_client_id

    def test_expired_state_rejected(self):
        """An artificially aged state must be rejected."""
        import time
        settings.GITHUB_CLIENT_ID = "test_id"
        result = github_auth.start_oauth_flow()
        state = result["state"]

        # Age the session beyond TTL
        github_auth._oauth_sessions[state]["created_at"] = (
            time.time() - github_auth._OAUTH_STATE_TTL_SECONDS - 1
        )

        with self.assertRaises(ValueError) as ctx:
            github_auth.handle_oauth_callback("dummy_code", state)
        self.assertIn("Invalid or expired", str(ctx.exception))

    def test_valid_state_present(self):
        settings.GITHUB_CLIENT_ID = "test_id"
        result = github_auth.start_oauth_flow()
        state = result["state"]
        self.assertIn(state, github_auth._oauth_sessions)


class TestGitRoutes(unittest.TestCase):
    """Integration tests for git API routes."""

    def setUp(self):
        self.client = TestClient(app)

    def test_git_status_missing_path_param(self):
        response = self.client.get("/api/git/status")
        # path query param is required
        self.assertIn(response.status_code, (400, 422))

    def test_git_init_invalid_path(self):
        response = self.client.post("/api/git/init", json={"path": "/nonexistent/path/xyz"})
        # ValueError raised for nonexistent path → HTTP 400
        self.assertEqual(response.status_code, 400)

    def test_files_to_commit_nonexistent_path(self):
        response = self.client.post("/api/git/files-to-commit", json={
            "path": "/nonexistent/path/xyz"
        })
        # Should return empty list or error, not crash
        self.assertIn(response.status_code, (200, 500))


if __name__ == "__main__":
    unittest.main()
