"""Configuration constants for the annotation import tool."""

from pathlib import Path

# Database configuration
DB_FILE = Path.home() / "Zotero" / "zotero.sqlite"
ZOTERO_STORAGE_DIR = Path.home() / "drive" / "Zotero"  # Where EPUB files are stored
LIBRARY_ID = 1

# Zotero annotation settings
ANNOTATION_ITEM_TYPE_ID = 1  # itemTypeID for annotation
HIGHLIGHT_TYPE = 1  # type = 1 for highlight annotation
DEFAULT_HIGHLIGHT_COLOR = "#ffd400"

# Zotero key generation
ZOTERO_KEY_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # Excludes 0, 1, I, O
ZOTERO_KEY_LENGTH = 8
