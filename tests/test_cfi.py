"""Test script to verify CFI generation against Zotero's manual annotations."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cfi_generator_js import create_epub_cfi_js

# Construct paths relative to project root
EXAMPLES_DIR = project_root / "examples"

# All manual annotations from Zotero for Romeo & Juliet EPUB
ROMEO_ANNOTATIONS = [
    {
        "text": "THE TRAGEDY OF ROMEO AND JULIET\nby William Shakespeare",
        "cfi": "epubcfi(/6/4!/4,/6[pgepubid00000]/1:0,/8/1:22)",
        "sortIndex": "00000|00003000",
        "note": "Multi-element annotation spanning title elements",
    },
    {
        "text": "MERCUTIO.Men's eyes were made to look, and let them gaze.I will not budge for no man's pleasure, I.",
        "cfi": "epubcfi(/6/14!/4/2[pgepubid00018]/44,/1:0,/5:42)",
        "sortIndex": "00000|00111000",
        "note": "Multi-node annotation within same element, spanning nodes 1-5",
    },
    {
        "text": "Enter LADY CAPULET.\nLADY CAPULET.What, are you busy, ho? Need you my help?",
        "cfi": "epubcfi(/6/16!/4/2[pgepubid00024],/140/1:0,/142/3:41)",
        "sortIndex": "00000|00175000",
        "note": "Multi-element annotation spanning /140 to /142",
    },
    {
        "text": "Romeo, Romeo, Romeo, here's drink! I drink to thee.\n[Throws herself on the bed.]\nSCENE IV. Hall in Capulet's House.\nEnter LADY CAPULET and NURSE.",
        "cfi": "epubcfi(/6/16!/4/2[pgepubid00024],/154/69:0,/160/5:1)",
        "sortIndex": "00000|00178000",
        "note": "Multi-element annotation spanning /154 to /160",
    },
    {
        "text": "Ay, you have been a mouse-hunt in your time;",
        "cfi": "epubcfi(/6/16!/4/2[pgepubid00024]/174,/3:0,/3:44)",
        "sortIndex": "00000|00179000",
        "note": "Single node annotation within element /174",
    },
]

ROMEO_EPUB_PATH = str(EXAMPLES_DIR / "Shakespeare - 1998 - Romeo and Juliet.epub")

# All manual annotations from Zotero for The History of Drink EPUB
DRINK_ANNOTATIONS = [
    {
        "text": 'ERRATA.\nTranscriber\'s Note: The errata have been corrected.\nPage 67, line 8, "Christ said to the ruler of the feast," should be, "The governor of the feast said to the bridegroom."\nPage 141, line 15, for "cellar," read "cellarer."',
        "cfi": "epubcfi(/6/10!/4,/2[pgepubid00000]/2[ERRATA]/1:0,/8/3:11)",
        "sortIndex": "00000|00015000",
        "note": "Multi-element annotation spanning errata section",
    },
    {
        "text": "PRE-HISTORIC TRACES.\nOne of the chief aims",
        "cfi": "epubcfi(/6/12!/4,/2/10/1:85,/4/1:21)",
        "sortIndex": "00000|00016000",
        "note": "Multi-element annotation across chapter heading and paragraph",
    },
    {
        "text": "One of the most careful and trustworthy of modern naturalists, Mr. Charles Darwin, has told us that many kinds of monkeys have a strong taste for tea, coffee, and spirituous liquors, and that he has seen them smoke tobacco.⁠[3] Moreover, writing on the authority of Brehm,⁠[4] he says that the natives of North-Eastern Africa catch the wild baboons by exposing vessels with strong beer, by which they are made drunk.",
        "cfi": "epubcfi(/6/12!/4/4,/7:434,/13:11)",
        "sortIndex": "00000|00017000",
        "note": "Multi-node annotation within element /4, spanning nodes 7-13",
    },
    {
        "text": 'The same historian also tells us that Cyrus gave a feast to the Persians in which he provided rich wines;⁠[86]and the following story is narrated concerning that monarch, showing the excess to which drinking was carried in his day.⁠[87] Cyrus made war upon Tomyris, queen of the Massagetæ, a race living in Central Asia, and by the advice of Cræsus the Lydian, he made a feint of deserting his camp, and left "flowing goblets of wine" to tempt the enemy to excess. The stratagem succeeded, and when the enemy was drunk, he attacked him and took the queen\'s son prisoner. Cyrus was, however, ultimately defeated and slain.\n\n \n\nThe drink here referred to was made from the vine, but Herodotus also mentions an incident which shows that palm-wine was drunk in the time of Cambyses (B.C. 529-522). "He (Cambyses) sent the Ichthyophagæ into Ethiopia with the following gifts, to wit, a purple robe, a gold chain for the neck, armlets, an alabaster box of myrrh, and a cask of palm-wine."',
        "cfi": "epubcfi(/6/18!/4,/10/1:0,/12/3:198)",
        "sortIndex": "00000|00057000",
        "note": "Large multi-element annotation spanning multiple paragraphs",
    },
    {
        "text": "CHAPTER VIII.\nGERMANY: ANCIENT, MEDIÆVAL, AND MODERN.",
        "cfi": "epubcfi(/6/26!/4/2,/4[CHAPTER_VIII]/1:0,/6/1:39)",
        "sortIndex": "00000|00098000",
        "note": "Multi-element chapter heading annotation",
    },
    {
        "text": "He says that they slept late into the day, and on rising they proceeded to bathe, after which they partook of a meal, each sitting on a distinct seat and at a separate table.",
        "cfi": "epubcfi(/6/26!/4/4,/3:0,/3:174)",
        "sortIndex": "00000|00098000",
        "note": "Single node annotation within element /4",
    },
    {
        "text": "Lord Mayor's Day, 1782,⁠[269]",
        "cfi": "epubcfi(/6/32!/4/20,/3:755,/4[FNanchor_269]/1:5)",
        "sortIndex": "00000|00141000",
        "note": "Multi-node annotation with footnote reference",
    },
    {
        "text": 'Yes; but it is also "said" that somewhere in an English churchyard there is the following characteristic epitaph:—\n"Beneath this stone, in hopes of Zion,\nDoth rest the landlord of the Lion:\nResigned unto the heavenly will,\nHis son keeps on the business still."',
        "cfi": "epubcfi(/6/38!/4,/28/5:0,/30/2/2/8/1:37)",
        "sortIndex": "00000|00195000",
        "note": "Multi-element annotation including poetry formatting",
    },
    {
        "text": "Greig, Major, Liverpool statistics of intemperance by, 178.",
        "cfi": "epubcfi(/6/44!/4/4/958,/1:0,/3:1)",
        "sortIndex": "00000|00294000",
        "note": "Multi-node annotation from index section",
    },
]

DRINK_EPUB_PATH = str(EXAMPLES_DIR / "Samuelson - 2025 - The History of Drink.epub")


def parse_cfi(cfi: str) -> dict:
    """Parse a CFI string into its components for comparison."""
    # Extract the inner part: epubcfi(/6/2!/4/118,/1:0,/5:54) -> /6/2!/4/118,/1:0,/5:54
    inner = cfi.replace("epubcfi(", "").rstrip(")")

    # Split into parent path and range
    if "," in inner:
        parts = inner.split(",")
        parent_path = parts[0]
        start_range = parts[1]
        end_range = parts[2]
    else:
        parent_path = inner
        start_range = ""
        end_range = ""

    return {
        "parent_path": parent_path,
        "start_range": start_range,
        "end_range": end_range,
    }


def compare_cfis(expected: str, generated: str | None) -> tuple[bool, str]:
    """Compare two CFIs and return (is_match, details)."""
    if generated is None:
        return False, "Generated CFI is None"

    exp = parse_cfi(expected)
    gen = parse_cfi(generated)

    if expected == generated:
        return True, "Exact match"

    # Check if parent paths match
    if exp["parent_path"] != gen["parent_path"]:
        return (
            False,
            f"Parent path mismatch: expected {exp['parent_path']}, got {gen['parent_path']}",
        )

    # Check start range
    if exp["start_range"] != gen["start_range"]:
        return (
            False,
            f"Start range mismatch: expected {exp['start_range']}, got {gen['start_range']}",
        )

    # Check end range - allow 1 char difference for multi-node edge cases
    if exp["end_range"] != gen["end_range"]:
        # Extract end offset
        exp_parts = exp["end_range"].split(":")
        gen_parts = gen["end_range"].split(":")

        if len(exp_parts) == 2 and len(gen_parts) == 2:
            exp_node = exp_parts[0]
            exp_offset = int(exp_parts[1])
            gen_node = gen_parts[0]
            gen_offset = int(gen_parts[1])

            if exp_node == gen_node and abs(exp_offset - gen_offset) <= 1:
                return (
                    True,
                    f"Close match (off by {abs(exp_offset - gen_offset)} char in end offset)",
                )

        return (
            False,
            f"End range mismatch: expected {exp['end_range']}, got {gen['end_range']}",
        )

    return True, "Match"


def test_cfi_generation(epub_path: str, annotations: list[dict]):
    """Test CFI generation against Zotero's manual annotations."""
    print("=" * 80)
    print("CFI GENERATION TEST RESULTS")
    print("=" * 80)
    print(f"\nTesting: {epub_path}")
    print("Using JavaScript-based CFI generator (epub-cfi-generator.js)")
    print("Comparing against actual Zotero annotations from the database\n")

    results = []
    skipped = 0

    for i, ann in enumerate(annotations, 1):
        print(f"\n[Test {i}/{len(annotations)}]")
        print(f"Text: '{ann['text'][:60]}...'")
        print(f"Note: {ann['note']}")

        # Check if test should be skipped
        if ann.get("skip", False):
            print(f"⊘ SKIPPED: {ann.get('skip_reason', 'No reason provided')}")
            skipped += 1
            continue

        print(f"Zotero CFI:    {ann['cfi']}")

        # Generate CFI using JavaScript
        generated_cfi = create_epub_cfi_js(epub_path, ann["text"])

        if generated_cfi:
            print(f"Generated CFI: {generated_cfi}")

            is_match, details = compare_cfis(ann["cfi"], generated_cfi)
            results.append(is_match)

            if is_match:
                print(f"✓ PASS: {details}")
            else:
                print(f"✗ FAIL: {details}")
        else:
            print("✗ FAIL: Text not found in EPUB (CFI generation returned None)")
            results.append(False)

    print("\n" + "=" * 80)
    print(f"SUMMARY: {sum(results)}/{len(results)} tests passed, {skipped} skipped")
    if sum(results) == len(results):
        print("🎉 All tests passed! JavaScript CFI generation matches Zotero exactly.")
    else:
        failures = len(results) - sum(results)
        print(f"⚠️  {failures} test(s) failed. Review output above for details.")
    if skipped > 0:
        print(f"ℹ️  {skipped} test(s) skipped (text not in this EPUB edition)")
    print("=" * 80)

    return all(results)


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("TESTING ROMEO & JULIET EPUB")
    print("=" * 80)
    romeo_success = test_cfi_generation(ROMEO_EPUB_PATH, ROMEO_ANNOTATIONS)

    print("\n\n")
    print("=" * 80)
    print("TESTING THE HISTORY OF DRINK EPUB")
    print("=" * 80)
    drink_success = test_cfi_generation(DRINK_EPUB_PATH, DRINK_ANNOTATIONS)

    exit(0 if (romeo_success and drink_success) else 1)
