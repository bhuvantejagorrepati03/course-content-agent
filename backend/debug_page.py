"""Debug: show exact text of pages containing course 22CS201."""
import sys
sys.path.insert(0, ".")
import pymupdf

path = "data/uploads/4537971a326d184f.pdf"
doc = pymupdf.open(path)

# Find pages with 22CS201
for i in range(len(doc)):
    text = doc[i].get_text("text")
    if "22CS201" in text or "22TP201" in text:
        print(f"\n{'='*60}")
        print(f"PAGE {i+1}")
        print(repr(text[:600]))
        break

# Also show a few consecutive pages near that area
doc.close()
