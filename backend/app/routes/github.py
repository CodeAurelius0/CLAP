"""
github.py — Routes for GitHub repository management.

Authentication routes have been moved to routes/auth.py.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.github_service import create_repository

router = APIRouter()


class CreateRepoRequest(BaseModel):
    name: str
    description: str = ""
    private: bool = True


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
