"""Debug pages 60-62 for 22CS201."""
import sys
sys.path.insert(0, ".")
import pymupdf
from app.services.curriculum_parser import _pages_to_course_blocks, _strip_page_header
from app.utils.text_cleaner import clean_text

doc = pymupdf.open("data/uploads/4537971a326d184f.pdf")
pages = [(i+1, doc[i].get_text("text")) for i in range(len(doc))]
doc.close()

# Show raw pages 60-62
for pg in [60, 61, 62]:
    raw = pages[pg-1][1]
    print(f"\n=== PAGE {pg} (raw first 600 chars) ===")
    print(repr(raw[:600]))

# Also show what block is built for 22CS201
blocks = _pages_to_course_blocks(pages)
for block_text, src_pages in blocks:
    if 60 in src_pages:
        print(f"\n=== BLOCK containing page 60, src_pages={src_pages} ===")
        print(repr(block_text[:800]))
        break
