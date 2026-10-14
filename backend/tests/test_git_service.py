"""
test_git_service.py — Tests for git_service.py.
"""

import os
import subprocess
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

from app.services import git_service


class TestIsGitInstalled(unittest.TestCase):
    def test_git_is_installed(self):
        # On any dev machine running this, git should be available
        self.assertTrue(git_service.is_git_installed())


class TestGetGitStatus(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_non_git_directory(self):
        result = git_service.get_git_status(self.tmpdir)
        self.assertFalse(result["is_repo"])
        self.assertFalse(result["has_remote"])
        self.assertFalse(result["has_commits"])

    def test_git_repo_no_commits(self):
        subprocess.run(["git", "init", "-b", "main"], cwd=self.tmpdir, check=True,
                       capture_output=True)
        result = git_service.get_git_status(self.tmpdir)
        self.assertTrue(result["is_repo"])
        self.assertFalse(result["has_commits"])
        self.assertFalse(result["has_remote"])

    def test_git_repo_with_commit(self):
        subprocess.run(["git", "init", "-b", "main"], cwd=self.tmpdir, check=True,
                       capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.tmpdir,
                       check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.tmpdir,
                       check=True, capture_output=True)
        # Create a file and commit
        test_file = os.path.join(self.tmpdir, "hello.txt")
        with open(test_file, "w") as f:
            f.write("hello")
        subprocess.run(["git", "add", "."], cwd=self.tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.tmpdir, check=True,
                       capture_output=True)
        result = git_service.get_git_status(self.tmpdir)
        self.assertTrue(result["is_repo"])
        self.assertTrue(result["has_commits"])
        self.assertEqual(result["branch"], "main")
        self.assertGreater(result["tracked_files"], 0)


class TestInitRepo(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_fresh_directory(self):
        result = git_service.init_repo(self.tmpdir)
        self.assertTrue(result["initialized"])
        self.assertEqual(result["branch"], "main")
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, ".git")))

    def test_init_already_initialized_raises(self):
        subprocess.run(["git", "init"], cwd=self.tmpdir, check=True, capture_output=True)
        with self.assertRaises(ValueError) as ctx:
            git_service.init_repo(self.tmpdir)
        self.assertIn("already initialized", str(ctx.exception))

    @patch("app.services.git_service.is_git_installed", return_value=False)
    def test_init_without_git_raises(self, _):
        with self.assertRaises(RuntimeError):
            git_service.init_repo(self.tmpdir)


class TestStageAndCommit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.tmpdir, check=True,
                       capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.tmpdir,
                       check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.tmpdir,
                       check=True, capture_output=True)
        # Create test file
        with open(os.path.join(self.tmpdir, "readme.md"), "w") as f:
            f.write("# Test")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_stage_all(self):
        result = git_service.stage_files(self.tmpdir)
        self.assertIn("staged_files", result)
        self.assertIn("readme.md", result["staged_files"])
        self.assertGreater(result["count"], 0)

    def test_stage_specific_file(self):
        result = git_service.stage_files(self.tmpdir, ["readme.md"])
        self.assertIn("readme.md", result["staged_files"])

    def test_commit_with_message(self):
        git_service.stage_files(self.tmpdir)
        result = git_service.create_commit(self.tmpdir, "Initial commit")
        self.assertTrue(result["committed"])
        self.assertEqual(result["message"], "Initial commit")

    def test_commit_empty_message_raises(self):
        with self.assertRaises(ValueError):
            git_service.create_commit(self.tmpdir, "   ")

    def test_get_files_to_commit(self):
        files = git_service.get_files_to_commit(self.tmpdir)
        self.assertIsInstance(files, list)
        self.assertGreater(len(files), 0)


class TestAddRemote(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.tmpdir, check=True,
                       capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_new_remote(self):
        result = git_service.add_remote(self.tmpdir, "https://github.com/user/repo.git")
        self.assertEqual(result["remote"], "origin")
        self.assertEqual(result["url"], "https://github.com/user/repo.git")
        self.assertEqual(result["action"], "added")

    def test_update_existing_remote(self):
        git_service.add_remote(self.tmpdir, "https://github.com/user/repo1.git")
        result = git_service.add_remote(self.tmpdir, "https://github.com/user/repo2.git")
        self.assertEqual(result["action"], "updated")
        self.assertEqual(result["url"], "https://github.com/user/repo2.git")
