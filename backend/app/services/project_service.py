"""
project_service.py — Business logic for project operations.
"""

import os
import sys

# Add the CLAP root so the `analyzer` package is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from analyzer import ProjectAnalyzer
from analyzer.gitignore import generate_gitignore, merge_gitignore, read_existing_gitignore


_BLOCKED_PATHS = {
    "/", "/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64", "/boot",
    "/sys", "/proc", "/dev", "/root",
}


def validate_project_path(path: str) -> dict:
    """
    Validate that the given path exists, is a directory, and is not a
    restricted system path.
    Returns project info or raises ValueError.
    """
    # Normalise and resolve the path
    resolved = os.path.abspath(os.path.expanduser(path))

    if resolved in _BLOCKED_PATHS:
        raise ValueError(f"Access to this path is not allowed: {resolved}")

    if not os.path.exists(resolved):
        raise ValueError(f"Path does not exist: {resolved}")

    if not os.path.isdir(resolved):
        raise ValueError(f"Path is not a directory: {resolved}")

    project_name = os.path.basename(resolved)

    return {
        "path": resolved,
        "name": project_name,
    }


def analyse_project(path: str) -> dict:
    """Run full project analysis."""
    resolved = os.path.abspath(os.path.expanduser(path))
    analyzer = ProjectAnalyzer(resolved)
    return analyzer.run_full_analysis()


def create_gitignore(path: str, languages: list[str], frameworks: list[str] | None = None, mode: str = "create") -> dict:
    """
    Generate and write a .gitignore file.
    
    mode: "create" — write new, fail if exists
          "replace" — overwrite existing
          "merge" — merge with existing
    """
    resolved = os.path.abspath(os.path.expanduser(path))
    gitignore_path = os.path.join(resolved, ".gitignore")
    existing = read_existing_gitignore(resolved)

    generated = generate_gitignore(languages, frameworks)

    if mode == "create":
        if existing is not None:
            raise ValueError(".gitignore already exists. Use 'replace' or 'merge' mode.")
        content = generated
    elif mode == "replace":
        content = generated
    elif mode == "merge":
        if existing is None:
            content = generated
        else:
            content = merge_gitignore(existing, generated)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    with open(gitignore_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    return {
        "path": gitignore_path,
        "mode": mode,
        "content": content,
    }
