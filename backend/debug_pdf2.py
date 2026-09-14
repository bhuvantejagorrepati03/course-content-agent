"""Check regulation detection and course block structure."""
import sys, re
sys.path.insert(0, ".")
import pymupdf
from app.utils.text_cleaner import clean_text

path = "data/uploads/4537971a326d184f.pdf"
doc = pymupdf.open(path)

# Get first 10 pages text
text_pages = []
for i in range(min(10, doc.page_count)):
    t = doc[i].get_text("text")
    text_pages.append((i+1, t))
doc.close()

full_raw = "\n".join(t for _, t in text_pages)
full_clean = clean_text(full_raw)

print("=== Raw first 500 chars ===")
print(repr(full_raw[:500]))
print("\n=== Clean first 500 chars ===")
print(repr(full_clean[:500]))

# Test all regulation patterns
patterns = [
    re.compile(r"\bR[-\s]?(\d{2,4})\b", re.IGNORECASE),
    re.compile(r"Regulation\s*[:=-]?\s*R?(\d{2,4})", re.IGNORECASE),
    re.compile(r"R\s?22", re.IGNORECASE),
]
print("\n=== Regulation pattern matches in first 5000 chars ===")
sample = full_clean[:5000]
for p in patterns:
    m = p.search(sample)
    if m:
        print(f"  MATCH: '{m.group(0)}' at pos {m.start()}")

# Show context around "R22" mentions
for m in re.finditer(r"R\s?2\s?2", full_clean[:5000], re.IGNORECASE):
    start = max(0, m.start()-30)
    end = min(len(full_clean), m.end()+30)
    print(f"  Context: ...{repr(full_clean[start:end])}...")

# Course code detection
print("\n=== Course codes in first 50 pages ===")
all_text = "\n".join(t for _, t in text_pages)
codes = re.findall(r"\b(22[A-Z]{2,4}\d{3}[A-Z]?)\b", all_text, re.IGNORECASE)
print(f"Found {len(codes)} course code mentions: {sorted(set(codes))[:20]}")
