"""
Parse-only test — reads the PDF directly, no DB writes, no ChromaDB.
Verifies units/topics/COs for 4 target courses.
"""
import sys
sys.path.insert(0, ".")

import pymupdf
from app.services.curriculum_parser import _pages_to_course_blocks, _parse_one_course

PDF = "data/uploads/4537971a326d184f.pdf"
TARGETS = {"22MT103", "22PY105", "22TP201", "22CS201"}

doc = pymupdf.open(PDF)
pages = [(i+1, doc[i].get_text("text")) for i in range(len(doc))]
doc.close()

blocks = _pages_to_course_blocks(pages)
print(f"Total blocks: {len(blocks)}\n")

for block_text, src_pages in blocks:
    course = _parse_one_course(block_text, "R22", "B.Tech", "CSE", "Computer Science and Engineering", src_pages)
    if course and course.course_code in TARGETS:
        total_topics = sum(len(u.topics) for u in course.units)
        print(f"{'='*55}")
        print(f"CODE:     {course.course_code}")
        print(f"TITLE:    {course.course_name}")
        print(f"PAGES:    {src_pages}")
        print(f"UNITS:    {len(course.units)}")
        print(f"TOPICS:   {total_topics}")
        print(f"COs:      {len(course.outcomes)}")
        print(f"MAPPINGS: {len(course.mappings)}")
        for u in course.units:
            topics_preview = [t.name[:45] for t in u.topics[:3]]
            print(f"  Unit {u.number} '{u.name[:40]}' [{u.hours}h, {len(u.topics)} topics]")
            for tp in topics_preview:
                print(f"    • {tp}")
        for co in course.outcomes:
            print(f"  {co.co_number}: {co.description[:60]} [{co.bloom_level}]")
        print()
