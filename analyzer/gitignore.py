"""
gitignore.py — Generate and manage .gitignore files.

Provides templates per project type and merges with existing rules.
"""

import os

# Per-language .gitignore templates
TEMPLATES: dict[str, list[str]] = {
    "Python": [
        "# Python",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "build/",
        "dist/",
        "*.egg-info/",
        "*.egg",
        ".venv/",
        "venv/",
        "env/",
        ".env",
        ".env.local",
        "*.whl",
        ".mypy_cache/",
        ".pytest_cache/",
        ".tox/",
        "htmlcov/",
        ".coverage",
        "pip-log.txt",
    ],
    "JavaScript": [
        "# Node / JavaScript",
        "node_modules/",
        "dist/",
        "build/",
        ".env",
        ".env.local",
        ".env.*.local",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        ".eslintcache",
        "coverage/",
    ],
    "TypeScript": [
        "# Node / TypeScript",
        "node_modules/",
        "dist/",
        "build/",
        ".env",
        ".env.local",
        ".env.*.local",
        "npm-debug.log*",
        "yarn-debug.log*",
        "*.tsbuildinfo",
        "coverage/",
    ],
    "Java": [
        "# Java",
        "target/",
        "*.class",
        "*.jar",
        "*.war",
        "*.ear",
        ".gradle/",
        "build/",
        ".settings/",
        ".classpath",
        ".project",
    ],
    "C": [
        "# C / C++",
        "build/",
        "*.o",
        "*.obj",
        "*.exe",
        "*.out",
        "*.a",
        "*.so",
        "*.dll",
        "*.lib",
    ],
    "C++": [
        "# C / C++",
        "build/",
        "*.o",
        "*.obj",
        "*.exe",
        "*.out",
        "*.a",
        "*.so",
        "*.dll",
        "*.lib",
    ],
    "C/C++": [
        "# C / C++",
        "build/",
        "*.o",
        "*.obj",
        "*.exe",
        "*.out",
        "*.a",
        "*.so",
        "*.dll",
        "*.lib",
    ],
    "Rust": [
        "# Rust",
        "target/",
        "Cargo.lock",
    ],
    "Go": [
        "# Go",
        "bin/",
        "*.exe",
        "*.test",
    ],
    "Ruby": [
        "# Ruby",
        "vendor/bundle/",
        ".bundle/",
        "*.gem",
        "coverage/",
        "log/",
        "tmp/",
    ],
    "PHP": [
        "# PHP",
        "vendor/",
        ".env",
        "*.log",
        "storage/",
    ],
}

# Common entries for all projects
COMMON_RULES = [
    "# OS files",
    ".DS_Store",
    "Thumbs.db",
    "*.swp",
    "*.swo",
    "*~",
    "",
    "# IDE",
    ".idea/",
    ".vscode/",
    "*.sublime-project",
    "*.sublime-workspace",
]


def generate_gitignore(languages: list[str], frameworks: list[str] | None = None) -> str:
    """
    Generate a .gitignore string based on detected languages/frameworks.
    """
    lines: list[str] = []
    seen_sections: set[str] = set()

    # Add common rules first
    lines.extend(COMMON_RULES)
    lines.append("")

    # Add language-specific rules
    for lang in languages:
        template = TEMPLATES.get(lang)
        if template and lang not in seen_sections:
            seen_sections.add(lang)
            lines.extend(template)
            lines.append("")

    # React/Next.js/Vue etc. are JS-based — ensure node_modules is included
    if frameworks:
        js_frameworks = {"React", "Next.js", "Vue", "Nuxt", "Angular", "Svelte", "Electron"}
        if any(fw in js_frameworks for fw in frameworks):
            if "JavaScript" not in seen_sections and "TypeScript" not in seen_sections:
                lines.extend(TEMPLATES["JavaScript"])
                lines.append("")

    return "\n".join(lines) + "\n"


def detect_ignorable_dirs(project_path: str, languages: list[str]) -> list[dict]:
    """
    Check whether common generated/dependency directories exist
    that should probably be in .gitignore.
    """
    # Map of directory name -> which languages commonly produce it
    check_dirs = {
        "node_modules": ["JavaScript", "TypeScript"],
        "__pycache__": ["Python"],
        ".venv": ["Python"],
        "venv": ["Python"],
        "dist": ["JavaScript", "TypeScript", "Python"],
        "build": ["JavaScript", "TypeScript", "Java", "C", "C++", "C/C++"],
        "target": ["Java", "Rust"],
        ".next": ["JavaScript", "TypeScript"],
        ".nuxt": ["JavaScript", "TypeScript"],
        "vendor": ["PHP", "Ruby", "Go"],
        "coverage": ["JavaScript", "TypeScript", "Python"],
    }

    found = []
    for dirname, relevant_langs in check_dirs.items():
        full_path = os.path.join(project_path, dirname)
        if os.path.isdir(full_path):
            found.append({
                "name": dirname,
                "relevant_languages": relevant_langs,
                "should_ignore": True,
            })

    return found


def read_existing_gitignore(project_path: str) -> str | None:
    """Read existing .gitignore content, or None if it doesn't exist."""
    gitignore_path = os.path.join(project_path, ".gitignore")
    if not os.path.isfile(gitignore_path):
        return None
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def merge_gitignore(existing: str, generated: str) -> str:
    """
    Merge generated rules into existing .gitignore, avoiding duplicates.
    """
    existing_lines = set(
        line.strip()
        for line in existing.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )

    result_lines = [existing.rstrip()]
    result_lines.append("")
    result_lines.append("# Added by CLAP")

    for line in generated.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped not in existing_lines:
            result_lines.append(stripped)

    return "\n".join(result_lines) + "\n"
