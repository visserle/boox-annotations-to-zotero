"""Data models for annotations."""

from dataclasses import dataclass


@dataclass
class Annotation:
    """Represents a single annotation from the text file."""

    timestamp: str
    page: str
    text: str
    position: str | None = None
    cfi: str | None = None
    sort_index: str | None = None

    def __post_init__(self):
        """Clean up text after initialization."""
        self.text = self.text.strip()

    def __repr__(self):
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"Annotation(page={self.page}, text='{preview}')"


@dataclass
class EPUBInfo:
    """Information about an EPUB file in the Zotero database."""

    item_id: int
    parent_id: int
    filename: str

    def get_full_path(self, storage_dir) -> str:
        """Get the full path to the EPUB file.

        Args:
            storage_dir: Path to the Zotero storage directory

        Returns:
            Full path to the EPUB file
        """
        from pathlib import Path

        return str(Path(storage_dir) / self.filename)


@dataclass
class TextLocation:
    """Location of text within an EPUB."""

    spine_index: int
    char_offset: int
    text_length: int
