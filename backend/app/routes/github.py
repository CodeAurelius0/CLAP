"""
github.py — Routes for GitHub authentication and repository management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.github_service import (
    start_device_flow,
    poll_device_flow,
    get_authenticated_user,
    create_repository,
    set_token_from_pat,
    get_stored_token,
    clear_token,
)

router = APIRouter()


class DevicePollRequest(BaseModel):
    device_code: str


class PATRequest(BaseModel):
    token: str


class CreateRepoRequest(BaseModel):
    name: str
    description: str = ""
    private: bool = True


@router.get("/auth/status")
async def auth_status():
    """Check if GitHub is authenticated."""
    token = get_stored_token()
    if not token:
        return {
            "success": True,
            "data": {"authenticated": False},
            "error": None,
        }

    try:
        user = get_authenticated_user()
        return {
            "success": True,
            "data": {"authenticated": True, "user": user},
            "error": None,
        }
    except Exception:
        return {
            "success": True,
            "data": {"authenticated": False},
            "error": None,
        }


@router.post("/auth/device")
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


@router.post("/auth/device/poll")
async def poll_device_auth(req: DevicePollRequest):
    """Poll for device flow completion."""
    try:
        result = poll_device_flow(req.device_code)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_POLL_ERROR", "message": str(e)},
        })


@router.post("/auth/token")
async def auth_with_pat(req: PATRequest):
    """Authenticate using a Personal Access Token."""
    try:
        result = set_token_from_pat(req.token)
        return {"success": True, "data": result, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=401, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITHUB_TOKEN_INVALID", "message": str(e)},
        })


@router.post("/auth/logout")
async def logout():
    """Clear GitHub authentication."""
    clear_token()
    return {
        "success": True,
        "data": {"authenticated": False},
        "error": None,
    }


@router.get("/user")
async def get_user():
    """Get the authenticated GitHub user."""
    try:
        user = get_authenticated_user()
        return {"success": True, "data": user, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=401, detail={
            "success": False,
            "data": None,
            "error": {"code": "NOT_AUTHENTICATED", "message": str(e)},
        })


@router.post("/repository")
async def create_repo_route(req: CreateRepoRequest):
    """Create a new GitHub repository."""
    try:
        result = create_repository(req.name, req.description, req.private)
        return {"success": True, "data": result, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "data": None,
            "error": {"code": "REPO_CREATE_ERROR", "message": str(e)},
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "REPO_CREATE_ERROR", "message": str(e)},
        })
