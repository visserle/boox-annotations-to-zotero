"""
Main entry point for Zotero annotation import tool.

Import annotations from Boox e-readers into Zotero's EPUB reader.
"""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

from src.config import COLOR_MAP, ZOTERO_DATA_DIR
from src.database import find_epub_in_database
from src.import_annotations import (
    import_annotations_to_database,
    print_import_summary,
)
from src.log_config import configure_logging
from src.text_processing import extract_book_identifier, parse_annotation_file
from src.zotero_utils import get_zotero_storage_dir

logger = logging.getLogger(__name__.rsplit(".", maxsplit=1)[-1])


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Import Boox annotations into Zotero",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s annotations.txt             # Import annotation file
  %(prog)s --debug annotations.txt     # Show debug information
        """,
    )

    parser.add_argument(
        "annotation_file",
        type=Path,
        help="annotation file to import",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug logging",
    )

    parser.add_argument(
        "--zotero-dir",
        type=Path,
        metavar="PATH",
        help=f"path to Zotero data directory (default: {ZOTERO_DATA_DIR})",
    )

    parser.add_argument(
        "--highlight-color",
        type=str,
        choices=COLOR_MAP.keys(),
        default="yellow",
        help="highlight color for imported annotations (default: yellow)",
    )

    return parser.parse_args()


def main():
    """Main entry point for the annotation import tool."""
    args = parse_args()

    # Configure logging based on arguments
    log_level = logging.DEBUG if args.debug else logging.INFO
    configure_logging(stream_level=log_level)

    # Determine Zotero data directory
    zotero_dir = args.zotero_dir if args.zotero_dir else ZOTERO_DATA_DIR
    db_path = zotero_dir / "zotero.sqlite"

    # Get storage directory (may be different from data_dir/storage if custom path is set)
    try:
        storage_dir = get_zotero_storage_dir()
    except (FileNotFoundError, ValueError):
        # Fallback to default location
        storage_dir = zotero_dir / "storage"

    # Check if database exists
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        sys.exit(1)

    # Resolve annotation file path
    annotation_path = args.annotation_file.resolve()
    if not annotation_path.exists():
        logger.error(f"File not found: {annotation_path}")
        sys.exit(1)

    # Extract book identifier and find EPUB in database
    book_identifier = extract_book_identifier(annotation_path)
    logger.debug(f"Searching for book: {book_identifier}")

    try:
        epub_info = find_epub_in_database(db_path, book_identifier)
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            logger.error("Database is locked. Please close Zotero and try again.")
            sys.exit(1)
        raise

    if not epub_info:
        logger.error(f"EPUB not found in Zotero database: {book_identifier}")
        logger.error("Ensure the EPUB is imported and filename matches")
        sys.exit(1)

    # For low-confidence matches, ask user to confirm
    CONFIDENCE_THRESHOLD = 0.9
    if epub_info.confidence < CONFIDENCE_THRESHOLD:
        logger.warning(
            f"Found potential match with {epub_info.confidence:.0%} confidence:"
        )
        logger.warning(f"  File: {epub_info.filename}")
        logger.warning(f"  Match method: {epub_info.match_method}")
        logger.warning(f"  Searching for: {book_identifier}")

        response = input("\nIs this the correct EPUB? [y/N]: ").strip().lower()
        if response not in ["y", "yes"]:
            logger.error("Match rejected by user. Please check the EPUB filename.")
            sys.exit(1)
        logger.info("Match confirmed by user.")

    logger.info(f"Located EPUB: {epub_info.filename}")
    logger.debug(f"  Attachment ID: {epub_info.item_id}")
    logger.debug(f"  Parent ID: {epub_info.parent_id}")
    logger.debug(f"  Confidence: {epub_info.confidence:.0%} ({epub_info.match_method})")

    # Locate EPUB file in Zotero storage
    epub_path = Path(epub_info.get_full_path(storage_dir))
    if not epub_path.exists():
        logger.error(f"EPUB file missing: {epub_path}")
        logger.error(f"Check Zotero storage directory: {storage_dir}")
        sys.exit(1)

    # Parse annotations
    annotations = parse_annotation_file(annotation_path)
    logger.info(f"Parsed {len(annotations)} annotation(s)")

    if not annotations:
        logger.warning("No annotations found")
        sys.exit(0)

    # Show preview
    for i, ann in enumerate(annotations[:3], 1):
        preview = ann.text[:60] + "..." if len(ann.text) > 60 else ann.text
        logger.debug(f"  [{i}] Page {ann.page}: {preview}")

    # Import annotations
    successful, skipped, failed = import_annotations_to_database(
        db_path,
        annotations,
        epub_path,
        epub_info.item_id,
        COLOR_MAP[args.highlight_color],
    )

    # Show summary
    print_import_summary(successful, skipped, failed, db_path)


if __name__ == "__main__":
    main()
