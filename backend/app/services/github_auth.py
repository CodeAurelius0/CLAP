"""
github_auth.py — GitHub authentication orchestration.

Handles:
  • OAuth Authorization Code Flow with PKCE (browser flow)
  • Device Flow initiation and polling (CLI / native fallback)
  • Personal Access Token (PAT) validation
  • Secure session lifecycle (store / check / clear)

Credentials are stored securely via credential_store.py (Windows Credential Manager /
OS Keyring) and are NEVER exposed to the frontend or written to logs.
"""

import os
import time
import base64
import hashlib
import secrets
import logging
import urllib.parse
from typing import Optional

import httpx

from app.config import settings
from app.services.credential_store import (
    save_credential,
    get_credential,
    delete_credential,
    has_credential,
)

logger = logging.getLogger(__name__)

# Cached user profile (avoids repeated /user calls for the same token)
_cached_user: Optional[dict] = None

# In-memory PKCE / OAuth sessions: {state: {code_verifier, redirect_uri, created_at}}
_oauth_sessions: dict[str, dict] = {}
_OAUTH_STATE_TTL_SECONDS = 600  # 10 minutes


# ------------------------------------------------------------------
# Token helpers
# ------------------------------------------------------------------

def get_token() -> Optional[str]:
    """Return the stored GitHub token, or None."""
    return get_credential("github_token")


def _store_token(token: str) -> None:
    """Store token in the credential store and invalidate cached user."""
    global _cached_user
    save_credential(token, "github_token")
    _cached_user = None


def _clear() -> None:
    """Remove stored credentials and cached state."""
    global _cached_user
    delete_credential("github_token")
    _cached_user = None


def _cleanup_expired_sessions() -> None:
    """Prune expired OAuth state sessions."""
    now = time.time()
    expired = [k for k, v in _oauth_sessions.items() if now - v["created_at"] > _OAUTH_STATE_TTL_SECONDS]
    for k in expired:
        _oauth_sessions.pop(k, None)


# ------------------------------------------------------------------
# OAuth Authorization Code Flow with PKCE (Primary Flow)
# ------------------------------------------------------------------

def start_oauth_flow(redirect_uri: Optional[str] = None) -> dict:
    """
    Initiate the GitHub OAuth Authorization Code flow with PKCE.

    Returns:
        {
            "auth_url": str,
            "state": str
        }
    """
    if not settings.GITHUB_CLIENT_ID:
        raise ValueError(
            "GitHub Client ID is not configured. "
            "Set GITHUB_CLIENT_ID in your environment or backend/.env file."
        )

    _cleanup_expired_sessions()

    # Generate cryptographically secure state and PKCE verifier
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)

    # Compute code_challenge = base64url(sha256(verifier)) without padding
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    callback_url = redirect_uri or f"{settings.BACKEND_URL}/api/auth/github/callback"

    _oauth_sessions[state] = {
        "code_verifier": code_verifier,
        "redirect_uri": callback_url,
        "created_at": time.time(),
    }

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": callback_url,
        "scope": "repo read:user user:email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    auth_url = f"{settings.GITHUB_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    return {
        "auth_url": auth_url,
        "state": state,
    }


def handle_oauth_callback(code: str, state: str) -> dict:
    """
    Exchange authorization code for an access token using PKCE.
    Validates state and code_verifier, saves the token, and returns the user profile.
    """
    _cleanup_expired_sessions()

    session = _oauth_sessions.pop(state, None)
    if not session:
        raise ValueError("Invalid or expired OAuth state parameter. Please try authorizing again.")

    if not settings.GITHUB_CLIENT_ID:
        raise ValueError("GitHub Client ID is not configured.")

    payload = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "code": code,
        "code_verifier": session["code_verifier"],
        "redirect_uri": session["redirect_uri"],
    }
    if settings.GITHUB_CLIENT_SECRET:
        payload["client_secret"] = settings.GITHUB_CLIENT_SECRET

    response = httpx.post(
        settings.GITHUB_ACCESS_TOKEN_URL,
        data=payload,
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if "access_token" in data:
        token = data["access_token"]
        _store_token(token)
        user = fetch_authenticated_user(force=True)
        return {"authenticated": True, "user": user}

    error_desc = data.get("error_description") or data.get("error") or "Unknown OAuth error"
    raise ValueError(f"GitHub authorization failed: {error_desc}")


# ------------------------------------------------------------------
# Device Flow (Native / CLI Fallback)
# ------------------------------------------------------------------

def start_device_flow() -> dict:
    """
    Initiate the GitHub Device Flow.

    Returns {device_code, user_code, verification_uri, expires_in, interval}.
    """
    if not settings.GITHUB_CLIENT_ID:
        raise ValueError(
            "GitHub Client ID is not configured. "
            "Set GITHUB_CLIENT_ID in your environment or backend/.env file."
        )

    response = httpx.post(
        settings.GITHUB_DEVICE_CODE_URL,
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "scope": "repo read:user user:email",
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
    Poll GitHub for device-flow completion.

    Returns one of:
      {"status": "complete"}          — token obtained and stored
      {"status": "pending"}           — user hasn't authorised yet
      {"status": "error", "message":} — unrecoverable error
    """
    if not settings.GITHUB_CLIENT_ID:
        raise ValueError("GitHub Client ID is not configured.")

    response = httpx.post(
        settings.GITHUB_ACCESS_TOKEN_URL,
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
        _store_token(data["access_token"])
        return {"status": "complete"}

    error = data.get("error", "unknown_error")
    if error == "authorization_pending":
        return {"status": "pending"}
    if error == "slow_down":
        return {"status": "pending", "slow_down": True}
    if error == "expired_token":
        return {"status": "error", "message": "Device code expired. Please restart authentication."}

    return {"status": "error", "message": data.get("error_description", error)}


# ------------------------------------------------------------------
# PAT validation
# ------------------------------------------------------------------

def validate_and_store_pat(pat: str) -> dict:
    """
    Validate a Personal Access Token by calling the GitHub /user API.
    If valid, stores it securely in the OS credential store and returns the user profile.
    """
    _store_token(pat)
    try:
        user = fetch_authenticated_user(force=True)
        return {"authenticated": True, "user": user}
    except Exception:
        _clear()
        raise ValueError(
            "Could not authenticate with this token. "
            "Please check that the token is valid, has not expired, and has repository access permissions."
        )


# ------------------------------------------------------------------
# User profile
# ------------------------------------------------------------------

def fetch_authenticated_user(force: bool = False) -> dict:
    """
    Fetch the authenticated user's GitHub profile.
    Results are cached per token.
    """
    global _cached_user

    token = get_token()
    if not token:
        raise ValueError("Not authenticated with GitHub")

    if _cached_user and not force:
        return _cached_user

    try:
        response = httpx.get(
            f"{settings.GITHUB_API_BASE}/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=30,
        )
    except httpx.NetworkError as e:
        raise RuntimeError(f"Network error while connecting to GitHub: {e}")
    except httpx.TimeoutException:
        raise RuntimeError("GitHub API request timed out.")

    if response.status_code == 401:
        # Token expired or revoked
        _clear()
        raise ValueError("GitHub token is no longer valid or has expired. Please reconnect.")

    if response.status_code >= 500:
        raise RuntimeError("GitHub is currently experiencing service issues. Please try again later.")

    response.raise_for_status()
    data = response.json()

    # Fetch primary email if not included in /user response
    email = data.get("email")
    if not email:
        try:
            email_resp = httpx.get(
                f"{settings.GITHUB_API_BASE}/user/emails",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=15,
            )
            if email_resp.status_code == 200:
                emails = email_resp.json()
                primary = next((e for e in emails if e.get("primary")), None)
                if primary:
                    email = primary["email"]
        except Exception:
            pass  # Email is non-critical

    _cached_user = {
        "login": data["login"],
        "name": data.get("name"),
        "avatar_url": data.get("avatar_url"),
        "email": email,
        "html_url": data.get("html_url", f"https://github.com/{data['login']}"),
    }
    return _cached_user


# ------------------------------------------------------------------
# Auth status
# ------------------------------------------------------------------

def get_auth_status() -> dict:
    """
    Check current authentication state.
    Returns {authenticated, provider, username, user}.
    """
    if not has_credential("github_token"):
        return {
            "authenticated": False,
            "provider": None,
            "username": None,
            "user": None,
        }

    try:
        user = fetch_authenticated_user()
        return {
            "authenticated": True,
            "provider": "github",
            "username": user["login"],
            "user": user,
        }
    except Exception:
        # Token stored but invalid/expired — clean up
        _clear()
        return {
            "authenticated": False,
            "provider": None,
            "username": None,
            "user": None,
            "expired": True,
        }


def disconnect() -> None:
    """Disconnect GitHub by removing stored credentials."""
    _clear()
