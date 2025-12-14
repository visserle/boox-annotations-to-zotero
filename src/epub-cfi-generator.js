#!/usr/bin/env node

/**
 * EPUB CFI Generator
 * 
 * Parses EPUB files and generates CFIs that match Zotero's behavior exactly.
 * Includes fuzzy matching to handle text extraction issues (e.g., missing spaces
 * at line breaks) from e-reader devices like Boox.
 * 
 * Usage: node epub-cfi-generator.js <epub_file> <search_text> [--output json]
 */

import { readFile } from 'fs/promises';
import JSZip from 'jszip';
import { parseString } from 'xml2js';
import { promisify } from 'util';
import { JSDOM } from 'jsdom';
import EpubCFI from './epubcfi.js';

const parseXml = promisify(parseString);

/**
 * Parse EPUB file and extract metadata
 */
async function parseEpub(epubPath) {
    const data = await readFile(epubPath);
    const zip = await JSZip.loadAsync(data);

    // Find and parse container.xml
    const containerXml = await zip.file('META-INF/container.xml').async('string');
    const container = await parseXml(containerXml);

    // Get path to OPF file
    const opfPath = container.container.rootfiles[0].rootfile[0]['$']['full-path'];
    const opfDir = opfPath.substring(0, opfPath.lastIndexOf('/') + 1);

    // Parse OPF file
    const opfXml = await zip.file(opfPath).async('string');
    const opf = await parseXml(opfXml);

    // Extract spine and manifest
    const manifest = {};
    const manifestItems = opf.package.manifest[0].item || [];

    for (const item of manifestItems) {
        manifest[item['$'].id] = {
            href: opfDir + item['$'].href,
            mediaType: item['$']['media-type']
        };
    }

    const spine = [];
    const spineItems = opf.package.spine[0].itemref || [];

    for (const itemref of spineItems) {
        const idref = itemref['$'].idref;
        if (manifest[idref]) {
            spine.push({
                id: idref,
                ...manifest[idref]
            });
        }
    }

    return { zip, spine, opfDir };
}

/**
 * Normalize text for searching (remove extra whitespace, etc.)
 */
function normalizeText(text) {
    return text
        .replace(/\s+/g, ' ')
        .replace(/[\u2018\u2019]/g, "'")
        .replace(/[\u201C\u201D]/g, '"')
        .trim();
}

/**
 * Find text in a DOM document and return a Range
 * 
 * @param {Document} doc - The DOM document to search in
 * @param {string} searchText - The text to search for
 * @param {boolean} useFuzzyMatch - If true, ignores whitespace differences
 * @param {number} skipChars - Number of characters to skip from the start (for finding later occurrences)
 * @returns {Range|null} DOM Range object or null if not found
 */
function findTextInDocument(doc, searchText, useFuzzyMatch = false, skipChars = 0) {
    const normalizedSearch = normalizeText(searchText);
    const walker = doc.createTreeWalker(
        doc.body || doc.documentElement,
        4, // NodeFilter.SHOW_TEXT
        null
    );

    let accumulatedText = '';
    const textNodes = [];

    // Collect all text nodes and their content
    let currentNode;
    while ((currentNode = walker.nextNode())) {
        const nodeText = currentNode.textContent;
        if (nodeText.trim().length === 0) continue;

        const normalizedNodeText = normalizeText(nodeText);
        const previousLength = accumulatedText.length;

        if (accumulatedText.length > 0) {
            accumulatedText += ' ';
        }
        accumulatedText += normalizedNodeText;

        textNodes.push({
            node: currentNode,
            startOffset: previousLength > 0 ? previousLength + 1 : 0,
            endOffset: accumulatedText.length,
            normalizedText: normalizedNodeText,
            originalText: nodeText
        });
    }

    let searchStartPos = -1;
    let searchEndPos = -1;

    if (!useFuzzyMatch) {
        // Try exact match first (case-insensitive)
        const searchLower = accumulatedText.toLowerCase();
        const normalizedSearchLower = normalizedSearch.toLowerCase();
        // Start searching from skipChars position to find later occurrences
        searchStartPos = searchLower.indexOf(normalizedSearchLower, skipChars);
        if (searchStartPos !== -1) {
            searchEndPos = searchStartPos + normalizedSearch.length;
        }
    } else {
        // Fuzzy match: compare texts with all whitespace removed
        // This handles cases where e-readers remove spaces at line breaks
        const textNoSpaces = accumulatedText.replace(/\s+/g, '').toLowerCase();
        const searchNoSpaces = normalizedSearch.replace(/\s+/g, '').toLowerCase();

        // Map skipChars to position in no-spaces text
        let skipNoSpaces = 0;
        for (let i = 0; i < Math.min(skipChars, accumulatedText.length); i++) {
            if (!/\s/.test(accumulatedText[i])) {
                skipNoSpaces++;
            }
        }

        const fuzzyPosNoSpaces = textNoSpaces.indexOf(searchNoSpaces, skipNoSpaces);

        if (fuzzyPosNoSpaces !== -1) {
            // Map position in whitespace-stripped text back to original text
            // by counting non-space characters
            let nonSpacesSeen = 0;
            for (let i = 0; i < accumulatedText.length; i++) {
                if (!/\s/.test(accumulatedText[i])) {
                    if (nonSpacesSeen === fuzzyPosNoSpaces) {
                        searchStartPos = i;
                        break;
                    }
                    nonSpacesSeen++;
                }
            }

            // Find end: count searchNoSpaces.length non-space chars from start
            nonSpacesSeen = 0;
            for (let i = searchStartPos; i < accumulatedText.length; i++) {
                if (!/\s/.test(accumulatedText[i])) {
                    nonSpacesSeen++;
                    if (nonSpacesSeen === searchNoSpaces.length) {
                        searchEndPos = i + 1; // +1 because we want position after the last char
                        break;
                    }
                }
            }
        }
    }

    if (searchStartPos === -1) {
        return null;
    }

    // Find which text nodes contain the start and end
    let startTextNode = null;
    let endTextNode = null;
    let startNodeOffset = 0;
    let endNodeOffset = 0;

    for (const nodeInfo of textNodes) {
        if (searchStartPos >= nodeInfo.startOffset && searchStartPos < nodeInfo.endOffset) {
            startTextNode = nodeInfo;
            // Calculate offset within the original (non-normalized) text
            const relativePos = searchStartPos - nodeInfo.startOffset;
            startNodeOffset = mapNormalizedToOriginalOffset(nodeInfo.normalizedText, nodeInfo.originalText, relativePos);
        }

        if (searchEndPos > nodeInfo.startOffset && searchEndPos <= nodeInfo.endOffset) {
            endTextNode = nodeInfo;
            const relativePos = searchEndPos - nodeInfo.startOffset;
            endNodeOffset = mapNormalizedToOriginalOffset(nodeInfo.normalizedText, nodeInfo.originalText, relativePos);
        }

        if (startTextNode && endTextNode) break;
    }

    if (!startTextNode || !endTextNode) {
        return null;
    }

    // Create range
    const range = doc.createRange();
    range.setStart(startTextNode.node, startNodeOffset);
    range.setEnd(endTextNode.node, endNodeOffset);

    return range;
}

/**
 * Map position in normalized text to position in original text
 */
function mapNormalizedToOriginalOffset(normalized, original, normalizedOffset) {
    let normPos = 0;
    let origPos = 0;

    while (normPos < normalizedOffset && origPos < original.length) {
        const origChar = original[origPos];

        // Skip whitespace that was normalized
        if (/\s/.test(origChar)) {
            // Check if this is part of a whitespace sequence
            let wsCount = 0;
            let tempPos = origPos;
            while (tempPos < original.length && /\s/.test(original[tempPos])) {
                wsCount++;
                tempPos++;
            }

            if (wsCount > 1) {
                // Multiple whitespace chars normalized to one space
                origPos += wsCount;
                normPos++;
            } else {
                origPos++;
                normPos++;
            }
        } else {
            origPos++;
            normPos++;
        }
    }

    return origPos;
}

/**
 * Search for text in EPUB and generate CFI
 */
async function generateCFI(epubPath, searchText, options = {}) {
    const { zip, spine } = await parseEpub(epubPath);
    const results = [];
    let foundMatch = false;

    // Search through all spine items
    for (let i = 0; i < spine.length; i++) {
        const spineItem = spine[i];

        try {
            // Load the HTML content
            let htmlContent = await zip.file(spineItem.href).async('string');

            // Decode common HTML entities that may not be resolved by XML parser
            // This is necessary because JSDOM's XML parser doesn't load external DTDs
            // Note: We must NOT replace &amp;, &lt;, &gt; as these are core XML entities
            // and replacing them would break the XML structure
            htmlContent = htmlContent
                .replace(/&nbsp;/g, '\u00A0')
                .replace(/&mdash;/g, '\u2014')
                .replace(/&ndash;/g, '\u2013')
                .replace(/&lsquo;/g, '\u2018')
                .replace(/&rsquo;/g, '\u2019')
                .replace(/&ldquo;/g, '\u201C')
                .replace(/&rdquo;/g, '\u201D')
                .replace(/&hellip;/g, '\u2026');

            // Parse HTML with JSDOM
            const dom = new JSDOM(htmlContent, { contentType: 'application/xhtml+xml' });
            const doc = dom.window.document;

            // Get all text content
            const bodyText = doc.body ? doc.body.textContent : doc.documentElement.textContent;
            const normalizedBodyText = normalizeText(bodyText);
            const normalizedSearch = normalizeText(searchText);

            // Check both exact and fuzzy (whitespace-insensitive) match
            const exactMatch = normalizedBodyText.toLowerCase().includes(normalizedSearch.toLowerCase());
            const fuzzyMatch = !exactMatch &&
                normalizedBodyText.replace(/\s+/g, '').toLowerCase().includes(normalizedSearch.replace(/\s+/g, '').toLowerCase());

            if (exactMatch || fuzzyMatch) {
                // Try exact match first
                let range = exactMatch ? findTextInDocument(doc, searchText, false) : null;

                // If exact match failed, try fuzzy
                if (!range) {
                    range = findTextInDocument(doc, searchText, true);
                }

                if (range) {
                    // Generate base CFI for this spine position
                    // Format: /6/SPINE where SPINE = (index + 1) * 2
                    const baseCfi = `/6/${(i + 1) * 2}`;

                    // Create CFI from range
                    const cfi = new EpubCFI(range, baseCfi);
                    const cfiString = cfi.toString();

                    results.push({
                        cfi: cfiString,
                        spineIndex: i,
                        spineId: spineItem.id,
                        href: spineItem.href,
                        foundText: range.toString().substring(0, 100)
                    });

                    foundMatch = true;

                    if (!options.findAll) {
                        break; // Stop after first match unless findAll is true
                    }
                }
            }
        } catch (error) {
            console.error(`Error processing spine item ${i}:`, error.message);
        }
    }

    if (!foundMatch) {
        return null;
    }

    return options.findAll ? results : results[0];
}

/**
 * Process multiple search texts in batch
 */
async function generateCFIBatch(epubPath, searchTexts, options = {}) {
    // Parse EPUB once
    const { zip, spine } = await parseEpub(epubPath);
    const results = [];

    // Track last match position to handle duplicate text
    let lastSpineIndex = 0;
    let lastTextOffset = 0;

    // Search for each text
    for (const searchText of searchTexts) {
        let foundMatch = false;

        // Search through all spine items, starting from last match position
        for (let i = lastSpineIndex; i < spine.length; i++) {
            const spineItem = spine[i];

            try {
                // Load the HTML content
                let htmlContent = await zip.file(spineItem.href).async('string');

                htmlContent = htmlContent
                    .replace(/&nbsp;/g, '\u00A0')
                    .replace(/&mdash;/g, '\u2014')
                    .replace(/&ndash;/g, '\u2013')
                    .replace(/&lsquo;/g, '\u2018')
                    .replace(/&rsquo;/g, '\u2019')
                    .replace(/&ldquo;/g, '\u201C')
                    .replace(/&rdquo;/g, '\u201D')
                    .replace(/&hellip;/g, '\u2026');

                const dom = new JSDOM(htmlContent, { contentType: 'application/xhtml+xml' });
                const doc = dom.window.document;

                const bodyText = doc.body ? doc.body.textContent : doc.documentElement.textContent;
                const normalizedBodyText = normalizeText(bodyText);
                const normalizedSearch = normalizeText(searchText);

                const exactMatch = normalizedBodyText.toLowerCase().includes(normalizedSearch.toLowerCase());
                const fuzzyMatch = !exactMatch &&
                    normalizedBodyText.replace(/\s+/g, '').toLowerCase().includes(normalizedSearch.replace(/\s+/g, '').toLowerCase());

                if (exactMatch || fuzzyMatch) {
                    // Calculate skip offset: skip all text from previous spine items plus offset in current item
                    const skipChars = (i === lastSpineIndex) ? lastTextOffset : 0;

                    let range = exactMatch ? findTextInDocument(doc, searchText, false, skipChars) : null;
                    if (!range) {
                        range = findTextInDocument(doc, searchText, true, skipChars);
                    }

                    if (range) {
                        const baseCfi = `/6/${(i + 1) * 2}`;
                        const cfi = new EpubCFI(range, baseCfi);
                        const cfiString = cfi.toString();

                        results.push({ cfi: cfiString, searchText });
                        foundMatch = true;

                        // Update last match position for next search
                        lastSpineIndex = i;

                        // Calculate end position in normalized text space
                        // This must match the accumulated text in findTextInDocument
                        const walker = doc.createTreeWalker(
                            doc.body || doc.documentElement,
                            4, // NodeFilter.SHOW_TEXT
                            null
                        );

                        let accumulatedText = '';
                        let node;
                        let foundEnd = false;

                        while ((node = walker.nextNode())) {
                            const nodeText = node.textContent;
                            if (nodeText.trim().length === 0) continue;

                            const normalizedNodeText = normalizeText(nodeText);

                            if (node === range.endContainer) {
                                // Found the end container - add partial text up to endOffset
                                // Map the endOffset in original text to normalized text
                                const partialOriginal = nodeText.substring(0, range.endOffset);
                                const partialNormalized = normalizeText(partialOriginal);
                                if (accumulatedText.length > 0) {
                                    accumulatedText += ' ';
                                }
                                accumulatedText += partialNormalized;
                                foundEnd = true;
                                break;
                            } else {
                                // Add the full normalized text of this node
                                if (accumulatedText.length > 0) {
                                    accumulatedText += ' ';
                                }
                                accumulatedText += normalizedNodeText;
                            }
                        }

                        lastTextOffset = accumulatedText.length;

                        break;
                    }
                }
            } catch (error) {
                // Continue to next spine item
            }
        }

        if (!foundMatch) {
            results.push({ cfi: null, searchText, error: 'Text not found' });
            // Don't update position tracking if we didn't find a match
        }
    }

    return results;
}

/**
 * Main CLI handler
 */
async function main() {
    const args = process.argv.slice(2);

    if (args.length < 2) {
        console.error('Usage: node epub-cfi-generator.js <epub_file> <search_text|batch_file> [--output json] [--find-all] [--batch]');
        console.error('');
        console.error('Options:');
        console.error('  --output json    Output results as JSON');
        console.error('  --find-all       Find all occurrences (default: first only)');
        console.error('  --batch          Second argument is a JSON file with array of search texts');
        process.exit(1);
    }

    const epubPath = args[0];
    const searchTextOrFile = args[1];
    const outputJson = args.includes('--output') && args[args.indexOf('--output') + 1] === 'json';
    const findAll = args.includes('--find-all');
    const batchMode = args.includes('--batch');

    try {
        if (batchMode) {
            // Batch mode: searchTextOrFile is JSON string with array of texts
            const searchTexts = JSON.parse(searchTextOrFile);
            const results = await generateCFIBatch(epubPath, searchTexts);
            console.log(JSON.stringify(results));
        } else {
            // Single mode
            const searchText = searchTextOrFile;
            const result = await generateCFI(epubPath, searchText, { findAll });

            if (!result) {
                if (outputJson) {
                    console.log(JSON.stringify({ error: 'Text not found in EPUB' }));
                } else {
                    console.error('Error: Text not found in EPUB');
                }
                process.exit(1);
            }

            if (outputJson) {
                console.log(JSON.stringify(result, null, 2));
            } else {
                if (findAll) {
                    result.forEach((r, i) => {
                        console.log(`Match ${i + 1}:`);
                        console.log(`  CFI: ${r.cfi}`);
                        console.log(`  Spine: ${r.spineIndex} (${r.spineId})`);
                        console.log(`  Text: ${r.foundText}...`);
                        console.log('');
                    });
                } else {
                    console.log(result.cfi);
                }
            }
        }
    } catch (error) {
        if (outputJson || batchMode) {
            console.log(JSON.stringify({ error: error.message }));
        } else {
            console.error('Error:', error.message);
        }
        process.exit(1);
    }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

export { generateCFI, generateCFIBatch, findTextInDocument, normalizeText };
