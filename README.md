# Boox Annotations to Zotero

Import annotations from Boox e-readers into Zotero's EPUB reader with accurate positioning using EPUB CFI (Canonical Fragment Identifier).

## Features

- Imports Boox highlights directly into Zotero's database
- Generates accurate EPUB CFIs matching Zotero's format exactly
- Automatic database backup before import
- Auto-detects annotation files

## Requirements

- **Python 3.12+**
- **Node.js 14+**
- **Zotero** with EPUB files in your library

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/visserle/boox-annotations-to-zotero.git
   cd boox-annotations-to-zotero
   ```

2. **Install JavaScript dependencies:**
   ```bash
   npm install
   ```

3. **Set up CFI generator:**
   ```bash
   chmod +x setup-cfi.sh
   ./setup-cfi.sh
   ```

## Configuration

Edit `src/config.py` to match your setup:

```python
# Path to Zotero database
DB_FILE = Path.home() / "Zotero" / "zotero.sqlite"

# Path to Zotero storage directory  
ZOTERO_STORAGE_DIR = Path.home() / "drive" / "Zotero"
```

**Important:** Adjust `ZOTERO_STORAGE_DIR` to where your Zotero storage folder is located (this is where your EPUB files are stored).

## Usage

1. **Export annotations from your Boox device** (the file should be named like `Book Title-annotation-YYYY-MM-DD_HH_MM_SS.txt`)

2. **Place the annotation file in the project directory**

3. **Run the import:**
   ```bash
   python main.py
   ```
   
   Or specify a file:
   ```bash
   python main.py path/to/annotations.txt
   ```

4. **Restart Zotero** to see your imported annotations

### Command-Line Options

```bash
# Auto-detect annotation file
python main.py

# Specify annotation file
python main.py annotations.txt

# Debug mode (verbose output)
python main.py --debug annotations.txt

# Custom database path
python main.py --db /path/to/zotero.sqlite

# Custom storage directory
python main.py --storage /path/to/storage
```

## How It Works

1. **Parses** the Boox annotation file
2. **Finds** the matching EPUB in Zotero's database
3. **Generates** EPUB CFIs using JavaScript (ensures compatibility with Zotero)
4. **Imports** annotations directly into Zotero's SQLite database
5. **Creates** a backup before making changes

The tool uses JavaScript for CFI generation because it uses the same `epubcfi.js` code that Zotero uses, ensuring perfect compatibility.

## Troubleshooting

### "Database not found"

Update the `DB_FILE` path in `src/config.py` to point to your `zotero.sqlite` file.

### "EPUB not found in Zotero database"

Make sure:
- The EPUB is imported in Zotero
- The filename in Zotero matches the Boox annotation filename (author and title)

### "Text not found in EPUB"

The tool will use a fallback CFI based on page number. The annotation will still be imported but may not be positioned exactly.

## Limitations

- Only supports highlight annotations
- There can only be one color as Boox does not store color information in the annotation file

## Running Tests

```bash
# Test CFI generation against Zotero annotations
python test/test_cfi.py
```

The test suite compares generated CFIs against actual Zotero annotations from Romeo & Juliet and The History of Drink.

Tested with Python 3.13.9, Node.js 25.2.1 and Zotero 7.0.30 on an M2 MacBook Air.
