"""
Main entry point for Zotero annotation import tool.

Import annotations from Boox e-readers into Zotero's EPUB reader.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.config import DB_FILE, ZOTERO_STORAGE_DIR
from src.log_config import configure_logging
from src.text_processing import parse_annotation_file, extract_book_identifier
from src.database import find_epub_in_database
from src.import_annotations import (
    find_annotation_file,
    import_annotations_to_database,
    print_import_summary,
)

logger = logging.getLogger(__name__.rsplit(".", maxsplit=1)[-1])


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Import Boox annotations into Zotero",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Auto-detect annotation file
  %(prog)s annotations.txt              # Import specific file
  %(prog)s --debug annotations.txt     # Show debug information
        """,
    )

    parser.add_argument(
        "annotation_file",
        nargs="?",
        type=Path,
        help="annotation file to import (auto-detected if not provided)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug logging",
    )

    parser.add_argument(
        "--db",
        type=Path,
        metavar="PATH",
        help=f"path to Zotero database (default: {DB_FILE})",
    )

    parser.add_argument(
        "--storage",
        type=Path,
        metavar="PATH",
        help=f"path to Zotero storage directory (default: {ZOTERO_STORAGE_DIR})",
    )

    return parser.parse_args()


def main():
    """Main entry point for the annotation import tool."""
    args = parse_args()

    # Configure logging based on arguments
    log_level = logging.DEBUG if args.debug else logging.INFO
    configure_logging(stream_level=log_level)

    base_dir = Path(__file__).parent
    db_path = (
        args.db
        if args.db
        else (DB_FILE if DB_FILE.is_absolute() else base_dir / DB_FILE)
    )
    storage_dir = args.storage if args.storage else ZOTERO_STORAGE_DIR

    # Check if database exists
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.error("Make sure zotero.sqlite exists or specify path with --db")
        sys.exit(1)

    # Determine annotation file
    if args.annotation_file:
        annotation_path = args.annotation_file
        if not annotation_path.is_absolute():
            annotation_path = base_dir / annotation_path
    else:
        annotation_path = find_annotation_file(base_dir)
        if annotation_path is None:
            logger.error("No annotation file found")
            logger.error("Provide a file or place *-annotation-*.txt in this directory")
            sys.exit(1)
        logger.info(f"Auto-detected: {annotation_path.name}")

    if not annotation_path.exists():
        logger.error(f"File not found: {annotation_path}")
        sys.exit(1)

    # Extract book identifier and find EPUB in database
    book_identifier = extract_book_identifier(annotation_path.name)
    logger.debug(f"Searching for book: {book_identifier}")

    epub_info = find_epub_in_database(str(db_path), book_identifier)
    if not epub_info:
        logger.error(f"EPUB not found in Zotero database: {book_identifier}")
        logger.error("Ensure the EPUB is imported and filename matches")
        sys.exit(1)

    logger.info(f"Located EPUB: {epub_info.filename}")
    logger.debug(f"  Attachment ID: {epub_info.item_id}")
    logger.debug(f"  Parent ID: {epub_info.parent_id}")

    # Locate EPUB file in Zotero storage
    epub_path = Path(epub_info.get_full_path(storage_dir))
    if not epub_path.exists():
        logger.error(f"EPUB file missing: {epub_path}")
        logger.error(f"Check Zotero storage directory: {storage_dir}")
        sys.exit(1)

    # Parse annotations
    annotations = parse_annotation_file(str(annotation_path))
    logger.info(
        f"Parsed {len(annotations)} annotation{'s' if len(annotations) != 1 else ''}"
    )

    if not annotations:
        logger.warning("No annotations found")
        sys.exit(0)

    # Show preview
    for i, ann in enumerate(annotations[:3], 1):
        preview = ann.text[:60] + "..." if len(ann.text) > 60 else ann.text
        logger.debug(f"  [{i}] Page {ann.page}: {preview}")

    # Import annotations
    successful, skipped, failed = import_annotations_to_database(
        str(db_path), annotations, str(epub_path), epub_info.item_id
    )

    # Show summary
    backup_path = f"{db_path}.pre-import-backup"
    print_import_summary(successful, skipped, failed, backup_path)


if __name__ == "__main__":
    main()
