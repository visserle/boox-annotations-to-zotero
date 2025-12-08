"""JavaScript-based CFI generation using epub.js and Node.js."""

import json
import subprocess
from pathlib import Path
from typing import Optional


def create_epub_cfi_js(epub_path: str, search_text: str) -> Optional[str]:
    """
    Create an EPUB CFI using the JavaScript implementation with epub.js.

    This function calls the Node.js epub-cfi-generator.js script which uses
    futurepress/epub.js to parse the EPUB and generate a CFI that matches
    Zotero's behavior exactly.

    Args:
        epub_path: Path to the EPUB file
        search_text: The text to search for and generate CFI from

    Returns:
        CFI string or None if generation fails
    """
    try:
        # Get the path to the epub-cfi-generator.js script (in src directory)
        script_dir = Path(__file__).parent
        cfi_generator = script_dir / "epub-cfi-generator.js"

        if not cfi_generator.exists():
            print(f"Error: CFI generator script not found at {cfi_generator}")
            return None

        # Call Node.js script with JSON output for better error handling
        result = subprocess.run(
            ["node", str(cfi_generator), epub_path, search_text, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30,  # Increased timeout for EPUB parsing
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout.strip())

                if "error" in output:
                    print(f"CFI generation error: {output['error']}")
                    return None

                # Extract CFI from output
                cfi = output.get("cfi")
                return cfi if cfi else None

            except json.JSONDecodeError:
                # Fallback: try to parse as plain text CFI
                cfi = result.stdout.strip()
                return cfi if cfi and cfi.startswith("epubcfi(") else None
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"CFI generation failed: {error_msg}")
            return None

    except subprocess.TimeoutExpired:
        print("Error: CFI generation timed out")
        return None
    except Exception as e:
        print(f"Error generating CFI with JavaScript: {e}")
        return None
