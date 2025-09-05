"""
Lightweight loader to bring Streamlit-style secrets into os.environ for CLI scripts.

Usage:
    from tools.secrets_loader import load_local_secrets_to_env
    load_local_secrets_to_env()  # before importing code that reads os.getenv

Looks for .streamlit/secrets.toml in the current working directory or parents.
Does nothing if the file is missing. Does not overwrite existing env vars.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


def _find_secrets_file() -> Path | None:
    """Find .streamlit/secrets.toml in CWD or parent directories."""
    p = Path.cwd()
    for _ in range(6):  # walk up a few levels max
        candidate = p / ".streamlit" / "secrets.toml"
        if candidate.exists():
            return candidate
        p = p.parent
    return None


def _load_toml(path: Path) -> Dict[str, Any]:
    try:
        try:
            import tomllib  # Python 3.11+
            data = tomllib.loads(path.read_text())
        except Exception:
            import tomli  # type: ignore
            data = tomli.loads(path.read_text())
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def _put_env(k: str, v: Any) -> None:
    if v is None:
        return
    k = str(k)
    v = str(v)
    # Do not override existing process env
    if k not in os.environ or os.environ.get(k, "") == "":
        os.environ[k] = v


def load_local_secrets_to_env() -> None:
    """Load secrets.toml (if present) and set values into os.environ.

    Rules:
    - Top-level simple values (str/int/bool/float) are exported as-is by key name.
    - Nested tables/dicts are flattened with UPPERCASE child keys.
      Example: { database = { url = "..." } } -> DATABASE_URL
    - Existing environment variables are not overwritten.
    """
    path = _find_secrets_file()
    if not path:
        return

    data = _load_toml(path)
    if not data:
        return

    for k, v in data.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            _put_env(k, v)
        elif isinstance(v, dict):
            # Flatten one level deep using upper-case child keys
            for kk, vv in v.items():
                _put_env(f"{k}_{str(kk).upper()}", vv)
                # Also export just the child for common patterns
                _put_env(str(kk).upper(), vv)
        # ignore other types (lists, etc.)

