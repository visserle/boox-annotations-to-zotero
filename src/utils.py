"""Utility functions for annotation processing."""

import json


def create_position_json(cfi: str, page_label: str = "") -> str:
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
