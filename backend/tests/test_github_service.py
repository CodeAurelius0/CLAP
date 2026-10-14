"""
test_github_service.py — Tests for github_service.py (repository creation).
"""

import unittest
from unittest.mock import patch, MagicMock

from app.services import github_service, github_auth


class TestCreateRepository(unittest.TestCase):
    def setUp(self):
        github_auth.disconnect()

    def tearDown(self):
        github_auth.disconnect()

    def test_create_repo_not_authenticated_raises(self):
        with self.assertRaises(ValueError) as ctx:
            github_service.create_repository("my-repo")
        self.assertIn("Not authenticated", str(ctx.exception))

    def test_create_repo_invalid_name_raises(self):
        # Store a fake token
        from app.services.credential_store import save_credential
        save_credential("fake_token", "github_token")
        try:
            with self.assertRaises(ValueError) as ctx:
                github_service.create_repository("invalid name!")
            self.assertIn("Invalid repository name", str(ctx.exception))
        finally:
            github_auth.disconnect()

    @patch("httpx.post")
    def test_create_repo_success(self, mock_post):
        from app.services.credential_store import save_credential
        save_credential("fake_token", "github_token")
        try:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "name": "my-repo",
                "full_name": "octocat/my-repo",
                "html_url": "https://github.com/octocat/my-repo",
                "clone_url": "https://github.com/octocat/my-repo.git",
                "ssh_url": "git@github.com:octocat/my-repo.git",
                "private": True,
            }
            mock_post.return_value = mock_response

            result = github_service.create_repository("my-repo", "A test repo", True)
            self.assertEqual(result["name"], "my-repo")
            self.assertEqual(result["full_name"], "octocat/my-repo")
            self.assertTrue(result["private"])
        finally:
            github_auth.disconnect()

    @patch("httpx.post")
    def test_create_repo_already_exists(self, mock_post):
        from app.services.credential_store import save_credential
        save_credential("fake_token", "github_token")
        try:
            mock_response = MagicMock()
            mock_response.status_code = 422
            mock_response.json.return_value = {
                "message": "Repository creation failed.",
                "errors": [{"message": "name already exists on this account"}],
            }
            mock_post.return_value = mock_response

            with self.assertRaises(ValueError) as ctx:
                github_service.create_repository("existing-repo")
            self.assertIn("already exists", str(ctx.exception))
        finally:
            github_auth.disconnect()


class TestCreateRepoRoute(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)
        github_auth.disconnect()

    def tearDown(self):
        github_auth.disconnect()

    def test_create_repo_unauthenticated_returns_400(self):
        response = self.client.post("/api/github/repository", json={
            "name": "test-repo",
            "description": "",
            "private": True,
        })
        self.assertEqual(response.status_code, 400)

    def test_create_repo_invalid_name_returns_400(self):
        response = self.client.post("/api/github/repository", json={
            "name": "invalid name!",
            "description": "",
            "private": True,
        })
        self.assertEqual(response.status_code, 400)
