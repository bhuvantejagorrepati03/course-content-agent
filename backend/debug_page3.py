"""Show pages around page 45 (where Data Structures likely is, per TOC)."""
import sys
sys.path.insert(0, ".")
import pymupdf
from app.utils.text_cleaner import clean_text
import re

path = "data/uploads/4537971a326d184f.pdf"
doc = pymupdf.open(path)
print(f"Total pages: {len(doc)}")

# Find all pages with structural keywords AND course codes
_struct = re.compile(r"L\s+T\s+P\s+C|MODULE|UNIT\s+\d|COURSE\s+OUTCOME|TEXT\s*BOOK|PRE.REQUISITE", re.IGNORECASE)
_code = re.compile(r"([A-Z]{2,4}\d{3,5}[A-Z]?)")

found = []
for i in range(len(doc)):
    t = clean_text(doc[i].get_text("text"))
    has_struct = bool(_struct.search(t))
    codes = [m.group(1) for m in _code.finditer(t) if len(m.group(1)) >= 5]
    if has_struct or codes:
        found.append((i+1, has_struct, codes[:3]))

print(f"\nPages with structural markers OR course codes: {len(found)}")
print("First 30:")
for p, s, c in found[:30]:
    print(f"  page={p:3d}  struct={s}  codes={c}")

# Show a page that has structural markers + a real code
for p, s, c in found:
    if s and c:
        print(f"\n=== DETAIL PAGE {p} ===")
        print(repr(clean_text(doc[p-1].get_text("text"))[:500]))
        break

doc.close()
