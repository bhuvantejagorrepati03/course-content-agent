"""
RBAC verification tests.
Tests every permission boundary in the backend.

Run:  .venv\Scripts\python.exe test_rbac.py
"""
import io
import zipfile
import httpx

BASE = "http://127.0.0.1:8000"

PASS = "PASS"
FAIL = "FAIL"
results = {}


def make_pdf() -> bytes:
    return b"%PDF-1.4\nTest syllabus content for RBAC testing"


def make_docx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>RBAC test</w:t></w:r></w:p></w:body></w:document>')
    return buf.getvalue()


def check(label: str, condition: bool):
    status = PASS if condition else FAIL
    results[label] = status
    sym = "✓" if condition else "✗"
    print(f"  {sym}  [{status}]  {label}")
    return condition


print("\n" + "=" * 60)
print("  RBAC Backend Security Tests")
print("=" * 60)

# ── 1. Health ─────────────────────────────────────────────────
print("\n1. Backend health")
with httpx.Client(timeout=10) as c:
    r = c.get(f"{BASE}/health")
    check("Health check returns 200", r.status_code == 200)

# ── 2. List documents — no role required (both roles can read) ─
print("\n2. List documents (no role enforcement — both allowed)")
with httpx.Client(timeout=10) as c:
    # No header → defaults to faculty
    r = c.get(f"{BASE}/api/syllabus")
    check("GET /api/syllabus no header → 200", r.status_code == 200)

    r = c.get(f"{BASE}/api/syllabus", headers={"X-User-Role": "student"})
    check("GET /api/syllabus student → 200", r.status_code == 200)

    r = c.get(f"{BASE}/api/syllabus", headers={"X-User-Role": "faculty"})
    check("GET /api/syllabus faculty → 200", r.status_code == 200)

# ── 3. Upload — faculty allowed, student blocked ──────────────
print("\n3. Upload: faculty ALLOWED, student BLOCKED")
pdf_bytes = make_pdf()
uploaded_id = None

with httpx.Client(timeout=30) as c:
    # Faculty upload — should succeed
    r = c.post(
        f"{BASE}/api/syllabus/upload",
        files={"file": ("rbac_test.pdf", pdf_bytes, "application/pdf")},
        headers={"X-User-Role": "faculty"},
    )
    ok = r.status_code in (200, 202)
    check("Faculty upload PDF → 202 Accepted", ok)
    if ok:
        uploaded_id = r.json().get("data", {}).get("document_id")

    # Student upload — must return 403
    r = c.post(
        f"{BASE}/api/syllabus/upload",
        files={"file": ("student_attempt.pdf", pdf_bytes + b"modified", "application/pdf")},
        headers={"X-User-Role": "student"},
    )
    check("Student upload → 403 Forbidden", r.status_code == 403)
    if r.status_code == 403:
        body = r.json()
        msg = body.get("detail", "")
        check(
            "403 message mentions faculty/permission",
            "faculty" in msg.lower() or "permission" in msg.lower(),
        )

    # No header — defaults to faculty — should succeed (won't be a dup since bytes differ)
    r = c.post(
        f"{BASE}/api/syllabus/upload",
        files={"file": ("no_header.pdf", pdf_bytes + b"no-header-version", "application/pdf")},
        # no X-User-Role header
    )
    check("No role header (defaults to faculty) → 202", r.status_code in (200, 202))
    if r.status_code in (200, 202):
        extra_id = r.json().get("data", {}).get("document_id")
        # clean up immediately
        c.delete(f"{BASE}/api/syllabus/{extra_id}", headers={"X-User-Role": "faculty"})

# ── 4. Delete — faculty allowed, student blocked ──────────────
print("\n4. Delete: faculty ALLOWED, student BLOCKED")
with httpx.Client(timeout=15) as c:
    if uploaded_id:
        # Student delete — must return 403
        r = c.delete(
            f"{BASE}/api/syllabus/{uploaded_id}",
            headers={"X-User-Role": "student"},
        )
        check("Student DELETE → 403 Forbidden", r.status_code == 403)
        if r.status_code == 403:
            msg = r.json().get("detail", "")
            check(
                "403 delete message mentions faculty/permission",
                "faculty" in msg.lower() or "permission" in msg.lower(),
            )

        # Faculty delete — should succeed
        r = c.delete(
            f"{BASE}/api/syllabus/{uploaded_id}",
            headers={"X-User-Role": "faculty"},
        )
        check("Faculty DELETE → 200 OK", r.status_code == 200)
        if r.status_code == 200:
            check("Delete response contains deleted=True", r.json().get("data", {}).get("deleted") is True)
    else:
        print("  (skipped — no upload_id from step 3)")

# ── 5. Chat — both roles can use AI assistant ──────────────────
print("\n5. AI Chat: both roles allowed")
with httpx.Client(timeout=60) as c:
    payload = {"course_id": 1, "message": "What is Unit 1?", "history": []}

    r = c.post(f"{BASE}/api/chat", json=payload, headers={"X-User-Role": "faculty"})
    check("Faculty chat → 200", r.status_code == 200)
    if r.status_code == 200:
        answer = r.json().get("data", {}).get("answer", "")
        check("Faculty chat has non-empty answer", len(answer) > 10)

    r = c.post(f"{BASE}/api/chat", json=payload, headers={"X-User-Role": "student"})
    check("Student chat → 200", r.status_code == 200)
    if r.status_code == 200:
        answer = r.json().get("data", {}).get("answer", "")
        check("Student chat has non-empty answer", len(answer) > 10)

# ── 6. Courses — both roles can read ──────────────────────────
print("\n6. Course endpoints: both roles allowed")
with httpx.Client(timeout=10) as c:
    r = c.get(f"{BASE}/api/courses", headers={"X-User-Role": "student"})
    check("Student GET /api/courses → 200", r.status_code == 200)

    r = c.get(f"{BASE}/api/courses/1", headers={"X-User-Role": "student"})
    check("Student GET /api/courses/1 → 200", r.status_code == 200)

    r = c.get(f"{BASE}/api/courses/1/units", headers={"X-User-Role": "student"})
    check("Student GET /api/courses/1/units → 200", r.status_code == 200)

    r = c.get(f"{BASE}/api/courses/1/outcomes", headers={"X-User-Role": "student"})
    check("Student GET /api/courses/1/outcomes → 200", r.status_code == 200)

    r = c.get(f"{BASE}/api/textbooks?course_id=1", headers={"X-User-Role": "student"})
    check("Student GET /api/textbooks → 200", r.status_code == 200)

    r = c.get(f"{BASE}/api/mapping/1", headers={"X-User-Role": "student"})
    check("Student GET /api/mapping/1 → 200", r.status_code == 200)

# ── 7. Invalid role ────────────────────────────────────────────
print("\n7. Invalid role header")
with httpx.Client(timeout=10) as c:
    r = c.post(
        f"{BASE}/api/syllabus/upload",
        files={"file": ("bad.pdf", pdf_bytes + b"bad-role", "application/pdf")},
        headers={"X-User-Role": "admin"},
    )
    check("Invalid role 'admin' → 400 or 403", r.status_code in (400, 403))

# ── Summary ────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for v in results.values() if v == PASS)
failed = sum(1 for v in results.values() if v == FAIL)
print(f"  Results: {passed} PASS  |  {failed} FAIL")
if failed:
    print("\n  FAILED tests:")
    for k, v in results.items():
        if v == FAIL:
            print(f"    ✗ {k}")
else:
    print("\n  ALL TESTS PASSED ✓")
print("=" * 60)
