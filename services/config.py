"""
Config management — saves/loads user preferences locally.

When running as a PyInstaller bundle, the executable is read-only.
All user data (config, tokens) is stored in the user's data directory:
  - macOS/Linux: ~/.gdrivecloner/
  - Windows:     %APPDATA%\\GDriveCloner\\
"""
import os
import json
import sys


def _get_data_dir() -> str:
    """Return platform-appropriate user data directory for GDriveCloner."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        data_dir = os.path.join(base, "GDriveCloner")
    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".gdrivecloner")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


DATA_DIR = _get_data_dir()
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

_DEFAULTS = {
    "source_folder_id": "root",
    "source_folder_name": "My Drive",
    "default_duration_hours": 24,
    "temp_folder_prefix": "Tài liệu Share Tạm - ",
    "last_link": "",
}


def load() -> dict:
    path = os.path.abspath(CONFIG_PATH)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults for any missing keys
        return {**_DEFAULTS, **data}
    return dict(_DEFAULTS)


def save(cfg: dict):
    path = os.path.abspath(CONFIG_PATH)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get(key: str):
    return load().get(key, _DEFAULTS.get(key))


def set_value(key: str, value):
    cfg = load()
    cfg[key] = value
    save(cfg)
