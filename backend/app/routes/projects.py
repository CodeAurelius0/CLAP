"""
projects.py — Routes for project selection and validation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.project_service import validate_project_path

router = APIRouter()


class SelectProjectRequest(BaseModel):
    path: str


@router.post("/select")
async def select_project(req: SelectProjectRequest):
    """Validate and select a project directory."""
    try:
        project = validate_project_path(req.path)
        return {
            "success": True,
            "data": project,
            "error": None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "data": None,
            "error": {"code": "INVALID_PATH", "message": str(e)},
        })
