"""Utility functions for annotation processing."""

import json
import re
from pathlib import Path


def _read_zotero_pref(key: str) -> str | None:
    """Read a preference value from Zotero's prefs.js file."""
    prefs_file = Path.home() / "Library/Application Support/Zotero/Profiles"
    prefs_files = list(prefs_file.glob("*/prefs.js"))

    if not prefs_files:
        raise FileNotFoundError("Zotero preferences not found")

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


def create_position_json(cfi: str, page_label: str = "") -> str:
    """
    Create the position JSON for Zotero.

    For EPUB annotations, Zotero uses FragmentSelector with CFI.
    """
    position = {
        "type": "FragmentSelector",
        "conformsTo": "http://www.idpf.org/epub/linking/cfi/epub-cfi.html",
        "value": cfi,
    }
    return json.dumps(position)
