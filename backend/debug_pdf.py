"""Debug: extract first 5000 chars of the R22 PDF to understand its structure."""
import sys, pathlib
sys.path.insert(0, ".")

import pymupdf

path = "data/uploads/4537971a326d184f.pdf"
doc = pymupdf.open(path)
print(f"Pages: {doc.page_count}")
print("="*60)
# Print pages 1-3 text
for i in range(min(3, doc.page_count)):
    page = doc[i]
    text = page.get_text("text")
    print(f"\n--- PAGE {i+1} ---")
    print(text[:2000])
doc.close()
