"""
detector.py — Detect the project type and technology stack.

Inspects file extensions and known config files to determine
what language/framework the project uses.
"""

import os
from typing import Optional


# Maps config filenames to (language, framework | None)
CONFIG_INDICATORS = {
    "package.json": ("JavaScript", None),
    "tsconfig.json": ("TypeScript", None),
    "requirements.txt": ("Python", None),
    "pyproject.toml": ("Python", None),
    "Pipfile": ("Python", None),
    "setup.py": ("Python", None),
    "Cargo.toml": ("Rust", None),
    "go.mod": ("Go", None),
    "pom.xml": ("Java", "Maven"),
    "build.gradle": ("Java", "Gradle"),
    "CMakeLists.txt": ("C/C++", "CMake"),
    "Makefile": (None, "Make"),
    "Gemfile": ("Ruby", None),
    "composer.json": ("PHP", None),
}

# Maps file extensions to languages
EXTENSION_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++",
    ".hpp": "C++",
    ".rs": "Rust",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
}

# Keywords in package.json dependencies that reveal frameworks
PACKAGE_JSON_FRAMEWORKS = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "angular": "Angular",
    "svelte": "Svelte",
    "express": "Express",
    "fastify": "Fastify",
    "electron": "Electron",
}


def detect_project_type(project_path: str) -> dict:
    """
    Analyse the project directory and return detection results.

    Returns a dict with:
        languages:  list of detected languages (ordered by file count)
        frameworks: list of detected frameworks
        primary:    best-guess single label like "React" or "Python"
        confidence: "high" | "medium" | "low"
    """
    languages: dict[str, int] = {}   # language -> file count
    frameworks: list[str] = []
    config_files_found: list[str] = []

    top_entries = os.listdir(project_path)

    # Check config files in project root
    for filename, (lang, framework) in CONFIG_INDICATORS.items():
        if filename in top_entries:
            config_files_found.append(filename)
            if lang:
                languages[lang] = languages.get(lang, 0) + 5  # weight config files
            if framework and framework not in frameworks:
                frameworks.append(framework)

    # Check package.json for JS/TS frameworks
    pkg_path = os.path.join(project_path, "package.json")
    if os.path.isfile(pkg_path):
        _detect_package_json_frameworks(pkg_path, frameworks)

    # Walk source files (skip hidden dirs and common non-source dirs)
    skip_dirs = {
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        "dist", "build", "target", ".next", ".nuxt", "vendor",
    }

    for root, dirs, files in os.walk(project_path):
        # Prune directories we don't want to traverse
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            lang = EXTENSION_MAP.get(ext)
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

    # Sort languages by count
    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    lang_names = [name for name, _ in sorted_langs]

    # Determine primary label
    primary = _determine_primary(lang_names, frameworks)
    confidence = _determine_confidence(sorted_langs, config_files_found)

    return {
        "languages": lang_names,
        "frameworks": frameworks,
        "primary": primary,
        "confidence": confidence,
        "config_files": config_files_found,
    }


def _detect_package_json_frameworks(
    pkg_path: str, frameworks: list[str]
) -> None:
    """Read package.json and look for known framework dependencies."""
    import json

    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    all_deps: dict = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        all_deps.update(data.get(key, {}))

    for dep_name, framework_label in PACKAGE_JSON_FRAMEWORKS.items():
        if dep_name in all_deps and framework_label not in frameworks:
            frameworks.append(framework_label)


def _determine_primary(languages: list[str], frameworks: list[str]) -> str:
    """Pick the best single label for the project."""
    # Frameworks are more specific than languages
    priority_frameworks = ["React", "Next.js", "Vue", "Nuxt", "Angular", "Svelte", "Electron"]
    for fw in priority_frameworks:
        if fw in frameworks:
            return fw

    if languages:
        return languages[0]

    return "Generic Project"


def _determine_confidence(
    sorted_langs: list[tuple[str, int]],
    config_files: list[str],
) -> str:
    if config_files and sorted_langs:
        return "high"
    if config_files or sorted_langs:
        return "medium"
    return "low"
