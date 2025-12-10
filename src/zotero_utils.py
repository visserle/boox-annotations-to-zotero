"""Utility functions for annotation processing."""

import platform
import re
from pathlib import Path


def _get_zotero_profiles_dir() -> Path:
    """Get the Zotero profiles directory based on the operating system."""
    system = platform.system()

    if system == "Darwin":  # macOS
        return Path.home() / "Library/Application Support/Zotero/Profiles"
    elif system == "Windows":
        # Use APPDATA environment variable
        appdata = Path.home() / "AppData/Roaming"
        return appdata / "Zotero/Profiles"
    else:  # Linux and other Unix-like systems
        # Try common locations
        zotero_dir = Path.home() / ".zotero/zotero"
        if zotero_dir.exists():
            return zotero_dir / "Profiles"
        # Alternative location
        return Path.home() / ".zotero/zotero/Profiles"


def _read_zotero_pref(key: str) -> str | None:
    """Read a preference value from Zotero's prefs.js file."""
    prefs_dir = _get_zotero_profiles_dir()
    prefs_files = list(prefs_dir.glob("*/prefs.js"))

    if not prefs_files:
        raise FileNotFoundError(
            f"Zotero preferences not found in {prefs_dir}. "
            "Make sure Zotero is installed and has been run at least once."
        )

    content = prefs_files[0].read_text()
    match = re.search(rf'user_pref\("{re.escape(key)}",\s*"([^"]+)"\)', content)
    return match.group(1) if match else None


def get_zotero_data_dir() -> Path:
    """Get Zotero's data directory from preferences."""
    data_dir = _read_zotero_pref("extensions.zotero.dataDir")
    if not data_dir:
        raise ValueError("Zotero data directory not configured")
    return Path(data_dir)


def get_zotero_storage_dir() -> Path:
    """Get Zotero's storage directory from preferences."""
    # Try custom base attachment path first
    storage_dir = _read_zotero_pref("extensions.zotero.baseAttachmentPath")
    if storage_dir:
        return Path(storage_dir)

    # Fall back to default storage location
    return get_zotero_data_dir() / "storage"
