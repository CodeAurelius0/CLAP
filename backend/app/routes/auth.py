"""
auth.py — Routes for GitHub authentication.

Endpoints:
    GET  /api/auth/github/start       — Start GitHub OAuth authorization
    GET  /api/auth/github/callback    — Handle GitHub OAuth redirect
    GET  /api/auth/status             — Check current auth state
    GET  /api/auth/user               — Get authenticated user profile
    POST /api/auth/token              — Authenticate with a PAT
    POST /api/auth/disconnect         — Remove stored credentials
    POST /api/auth/github/start       — Start GitHub Device Flow (fallback)
    POST /api/auth/github/poll        — Poll Device Flow for completion
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import html as _html

from app.config import settings
from app.services.github_auth import (
    get_auth_status,
    start_oauth_flow,
    handle_oauth_callback,
    start_device_flow,
    poll_device_flow,
    validate_and_store_pat,
    fetch_authenticated_user,
    disconnect,
)

router = APIRouter()


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------

class DevicePollRequest(BaseModel):
    device_code: str


class PATRequest(BaseModel):
    token: str


# ------------------------------------------------------------------
# Auth status & profile
# ------------------------------------------------------------------

@router.get("/status")
async def auth_status():
    """Check whether GitHub is currently authenticated."""
    status = get_auth_status()
    return {"success": True, "data": status, "error": None}


@router.get("/user")
async def auth_user():
    """Get the authenticated user's profile."""
    try:
        user = fetch_authenticated_user()
        return {"success": True, "data": user, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=401, detail={
            "success": False,
            "data": None,
            "error": {"code": "NOT_AUTHENTICATED", "message": str(e)},
        })


# ------------------------------------------------------------------
# OAuth Authorization Code Flow with PKCE
# ------------------------------------------------------------------

@router.get("/github/start")
async def start_oauth(
    request: Request,
    redirect_uri: Optional[str] = None,
    json_mode: bool = Query(False, alias="json"),
):
    """
    Start GitHub OAuth authorization flow.
    If json_mode is True, returns JSON with the auth_url.
    Otherwise, redirects the browser directly to GitHub's authorization page.
    """
    try:
        result = start_oauth_flow(redirect_uri)
        auth_url = result["auth_url"]

        # Check if caller wants JSON (e.g. from fetch) or direct redirect
        accept = request.headers.get("accept", "")
        if json_mode or "application/json" in accept:
            return {"success": True, "data": result, "error": None}

        return RedirectResponse(url=auth_url, status_code=302)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_AUTH_CONFIG_ERROR", "message": str(e)},
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_AUTH_ERROR", "message": str(e)},
        })


@router.get("/github/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """
    Handle GitHub OAuth redirect callback.
    Renders an HTML response that communicates with the CLAP frontend window.
    """
    frontend_url = settings.FRONTEND_URL

    # Case 1: GitHub returned an error (e.g. user clicked Cancel / Deny)
    if error:
        is_denied = error == "access_denied"
        title = "Authorization Cancelled" if is_denied else "GitHub Authorization Failed"
        message = (
            "GitHub authorization was cancelled. No changes were made to your account."
            if is_denied
            else (error_description or error)
        )
        return HTMLResponse(
            content=_render_auth_page(
                success=False,
                title=title,
                message=message,
                redirect_url=f"{frontend_url}/?auth_error={'denied' if is_denied else 'failed'}",
                target_origin=frontend_url,
                error_code="denied" if is_denied else "error",
            ),
            status_code=200,
        )

    # Case 2: Missing code or state
    if not code or not state:
        return HTMLResponse(
            content=_render_auth_page(
                success=False,
                title="Invalid Authorization Response",
                message="GitHub authorization response was incomplete. Please try again.",
                redirect_url=f"{frontend_url}/?auth_error=incomplete",
                target_origin=frontend_url,
                error_code="incomplete",
            ),
            status_code=400,
        )

    # Case 3: Exchange code for token
    try:
        result = handle_oauth_callback(code, state)
        user = result.get("user", {})
        username = user.get("login", "User")
        return HTMLResponse(
            content=_render_auth_page(
                success=True,
                title="GitHub Connected",
                message=f"Connected as @{username}. You can return to CLAP now.",
                redirect_url=f"{frontend_url}/?auth=success",
                target_origin=frontend_url,
                username=username,
            ),
            status_code=200,
        )
    except Exception as e:
        return HTMLResponse(
            content=_render_auth_page(
                success=False,
                title="Authorization Failed",
                message=str(e),
                redirect_url=f"{frontend_url}/?auth_error=exchange_failed",
                target_origin=frontend_url,
                error_code="exchange_failed",
            ),
            status_code=400,
        )


def _render_auth_page(
    success: bool,
    title: str,
    message: str,
    redirect_url: str,
    target_origin: str = "*",
    username: str = "",
    error_code: str = "",
) -> str:
    """Helper to render a clean, self-closing callback response page."""
    # HTML-escape dynamic values to prevent reflected XSS
    safe_title = _html.escape(title)
    safe_message = _html.escape(message)
    safe_username = _html.escape(username)
    safe_error_code = _html.escape(error_code)
    # target_origin must be a URL — escape it for JS string context
    safe_target_origin = _html.escape(target_origin, quote=True)

    icon = "✓" if success else "✕"
    icon_color = "#238636" if success else "#da3633"
    msg_type = "CLAP_AUTH_SUCCESS" if success else "CLAP_AUTH_ERROR"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CLAP — {safe_title}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: #0d1117;
      color: #f0f6fc;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }}
    .card {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 36px 40px;
      text-align: center;
      max-width: 420px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }}
    .icon {{
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: rgba(35, 134, 54, 0.15);
      color: {icon_color};
      font-size: 26px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 20px;
      border: 1px solid {icon_color};
    }}
    h1 {{
      font-size: 20px;
      font-weight: 600;
      margin: 0 0 10px;
    }}
    p {{
      color: #8b949e;
      font-size: 14px;
      line-height: 1.5;
      margin: 0 0 24px;
    }}
    .btn {{
      display: inline-block;
      background: #238636;
      color: #ffffff;
      text-decoration: none;
      padding: 10px 24px;
      border-radius: 6px;
      font-weight: 500;
      font-size: 14px;
      transition: background 0.15s ease;
    }}
    .btn:hover {{
      background: #2ea043;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{icon}</div>
    <h1>{safe_title}</h1>
    <p>{safe_message}</p>
    <a href="{redirect_url}" class="btn">Return to CLAP</a>
  </div>
  <script>
    // Post message to opener if opened in a popup window
    if (window.opener) {{
      try {{
        window.opener.postMessage({{
          type: '{msg_type}',
          success: {str(success).lower()},
          username: '{safe_username}',
          errorCode: '{safe_error_code}'
        }}, '{safe_target_origin}');
        setTimeout(function() {{
          window.close();
        }}, 1200);
      }} catch (e) {{}}
    }}
    // Also automatically redirect if window wasn't a popup or close didn't fire
    setTimeout(function() {{
      window.location.href = "{redirect_url}";
    }}, 2000);
  </script>
</body>
</html>"""


# ------------------------------------------------------------------
# Device Flow (Fallback for CLI / headless environments)
# ------------------------------------------------------------------

@router.post("/github/start")
async def start_device_auth():
    """Start GitHub Device Flow authentication."""
    try:
        result = start_device_flow()
        return {"success": True, "data": result, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_AUTH_ERROR", "message": str(e)},
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_AUTH_ERROR", "message": str(e)},
        })


@router.post("/github/poll")
async def poll_device_auth(req: DevicePollRequest):
    """Poll for Device Flow completion."""
    try:
        result = poll_device_flow(req.device_code)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_POLL_ERROR", "message": str(e)},
        })


# ------------------------------------------------------------------
# PAT authentication
# ------------------------------------------------------------------

@router.post("/token")
async def auth_with_pat(req: PATRequest):
    """Authenticate using a Personal Access Token."""
    try:
        result = validate_and_store_pat(req.token)
        return {"success": True, "data": result, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=401, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_TOKEN_INVALID", "message": str(e)},
        })
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_UNAVAILABLE", "message": str(e)},
        })


# ------------------------------------------------------------------
# Disconnect
# ------------------------------------------------------------------

@router.post("/disconnect")
async def auth_disconnect():
    """Remove GitHub authentication credentials."""
    disconnect()
    return {
        "success": True,
        "data": {"authenticated": False},
        "error": None,
    }
