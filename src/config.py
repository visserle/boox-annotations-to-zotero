"""Configuration constants for the annotation import tool."""

import warnings
from pathlib import Path
from src.utils import get_zotero_data_dir, get_zotero_storage_dir

# Auto-detect Zotero paths with fallback to defaults
try:
    ZOTERO_DATA_DIR = get_zotero_data_dir()
    ZOTERO_STORAGE_DIR = get_zotero_storage_dir()
except (FileNotFoundError, ValueError) as e:
    warnings.warn(f"Could not auto-detect Zotero paths: {e}. Using defaults.")
    ZOTERO_DATA_DIR = Path.home() / "Zotero"
    ZOTERO_STORAGE_DIR = ZOTERO_DATA_DIR / "storage"

DB_FILE = ZOTERO_DATA_DIR / "zotero.sqlite"
LIBRARY_ID = 1

# Zotero annotation settings
ANNOTATION_ITEM_TYPE_ID = 1  # itemTypeID for annotation
HIGHLIGHT_TYPE = 1  # type = 1 for highlight annotation
DEFAULT_HIGHLIGHT_COLOR = "#ffd400"
