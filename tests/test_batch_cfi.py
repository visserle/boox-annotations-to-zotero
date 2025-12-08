"""Test batch CFI generation performance."""

import time
from pathlib import Path
from src.cfi_generator_js import create_epub_cfi_js, create_epub_cfi_batch_js

# Test file
EPUB_PATH = (
    Path(__file__).parent.parent
    / "examples"
    / "Shakespeare - 1998 - Romeo and Juliet.epub"
)

# Sample annotations
TEST_TEXTS = [
    "THE TRAGEDY OF ROMEO AND JULIET",
    "MERCUTIO.Men's eyes were made to look, and let them gaze.",
    "Enter LADY CAPULET.",
    "Romeo, Romeo, Romeo, here's drink! I drink to thee.",
    "Ay, you have been a mouse-hunt in your time;",
]


def test_individual_calls():
    """Test individual CFI generation (old method)."""
    print("\n" + "=" * 80)
    print("Testing INDIVIDUAL CFI generation (old method)")
    print("=" * 80)

    start = time.time()
    results = []
    for text in TEST_TEXTS:
        cfi = create_epub_cfi_js(EPUB_PATH, text)
        results.append(cfi)
    elapsed = time.time() - start

    print(f"Generated {len(results)} CFIs in {elapsed:.2f}s")
    print(f"Average: {elapsed / len(results):.2f}s per CFI")
    print(f"Success: {sum(1 for r in results if r)} / {len(results)}")

    return elapsed, results


def test_batch_calls():
    """Test batch CFI generation (new method)."""
    print("\n" + "=" * 80)
    print("Testing BATCH CFI generation (new method)")
    print("=" * 80)

    start = time.time()
    results = create_epub_cfi_batch_js(EPUB_PATH, TEST_TEXTS)
    elapsed = time.time() - start

    print(f"Generated {len(results)} CFIs in {elapsed:.2f}s")
    print(f"Average: {elapsed / len(results):.2f}s per CFI")
    print(f"Success: {sum(1 for r in results if r)} / {len(results)}")

    return elapsed, results


def main():
    print("\n" + "=" * 80)
    print("BATCH CFI GENERATION PERFORMANCE TEST")
    print("=" * 80)
    print(f"EPUB: {EPUB_PATH.name}")
    print(f"Annotations: {len(TEST_TEXTS)}")

    # Test individual calls
    time_individual, results_individual = test_individual_calls()

    # Test batch calls
    time_batch, results_batch = test_batch_calls()

    # Compare results
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"Individual: {time_individual:.2f}s")
    print(f"Batch:      {time_batch:.2f}s")
    print(f"Speedup:    {time_individual / time_batch:.1f}x faster")

    # Verify results match
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    matches = sum(1 for i, b in zip(results_individual, results_batch) if i == b)
    print(f"Results match: {matches}/{len(TEST_TEXTS)}")

    if matches == len(TEST_TEXTS):
        print("✓ All CFIs match between individual and batch mode")
    else:
        print("✗ Mismatch detected!")
        for i, (ind, bat) in enumerate(zip(results_individual, results_batch)):
            if ind != bat:
                print(f"  Text {i + 1}: Individual={ind}, Batch={bat}")

    print("\n" + "=" * 80)
    print(f"🎉 Batch mode is {time_individual / time_batch:.1f}x faster!")
    print("=" * 80)


if __name__ == "__main__":
    main()
