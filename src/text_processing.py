"""Text processing utilities for annotation parsing and normalization."""

import re
from pathlib import Path
from src.models import Annotation


def normalize_text(text: str) -> str:
    """
    Normalize text for matching by handling smart quotes and whitespace.

    Converts Unicode smart quotes and apostrophes to ASCII equivalents
    so that text from annotation files can match EPUB content.
    """
    replacements = {
        "\u201c": '"',  # " -> "
        "\u201d": '"',  # " -> "
        "\u2018": "'",  # ' -> '
        "\u2019": "'",  # ' -> '
    }

    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)

    # Collapse whitespace
    return re.sub(r"\s+", " ", text.strip())


def parse_annotation_file(file_path: str | Path) -> list[Annotation]:
    """
    Parse the annotation text file and extract annotations.

    Expected format:
        -------------------
        YYYY-MM-DD HH:MM | Page No.: XXX
        Annotation text here...
        -------------------
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    annotations = []
    sections = content.split("-------------------")

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract timestamp and page number
        match = re.search(
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+\|\s+Page No\.:\s+(\d+)", section
        )
        if not match:
            continue

        timestamp, page = match.groups()

        # Extract annotation text (everything after the timestamp line)
        # Find the line with the timestamp and take all content after it
        lines = section.split("\n")
        text_lines = []
        found_timestamp = False

        for line in lines:
            if found_timestamp:
                text_lines.append(line)
            elif re.search(
                r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+\|\s+Page No\.:\s+\d+", line
            ):
                found_timestamp = True

        text = "\n".join(text_lines).strip()

        if text:
            annotations.append(Annotation(timestamp=timestamp, page=page, text=text))

    return annotations


def extract_book_identifier(annotation_file_path: str | Path) -> str:
    """
    Extract the book identifier from the first line of an annotation file.

    The first line format is: "Reading Notes | <<Book Identifier>>Author Name"
    Returns: The text between << and >>
    """
    with open(annotation_file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    # Extract text between << and >>
    match = re.search(r"<<(.+?)>>", first_line)
    if match:
        return match.group(1).strip()

    # Fallback: if pattern not found, raise an error
    raise ValueError(f"Could not extract book identifier from first line: {first_line}")
