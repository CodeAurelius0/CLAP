"""
analysis.py — Routes for project analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.project_service import analyse_project, create_gitignore

router = APIRouter()


class AnalyseRequest(BaseModel):
    path: str


class GitignoreRequest(BaseModel):
    path: str
    languages: list[str]
    frameworks: list[str] | None = None
    mode: str = "create"  # "create" | "replace" | "merge"


@router.post("/analyze")
async def analyze_project_route(req: AnalyseRequest):
    """Run full project analysis."""
    try:
        result = analyse_project(req.path)
        return {
            "success": True,
            "data": result,
            "error": None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "data": None,
            "error": {"code": "ANALYSIS_ERROR", "message": str(e)},
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)},
        })


@router.post("/gitignore")
async def create_gitignore_route(req: GitignoreRequest):
    """Generate and write a .gitignore file."""
    try:
        result = create_gitignore(
            req.path,
            req.languages,
            req.frameworks,
            req.mode,
        )
        return {
            "success": True,
            "data": result,
            "error": None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "data": None,
            "error": {"code": "GITIGNORE_ERROR", "message": str(e)},
        })
