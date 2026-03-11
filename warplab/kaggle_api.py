from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _load_access_token_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    token = path.read_text().strip()
    if not token:
        return {}
    return {"KAGGLE_API_TOKEN": token}


def _load_legacy_kaggle_json(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}

    values: dict[str, str] = {}
    username = payload.get("username")
    key = payload.get("key")
    if isinstance(username, str) and username.strip():
        values["KAGGLE_USERNAME"] = username.strip()
    if isinstance(key, str) and key.strip():
        values["KAGGLE_KEY"] = key.strip()
    return values


def _merged_kaggle_values(root_dir: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    home = Path.home()

    for source in (
        load_dotenv(root_dir / ".env"),
        _load_access_token_file(home / ".kaggle" / "access_token"),
        _load_legacy_kaggle_json(home / ".kaggle" / "kaggle.json"),
    ):
        values.update(source)

    for key in ("KAGGLE_API_TOKEN", "KAGGLE_USERNAME", "KAGGLE_KEY"):
        value = os.environ.get(key)
        if value:
            values[key] = value
    return values


def kaggle_credentials(root_dir: Path | None = None) -> dict[str, str | None]:
    root_dir = (root_dir or Path.cwd()).resolve()
    resolved = _merged_kaggle_values(root_dir)
    api_token = resolved.get("KAGGLE_API_TOKEN")
    username = resolved.get("KAGGLE_USERNAME")
    key = resolved.get("KAGGLE_KEY")
    return {"api_token": api_token, "username": username, "key": key}


def resolve_kaggle_username(root_dir: Path | None = None) -> str | None:
    root_dir = (root_dir or Path.cwd()).resolve()
    credentials = kaggle_credentials(root_dir)
    if credentials.get("username"):
        return str(credentials["username"])

    if credentials.get("api_token"):
        os.environ["KAGGLE_API_TOKEN"] = str(credentials["api_token"])
    if credentials.get("key"):
        os.environ["KAGGLE_KEY"] = str(credentials["key"])
    if credentials.get("username"):
        os.environ["KAGGLE_USERNAME"] = str(credentials["username"])

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ModuleNotFoundError:
        return None

    try:
        api = KaggleApi()
        api.authenticate()
        username = api.config_values.get("username")
        if username:
            return str(username)
    except Exception:
        return None

    return None


def kaggle_doctor(root_dir: Path | None = None) -> dict[str, Any]:
    credentials = kaggle_credentials(root_dir)
    status: dict[str, Any] = {
        "has_api_token": bool(credentials.get("api_token")),
        "has_username": bool(credentials.get("username")),
        "has_key": bool(credentials.get("key")),
        "authenticated": False,
        "username": credentials.get("username"),
    }

    if not status["has_api_token"] and (not status["has_username"] or not status["has_key"]):
        status["error"] = "Missing KAGGLE_API_TOKEN and missing legacy KAGGLE_USERNAME/KAGGLE_KEY."
        return status

    if credentials.get("api_token"):
        os.environ["KAGGLE_API_TOKEN"] = str(credentials["api_token"])
    if credentials.get("username"):
        os.environ["KAGGLE_USERNAME"] = str(credentials["username"])
    if credentials.get("key"):
        os.environ["KAGGLE_KEY"] = str(credentials["key"])

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ModuleNotFoundError as exc:
        status["error"] = f"Kaggle package not installed: {exc}"
        return status

    try:
        api = KaggleApi()
        api.authenticate()
        resolved_username = api.config_values.get("username") or credentials.get("username")
        status["username"] = resolved_username
        kernels = api.kernels_list(user=resolved_username, page=1, page_size=5) if resolved_username else []
        status["authenticated"] = True
        status["kernel_count_sample"] = len(kernels)
        status["kernel_refs"] = [getattr(kernel, "ref", None) for kernel in kernels]
    except Exception as exc:
        status["error"] = str(exc)

    return status


def format_kaggle_doctor_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2)
