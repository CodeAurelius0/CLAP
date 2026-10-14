"""
test_project_service.py — Tests for project_service.py (path validation, gitignore, analysis).
"""

import os
import tempfile
import shutil
import unittest

from app.services.project_service import validate_project_path, create_gitignore


class TestValidateProjectPath(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_valid_directory(self):
        result = validate_project_path(self.tmpdir)
        self.assertEqual(result["path"], os.path.abspath(self.tmpdir))
        self.assertIsNotNone(result["name"])

    def test_nonexistent_path_raises(self):
        with self.assertRaises(ValueError) as ctx:
            validate_project_path("/tmp/clap_does_not_exist_xyz_123")
        self.assertIn("does not exist", str(ctx.exception))

    def test_file_path_raises(self):
        test_file = os.path.join(self.tmpdir, "file.txt")
        with open(test_file, "w") as f:
            f.write("hi")
        with self.assertRaises(ValueError) as ctx:
            validate_project_path(test_file)
        self.assertIn("not a directory", str(ctx.exception))

    def test_blocked_root_path_raises(self):
        with self.assertRaises(ValueError) as ctx:
            validate_project_path("/")
        self.assertIn("not allowed", str(ctx.exception))

    def test_blocked_etc_path_raises(self):
        with self.assertRaises(ValueError) as ctx:
            validate_project_path("/etc")
        self.assertIn("not allowed", str(ctx.exception))

    def test_tilde_expansion(self):
        # ~ should be expanded without error (home dir should be valid)
        result = validate_project_path("~")
        self.assertEqual(result["path"], os.path.expanduser("~"))


class TestCreateGitignore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_gitignore(self):
        result = create_gitignore(self.tmpdir, ["Python"])
        self.assertTrue(os.path.isfile(result["path"]))
        self.assertIn("__pycache__", result["content"])

    def test_create_fails_if_exists(self):
        create_gitignore(self.tmpdir, ["Python"])
        with self.assertRaises(ValueError) as ctx:
            create_gitignore(self.tmpdir, ["Python"], mode="create")
        self.assertIn("already exists", str(ctx.exception))

    def test_replace_mode(self):
        create_gitignore(self.tmpdir, ["Python"])
        result = create_gitignore(self.tmpdir, ["JavaScript"], mode="replace")
        self.assertIn("node_modules", result["content"])

    def test_merge_mode(self):
        create_gitignore(self.tmpdir, ["Python"])
        result = create_gitignore(self.tmpdir, ["JavaScript"], mode="merge")
        self.assertIn("__pycache__", result["content"])
        self.assertIn("node_modules", result["content"])

    def test_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            create_gitignore(self.tmpdir, ["python"], mode="invalid")
