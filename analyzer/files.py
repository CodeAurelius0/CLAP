"""
files.py — Large file detection and basic secret scanning.
"""

import os
import re
from typing import Optional

# Default thresholds
LARGE_FILE_WARNING = 50 * 1024 * 1024   # 50 MB
LARGE_FILE_CRITICAL = 100 * 1024 * 1024  # 100 MB

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", "target", ".next", ".nuxt", "vendor",
}

# Files that commonly contain secrets
SECRET_FILES = {
    ".env", ".env.local", ".env.production", ".env.staging",
    ".env.development", "credentials.json", "service-account.json",
    "secrets.json", "id_rsa", "id_ed25519",
}

# Patterns that suggest secret values in text files
SECRET_PATTERNS = [
    re.compile(r"(?:API_KEY|APIKEY)\s*[=:]\s*.+", re.IGNORECASE),
    re.compile(r"(?:SECRET_KEY|SECRETKEY)\s*[=:]\s*.+", re.IGNORECASE),
    re.compile(r"(?:PASSWORD|PASSWD)\s*[=:]\s*.+", re.IGNORECASE),
    re.compile(r"(?:ACCESS_TOKEN|AUTH_TOKEN|TOKEN)\s*[=:]\s*.+", re.IGNORECASE),
    re.compile(r"(?:PRIVATE_KEY)\s*[=:]\s*.+", re.IGNORECASE),
    re.compile(r"(?:DATABASE_URL|DB_PASSWORD)\s*[=:]\s*.+", re.IGNORECASE),
    re.compile(r"(?:AWS_SECRET|AWS_ACCESS)\s*[=:]\s*.+", re.IGNORECASE),
]

# File extensions we'll scan for secrets (text-like files only)
SCANNABLE_EXTENSIONS = {
    ".env", ".txt", ".cfg", ".ini", ".conf", ".yaml", ".yml",
    ".json", ".toml", ".properties", ".sh", ".bat", ".ps1",
    ".py", ".js", ".ts", ".rb", ".php", ".java",
}


def detect_large_files(
    project_path: str,
    warning_bytes: int = LARGE_FILE_WARNING,
    critical_bytes: int = LARGE_FILE_CRITICAL,
) -> list[dict]:
    """
    Walk the project and find files exceeding the warning threshold.

    Returns a list of dicts with: path (relative), size_bytes, level ("warning" | "critical").
    """
    large_files = []

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for fname in files:
            full = os.path.join(root, fname)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue

            if size >= warning_bytes:
                level = "critical" if size >= critical_bytes else "warning"
                large_files.append({
                    "path": os.path.relpath(full, project_path),
                    "size_bytes": size,
                    "size_display": _format_size(size),
                    "level": level,
                })

    # Sort largest first
    large_files.sort(key=lambda x: x["size_bytes"], reverse=True)
    return large_files


def detect_secrets(project_path: str) -> list[dict]:
    """
    Basic secret detection: check for known secret files and scan
    small text files for obvious secret patterns.

    Returns a list of dicts with: path, type ("file" | "pattern"), detail.
    """
    findings: list[dict] = []

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, project_path)

            # Check filename
            if fname.lower() in SECRET_FILES:
                findings.append({
                    "path": rel,
                    "type": "file",
                    "detail": f"{fname} may contain credentials",
                })
                continue

            # For small text files, scan for patterns
            ext = os.path.splitext(fname)[1].lower()
            if ext in SCANNABLE_EXTENSIONS or fname.startswith(".env"):
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue

                # Only scan files under 1 MB
                if size > 1 * 1024 * 1024:
                    continue

                _scan_file_for_secrets(full, rel, findings)

    return findings


def _scan_file_for_secrets(
    filepath: str, rel_path: str, findings: list[dict]
) -> None:
    """Scan a single text file for obvious secret patterns."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                for pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        findings.append({
                            "path": rel_path,
                            "type": "pattern",
                            "detail": f"Possible secret at line {line_num}",
                        })
                        # One finding per file is enough for v0.1
                        return
    except OSError:
        pass


def _format_size(size_bytes: int) -> str:
    """Format byte count as human-readable string."""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024**3):.1f} GB"
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024**2):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"
