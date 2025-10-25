import os
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv


def project_root() -> Path:
    # src/util/env_util.py -> src -> project root
    return Path(__file__).resolve().parents[2]


def load_env(verbose: bool = False) -> Dict[str, Any]:
    """Load .env from project root and current working directory.

    Returns diagnostic info: loaded paths, key presence, base URLs, cwd.
    """
    info: Dict[str, Any] = {}
    cwd = Path.cwd()
    root = project_root()
    root_env = root / ".env"
    cwd_env = cwd / ".env"

    loaded_paths = []
    # Load project root .env first
    if root_env.exists():
        load_dotenv(dotenv_path=str(root_env), override=False)
        loaded_paths.append(str(root_env))
    # Then CWD .env (won't override existing by default)
    if cwd_env.exists() and cwd_env != root_env:
        load_dotenv(dotenv_path=str(cwd_env), override=False)
        loaded_paths.append(str(cwd_env))

    info["cwd"] = str(cwd)
    info["root"] = str(root)
    info["loaded_env_files"] = loaded_paths

    def mask(val: Optional[str]) -> str:
        if not val:
            return "(missing)"
        v = val.strip()
        if len(v) <= 10:
            return v[:2] + "***" + v[-2:]
        return v[:6] + "***" + v[-4:]

    info["OPENAI_API_KEY"] = mask(os.getenv("OPENAI_API_KEY"))
    info["ANTHROPIC_API_KEY"] = mask(os.getenv("ANTHROPIC_API_KEY"))
    info["OPENAI_BASE_URL"] = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
    info["ANTHROPIC_BASE_URL"] = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

    if verbose:
        print("[env] cwd=", info["cwd"])  # noqa: T201
        print("[env] root=", info["root"])  # noqa: T201
        print("[env] loaded .env files:")  # noqa: T201
        for p in loaded_paths:
            print("   -", p)  # noqa: T201
        print("[env] OPENAI_API_KEY:", info["OPENAI_API_KEY"])  # noqa: T201
        print("[env] ANTHROPIC_API_KEY:", info["ANTHROPIC_API_KEY"])  # noqa: T201
        print("[env] OPENAI_BASE_URL:", info["OPENAI_BASE_URL"])  # noqa: T201
        print("[env] ANTHROPIC_BASE_URL:", info["ANTHROPIC_BASE_URL"])  # noqa: T201

    return info

