"""
git.py — Routes for Git operations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.git_service import (
    get_git_status,
    init_repo,
    stage_files,
    create_commit,
    add_remote,
    push,
    get_files_to_commit,
)

router = APIRouter()


class ProjectPathRequest(BaseModel):
    path: str


class InitRequest(BaseModel):
    path: str
    branch: str = "main"


class StageRequest(BaseModel):
    path: str
    files: Optional[list[str]] = None


class CommitRequest(BaseModel):
    path: str
    message: str


class RemoteRequest(BaseModel):
    path: str
    url: str
    name: str = "origin"


class PushRequest(BaseModel):
    path: str
    remote: str = "origin"
    branch: str = "main"


@router.get("/status")
async def git_status_route(path: str):
    """Get Git status for a project."""
    try:
        result = get_git_status(path)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_STATUS_ERROR", "message": str(e)},
        })


@router.post("/init")
async def git_init_route(req: InitRequest):
    """Initialize a new Git repository."""
    try:
        result = init_repo(req.path, req.branch)
        return {"success": True, "data": result, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_INIT_ERROR", "message": str(e)},
        })
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_NOT_FOUND", "message": str(e)},
        })


@router.post("/stage")
async def git_stage_route(req: StageRequest):
    """Stage files for commit."""
    try:
        result = stage_files(req.path, req.files)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_STAGE_ERROR", "message": str(e)},
        })


@router.post("/files-to-commit")
async def files_to_commit_route(req: ProjectPathRequest):
    """Preview files that would be committed."""
    try:
        files = get_files_to_commit(req.path)
        return {"success": True, "data": {"files": files, "count": len(files)}, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_FILES_ERROR", "message": str(e)},
        })


@router.post("/commit")
async def git_commit_route(req: CommitRequest):
    """Create a commit."""
    try:
        result = create_commit(req.path, req.message)
        return {"success": True, "data": result, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_COMMIT_ERROR", "message": str(e)},
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_COMMIT_ERROR", "message": str(e)},
        })


@router.post("/remote")
async def git_remote_route(req: RemoteRequest):
    """Add or update a remote."""
    try:
        result = add_remote(req.path, req.url, req.name)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_REMOTE_ERROR", "message": str(e)},
        })


@router.post("/push")
async def git_push_route(req: PushRequest):
    """Push to remote."""
    try:
        result = push(req.path, req.remote, req.branch)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        msg = str(e)
        # Provide user-friendly error messages
        if "authentication" in msg.lower() or "permission" in msg.lower():
            user_msg = "Git could not authenticate with GitHub. Check your GitHub connection and try again."
        elif "rejected" in msg.lower():
            user_msg = "Push was rejected. The remote repository may have conflicting changes."
        else:
            user_msg = f"Push failed: {msg}"

        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "GIT_PUSH_ERROR", "message": user_msg},
        })
