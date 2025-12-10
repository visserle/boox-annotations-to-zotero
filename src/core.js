/**
 * Utility functions for EpubCFI
 */

/**
 * Extend an object with properties from another object
 * @param {Object} target - Object to extend
 * @param {Object} source - Source object
 * @returns {Object} Extended object
 */
export function extend(target, source) {
    for (let prop in source) {
        if (source.hasOwnProperty(prop)) {
            target[prop] = source[prop];
        }
    }
    return target;
}

/**
 * Get the type of an object
 * @param {*} obj - Object to check
 * @returns {string} Type name
 */
export function type(obj) {
    return Object.prototype.toString.call(obj).slice(8, -1);
}

/**
 * Find all element children of a node
 * @param {Node} node - Parent node
 * @returns {Array} Array of element children
 */
export function findChildren(node) {
    const children = [];
    if (!node || !node.childNodes) return children;

    for (let i = 0; i < node.childNodes.length; i++) {
        const child = node.childNodes[i];
        if (child.nodeType === 1) { // ELEMENT_NODE
            children.push(child);
        }
    }
    return children;
}

/**
 * Check if a value is a number
 * @param {*} n - Value to check
 * @returns {boolean} True if number
 */
export function isNumber(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
}

/**
 * Minimal Range object implementation for environments without native Range
 * @class
 */
export class RangeObject {
    constructor() {
        this.startContainer = null;
        this.startOffset = 0;
        this.endContainer = null;
        this.endOffset = 0;
        this.collapsed = true;
        this.commonAncestorContainer = null;
    }

    setStart(node, offset) {
        this.startContainer = node;
        this.startOffset = offset;
        this._updateCollapsed();
    }

    setEnd(node, offset) {
        this.endContainer = node;
        this.endOffset = offset;
        this._updateCollapsed();
    }

    _updateCollapsed() {
        this.collapsed = (
            this.startContainer === this.endContainer &&
            this.startOffset === this.endOffset
        );
    }

    toString() {
        if (!this.startContainer) return '';

        if (this.collapsed) {
            return '';
        }

        // Simple implementation - extract text content
        // This is a simplified version and may not handle all cases
        if (this.startContainer === this.endContainer) {
            if (this.startContainer.nodeType === 3) { // TEXT_NODE
                return this.startContainer.textContent.substring(
                    this.startOffset,
                    this.endOffset
                );
            }
        }

        return '';
    }
}
