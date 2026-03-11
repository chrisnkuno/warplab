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


def kaggle_credentials(root_dir: Path | None = None) -> dict[str, str | None]:
    root_dir = (root_dir or Path.cwd()).resolve()
    dotenv_values = load_dotenv(root_dir / ".env")
    api_token = os.environ.get("KAGGLE_API_TOKEN") or dotenv_values.get("KAGGLE_API_TOKEN")
    username = os.environ.get("KAGGLE_USERNAME") or dotenv_values.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY") or dotenv_values.get("KAGGLE_KEY")
    return {"api_token": api_token, "username": username, "key": key}


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
        kernels = api.kernels_list(user=credentials["username"], page=1, page_size=5)
        status["authenticated"] = True
        status["kernel_count_sample"] = len(kernels)
        status["kernel_refs"] = [getattr(kernel, "ref", None) for kernel in kernels]
    except Exception as exc:
        status["error"] = str(exc)

    return status


def format_kaggle_doctor_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2)
