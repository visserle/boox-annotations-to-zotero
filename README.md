# Boox Annotations to Zotero

Import annotations from Boox e-readers into Zotero's EPUB reader with accurate positioning.

## Features

- ✅ Imports Boox annotations directly into Zotero database
- ✅ Generates EPUB CFIs (Canonical Fragment Identifiers) matching Zotero's format exactly
- ✅ Preserves annotation text and timestamps
- ✅ Automatic database backup before import
- ✅ Smart text search with normalization

## Quick Start

### Prerequisites

1. **Node.js** (v14 or higher)
   ```bash
   node --version
   ```

2. **Python 3.8+**
   ```bash
   python3 --version
   ```

3. **Zotero** with EPUB files in your library

### Installation

1. Clone this repository
2. Install JavaScript dependencies:
   ```bash
   npm install
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. Export your Boox annotations (they should be in a `.txt` file with format: `*-annotation-*.txt`)

2. Place the annotation file in the project directory

3. Run the import:
   ```bash
   python3 main.py
   ```

4. Restart Zotero to see your annotations!

## How It Works

### CFI Generation (JavaScript)

The project uses **JavaScript** for CFI generation to ensure perfect compatibility with Zotero:

```javascript
// epub-cfi-generator.js parses EPUB and generates CFI
node epub-cfi-generator.js book.epub "annotation text"
// Output: epubcfi(/6/4!/4/2/10,/1:0,/1:50)
```

This JavaScript implementation:
- Uses the same `EpubCFI` class as Zotero
- Parses EPUBs with JSZip (avoiding browser dependencies)
- Searches text with proper normalization
- Generates accurate character offsets

### Python Integration

The Python code handles:
- Parsing Boox annotation files
- Finding EPUB files in Zotero's database
- Calling JavaScript CFI generator
- Inserting annotations into Zotero's SQLite database

```python
from cfi_generator_js import create_epub_cfi_js

# Generate CFI for an annotation
cfi = create_epub_cfi_js("path/to/book.epub", "annotation text")
# Returns: "epubcfi(/6/4!/4/2/10,/1:0,/1:50)"
```

## Project Structure

```
├── epub-cfi-generator.js    # Main CFI generator (JavaScript)
├── cfi_generator_js.py       # Python wrapper for JS generator
├── main.py                   # Main entry point
├── import_annotations.py     # Annotation import logic
├── database.py               # Zotero database operations
├── text_processing.py        # Annotation file parsing
├── config.py                 # Configuration
├── epub_handler.py           # EPUB utilities (only create_position_json used)
├── src/
│   ├── epubcfi.js           # Core CFI implementation (from Zotero)
│   └── utils/core.js        # Utility functions
└── test_cfi.py              # CFI tests comparing against Zotero
```

## Configuration

Edit `config.py` to customize:

```python
# Path to Zotero database
DB_FILE = Path("zotero.sqlite")

# Path to Zotero storage directory
ZOTERO_STORAGE_DIR = Path.home() / "Zotero" / "storage"

# Text search settings
MAX_SEARCH_LENGTH = 200
MIN_SENTENCE_LENGTH = 20
```

## Technical Details

### Why JavaScript for CFI Generation?

Python libraries for EPUB CFI generation don't match Zotero's exact behavior. By using the same JavaScript code that Zotero uses (from `epubcfi.js`), we ensure perfect compatibility.

### CFI Format

EPUB CFIs follow this format:
```
epubcfi(/6/SPINE!/4/ELEMENT,/TEXT_NODE:START,/TEXT_NODE:END)
```

Example: `epubcfi(/6/4!/4/2/10,/1:0,/1:50)`
- `/6/4` - Spine position (chapter 2)
- `!/4/2/10` - Path to element in chapter
- `/1:0,/1:50` - Text range (characters 0-50 in text node 1)

### Database Schema

Annotations are stored in Zotero's `itemAnnotations` table:

| Column | Description |
|--------|-------------|
| `parentItemID` | Reference to EPUB attachment |
| `text` | Annotation text |
| `comment` | User comments (unused) |
| `sortIndex` | Sort order for display |
| `position` | JSON with CFI and metadata |

## Troubleshooting

### "Text not found in EPUB"

The system will use a fallback CFI based on page number. This is less accurate but allows the annotation to be imported.

### "Database file not found"

Make sure `zotero.sqlite` is in the project directory or update `DB_FILE` in `config.py`.

### "Node.js command not found"

Install Node.js from https://nodejs.org/ or use your package manager:
- macOS: `brew install node`
- Ubuntu: `sudo apt install nodejs npm`

## Development

### Running Tests

```bash
# Test CFI generation against actual Zotero annotations
python3 test_cfi.py

# Test individual CFI generation
node epub-cfi-generator.js book.epub "text" --output json
```

### Adding Features

1. **Custom text normalization** - Edit `normalizeText()` in `epub-cfi-generator.js`
2. **Database schema changes** - Update `database.py`
3. **Annotation parsing** - Modify `text_processing.py`

## License

[Your License Here]

## Acknowledgments

- EPUB CFI implementation adapted from [Zotero](https://github.com/zotero/zotero)
- Built for the Boox e-reader community

