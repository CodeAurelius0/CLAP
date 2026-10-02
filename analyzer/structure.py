"""
structure.py — Analyse the project's file/directory structure.

Counts files, directories, source files, test files, docs, etc.
"""

import os
from typing import Optional


# Directories to skip when walking
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", "target", ".next", ".nuxt", "vendor",
    ".tox", ".mypy_cache", ".pytest_cache", "egg-info",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".java", ".c", ".cpp", ".h", ".hpp", ".rs", ".go",
    ".rb", ".php", ".cs", ".swift", ".kt",
}

TEST_INDICATORS = {"test", "tests", "spec", "specs", "__tests__"}

DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}

CONFIG_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".xml", ".env", ".properties",
}

CONFIG_FILES = {
    "Makefile", "Dockerfile", "docker-compose.yml",
    ".editorconfig", ".prettierrc", ".eslintrc",
    "babel.config.js", "webpack.config.js", "vite.config.js",
}


def analyse_structure(project_path: str) -> dict:
    """
    Walk the project tree and return structural metrics.

    Returns a dict with counts and detected notable directories/files.
    """
    total_files = 0
    total_dirs = 0
    source_files = 0
    test_files = 0
    doc_files = 0
    config_files = 0
    hidden_files = 0

    notable_items: list[dict] = []

    # Check notable top-level items
    _check_notable(project_path, notable_items)

    for root, dirs, files in os.walk(project_path):
        # Prune
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        total_dirs += len(dirs)

        # Detect if we're inside a test directory
        rel_root = os.path.relpath(root, project_path)
        in_test_dir = any(part.lower() in TEST_INDICATORS for part in rel_root.split(os.sep))

        for fname in files:
            total_files += 1
            ext = os.path.splitext(fname)[1].lower()

            if fname.startswith("."):
                hidden_files += 1

            if ext in SOURCE_EXTENSIONS:
                if in_test_dir:
                    test_files += 1
                else:
                    source_files += 1
            elif ext in DOC_EXTENSIONS:
                doc_files += 1
            elif ext in CONFIG_EXTENSIONS or fname in CONFIG_FILES:
                config_files += 1

    return {
        "total_files": total_files,
        "total_dirs": total_dirs,
        "source_files": source_files,
        "test_files": test_files,
        "doc_files": doc_files,
        "config_files": config_files,
        "hidden_files": hidden_files,
        "notable": notable_items,
    }


def _check_notable(project_path: str, notable: list[dict]) -> None:
    """Check for well-known directories and files in the project root."""
    checks = [
        ("src", "dir", "Source directory"),
        ("lib", "dir", "Library directory"),
        ("tests", "dir", "Test directory"),
        ("test", "dir", "Test directory"),
        ("docs", "dir", "Documentation directory"),
        ("README.md", "file", "README"),
        ("README.rst", "file", "README"),
        ("LICENSE", "file", "License file"),
        ("package.json", "file", "Node.js manifest"),
        ("requirements.txt", "file", "Python dependencies"),
        ("pyproject.toml", "file", "Python project config"),
        ("Cargo.toml", "file", "Rust manifest"),
        ("Makefile", "file", "Build file"),
        ("Dockerfile", "file", "Docker config"),
    ]

    for name, kind, label in checks:
        full = os.path.join(project_path, name)
        exists = (os.path.isdir(full) if kind == "dir" else os.path.isfile(full))
        if exists:
            notable.append({"name": name, "type": kind, "label": label})
