"""Configuration constants for the annotation import tool."""

import warnings
from pathlib import Path
from src.utils import get_zotero_data_dir

# Auto-detect Zotero data directory with fallback to default
try:
    ZOTERO_DATA_DIR = get_zotero_data_dir()
except (FileNotFoundError, ValueError) as e:
    warnings.warn(f"Could not auto-detect Zotero data directory: {e}. Using default.")
    ZOTERO_DATA_DIR = Path.home() / "Zotero"

LIBRARY_ID = 1

# Zotero annotation settings
ANNOTATION_ITEM_TYPE_ID = 1  # itemTypeID for annotation
HIGHLIGHT_TYPE = 1  # type = 1 for highlight annotation
DEFAULT_HIGHLIGHT_COLOR = "#ffd400"
