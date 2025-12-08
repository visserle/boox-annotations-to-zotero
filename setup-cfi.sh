#!/bin/bash

# Setup script for JavaScript CFI generation

echo "Setting up JavaScript CFI generation..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js first."
    echo "Visit https://nodejs.org/ or use your package manager:"
    echo "  macOS: brew install node"
    echo "  Ubuntu: sudo apt install nodejs npm"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 14 ]; then
    echo "Warning: Node.js version 14 or higher is recommended"
fi

# Install npm dependencies
echo "Installing npm dependencies..."
npm install

# Run tests
echo "Running tests..."
npm test

echo ""
echo "Setup complete! The JavaScript CFI generator is ready to use."
echo ""
echo "Usage from Python:"
echo "  from cfi_generator_js import create_epub_cfi_js"
echo ""
echo "Usage from command line:"
echo "  node cfi-generator.js <html_file> <search_text> <spine_index>"
