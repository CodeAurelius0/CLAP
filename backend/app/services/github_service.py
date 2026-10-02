"""
github_service.py — GitHub API interactions.

Uses GitHub Device Flow for authentication so users never
paste passwords. Tokens are kept in memory only.
"""

import re
import httpx
from typing import Optional

from app.config import settings

# In-memory token storage (not persisted to disk in v0.1)
_github_token: Optional[str] = None
_github_user: Optional[dict] = None


def get_stored_token() -> Optional[str]:
    return _github_token


def store_token(token: str) -> None:
    global _github_token, _github_user
    _github_token = token
    _github_user = None  # force re-fetch


def clear_token() -> None:
    global _github_token, _github_user
    _github_token = None
    _github_user = None


def start_device_flow() -> dict:
    """
    Initiate GitHub Device Flow authentication.
    Returns the device code, user code, and verification URI.
    """
    if not settings.GITHUB_CLIENT_ID:
        raise ValueError(
            "GitHub Client ID is not configured. "
            "Set the GITHUB_CLIENT_ID environment variable."
        )

    response = httpx.post(
        "https://github.com/login/device/code",
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "scope": "repo user",
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    return {
        "device_code": data["device_code"],
        "user_code": data["user_code"],
        "verification_uri": data["verification_uri"],
        "expires_in": data["expires_in"],
        "interval": data["interval"],
    }


def poll_device_flow(device_code: str) -> dict:
    """
    Poll GitHub for the device flow token.
    Returns {"status": "complete", "token": "..."} or
            {"status": "pending"} or {"status": "error", "message": "..."}.
    """
    if not settings.GITHUB_CLIENT_ID:
        raise ValueError("GitHub Client ID is not configured.")

    response = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if "access_token" in data:
        token = data["access_token"]
        store_token(token)
        return {"status": "complete"}

    error = data.get("error", "unknown_error")
    if error == "authorization_pending":
        return {"status": "pending"}
    elif error == "slow_down":
        return {"status": "pending", "slow_down": True}
    elif error == "expired_token":
        return {"status": "error", "message": "Device code expired. Please restart authentication."}
    else:
        return {"status": "error", "message": data.get("error_description", error)}


def get_authenticated_user() -> dict:
    """Get the authenticated GitHub user's info."""
    global _github_user

    token = get_stored_token()
    if not token:
        raise ValueError("Not authenticated with GitHub")

    if _github_user:
        return _github_user

    response = httpx.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    _github_user = {
        "login": data["login"],
        "name": data.get("name"),
        "avatar_url": data.get("avatar_url"),
    }
    return _github_user


def create_repository(
    name: str,
    description: str = "",
    private: bool = True,
) -> dict:
    """Create a new GitHub repository."""
    token = get_stored_token()
    if not token:
        raise ValueError("Not authenticated with GitHub")

    # Validate repo name
    if not re.match(r"^[a-zA-Z0-9._-]+$", name):
        raise ValueError(
            "Invalid repository name. Use only letters, numbers, hyphens, underscores, and dots."
        )

    response = httpx.post(
        "https://api.github.com/user/repos",
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


def set_token_from_pat(pat: str) -> dict:
    """
    Alternative auth: accept a Personal Access Token directly.
    Validates it by fetching the user profile.
    """
    # Temporarily store
    store_token(pat)

    try:
        user = get_authenticated_user()
        return {"authenticated": True, "user": user}
    except Exception:
        clear_token()
        raise ValueError("Invalid token. Could not authenticate with GitHub.")
