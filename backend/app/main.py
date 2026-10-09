from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import projects, analysis, git, github, auth


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# CORS — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/project", tags=["project"])
app.include_router(analysis.router, prefix="/api/project", tags=["analysis"])
app.include_router(git.router, prefix="/api/git", tags=["git"])
app.include_router(github.router, prefix="/api/github", tags=["github"])


@app.get("/api/health")
async def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": settings.APP_VERSION,
        },
        "error": None,
    }
