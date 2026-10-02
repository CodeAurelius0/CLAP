# CLAP

**C**ode · **L**aunch · **A**nalyse · **P**ush

A beginner-friendly local tool for analysing projects and publishing them to GitHub with a simple workflow.

---

## Features

- **Project Detection** — Automatically detects project type (Python, Node.js, React, Java, C/C++, Rust)
- **Structure Analysis** — Counts files, directories, source files, tests, and documentation
- **Git Readiness** — Checks Git status, `.gitignore`, and remote configuration
- **Secret Detection** — Warns about `.env` files and obvious credential patterns
- **Large File Detection** — Flags files that may cause problems on GitHub
- **`.gitignore` Generation** — Creates appropriate ignore rules for your project type
- **GitHub Integration** — Authenticate, create repositories, and push — all from one interface
- **Readiness Score** — A transparent score showing how prepared your project is for GitHub

## Architecture

```
┌─────────────┐     HTTP/REST     ┌─────────────┐
│   Frontend   │ ◄──────────────► │   Backend    │
│   (React)    │                  │  (FastAPI)   │
└─────────────┘                  └──────┬──────┘
                                        │
                                ┌───────┴───────┐
                                │   Analyzer     │
                                │   (Python)     │
                                └───────┬───────┘
                                        │
                            ┌───────────┼───────────┐
                            │           │           │
                        Local FS      Git CLI    GitHub API
```

## Tech Stack

| Layer    | Technology           |
|----------|----------------------|
| Frontend | React, Vite, CSS     |
| Backend  | Python, FastAPI      |
| Analyzer | Python (subprocess)  |
| Git      | Git CLI via subprocess |
| GitHub   | GitHub REST API v3   |

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Development

### Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Start the frontend

```bash
cd frontend
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

## Usage

1. Open CLAP in your browser
2. Select a local project directory
3. Review the analysis results
4. Fix any issues (generate `.gitignore`, etc.)
5. Connect your GitHub account
6. Create a repository and push

## Security

- GitHub tokens are never logged or displayed
- All Git operations use subprocess argument arrays (no `shell=True`)
- Paths are validated before any filesystem operation
- No project files are sent to external services
- Users must confirm all destructive operations

## Roadmap

- **v0.2** — Better secret scanning, README generation, commit message suggestions
- **v0.3** — AI architecture analysis, code quality suggestions
- **v0.4** — Branch management, pull requests, issue creation
- **v1.0** — Desktop application, organization support, plugin system

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request for significant changes.

## License

[MIT](LICENSE)
