"""JavaScript-based CFI generation using epub.js and Node.js."""

import json
import subprocess
from pathlib import Path


def create_epub_cfi_js(epub_path: str | Path, search_text: str) -> str | None:
    """
    Create an EPUB CFI using the JavaScript implementation with epub.js.

    This is a convenience wrapper around create_epub_cfi_batch_js for single annotations.
    For processing multiple annotations, use create_epub_cfi_batch_js directly for better performance.

    Args:
        epub_path: Path to the EPUB file
        search_text: The text to search for and generate CFI from

    Returns:
        CFI string or None if generation fails
    """
    # Use batch function with single item for consistency
    results = create_epub_cfi_batch_js(epub_path, [search_text])
    return results[0] if results else None


def create_epub_cfi_batch_js(
    epub_path: str | Path, search_texts: list[str]
) -> list[str | None]:
    """
    Create multiple EPUB CFIs in batch mode using a single Node.js subprocess.

    This is much faster than calling create_epub_cfi_js multiple times because
    the EPUB is only parsed once.

    Args:
        epub_path: Path to the EPUB file
        search_texts: List of texts to search for and generate CFIs from

    Returns:
        List of CFI strings (or None for failed generations) in same order as input
    """
    try:
        # Get the path to the epub-cfi-generator.js script
        cfi_generator = Path(__file__).parent / "epub-cfi-generator.js"

        # Prepare batch input as JSON
        batch_json = json.dumps(search_texts)

        # Call Node.js script in batch mode
        result = subprocess.run(
            [
                "node",
                str(cfi_generator),
                str(epub_path),
                batch_json,
                "--batch",
            ],
            capture_output=True,
            text=True,
            timeout=60,  # Longer timeout for batch processing
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout.strip())
                # Extract CFIs from batch results
                cfis = []
                for item in output:
                    if "error" in item or item.get("cfi") is None:
                        cfis.append(None)
                    else:
                        cfis.append(item["cfi"])
                return cfis

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing batch CFI results: {e}")
                return [None] * len(search_texts)
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"Batch CFI generation failed: {error_msg}")
            return [None] * len(search_texts)

    except subprocess.TimeoutExpired:
        print("Error: Batch CFI generation timed out")
        return [None] * len(search_texts)
    except Exception as e:
        print(f"Error generating batch CFIs with JavaScript: {e}")
        return [None] * len(search_texts)
