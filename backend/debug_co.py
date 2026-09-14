"""Debug CO parsing for 22CS201."""
import sys
sys.path.insert(0, ".")
import pymupdf
from app.services.curriculum_parser import (
    _pages_to_course_blocks, _CO_HDR_RE, _TEXT_RE, _REF_RE, _BLOOM_RE, _PO_RE, _parse_cos
)

doc = pymupdf.open("data/uploads/4537971a326d184f.pdf")
pages = [(i+1, doc[i].get_text("text")) for i in range(len(doc))]
doc.close()

blocks = _pages_to_course_blocks(pages)
target_block = None
for bt, sp in blocks:
    if 60 in sp:
        target_block = bt
        break

# Simulate the section scan to capture co_lines
import re
lines = target_block.splitlines()
co_lines = []
section = "header"
for raw_line in lines:
    line = raw_line.strip()
    if not line:
        continue
    if _CO_HDR_RE.search(line):
        section = "cos"
        continue
    if _TEXT_RE.search(line) or _REF_RE.search(line):
        if section == "cos":
            section = "books"
            break
        continue
    if section == "cos":
        co_lines.append(line)

print(f"co_lines collected: {len(co_lines)}")
for i, l in enumerate(co_lines):
    print(f"  [{i:2d}] {repr(l[:80])}")

# Now test _parse_cos directly
from app.services.curriculum_parser import ParsedCourse
c = ParsedCourse(course_code="22CS201", course_name="DBMS")
_parse_cos(co_lines, c)
print(f"\nOutcomes parsed: {len(c.outcomes)}")
for co in c.outcomes:
    print(f"  {co.co_number}: {co.description[:60]} [{co.bloom_level}] POs={co.po_mapping}")
