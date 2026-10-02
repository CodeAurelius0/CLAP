"""
analyzer.py — Main analyzer entry point.

Coordinates all sub-modules to produce a complete project analysis.
"""

import os

from analyzer.detector import detect_project_type
from analyzer.structure import analyse_structure
from analyzer.files import detect_large_files, detect_secrets
from analyzer.gitignore import (
    detect_ignorable_dirs,
    read_existing_gitignore,
    generate_gitignore,
)
from analyzer.scoring import calculate_readiness_score


class ProjectAnalyzer:
    """
    Analyses a local project directory for GitHub readiness.
    """

    def __init__(self, project_path: str):
        if not os.path.isdir(project_path):
            raise ValueError(f"Path is not a directory: {project_path}")
        self.project_path = os.path.abspath(project_path)

    def run_full_analysis(self) -> dict:
        """
        Run all analysis modules and return a combined result.
        """
        # Detect project type
        detection = detect_project_type(self.project_path)

        # Analyse structure
        structure = analyse_structure(self.project_path)

        # Detect large files
        large_files = detect_large_files(self.project_path)

        # Detect secrets
        secrets = detect_secrets(self.project_path)

        # Check for README
        has_readme = self._check_readme()

        # Check for .gitignore
        has_gitignore = os.path.isfile(
            os.path.join(self.project_path, ".gitignore")
        )
        existing_gitignore = read_existing_gitignore(self.project_path)

        # Check for .git
        git_status = self._check_git()

        # Detect ignorable directories
        ignorable_dirs = detect_ignorable_dirs(
            self.project_path, detection["languages"]
        )

        # Generate suggested .gitignore
        suggested_gitignore = generate_gitignore(
            detection["languages"], detection["frameworks"]
        )

        # Combine for scoring
        scoring_input = {
            "git_status": git_status,
            "has_readme": has_readme,
            "has_gitignore": has_gitignore,
            "large_files": large_files,
            "secrets": secrets,
            "structure": structure,
        }
        readiness = calculate_readiness_score(scoring_input)

        return {
            "project_path": self.project_path,
            "detection": detection,
            "structure": structure,
            "large_files": large_files,
            "secrets": secrets,
            "has_readme": has_readme,
            "has_gitignore": has_gitignore,
            "existing_gitignore": existing_gitignore,
            "suggested_gitignore": suggested_gitignore,
            "ignorable_dirs": ignorable_dirs,
            "git_status": git_status,
            "readiness": readiness,
        }

    def _check_readme(self) -> bool:
        """Check if a README file exists (any common extension)."""
        for name in ["README.md", "README.rst", "README.txt", "README"]:
            if os.path.isfile(os.path.join(self.project_path, name)):
                return True
        return False

    def _check_git(self) -> dict:
        """Check basic Git status without using Git commands."""
        git_dir = os.path.join(self.project_path, ".git")
        is_repo = os.path.isdir(git_dir)

        return {
            "is_repo": is_repo,
            "git_dir_exists": is_repo,
        }
