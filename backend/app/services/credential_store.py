"""
credential_store.py — Secure credential storage.

Uses the operating-system keyring so tokens are never written to
plain files, environment variables, or logs.

    Windows  → Credential Manager
    macOS    → Keychain
    Linux    → Secret Service / compatible keyring

Falls back to in-memory-only storage when the OS keyring is
unavailable (e.g. headless CI environments).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Keyring service identifier — every credential is stored under this name
_SERVICE_NAME = "CLAP-v0.1"
_TOKEN_KEY = "github_token"

# In-memory fallback (used when keyring is not available)
_memory_store: dict[str, str] = {}

# Whether we can use the real keyring
_keyring_available: bool = False

try:
    import keyring as _keyring

    # Quick smoke-test: some Linux environments have keyring installed
    # but no working backend.  Probe once so we know early.
    _keyring.get_password(_SERVICE_NAME, "__probe__")
    _keyring_available = True
except Exception:
    _keyring = None  # type: ignore[assignment]
    _keyring_available = False
    logger.info(
        "OS keyring unavailable — credentials will be stored in memory only "
        "and will not persist across restarts."
    )


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def save_credential(value: str, key: str = _TOKEN_KEY) -> None:
    """Securely save a credential."""
    if _keyring_available:
        try:
            _keyring.set_password(_SERVICE_NAME, key, value)
            return
        except Exception:
            logger.warning("Failed to write to OS keyring; falling back to memory.")
    _memory_store[key] = value


def get_credential(key: str = _TOKEN_KEY) -> Optional[str]:
    """Retrieve a stored credential.  Returns None when absent."""
    if _keyring_available:
        try:
            value = _keyring.get_password(_SERVICE_NAME, key)
            if value is not None:
                return value
        except Exception:
            logger.warning("Failed to read from OS keyring; falling back to memory.")
    return _memory_store.get(key)


def delete_credential(key: str = _TOKEN_KEY) -> None:
    """Remove a stored credential from both keyring and memory."""
    _memory_store.pop(key, None)
    if _keyring_available:
        try:
            _keyring.delete_password(_SERVICE_NAME, key)
        except Exception:
            # Credential may not exist — that's fine
            pass


def has_credential(key: str = _TOKEN_KEY) -> bool:
    """Check whether a credential is stored."""
    return get_credential(key) is not None
