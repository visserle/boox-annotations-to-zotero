![alt text](image.png)

# The Problem

EPUB annotations are stored externally in the e-reader's database or metadata, not in the file itself. Transfers between systems can be challenging. BOOX's NeoReader lets you export annotations as .txt files, but these lack EPUB CFI (Canonical Fragment Identifier), the standardized location identifier of highlights. Without CFIs, other EPUB readers like Zotero can't link highlights to specific locations in the book.

# The Solution

This repository helps with importing annotations from BOOX's NeoReader into Zotero's database. As the NeoReader export is inherently lossy, this tool reconstructs the CFI for each annotation using the same JavaScript code that Zotero uses internally. The highlighted text is matched against the EPUB content to reconstruct the CFI. Page numbers from the NeoReader export are used to narrow down the search area, improving accuracy.

## Features

- Automatically finds the corresponding EPUB in your Zotero library based on author and title information in the NeoReader export
- Generates accurate EPUB CFIs (Canonical Fragment Identifier) from the lossy NeoReader annotations
- Batch-imports the CFIs directly into Zotero's database
- Supports highlights with comments
- Prevents the import of duplicate annotations for easy updates
- Automatic database backup before import

## Usage

Tested with Zotero 7.0.30 on an M2 MacBook Air and NeoReader 38133 on a Boox Page.

1. **Export annotations from your Boox device**. From the NeoReader app, select Contents > Annotations > Select All > Export to Local Storage or Share. Make sure that the page number export is enabled in NeoReader settings (this is the default). The file should be named like `Book Title-annotation-YYYY-MM-DD_HH_MM_SS.txt`. Save the file to your computer.

2. **Clone this repository:**
   ```bash
   git clone https://github.com/visserle/boox-annotations-to-zotero.git
   cd boox-annotations-to-zotero
   ```

3. **Install JavaScript dependencies:**
   ```bash
   npm install
   ```

4. **Close Zotero.**

5. **Run the import:**
 Make sure sure that the EPUB file is available in Zotero and that the first line of the Boox annotation .txt states the author and title in the << >> brackets (see `/examples`). Zotero's path and database is automatically detected, but can be overridden with: `--zotero-dir /path/to/zotero`. The script creates a backup of your Zotero database before making any changes under the name `zotero.sqlite.pre-import-backup`.

   ```bash
   python -m main path/to/annotations.txt
   ```

1. **Restart Zotero** to see your imported annotations. If the text is not found in EPUB, the annotation will be imported, but without a CFI. It will still be visible in Zotero, but not linked to a specific location in the EPUB.

## Limitations

Boox does not store color information in the annotation file so there is only one highlight color available for the import (set via the `--highlight-color` flag).


## Alternative Solutions

Convert your EPUB to PDF and annotate the PDF, or use KOReader on your Boox device, which supports direct exports to Zotero with CFIs.