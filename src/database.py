"""Database operations for Zotero annotation import."""

import logging
import random
import sqlite3
import shutil
from datetime import datetime

from src.models import Annotation, EPUBInfo
from src.config import (
    LIBRARY_ID,
    ZOTERO_KEY_CHARS,
    ZOTERO_KEY_LENGTH,
    ANNOTATION_ITEM_TYPE_ID,
    HIGHLIGHT_TYPE,
    DEFAULT_HIGHLIGHT_COLOR,
)

logger = logging.getLogger(__name__.rsplit(".", maxsplit=1)[-1])


def generate_zotero_key() -> str:
    """
    Generate an 8-character key in Zotero format.

    Valid characters: 23456789ABCDEFGHIJKLMNPQRSTUVWXYZ
    Excludes: 0, 1, I, O (to avoid confusion)
    """
    return "".join(random.choice(ZOTERO_KEY_CHARS) for _ in range(ZOTERO_KEY_LENGTH))


def get_existing_keys(db_path: str) -> set[str]:
    """Get all existing keys from the database to avoid collisions."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key FROM items")
        return {row[0] for row in cursor.fetchall()}


def generate_unique_key(existing_keys: set[str]) -> str:
    """Generate a unique key that doesn't exist in the database."""
    while True:
        key = generate_zotero_key()
        if key not in existing_keys:
            existing_keys.add(key)
            return key


def find_epub_in_database(db_path: str, book_identifier: str) -> EPUBInfo | None:
    """
    Find the EPUB file and parent item ID in the Zotero database.

    Uses multiple matching strategies to find the best match:
    1. Exact substring match
    2. Fuzzy matching by tokenizing and matching significant parts
    3. Matching by creator and title from Zotero metadata

    Args:
        db_path: Path to zotero.sqlite
        book_identifier: The book identifier extracted from annotation filename

    Returns:
        EPUBInfo object or None if not found
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Strategy 1: Exact substring match (current approach)
        cursor.execute(
            """
            SELECT itemID, parentItemID, path 
            FROM itemAttachments 
            WHERE path LIKE ? AND path LIKE '%.epub'
            LIMIT 1
            """,
            (f"%{book_identifier}%",),
        )

        result = cursor.fetchone()
        if result:
            item_id, parent_id, path = result
            filename = path.removeprefix("attachments:")
            logger.debug(f"Database match (exact): {filename}")
            return EPUBInfo(item_id=item_id, parent_id=parent_id, filename=filename)

        # Strategy 2: Fuzzy matching - tokenize and find best partial match
        # Get all EPUB attachments
        cursor.execute(
            """
            SELECT itemID, parentItemID, path 
            FROM itemAttachments 
            WHERE path LIKE '%.epub'
            """
        )

        all_epubs = cursor.fetchall()
        if not all_epubs:
            logger.warning("No EPUB files found in Zotero database")
            return None

        # Tokenize the identifier for fuzzy matching
        identifier_tokens = set(book_identifier.lower().split())
        # Remove common words and year patterns
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
        }
        identifier_tokens = {
            t for t in identifier_tokens if t not in stop_words and not t.isdigit()
        }

        best_match = None
        best_score = 0

        for item_id, parent_id, path in all_epubs:
            filename = path.removeprefix("attachments:")
            # Remove .epub extension for matching
            filename_base = filename.removesuffix(".epub")
            filename_tokens = set(filename_base.lower().split())
            filename_tokens = {t for t in filename_tokens if t not in stop_words}

            # Calculate match score (Jaccard similarity)
            if identifier_tokens:
                intersection = identifier_tokens & filename_tokens
                union = identifier_tokens | filename_tokens
                score = len(intersection) / len(union) if union else 0

                if score > best_score:
                    best_score = score
                    best_match = (item_id, parent_id, filename)

        # Accept matches with score > 0.3 (at least 30% token overlap)
        if best_match and best_score > 0.3:
            item_id, parent_id, filename = best_match
            logger.debug(f"Database match (fuzzy, score={best_score:.2f}): {filename}")
            logger.debug(f"  Query: {book_identifier}")
            return EPUBInfo(item_id=item_id, parent_id=parent_id, filename=filename)

        # Strategy 3: Try matching with Zotero item metadata (creator + title)
        # This helps when the filename doesn't match the annotation filename pattern
        cursor.execute(
            """
            SELECT ia.itemID, ia.parentItemID, ia.path,
                   COALESCE(
                       (SELECT GROUP_CONCAT(lastName || ' ' || firstName, ', ')
                        FROM itemCreators ic
                        JOIN creators c ON ic.creatorID = c.creatorID
                        WHERE ic.itemID = ia.parentItemID),
                       ''
                   ) as creators,
                   COALESCE(
                       (SELECT value FROM itemData id
                        JOIN itemDataValues idv ON id.valueID = idv.valueID
                        WHERE id.itemID = ia.parentItemID AND id.fieldID = 1),
                       ''
                   ) as title
            FROM itemAttachments ia
            WHERE ia.path LIKE '%.epub'
            """
        )

        metadata_matches = cursor.fetchall()
        best_match = None
        best_score = 0

        for item_id, parent_id, path, creators, title in metadata_matches:
            # Combine creators and title for matching
            metadata_str = f"{creators} {title}".lower()
            metadata_tokens = set(metadata_str.split())
            metadata_tokens = {
                t for t in metadata_tokens if t not in stop_words and len(t) > 2
            }

            if identifier_tokens and metadata_tokens:
                intersection = identifier_tokens & metadata_tokens
                union = identifier_tokens | metadata_tokens
                score = len(intersection) / len(union) if union else 0

                if score > best_score:
                    best_score = score
                    filename = path.removeprefix("attachments:")
                    best_match = (item_id, parent_id, filename, creators, title)

        if best_match and best_score > 0.3:
            item_id, parent_id, filename, creators, title = best_match
            logger.debug(
                f"Database match (metadata, score={best_score:.2f}): {filename}"
            )
            logger.debug(f"  Authors: {creators}")
            logger.debug(f"  Title: {title}")
            return EPUBInfo(item_id=item_id, parent_id=parent_id, filename=filename)

        # No match found - log available EPUBs to help debugging
        logger.error("No matching EPUB found. Available EPUB files:")
        for item_id, parent_id, path in all_epubs[:10]:  # Show first 10
            filename = path.removeprefix("attachments:")
            logger.error(f"  - {filename}")
        if len(all_epubs) > 10:
            logger.error(f"  ... and {len(all_epubs) - 10} more")

        return None


def create_database_backup(db_path: str) -> str:
    """Create a backup of the database before making changes."""
    backup_path = f"{db_path}.pre-import-backup"
    shutil.copy2(db_path, backup_path)
    return backup_path


class AnnotationImporter:
    """Handles the import of annotations into the Zotero database."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        self.existing_keys: set[str] = set()

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.existing_keys = get_existing_keys(self.db_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

    def annotation_exists(self, annotation: Annotation, parent_item_id: int) -> bool:
        """
        Check if an annotation already exists in the database.

        Matches based on:
        - Parent item ID (same book)
        - Text content (exact match)
        - Timestamp (to distinguish multiple highlights of same text)

        Args:
            annotation: The annotation to check
            parent_item_id: The parent item ID to check against

        Returns:
            True if a matching annotation exists, False otherwise
        """
        try:
            assert self.cursor is not None, "Database cursor not initialized"

            # Parse timestamp to match the format in database
            dt = datetime.strptime(annotation.timestamp, "%Y-%m-%d %H:%M")
            date_added = dt.strftime("%Y-%m-%d %H:%M:%S")

            # Check for existing annotation with same parent, text, and timestamp
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM itemAnnotations ia
                JOIN items i ON ia.itemID = i.itemID
                WHERE ia.parentItemID = ?
                AND ia.text = ?
                AND i.dateAdded = ?
                """,
                (parent_item_id, annotation.text, date_added),
            )

            count = self.cursor.fetchone()[0]
            return count > 0

        except Exception as e:
            logger.warning(f"Error checking for duplicate annotation: {e}")
            # If we can't check, assume it doesn't exist to avoid data loss
            return False

    def insert_annotation(
        self,
        annotation: Annotation,
        parent_item_id: int,
        position_json: str,
        sort_index: str,
    ) -> bool | None:
        """
        Insert a single annotation into the database.

        Returns:
            True if successful, False if skipped (duplicate), None if failed
        """
        try:
            assert self.cursor is not None, "Database cursor not initialized"
            assert self.conn is not None, "Database connection not initialized"

            # Check if annotation already exists
            if self.annotation_exists(annotation, parent_item_id):
                logger.debug("  Duplicate detected, skipping")
                return False

            key = generate_unique_key(self.existing_keys)

            # Parse timestamp
            dt = datetime.strptime(annotation.timestamp, "%Y-%m-%d %H:%M")
            date_added = dt.strftime("%Y-%m-%d %H:%M:%S")

            # Insert into items table
            self.cursor.execute(
                """
                INSERT INTO items (
                    itemTypeID, dateAdded, dateModified, 
                    clientDateModified, libraryID, key, version, synced
                )
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
                """,
                (
                    ANNOTATION_ITEM_TYPE_ID,
                    date_added,
                    date_added,
                    date_added,
                    LIBRARY_ID,
                    key,
                ),
            )

            item_id = self.cursor.lastrowid

            # Insert into itemAnnotations table
            self.cursor.execute(
                """
                INSERT INTO itemAnnotations (
                    itemID, parentItemID, type, text, comment, 
                    color, pageLabel, sortIndex, position, isExternal
                )
                VALUES (?, ?, ?, ?, '', ?, '', ?, ?, 0)
                """,
                (
                    item_id,
                    parent_item_id,
                    HIGHLIGHT_TYPE,
                    annotation.text,
                    DEFAULT_HIGHLIGHT_COLOR,
                    sort_index,
                    position_json,
                ),
            )

            return True

        except Exception as e:
            logger.error(f"✗ Failed to insert annotation: {e}")
            if self.conn:
                self.conn.rollback()
            return None
