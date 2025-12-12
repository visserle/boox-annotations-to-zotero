"""
Core functionality for importing EPUB annotations into Zotero database.
"""

import json
import logging
from pathlib import Path

from src.cfi_generator_js import create_epub_cfi_batch_js
from src.database import AnnotationImporter, create_database_backup
from src.models import Annotation

logger = logging.getLogger(__name__.rsplit(".", maxsplit=1)[-1])


def import_annotations_to_database(
    db_path: str | Path,
    annotations: list[Annotation],
    epub_path: str | Path,
    parent_item_id: int,
    highlight_color: str,
) -> tuple[int, int, int]:
    """
    Import annotations into the Zotero database using JavaScript CFI generation.

    Returns:
        Tuple of (successful_count, skipped_count, failed_count)
    """
    logger.info(f"Importing {len(annotations)} annotation(s)...")

    # Create backup
    backup_path = create_database_backup(db_path)
    logger.debug(f"Database backup created at: {backup_path}")

    # Sort annotations by page number to ensure sequential processing
    # This helps disambiguate duplicate text by searching from the last match position
    sorted_annotations = sorted(
        annotations, key=lambda a: int(a.page) if a.page.isdigit() else 0
    )
    logger.debug(
        f"Sorted annotations by page: {[a.page for a in sorted_annotations[:5]]}"
        + ("..." if len(sorted_annotations) > 5 else "")
    )

    # Generate all CFIs in batch (much faster than individual calls)
    logger.debug("Generating CFIs in batch mode...")
    search_texts = [annotation.text for annotation in sorted_annotations]
    cfis = create_epub_cfi_batch_js(epub_path, search_texts)

    successful = 0
    skipped = 0
    failed = 0

    with AnnotationImporter(db_path) as importer:
        for idx, (annotation, cfi) in enumerate(zip(sorted_annotations, cfis), 1):
            logger.debug(
                f"[{idx}/{len(annotations)}] Processing page {annotation.page}"
            )

            if cfi:
                # Create position JSON from CFI
                position_json = _create_position_json(cfi)

                # For sort index, we'll use a simple page-based approach
                # since we no longer track spine index in Python
                sort_index = _create_sort_index_from_page(annotation.page)

                logger.debug(f"[{idx}/{len(annotations)}] CFI generated")
                logger.debug(f"  {cfi}")
            else:
                # Fallback: create a minimal CFI based on page number
                # This allows the annotation to be imported even if text search fails
                try:
                    page_num = int(annotation.page)
                except (ValueError, TypeError):
                    page_num = 0

                approx_spine = max(0, page_num // 10)
                cfi = f"epubcfi(/6/{(approx_spine + 1) * 2}!/4/2:0)"
                position_json = _create_position_json(cfi)
                sort_index = _create_sort_index_from_page(annotation.page)

                logger.warning(
                    f"[{idx}/{len(annotations)}] Text not found in EPUB, using fallback CFI (page {annotation.page})"
                )
                logger.debug(f"  Search text: {annotation.text[:50]}...")

            # Insert annotation
            result = importer.insert_annotation(
                annotation, parent_item_id, position_json, sort_index, highlight_color
            )

            if result is True:
                successful += 1
            elif result is False:
                # Skipped (duplicate)
                skipped += 1
            else:
                # Failed (error)
                failed += 1

    return successful, skipped, failed


def _create_position_json(cfi: str) -> str:
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


def _create_sort_index_from_page(page: str) -> str:
    """
    Create a sort index from page number.

    Format: "spine_index|character_offset" (matches Zotero's EPUB annotation format)
    Since we don't have spine position, we use page number as approximate offset.
    """
    try:
        # Try to parse page as integer
        page_num = int(page)
    except (ValueError, TypeError):
        # If page is not a number, use 0
        page_num = 0

    # Use page number * 1000 as approximate character offset for sorting
    # Spine index defaults to 00000
    char_offset = page_num * 1000
    return f"{0:05d}|{char_offset:08d}"


def print_import_summary(
    successful: int, skipped: int, failed: int, db_path: str | Path
):
    """Print a summary of the import operation."""
    logger.info("")
    logger.info(f"Imported: {successful} | Skipped: {skipped} | Failed: {failed}")
    if successful > 0:
        logger.info("Restart Zotero to see the imported annotations")
