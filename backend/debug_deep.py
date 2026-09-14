"""
Deep inspection: show full text of pages 13-22 to understand exact page structure
for the R22 VFSTR curriculum PDF.
"""
import sys, re
sys.path.insert(0, ".")
import pymupdf
from app.utils.text_cleaner import clean_text

path = "data/uploads/4537971a326d184f.pdf"
doc = pymupdf.open(path)

# Show full text of pages 13-23 (first few course detail pages)
for pg in range(12, 25):   # 0-indexed, so pages 13-26
    if pg >= len(doc):
        break
    raw = doc[pg].get_text("text")
    cleaned = clean_text(raw)
    print(f"\n{'='*70}")
    print(f"RAW PAGE {pg+1}:")
    print(repr(raw[:800]))

doc.close()
