"""
VFSTR-style curriculum PDF parser.

Handles multi-course curriculum booklets such as:
  "R22 B.Tech (CSE) Course Structure & Contents"

PDF page structure (per course):
  VFSTR
  {page_num}
  {Dept} - {Year} {Semester}
  [{optional image source URL}]
  {COURSE_CODE} {COURSE_TITLE (may span 1-3 lines)}
  Hours Per Week :
  L   T   P   C
  {l} {t} {p} {c}
  PREREQUISITE KNOWLEDGE: ...
  COURSE DESCRIPTION AND OBJECTIVES: ...
  MODULE-{n}
  UNIT-{n}  {L}L+{T}T+{P}P={total} Hours
  {UNIT TITLE}
  {topics and subtopics...}
  PRACTICES: ...
  SKILLS: ...
  COURSE OUTCOMES: ...
  TEXT BOOKS: ...
  REFERENCE BOOKS: ...

Consecutive pages that belong to the same course share the same code.
Continuation pages lack a new course code — they continue from the previous.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf   # PyMuPDF

from app.utils.text_cleaner import clean_text

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants & Regex
# ═══════════════════════════════════════════════════════════════════════════════

# R22-style course code: 22XX999 or 22XX999X
_CODE_RE = re.compile(r"\b(2[0-9][A-Z]{2,4}\d{3}[A-Z]?)\b")

# LTPC table inside a page
_LTPC_RE = re.compile(
    r"L\s+T\s+P\s+C\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
    re.IGNORECASE,
)
_LTSLPC_RE = re.compile(
    r"L\s+T\s+P\s+SL\s+C\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
    re.IGNORECASE,
)

# Unit header: UNIT-1, UNIT-2, UNIT 1, UNIT–1 (en-dash), etc.
# The title may be on the SAME line OR on the NEXT line — we handle both cases.
_UNIT_RE = re.compile(
    r"^UNIT[-\u2013\u2014\s]*(\d+)\s*"   # UNIT-1, UNIT–1, UNIT 2, etc. (hyphen/en-dash/em-dash)
    r"((?:\d+L\s*\+\s*\d+T\s*\+\s*\d+P(?:\s*\+\s*\d+SL)?\s*=\s*\d+\s*Hours?)?)"  # optional hour formula
    r"\s*(.*)$",                              # optional rest of line (title or empty)
    re.IGNORECASE,
)

# Hours inside unit header: 12L+8T+0P=20 Hours
_UNIT_HOURS_RE = re.compile(
    r"(\d+)L\s*\+\s*(\d+)T\s*\+\s*(\d+)P(?:\s*\+\s*(\d+)SL)?\s*=\s*(\d+)\s*Hours?",
    re.IGNORECASE,
)

# Module header: MODULE-1, MODULE-2, MODULE–1 (en-dash), MODULE–2
_MODULE_RE = re.compile(r"MODULE[-\u2013\u2014\s]*(\d+)", re.IGNORECASE)

# Section headers
_PREREQ_RE = re.compile(r"PREREQUISITE\s+KNOWLEDGE\s*:", re.IGNORECASE)
_DESC_RE    = re.compile(r"COURSE\s+DESCRIPTION\s+AND\s+OBJECTIVES?\s*:", re.IGNORECASE)
_PRACTICES_RE = re.compile(r"PRACTICES\s*:", re.IGNORECASE)
_SKILLS_RE    = re.compile(r"SKILLS\s*:", re.IGNORECASE)
_CO_HDR_RE    = re.compile(r"COURSE\s+OUTCOMES?\s*:", re.IGNORECASE)
_TEXT_RE      = re.compile(r"TEXT\s*BOOKS?\s*:", re.IGNORECASE)
_REF_RE       = re.compile(r"REFERENCE\s+BOOKS?\s*:", re.IGNORECASE)

# CO row: "1  Apply Maxwell... Understand  1  PO1,PO2,PO3"
_CO_NUM_RE = re.compile(r"^(\d+)\s+(.+)", re.IGNORECASE)
# Bloom's levels
_BLOOM_LEVELS = {
    "remember", "understand", "apply", "analyze", "analyse",
    "evaluate", "create", "knowledge", "comprehension", "application",
    "analysis", "synthesis", "evaluation",
}
_BLOOM_RE = re.compile(
    r"\b(Remember|Understand|Apply|Analy[sz]e|Evaluate|Create|"
    r"Knowledge|Comprehension|Application|Analysis|Synthesis|Evaluation)\b",
    re.IGNORECASE,
)

# PO mapping column: "PO1,PO2,PO3" or "PO1-PO3"
_PO_RE = re.compile(r"P[OS]O?\s*\d+", re.IGNORECASE)

# Page header to strip: "VFSTR \n13\nCSE - I Year I Semester"
_PAGE_HDR_RE = re.compile(
    r"^VFSTR\s*\n\d+\n[^\n]+\n?",
    re.IGNORECASE | re.MULTILINE,
)
# Optional image source block to strip
_SRC_RE = re.compile(
    r"(?:Image source|Source)\s*:?\s*https?://[^\n]+(?:\n[^\n]+){0,3}\n?",
    re.IGNORECASE,
)

# Regulation patterns
_REG_PATTERNS = [
    re.compile(r"\bR[-\s]?(\d{2,4})\b", re.IGNORECASE),
    re.compile(r"Regulation\s*[:=-]?\s*R?(\d{2,4})", re.IGNORECASE),
]
# Programme
_PROG_RE = re.compile(r"\b(B\.?\s*Tech|B\.?\s*E\.?|M\.?\s*Tech|MCA|MBA|BCA)\b", re.IGNORECASE)
# Branch
_BRANCH_RE = re.compile(
    r"Computer\s+Science\s+(?:and|&)\s+Engineering|CSE\b",
    re.IGNORECASE,
)
_PERIOD_RE = re.compile(
    r"\b(I{1,3}V?)\s+Year\s+(I{1,3}V?)\s+Semester\b",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ParsedTopic:
    name: str
    order: int = 0


@dataclass
class ParsedUnit:
    number: int
    name: str = ""
    hours: int = 0
    module_number: int = 0
    module_name: str = ""
    co_mapping: list[str] = field(default_factory=list)
    topics: list[ParsedTopic] = field(default_factory=list)


@dataclass
class ParsedOutcome:
    co_number: str     # "CO1"
    description: str
    bloom_level: str | None = None
    module_number: int | None = None
    po_mapping: list[str] = field(default_factory=list)


@dataclass
class ParsedBook:
    title: str
    author: str = ""
    edition: str | None = None
    publisher: str | None = None
    book_type: str = "textbook"


@dataclass
class ParsedMapping:
    co_number: str
    po_number: str
    value: int = 1


@dataclass
class ParsedCourse:
    course_code: str
    course_name: str
    regulation: str = ""
    programme: str = ""
    branch: str = ""
    branch_full: str = ""
    year: str = ""
    semester: str = ""
    credits: float = 0.0
    l_hours: int = 0
    t_hours: int = 0
    p_hours: int = 0
    total_hours: int = 0
    prerequisites: list[str] = field(default_factory=list)
    description: str = ""
    objectives: str = ""
    units: list[ParsedUnit] = field(default_factory=list)
    outcomes: list[ParsedOutcome] = field(default_factory=list)
    textbooks: list[ParsedBook] = field(default_factory=list)
    mappings: list[ParsedMapping] = field(default_factory=list)
    source_pages: list[int] = field(default_factory=list)


@dataclass
class ParsedCurriculum:
    regulation: str = ""
    programme: str = ""
    branch: str = ""
    branch_full: str = ""
    courses: list[ParsedCourse] = field(default_factory=list)
    detection_confidence: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _normalise_reg(raw: str) -> str:
    raw = raw.strip()
    if re.match(r"^R\d{2,4}$", raw, re.IGNORECASE):
        return raw.upper()
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 4:
        return f"R{digits[2:]}"
    return f"R{digits}"


def _detect_regulation(text: str) -> str:
    for pat in _REG_PATTERNS:
        m = pat.search(text)
        if m:
            return _normalise_reg(m.group(1))
    return ""


def _detect_programme(text: str) -> str:
    m = _PROG_RE.search(text[:5000])
    if not m:
        return ""
    raw = m.group(1).replace(" ", "").replace(".", "").upper()
    return "B.Tech" if raw in ("BTECH", "BE") else m.group(1)


def _detect_branch(text: str) -> tuple[str, str]:
    if _BRANCH_RE.search(text[:5000]):
        return "CSE", "Computer Science and Engineering"
    return "", ""


def _strip_page_header(text: str) -> str:
    """Remove the repeated 'VFSTR\n{num}\n{dept}' header from page text."""
    text = _PAGE_HDR_RE.sub("", text)
    text = _SRC_RE.sub("", text)
    return text.strip()


def _academic_period(text: str) -> tuple[str, str] | None:
    match = _PERIOD_RE.search(text)
    if not match:
        return None
    year = {"I": "I Year", "II": "II Year", "III": "III Year", "IV": "IV Year"}[match.group(1).upper()]
    semester = {"I": "I Semester", "II": "II Semester", "III": "III Semester", "IV": "IV Semester"}[match.group(2).upper()]
    return year, semester


def _period_from_block(text: str) -> tuple[str, str] | None:
    period = _academic_period(text)
    if period:
        return period
    if re.search(r"CURRICULUM PERIOD:\s*Pre-Semester", text, re.IGNORECASE):
        return "Pre-Semester", "Pre-Semester"
    return None


def _extract_ltcp(text: str) -> tuple[int, int, int, int, int] | None:
    """Return L, T, P, SL, C for both R22 and R25 course headers."""
    match = _LTSLPC_RE.search(text)
    if match:
        return tuple(int(value) for value in match.groups())  # type: ignore[return-value]
    match = _LTPC_RE.search(text)
    if match:
        lecture, tutorial, practical, credits = (int(value) for value in match.groups())
        return lecture, tutorial, practical, 0, credits
    return None


def _parse_book_line(line: str) -> ParsedBook | None:
    """Parse '1. Author, "Title", Publisher, Edition, Year.'"""
    line = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
    if len(line) < 10:
        return None
    # Extract quoted title if present
    title_m = re.search(r'"([^"]{5,})"', line)
    if title_m:
        title = title_m.group(1)
        rest = line.replace(f'"{title}"', "").strip(", ")
        parts = [p.strip() for p in rest.split(",") if p.strip()]
        author = parts[0] if parts else "Unknown"
        edition = publisher = None
        for p in parts[1:]:
            pl = p.lower()
            if re.search(r"\d+\s*(st|nd|rd|th)?\s*ed|edition", pl):
                edition = p
            elif any(k in pl for k in ["press", "pub", "pearson", "mcgraw", "oxford",
                                        "wiley", "tata", "phi", "prentice", "cengage",
                                        "elsevier", "springer", "tmh", "rai", "dhanpat",
                                        "himalaya", "chand", "narosa"]):
                publisher = p
        return ParsedBook(title=title, author=author, edition=edition, publisher=publisher)
    # No quotes — fall back to comma split
    parts = [p.strip() for p in line.split(",", 3)]
    if len(parts) < 2:
        return None
    author, title = parts[0], parts[1]
    edition = publisher = None
    for p in parts[2:]:
        pl = p.lower()
        if re.search(r"\d+\s*(st|nd|rd|th)?\s*ed|edition", pl):
            edition = p
        elif len(p) > 4:
            publisher = p
    return ParsedBook(title=title.strip('"'), author=author, edition=edition, publisher=publisher)


# ═══════════════════════════════════════════════════════════════════════════════
# Page-level course-block segmentation
# ═══════════════════════════════════════════════════════════════════════════════

def _find_course_code_in_page(raw_text: str) -> str | None:
    """
    Find the R22-style course code (22XXXNNN) in a single page's raw text.
    Returns the code string or None.
    """
    for m in _CODE_RE.finditer(raw_text):
        code = m.group(1).upper()
        # Must start with 2x where x is a digit
        if re.match(r"^2[0-9]", code):
            return code
    return None


def _pages_to_course_blocks(
    pages: list[tuple[int, str]]   # (1-indexed page_num, raw_text)
) -> list[tuple[str, list[int]]]:
    """
    Group pages into course blocks.

    Logic:
    - A page "starts a new course" if it contains an R22-style code AND
      the LTPC table (ensuring it's a course detail page, not just a reference).
    - Continuation pages (no code, but have UNIT/COURSE OUTCOMES etc.)
      are appended to the current course.
    - Pages with no code and no structural markers are skipped.
    """
    groups: list[tuple[str, list[int], list[str], tuple[str, str] | None]] = []
    current_code: str | None = None
    current_pages: list[int] = []
    current_texts: list[str] = []
    current_period: tuple[str, str] | None = None
    current_block_period: tuple[str, str] | None = None

    for page_num, raw in pages:
        if re.search(r"\bPRE\s*[- ]?SEMESTER\b", raw, re.IGNORECASE):
            current_period = ("Pre-Semester", "Pre-Semester")
        page_period = _academic_period(raw)
        if page_period:
            current_period = page_period
        code = _find_course_code_in_page(raw)
        has_ltpc = _extract_ltcp(raw) is not None
        has_content = bool(re.search(
            r"PREREQUISITE|MODULE|UNIT[-\s]*\d|COURSE\s+OUTCOME|TEXT\s*BOOK|REFERENCE",
            raw, re.IGNORECASE,
        ))

        if code and has_ltpc:
            # New course starts here
            if current_code and current_texts:
                groups.append((current_code, current_pages[:], current_texts[:], current_block_period))
            current_code = code
            current_pages = [page_num]
            current_texts = [raw]
            current_block_period = page_period or current_period
        elif current_code and (has_content or code == current_code):
            # Continuation of current course
            current_pages.append(page_num)
            current_texts.append(raw)
        # else: pre-content page (TOC etc.) — skip

    if current_code and current_texts:
        groups.append((current_code, current_pages, current_texts, current_block_period))

    # Convert to (merged_text, page_list)
    result = []
    for code, page_nums, texts, inherited_period in groups:
        period = next((_period_from_block(t) for t in texts if _period_from_block(t)), None) or inherited_period
        period_header = ""
        if period:
            period_header = (
                "CURRICULUM PERIOD: Pre-Semester\n"
                if period[0] == "Pre-Semester"
                else f"CURRICULUM PERIOD: {period[0]} {period[1]}\n"
            )
        merged = period_header + "\n".join(_strip_page_header(t) for t in texts)
        result.append((merged, page_nums))

    logger.info("Segmented %d course blocks from %d pages", len(result), len(pages))
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Per-course block parser
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_one_course(
    block: str,
    regulation: str,
    programme: str,
    branch: str,
    branch_full: str,
    source_pages: list[int],
) -> ParsedCourse | None:
    """Parse a single merged course block into a ParsedCourse."""
    lines = [l for l in block.splitlines() if l.strip()]
    if not lines:
        return None

    # ── Extract course code and title from first few lines ─────────────────
    code = None
    title_lines: list[str] = []
    code_line_idx = -1

    for i, ln in enumerate(lines[:15]):
        m = _CODE_RE.search(ln)
        if m and re.match(r"^2[0-9]", m.group(1)):
            code = m.group(1).upper()
            # Title is the rest of this line after the code
            rest = ln[m.end():].strip()
            if rest:
                title_lines.append(rest)
            code_line_idx = i
            break

    if not code:
        return None

    # Some R25 pages place the course title immediately before the code and
    # then begin the L/T/P/SL/C table. Recover that title without treating the
    # table headers as course-name text.
    if not title_lines and code_line_idx > 0:
        preceding = []
        for ln in lines[max(0, code_line_idx - 3):code_line_idx]:
            stripped = ln.strip()
            if stripped.upper() in {"L", "T", "P", "SL", "C"}:
                continue
            if re.search(r"Hours\s+Per\s+|MODULE|UNIT[-\s]*\d|PREREQUISITE", stripped, re.IGNORECASE):
                continue
            if stripped:
                preceding.append(stripped)
        if preceding:
            title_lines.extend(preceding)

    # Collect title continuation lines (all-caps lines immediately after code line)
    for ln in lines[code_line_idx + 1 : code_line_idx + 5]:
        stripped = ln.strip()
        # Title lines are usually ALL CAPS; stop at Hours Per Week or structural markers
        if re.search(r"Hours\s+Per\s+(?:Week|Semester)|PREREQUISITE|MODULE|UNIT[-\s]*\d", stripped, re.IGNORECASE):
            break
        if stripped.upper() in {"L", "T", "P", "SL", "C"} or re.fullmatch(r"L\s+T\s+P(?:\s+SL)?\s+C", stripped, re.IGNORECASE):
            break
        if stripped.isupper() and len(stripped) > 2:
            title_lines.append(stripped)
        elif stripped and not stripped[0].isdigit():
            # Mixed case continuation (e.g., "ORDINARY DIFFERENTIAL")
            title_lines.append(stripped)
        else:
            break

    course_name = " ".join(title_lines).strip()
    if not course_name:
        course_name = code

    course = ParsedCourse(
        course_code=code,
        course_name=course_name,
        regulation=regulation,
        programme=programme,
        branch=branch,
        branch_full=branch_full,
        source_pages=source_pages,
    )

    # ── LTPC ────────────────────────────────────────────────────────────────
    ltpc = _extract_ltcp(block)
    if ltpc:
        L, T, P, SL, C = ltpc
        course.l_hours, course.t_hours, course.p_hours = L, T, P
        course.credits = float(C)
        # Estimate total contact hours for a ~15-week semester
        course.total_hours = (L + T + P) * 15

    # ── Year / Semester from source pages header (e.g., "CSE - I Year I Semester") ─
    period = _period_from_block(block)
    if period:
        yr_map = {"I": "I Year", "II": "II Year", "III": "III Year", "IV": "IV Year"}
        if period[0] == "Pre-Semester":
            course.year = course.semester = "Pre-Semester"
        else:
            course.year = period[0]
            course.semester = period[1]

    # ── Parse the rest of the block by splitting into sections ─────────────
    _fill_sections(block, course)

    return course


def _fill_sections(block: str, course: ParsedCourse) -> None:
    """
    Scan through the block text and fill:
    prerequisites, description, modules/units/topics, COs, books.

    VFSTR R22 unit structure (title on following lines):
      UNIT-1                      <- unit header, no inline title
      12L+8T+0P=20 Hours          <- hours formula, separate line
      MATRICES                    <- unit title, separate line
      Definition of matrix...     <- topics start here
    """
    lines = block.splitlines()

    section = "header"
    current_module = 0
    current_module_name = ""
    current_unit: ParsedUnit | None = None
    topic_order = 0
    book_type = "textbook"
    unit_needs_title = False   # True = current_unit has no name yet; consume next non-hours line

    desc_lines: list[str] = []
    prereq_lines: list[str] = []
    co_lines: list[str] = []
    book_lines: list[tuple[str, str]] = []

    def commit_unit():
        nonlocal current_unit, unit_needs_title
        if current_unit is not None:
            course.units.append(current_unit)
            current_unit = None
        unit_needs_title = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # ── Section transitions (checked before everything else) ──────────
        if _PREREQ_RE.search(line):
            commit_unit()
            section = "prereq"
            rest = _PREREQ_RE.sub("", line).strip(": ")
            if rest:
                prereq_lines.append(rest)
            continue

        if _DESC_RE.search(line):
            commit_unit()
            section = "desc"
            rest = _DESC_RE.sub("", line).strip(": ")
            if rest:
                desc_lines.append(rest)
            continue

        if _MODULE_RE.match(line):
            commit_unit()
            section = "content"
            mm = _MODULE_RE.match(line)
            current_module = int(mm.group(1))
            current_module_name = line[mm.end():].strip("- :").strip()
            continue

        mu = _UNIT_RE.match(line)
        if mu:
            commit_unit()
            section = "content"
            unit_num   = int(mu.group(1))
            hours_str  = mu.group(2).strip()
            title_inline = mu.group(3).strip()

            total_h = 0
            hm = _UNIT_HOURS_RE.search(hours_str or line)
            if hm:
                total_h = int(hm.group(5))

            global_num = len(course.units) + 1
            current_unit = ParsedUnit(
                number=global_num,
                name=title_inline,   # may be empty — filled below
                hours=total_h,
                module_number=current_module,
                module_name=current_module_name,
            )
            topic_order = 0
            unit_needs_title = (title_inline == "")
            continue

        if _PRACTICES_RE.search(line) or _SKILLS_RE.search(line):
            # Some practical courses (notably Advanced Coding Competency) put
            # all of their syllabus content under PRACTICES immediately after
            # the unit title. Keep it attached when the unit has no topics yet.
            if current_unit is not None and not current_unit.topics:
                section = "content"
            else:
                commit_unit()
                section = "practices"
            continue

        if _CO_HDR_RE.search(line):
            commit_unit()
            section = "cos"
            continue

        if _TEXT_RE.search(line):
            commit_unit()
            section = "textbooks"
            book_type = "textbook"
            continue

        if _REF_RE.search(line):
            commit_unit()
            section = "refs"
            book_type = "reference"
            continue

        # Skip table header lines, but keep CO numbers
        if section != "cos" and re.match(r"^(Hours\s+Per\s+Week|LTPC|\d+)$", line, re.IGNORECASE):
            continue

        # ── Pending unit title resolution ──────────────────────────────────
        if unit_needs_title and current_unit is not None:
            hm = _UNIT_HOURS_RE.match(line)
            if hm:
                # This line is the hours formula — update hours and keep waiting
                current_unit.hours = int(hm.group(5))
                continue
            else:
                # This is the unit title
                current_unit.name = line
                unit_needs_title = False
                continue   # Do NOT add title as a topic

        # R25 practical courses may use MODULE-n plus an hours line without
        # an explicit UNIT-n header. Treat each such module as a unit.
        if current_unit is None and current_module and section == "content":
            hm = _UNIT_HOURS_RE.match(line)
            if hm:
                current_unit = ParsedUnit(
                    number=len(course.units) + 1,
                    name=current_module_name or f"Module {current_module}",
                    hours=int(hm.group(5)),
                    module_number=current_module,
                    module_name=current_module_name,
                )
                topic_order = 0
                continue

        # ── Section bodies ─────────────────────────────────────────────────
        if section == "prereq":
            if re.match(r"^(COURSE|MODULE|UNIT)\b", line, re.IGNORECASE):
                section = "content"
            else:
                prereq_lines.append(line)

        elif section == "desc":
            if re.match(r"^(MODULE|UNIT)\b", line, re.IGNORECASE):
                section = "content"
            else:
                desc_lines.append(line)

        elif section == "content":
            if current_unit is not None:
                if re.match(r"^\d{1,2}L\+", line):   # stray hours formula
                    continue
                topic_text = re.sub(r"^[●•\-\*►▸]\s*", "", line)
                topic_text = re.sub(r"^\d+[\.\)]\s*", "", topic_text).strip()
                if len(topic_text) > 4 and not topic_text.isnumeric():
                    current_unit.topics.append(ParsedTopic(name=topic_text, order=topic_order))
                    topic_order += 1

        elif section == "cos":
            co_lines.append(line)

        elif section in ("textbooks", "refs"):
            book_lines.append((line, book_type))

    commit_unit()

    # ── Post-process collected lines ───────────────────────────────────────
    raw_prereq = " ".join(prereq_lines).strip()
    if raw_prereq:
        parts = re.split(r"[,;]|\band\b", raw_prereq, flags=re.IGNORECASE)
        course.prerequisites = [p.strip() for p in parts if len(p.strip()) > 3]

    course.description = " ".join(desc_lines).strip()

    _parse_cos(co_lines, course)

    seen_books: set[str] = set()
    for raw_book_line, btype in book_lines:
        if re.match(r"^\d+[\.\)]", raw_book_line) or re.match(r"^[A-Z]\.", raw_book_line):
            bk = _parse_book_line(raw_book_line)
            if bk:
                key = bk.title[:40].lower()
                if key not in seen_books:
                    seen_books.add(key)
                    bk.book_type = btype
                    course.textbooks.append(bk)


def _parse_cos(co_lines: list[str], course: ParsedCourse) -> None:
    """
    Parse CO table lines into ParsedOutcome objects.

    Expected PDF extraction pattern:
        1
        Description
        Apply
        1
        1,10

        2
        Description
        Create
        1
        1,3
    """

    skip_words = {
        "co", "no.", "course", "outcomes", "blooms", "bloom",
        "level", "module", "mapping", "with", "pos",
        "upon", "successful", "completion", "students", "will",
        "have", "ability"
    }

    i = 0

    while i < len(co_lines):
        line = co_lines[i].strip()

        # A CO row starts with a bare number.
        if not re.match(r"^\d+$", line):
            i += 1
            continue

        co_num_str = line
        i += 1

        desc_parts: list[str] = []
        bloom: str | None = None
        po_refs: list[str] = []

        # Collect description until Bloom level.
        while i < len(co_lines):
            nxt = co_lines[i].strip()

            if not nxt:
                i += 1
                continue

            # Another CO number means this row has ended.
            if re.match(r"^\d+$", nxt) and not desc_parts:
                break

            # Bloom level.
            bm = _BLOOM_RE.fullmatch(nxt)

            if bm:
                bloom = bm.group(1).capitalize()

                bloom_map = {
                    "Knowledge": "Remember",
                    "Comprehension": "Understand",
                    "Application": "Apply",
                    "Analysis": "Analyze",
                    "Analyse": "Analyze",
                    "Synthesis": "Create",
                    "Evaluation": "Evaluate",
                }

                bloom = bloom_map.get(bloom, bloom)

                i += 1
                break

            # Description text.
            w = nxt.lower().strip(".,;:")

            if w not in skip_words and len(nxt) > 1:
                desc_parts.append(nxt)

            i += 1

        # First number after Bloom = Module No.
        if i < len(co_lines):
            module_value = co_lines[i].strip()

            if re.match(r"^[\d,\s]+$", module_value):
                i += 1

        # Second value after Bloom = PO mapping.
        if i < len(co_lines):
            mapping_value = co_lines[i].strip()

            # PO references such as PO1, PO2.
            found_pos = _PO_RE.findall(mapping_value)

            if found_pos:
                po_refs = [
                    p.upper().replace(" ", "")
                    for p in found_pos
                ]
                i += 1

            # Plain numbers such as 1,10 or 2.
            elif re.match(r"^[\d,\s]+$", mapping_value):
                for n in re.findall(r"\d+", mapping_value):
                    po_refs.append(f"PO{n}")
                i += 1

        desc = " ".join(desc_parts).strip().rstrip(".,;:")

        if len(desc) < 5:
            continue

        co_code = f"CO{co_num_str}"

        course.outcomes.append(
            ParsedOutcome(
                co_number=co_code,
                description=desc,
                bloom_level=bloom,
                po_mapping=po_refs,
            )
        )
        for po in po_refs:
            if re.match(r"P[OS]O?\d+$", po, re.IGNORECASE):
                course.mappings.append(ParsedMapping(
                    co_number=co_code, po_number=po.upper(), value=1
                ))


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level entry point
# ═══════════════════════════════════════════════════════════════════════════════

class CurriculumParser:
    """
    Parse a full curriculum PDF (multiple courses) into a ParsedCurriculum.
    Uses PyMuPDF directly for reliable page-by-page text extraction.
    """

    def parse(
        self,
        full_text: str,                          # not used (kept for compat)
        paged_texts: list[tuple[int, str]],      # (page_num, raw_text)
        filename: str = "",
        file_path: str = "",                     # NEW: path to original PDF
    ) -> ParsedCurriculum:
        # If we have the file path, re-extract using PyMuPDF directly
        pages = paged_texts

        if file_path and Path(file_path).exists():
            try:
                doc = pymupdf.open(file_path)
                pages = [(i + 1, doc[i].get_text("text")) for i in range(len(doc))]
                doc.close()
                logger.info("Re-extracted %d pages from %s", len(pages), filename)
            except Exception as exc:
                logger.warning("PyMuPDF re-extraction failed (%s), using paged_texts", exc)

        # Detect document-level metadata from full raw text
        all_text = "\n".join(t for _, t in pages)

        regulation = _detect_regulation(all_text)
        programme  = _detect_programme(all_text)
        branch, branch_full = _detect_branch(all_text)

        logger.info(
            "Document '%s': regulation=%s  programme=%s  branch=%s",
            filename, regulation or "?", programme or "?", branch or "?",
        )

        curriculum = ParsedCurriculum(
            regulation=regulation,
            programme=programme,
            branch=branch,
            branch_full=branch_full,
            detection_confidence=sum([
                0.4 if regulation else 0.0,
                0.3 if programme else 0.0,
                0.3 if branch else 0.0,
            ]),
        )

        # Segment pages into per-course blocks
        blocks = _pages_to_course_blocks(pages)

        for block_text, source_pages in blocks:
            course = _parse_one_course(
                block_text, regulation, programme, branch, branch_full, source_pages
            )
            if course and course.course_code:
                curriculum.courses.append(course)
            elif not course:
                logger.debug("Skipped block at pages %s — no valid course code", source_pages)

        logger.info(
            "Parsed '%s': %d courses, regulation=%s, branch=%s",
            filename, len(curriculum.courses), regulation, branch,
        )
        return curriculum


# Module-level singleton
curriculum_parser = CurriculumParser()
