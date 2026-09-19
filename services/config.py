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

DEFAULT_CONFIG = {
    "source_folder_id": "root",
    "source_folder_name": "My Drive",
    "default_duration_hours": 12,
    "temp_folder_prefix": "Tài liệu Share Tạm - ",
    "last_link": "",
    "terabox_mount_path": "T:\\"
}


def load() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save(config: dict):
    # keep only known keys
    clean_config = {k: config.get(k, DEFAULT_CONFIG[k]) for k in DEFAULT_CONFIG.keys()}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(clean_config, f, indent=2, ensure_ascii=False)


def get(key: str):
    return load().get(key, DEFAULT_CONFIG.get(key))


def set_value(key: str, value):
    cfg = load()
    cfg[key] = value
    save(cfg)
