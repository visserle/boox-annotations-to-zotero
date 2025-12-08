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

# Text matching configuration
MAX_SEARCH_LENGTH = 300  # Maximum characters to use for initial matching
MIN_SENTENCE_LENGTH = 20  # Minimum sentence length for fallback matching
FALLBACK_SEARCH_LENGTH = 50  # Characters to use for last resort matching

# Zotero key generation
ZOTERO_KEY_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # Excludes 0, 1, I, O
ZOTERO_KEY_LENGTH = 8
