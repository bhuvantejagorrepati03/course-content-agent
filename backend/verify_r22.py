"""
READ-ONLY verification of the R22 curriculum import.
No DB changes, no reprocessing, no ChromaDB writes.
"""
import sys, asyncio
sys.path.insert(0, ".")

import httpx
from app.database import SessionLocal
from app.models.course import Course
from app.models.unit import Unit
from app.models.topic import Topic
from app.models.outcome import CourseOutcome
from app.models.textbook import Textbook
from app.models.mapping import COPOMapping
from app.models.document import SyllabusDocument

BASE = "http://127.0.0.1:8000"

db = SessionLocal()

SEP = "=" * 70

def section(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

# ── 1. Overall DB state ───────────────────────────────────────────────────────
section("1. OVERALL DATABASE STATE")

all_courses = db.query(Course).order_by(Course.regulation, Course.course_code).all()
regs = sorted(set(c.regulation for c in all_courses))
print(f"Total courses in DB: {len(all_courses)}")
print(f"Regulations present: {regs}")
print(f"Source types: { {st: sum(1 for c in all_courses if c.source_type==st) for st in ['seed','imported']} }")
print(f"\nR22 courses: {sum(1 for c in all_courses if c.regulation=='R22')}")
print(f"R23 courses: {sum(1 for c in all_courses if c.regulation=='R23')}")

# ── 2. Check R23 still coexists ───────────────────────────────────────────────
section("2. R23 COEXISTENCE CHECK (additive behavior)")
r23 = db.query(Course).filter(Course.regulation == "R23").all()
if r23:
    print(f"✓  R23 courses still present ({len(r23)}): {[c.course_code for c in r23]}")
else:
    print("✗  WARNING: R23 courses missing!")

# ── 3. Specific course verification ──────────────────────────────────────────
TARGET_CODES = [
    "22MT103", "22PY105", "22CT103",
    "22TP201", "22CS201", "22CS203", "22CS207",
]

section("3. COURSE-BY-COURSE VERIFICATION")

problems = []

for code in TARGET_CODES:
    course = db.query(Course).filter(
        Course.course_code == code,
        Course.regulation == "R22",
    ).first()

    print(f"\n{'─'*60}")
    if not course:
        print(f"  ✗  {code}: NOT FOUND IN DATABASE")
        problems.append(f"{code}: missing")
        continue

    units = db.query(Unit).filter(Unit.course_id == course.id).order_by(Unit.unit_number).all()
    total_topics = sum(
        db.query(Topic).filter(Topic.unit_id == u.id).count() for u in units
    )
    outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == course.id).all()
    textbooks = db.query(Textbook).filter(
        Textbook.course_id == course.id, Textbook.book_type == "textbook"
    ).all()
    refs = db.query(Textbook).filter(
        Textbook.course_id == course.id, Textbook.book_type == "reference"
    ).all()
    mappings = db.query(COPOMapping).filter(COPOMapping.course_id == course.id).all()
    doc = db.query(SyllabusDocument).filter(SyllabusDocument.id == course.documents[0].id).first() \
        if course.documents else None

    print(f"  COURSE:      {course.course_name}")
    print(f"  CODE:        {course.course_code}")
    print(f"  REGULATION:  {course.regulation}")
    print(f"  PROGRAMME:   {course.program}")
    print(f"  BRANCH:      {course.branch}")
    print(f"  SEMESTER:    {course.semester}")
    print(f"  L/T/P/C:     {course.l_hours}/{course.t_hours}/{course.p_hours}/{course.credits}")
    print(f"  TOTAL HRS:   {course.total_hours}")
    print(f"  SOURCE TYPE: {course.source_type}")

    prereqs = [p.strip() for p in (course.prerequisites or "").split(",") if p.strip()]
    print(f"  PREREQUISITES ({len(prereqs)}): {prereqs[:3]}{'...' if len(prereqs)>3 else ''}")

    obj_snip = (course.description or "")[:120]
    print(f"  DESCRIPTION:  {obj_snip}{'...' if len(course.description or '')>120 else ''}")

    print(f"\n  UNITS ({len(units)}):")
    for u in units:
        topics = db.query(Topic).filter(Topic.unit_id == u.id).order_by(Topic.topic_order).all()
        print(f"    Unit {u.unit_number}: {u.unit_name[:55]}  [{u.hours}h, {len(topics)} topics]")
        for t in topics[:4]:
            print(f"      • {t.topic_name[:70]}")
        if len(topics) > 4:
            print(f"      ... +{len(topics)-4} more")

    print(f"\n  COURSE OUTCOMES ({len(outcomes)}):")
    for co in outcomes:
        print(f"    {co.co_number}: {co.description[:70]} [{co.bloom_level}]")

    print(f"\n  TEXTBOOKS ({len(textbooks)}):")
    for b in textbooks[:5]:
        print(f"    • {b.title[:60]}  — {b.author[:40]}")
    if len(textbooks) > 5:
        print(f"    ... +{len(textbooks)-5} more")

    print(f"\n  REFERENCE BOOKS ({len(refs)}):")
    for b in refs[:5]:
        print(f"    • {b.title[:60]}  — {b.author[:40]}")
    if len(refs) > 5:
        print(f"    ... +{len(refs)-5} more")

    print(f"\n  CO-PO MAPPINGS ({len(mappings)}):")
    for m in mappings[:8]:
        print(f"    {m.co_number} → {m.po_number} = {m.value}")
    if len(mappings) > 8:
        print(f"    ... +{len(mappings)-8} more")

    src = f"Doc {doc.id}: {doc.original_filename}" if doc else "No document linked"
    print(f"\n  SOURCE: {src}")
    print(f"  SOURCE PAGES: {course.source_pages if hasattr(course, 'source_pages') else 'N/A'}")

    # ── Validation checks ──────────────────────────────────────────────────
    if len(units) == 0:
        problems.append(f"{code}: units=0")
        print(f"  ✗  PROBLEM: no units!")
    else:
        print(f"  ✓  has {len(units)} units")

    if total_topics == 0:
        problems.append(f"{code}: topics=0")
        print(f"  ✗  PROBLEM: no topics!")
    else:
        print(f"  ✓  has {total_topics} topics total")

    if len(outcomes) == 0:
        print(f"  ⚠  no COs (may be OK if PDF section was missing)")
    else:
        print(f"  ✓  has {len(outcomes)} COs")

    if len(textbooks) + len(refs) > 20:
        problems.append(f"{code}: suspicious textbook count={len(textbooks)+len(refs)}")
        print(f"  ✗  PROBLEM: {len(textbooks)+len(refs)} books (may be cross-boundary)")

    if course.regulation != "R22":
        problems.append(f"{code}: wrong regulation={course.regulation}")
        print(f"  ✗  PROBLEM: regulation is {course.regulation}, expected R22")

# ── 4. API verification ───────────────────────────────────────────────────────
section("4. API ENDPOINT VERIFICATION")

try:
    with httpx.Client(timeout=15) as c:
        # /api/regulations
        r = c.get(f"{BASE}/api/regulations")
        if r.status_code == 200:
            regs_api = r.json()["data"]
            codes = [x["code"] for x in regs_api]
            print(f"✓  GET /api/regulations → {codes}")
            if "R22" in codes:
                print(f"   ✓  R22 present in regulations API")
            else:
                problems.append("R22 missing from /api/regulations")
                print(f"   ✗  R22 missing!")
            if "R23" in codes:
                print(f"   ✓  R23 still present (additive confirmed)")
        else:
            print(f"✗  GET /api/regulations → HTTP {r.status_code}")

        # /api/courses?regulation=R22
        r = c.get(f"{BASE}/api/courses?regulation=R22")
        if r.status_code == 200:
            r22_courses = r.json()["data"]
            print(f"\n✓  GET /api/courses?regulation=R22 → {len(r22_courses)} courses")
            for course_data in r22_courses[:8]:
                print(f"   {course_data['course_code']}  {course_data['course_name'][:45]}  "
                      f"[{course_data['regulation']}] units={course_data['unit_count']} "
                      f"topics={course_data['topic_count']} COs={course_data['co_count']}")
            if len(r22_courses) > 8:
                print(f"   ... +{len(r22_courses)-8} more")
        else:
            print(f"✗  /api/courses?regulation=R22 → HTTP {r.status_code}")

        # Spot-check: detail endpoints for key courses
        for code in ["22TP201", "22CS201", "22CS203", "22CS207"]:
            course_obj = db.query(Course).filter(
                Course.course_code == code, Course.regulation == "R22"
            ).first()
            if not course_obj:
                print(f"\n   {code}: not in DB, skipping API check")
                continue
            r = c.get(f"{BASE}/api/courses/{course_obj.id}")
            if r.status_code == 200:
                d = r.json()["data"]
                print(f"\n✓  GET /api/courses/{course_obj.id} ({code})")
                print(f"   units={len(d['units'])}  outcomes={len(d['outcomes'])}  "
                      f"textbooks={len(d['textbooks'])}")
                if d["units"]:
                    u0 = d["units"][0]
                    print(f"   Unit 1: {u0['unit_name'][:50]}  [{u0['hours']}h, "
                          f"{len(u0['topics'])} topics]")
            else:
                print(f"✗  GET /api/courses/{course_obj.id} ({code}) → {r.status_code}")

except Exception as e:
    print(f"⚠  Backend not reachable: {e}. Skipping API checks.")

# ── 5. RAG/AI retrieval check ─────────────────────────────────────────────────
section("5. AI RETRIEVAL CHECK")

# Find course IDs
ds_course = db.query(Course).filter(Course.course_code=="22TP201", Course.regulation=="R22").first()
dbms_course = db.query(Course).filter(Course.course_code=="22CS201", Course.regulation=="R22").first()
os_course = db.query(Course).filter(Course.course_code=="22CS207", Course.regulation=="R22").first()

queries = []
if ds_course:
    queries.append((ds_course.id, "What is Unit 1 of Data Structures under R22?"))
    queries.append((ds_course.id, "What are the course outcomes of R22 Data Structures?"))
if dbms_course:
    queries.append((dbms_course.id, "Which textbook is recommended for R22 DBMS?"))
if os_course:
    queries.append((os_course.id, "What topics are covered in Operating Systems under R22?"))

try:
    with httpx.Client(timeout=90) as c:
        for cid, question in queries:
            payload = {"course_id": cid, "message": question, "history": []}
            r = c.post(f"{BASE}/api/chat", json=payload)
            if r.status_code == 200:
                data = r.json()["data"]
                answer = data["answer"][:250]
                citations = data.get("citations", [])
                print(f"\nQ: {question}")
                print(f"A: {answer}...")
                if citations:
                    for cit in citations[:2]:
                        print(f"   Source: {cit.get('filename','')} | {cit.get('unit','')}")
                    # Verify R22 source
                    src_files = [cit.get("filename","") for cit in citations]
                    if any("R22" in f for f in src_files):
                        print(f"   ✓  Citation references R22 source")
                    else:
                        print(f"   ⚠  Citation source: {src_files}")
            else:
                print(f"\n✗  Chat failed for cid={cid}: HTTP {r.status_code}")
except Exception as e:
    print(f"⚠  Chat API not reachable: {e}")

# ── 6. Summary ────────────────────────────────────────────────────────────────
section("6. VERIFICATION SUMMARY")

all_r22 = db.query(Course).filter(Course.regulation=="R22").all()
all_r23 = db.query(Course).filter(Course.regulation=="R23").all()
total_units_r22 = sum(
    db.query(Unit).filter(Unit.course_id == c.id).count() for c in all_r22
)
total_topics_r22 = 0
for c in all_r22:
    for u in db.query(Unit).filter(Unit.course_id == c.id).all():
        total_topics_r22 += db.query(Topic).filter(Topic.unit_id == u.id).count()
total_cos_r22 = sum(
    db.query(CourseOutcome).filter(CourseOutcome.course_id == c.id).count() for c in all_r22
)
total_books_r22 = sum(
    db.query(Textbook).filter(Textbook.course_id == c.id).count() for c in all_r22
)
total_maps_r22 = sum(
    db.query(COPOMapping).filter(COPOMapping.course_id == c.id).count() for c in all_r22
)

print(f"""
Regulation:           R22
Programme:            B.Tech
Branch:               CSE
Courses imported:     {len(all_r22)}
Units imported:       {total_units_r22}
Topics imported:      {total_topics_r22}
COs imported:         {total_cos_r22}
Textbooks+Refs:       {total_books_r22}
CO-PO mappings:       {total_maps_r22}

R23 courses (coexist): {len(all_r23)}  {[c.course_code for c in all_r23]}

All regulations in DB: {sorted(set(c.regulation for c in db.query(Course).all()))}
""")

if problems:
    print(f"PROBLEMS FOUND ({len(problems)}):")
    for p in problems:
        print(f"  ✗  {p}")
else:
    print("✓  NO PROBLEMS DETECTED")

db.close()
