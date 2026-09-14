"""Debug why units are 0 - trace the unit parsing for 22MT103."""
import sys, re
sys.path.insert(0, ".")
import pymupdf
from app.services.curriculum_parser import (
    _pages_to_course_blocks, _parse_one_course, _strip_page_header,
    _UNIT_RE, _MODULE_RE, _CODE_RE, _LTPC_RE
)
from app.utils.text_cleaner import clean_text

path = "data/uploads/4537971a326d184f.pdf"
doc = pymupdf.open(path)
pages = [(i+1, doc[i].get_text("text")) for i in range(len(doc))]
doc.close()

blocks = _pages_to_course_blocks(pages)
print(f"Total blocks: {len(blocks)}")

# Find the 22MT103 block
target = None
for block_text, src_pages in blocks:
    m = _CODE_RE.search(block_text[:200])
    if m and m.group(1).upper() == "22MT103":
        target = (block_text, src_pages)
        break

if not target:
    print("22MT103 block not found!")
    sys.exit(1)

block_text, src_pages = target
print(f"\n22MT103 block spans pages: {src_pages}")
print(f"Block text length: {len(block_text)} chars")
print("\n--- First 1500 chars of merged block ---")
print(repr(block_text[:1500]))

print("\n--- Line-by-line scan for UNIT/MODULE hits ---")
lines = block_text.splitlines()
for i, line in enumerate(lines):
    stripped = line.strip()
    if not stripped:
        continue
    if _UNIT_RE.match(stripped):
        print(f"  LINE {i:3d} UNIT_RE MATCH: {repr(stripped[:80])}")
    if _MODULE_RE.match(stripped):
        print(f"  LINE {i:3d} MODULE_RE MATCH: {repr(stripped[:80])}")
    if "UNIT" in stripped.upper()[:10]:
        print(f"  LINE {i:3d} UNIT appears: {repr(stripped[:80])}")
