import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "CLAP"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # GitHub OAuth — Device Flow
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_API_BASE: str = "https://api.github.com"
    GITHUB_DEVICE_CODE_URL: str = "https://github.com/login/device/code"
    GITHUB_ACCESS_TOKEN_URL: str = "https://github.com/login/oauth/access_token"

    # Large file thresholds (bytes)
    LARGE_FILE_WARNING_BYTES: int = 50 * 1024 * 1024   # 50 MB
    LARGE_FILE_CRITICAL_BYTES: int = 100 * 1024 * 1024  # 100 MB

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
