"""
scoring.py — Calculate GitHub Readiness score.

A transparent scoring system that measures how well-prepared
a project is for publishing to GitHub — NOT code quality.
"""


def calculate_readiness_score(analysis: dict) -> dict:
    """
    Calculate a readiness score from 0–100 with a detailed breakdown.

    Expects an analysis dict containing:
        git_status, has_readme, has_gitignore,
        large_files, secrets, structure
    """
    breakdown: list[dict] = []
    total = 0

    # Git initialized — 20 points
    git_initialized = analysis.get("git_status", {}).get("is_repo", False)
    points = 20 if git_initialized else 0
    breakdown.append({
        "label": "Git initialized",
        "points": points,
        "max": 20,
        "passed": git_initialized,
    })
    total += points

    # .gitignore exists — 20 points
    has_gitignore = analysis.get("has_gitignore", False)
    points = 20 if has_gitignore else 0
    breakdown.append({
        "label": ".gitignore exists",
        "points": points,
        "max": 20,
        "passed": has_gitignore,
    })
    total += points

    # README exists — 15 points
    has_readme = analysis.get("has_readme", False)
    points = 15 if has_readme else 0
    breakdown.append({
        "label": "README exists",
        "points": points,
        "max": 15,
        "passed": has_readme,
    })
    total += points

    # No large files — 15 points
    large_files = analysis.get("large_files", [])
    no_large = len(large_files) == 0
    points = 15 if no_large else 0
    breakdown.append({
        "label": "No large files",
        "points": points,
        "max": 15,
        "passed": no_large,
        "detail": None if no_large else f"{len(large_files)} large file(s) detected",
    })
    total += points

    # No obvious secrets — 20 points
    secrets = analysis.get("secrets", [])
    no_secrets = len(secrets) == 0
    points = 20 if no_secrets else 0
    breakdown.append({
        "label": "No obvious secrets",
        "points": points,
        "max": 20,
        "passed": no_secrets,
        "detail": None if no_secrets else f"{len(secrets)} potential secret(s) found",
    })
    total += points

    # Recognized project structure — 10 points
    notable = analysis.get("structure", {}).get("notable", [])
    has_structure = len(notable) >= 2  # At least 2 recognized items
    points = 10 if has_structure else 0
    breakdown.append({
        "label": "Recognized project structure",
        "points": points,
        "max": 10,
        "passed": has_structure,
    })
    total += points

    return {
        "score": total,
        "max_score": 100,
        "breakdown": breakdown,
    }
