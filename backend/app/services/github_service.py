"""
github_service.py — GitHub API interactions.

Handles repository creation and other GitHub API calls.
Authentication is managed by github_auth.py.
Tokens are never exposed to callers.
"""

import re
import httpx

from app.config import settings
from app.services.github_auth import get_token


def create_repository(
    name: str,
    description: str = "",
    private: bool = True,
) -> dict:
    """Create a new GitHub repository."""
    token = get_token()
    if not token:
        raise ValueError("Not authenticated with GitHub")

    # Validate repo name
    if not re.match(r"^[a-zA-Z0-9._-]+$", name):
        raise ValueError(
            "Invalid repository name. Use only letters, numbers, hyphens, underscores, and dots."
        )

    response = httpx.post(
        f"{settings.GITHUB_API_BASE}/user/repos",
        json={
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False,  # We manage the local repo
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )

    if response.status_code == 422:
        error_data = response.json()
        errors = error_data.get("errors", [])
        for err in errors:
            if err.get("message", "").startswith("name already exists"):
                raise ValueError(f"Repository '{name}' already exists on your GitHub account.")
        raise ValueError(error_data.get("message", "Failed to create repository"))

    response.raise_for_status()
    data = response.json()

    return {
        "name": data["name"],
        "full_name": data["full_name"],
        "html_url": data["html_url"],
        "clone_url": data["clone_url"],
        "ssh_url": data["ssh_url"],
        "private": data["private"],
    }
