"""
git_service.py — Git operations using subprocess.

All Git commands use argument arrays (never shell=True)
for security.
"""

import os
import subprocess
import shutil
from typing import Optional


def is_git_installed() -> bool:
    """Check if git is available in PATH."""
    return shutil.which("git") is not None


def get_git_status(project_path: str) -> dict:
    """
    Get comprehensive Git status for a project directory.
    """
    resolved = os.path.abspath(project_path)
    git_dir = os.path.join(resolved, ".git")
    is_repo = os.path.isdir(git_dir)

    result = {
        "git_installed": is_git_installed(),
        "is_repo": is_repo,
        "branch": None,
        "has_remote": False,
        "remote_url": None,
        "has_commits": False,
        "uncommitted_changes": False,
        "tracked_files": 0,
        "untracked_files": [],
        "staged_files": [],
        "modified_files": [],
    }

    if not result["git_installed"] or not is_repo:
        return result

    # Get current branch
    try:
        branch = _run_git(resolved, ["rev-parse", "--abbrev-ref", "HEAD"])
        result["branch"] = branch.strip()
    except subprocess.CalledProcessError:
        result["branch"] = "main"

    # Check for remote
    try:
        remote = _run_git(resolved, ["remote", "-v"])
        if remote.strip():
            result["has_remote"] = True
            # Get first remote URL
            first_line = remote.strip().split("\n")[0]
            parts = first_line.split()
            if len(parts) >= 2:
                result["remote_url"] = parts[1]
    except subprocess.CalledProcessError:
        pass

    # Check for commits
    try:
        _run_git(resolved, ["rev-parse", "HEAD"])
        result["has_commits"] = True
    except subprocess.CalledProcessError:
        result["has_commits"] = False

    # Get status
    try:
        status_output = _run_git(resolved, ["status", "--porcelain"])
        lines = [l for l in status_output.split("\n") if l.strip()]

        for line in lines:
            if len(line) < 3:
                continue
            index_status = line[0]
            work_status = line[1]
            filepath = line[3:]

            if index_status == "?" and work_status == "?":
                result["untracked_files"].append(filepath)
            elif index_status in ("A", "M", "D", "R"):
                result["staged_files"].append(filepath)
            if work_status in ("M", "D"):
                result["modified_files"].append(filepath)

        result["uncommitted_changes"] = len(lines) > 0
    except subprocess.CalledProcessError:
        pass

    # Count tracked files
    try:
        ls_output = _run_git(resolved, ["ls-files"])
        tracked = [f for f in ls_output.split("\n") if f.strip()]
        result["tracked_files"] = len(tracked)
    except subprocess.CalledProcessError:
        pass

    return result


def init_repo(project_path: str, branch: str = "main") -> dict:
    """Initialize a new Git repository."""
    resolved = os.path.abspath(project_path)

    if not os.path.isdir(resolved):
        raise ValueError(f"Path does not exist or is not a directory: {resolved}")

    if os.path.isdir(os.path.join(resolved, ".git")):
        raise ValueError("Git repository already initialized")

    if not is_git_installed():
        raise RuntimeError("Git is not installed or not available in PATH")

    # Try `git init -b <branch>` (requires Git >= 2.28)
    try:
        _run_git(resolved, ["init", "-b", branch])
    except subprocess.CalledProcessError:
        # Older Git: init without -b, then rename the default branch
        _run_git(resolved, ["init"])
        try:
            _run_git(resolved, ["symbolic-ref", "HEAD", f"refs/heads/{branch}"])
        except subprocess.CalledProcessError:
            pass  # Non-critical — branch can be renamed later

    return {
        "initialized": True,
        "branch": branch,
        "path": resolved,
    }


def stage_files(project_path: str, files: list[str] | None = None) -> dict:
    """
    Stage files for commit.
    If files is None, stages all files (git add .).
    """
    resolved = os.path.abspath(project_path)

    if files:
        _run_git(resolved, ["add", "--"] + files)
    else:
        _run_git(resolved, ["add", "."])

    # Get the list of staged files
    staged_output = _run_git(resolved, ["diff", "--cached", "--name-only"])
    staged = [f for f in staged_output.split("\n") if f.strip()]

    return {
        "staged_files": staged,
        "count": len(staged),
    }


def get_files_to_commit(project_path: str) -> list[str]:
    """
    Preview which files would be staged if we ran git add .
    Uses git status to list all untracked and modified files.
    """
    resolved = os.path.abspath(project_path)

    try:
        # Get all files that would be added
        output = _run_git(resolved, ["status", "--porcelain"])
        files = []
        for line in output.split("\n"):
            if line.strip():
                # Status is first 2 chars, then space, then path
                filepath = line[3:] if len(line) > 3 else line.strip()
                if filepath:
                    files.append(filepath)
        return files
    except subprocess.CalledProcessError:
        return []


def create_commit(project_path: str, message: str) -> dict:
    """Create a commit with the given message."""
    resolved = os.path.abspath(project_path)

    if not message.strip():
        raise ValueError("Commit message cannot be empty")

    output = _run_git(resolved, ["commit", "-m", message])

    return {
        "committed": True,
        "message": message,
        "output": output.strip(),
    }


def add_remote(project_path: str, url: str, name: str = "origin") -> dict:
    """Add a remote to the repository."""
    resolved = os.path.abspath(project_path)

    # Check if remote already exists
    try:
        existing = _run_git(resolved, ["remote", "get-url", name])
        if existing.strip():
            # Remote exists — update it
            _run_git(resolved, ["remote", "set-url", name, url])
            return {"remote": name, "url": url, "action": "updated"}
    except subprocess.CalledProcessError:
        pass

    _run_git(resolved, ["remote", "add", name, url])
    return {"remote": name, "url": url, "action": "added"}


def push(project_path: str, remote: str = "origin", branch: str = "main") -> dict:
    """Push to the remote repository using stored credentials."""
    from app.services.github_auth import get_token

    resolved = os.path.abspath(project_path)
    token = get_token()

    args = []
    if token:
        # Pass authorization header for GitHub HTTPS push without prompting or saving in local git config
        args = ["-c", f"http.extraHeader=Authorization: Bearer {token}"]

    args += ["push", "-u", remote, branch]
    output = _run_git(resolved, args)

    return {
        "pushed": True,
        "remote": remote,
        "branch": branch,
        "output": output.strip(),
    }


def _run_git(cwd: str, args: list[str], env: Optional[dict] = None) -> str:
    """
    Run a git command safely with argument arrays.
    Returns stdout as string. Falls back to stderr for commands
    like `git push` that write progress to stderr.
    """
    cmd_env = os.environ.copy()
    cmd_env["GIT_TERMINAL_PROMPT"] = "0"
    if env:
        cmd_env.update(env)

    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
        env=cmd_env,
    )
    return result.stdout or result.stderr
