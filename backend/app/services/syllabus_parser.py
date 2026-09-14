"""
Rule-based syllabus parser.

Extracts:
  - course metadata
  - units / modules
  - topics per unit
  - course outcomes
  - textbooks & reference books
  - prerequisites
  - CO-PO-PSO mappings (when present)

Intentionally avoids relying on a fixed template — handles common
variations found in Indian university syllabi (Anna, JNTU, VTU, etc.).
"""
import re
import logging
from dataclasses import dataclass, field

from app.utils.text_cleaner import clean_text, normalize_unit_number

logger = logging.getLogger(__name__)

# ── Regex patterns ────────────────────────────────────────────────────────────

_UNIT_HEADER = re.compile(
    r"(?:UNIT|MODULE|CHAPTER)\s*[-–:]?\s*([IVXLC0-9]+)[:\s]+([^\n]+)?",
    re.IGNORECASE,
)
_CO_LINE = re.compile(
    r"(?:CO|C\.O\.?)\s*[-–]?\s*(\d+)\s*[:.]\s*(.+)",
    re.IGNORECASE,
)
_CO_SECTION_HEADER = re.compile(
    r"COURSE\s+OUTCOMES?|C\.?O\.?\s+LIST",
    re.IGNORECASE,
)
_TEXTBOOK_SECTION = re.compile(
    r"TEXT\s*BOOKS?|PRESCRIBED\s+BOOKS?|REFERENCE\s+BOOKS?|REFERENCES?\s*:",
    re.IGNORECASE,
)
_PREREQ_SECTION = re.compile(
    r"PRE[-\s]?REQUISITES?|PRIOR\s+KNOWLEDGE",
    re.IGNORECASE,
)
_HOURS_PATTERN = re.compile(r"(\d+)\s*(?:Hrs?\.?|Hours?)", re.IGNORECASE)
_COURSE_CODE = re.compile(r"\b([A-Z]{2,4}\d{3,4})\b")
_CREDITS = re.compile(r"Credits?\s*[:=]\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
_SEMESTER = re.compile(
    r"(?:Semester|Sem\.?)\s*[:–\-]?\s*(\w+)",
    re.IGNORECASE,
)
_REGULATION = re.compile(r"\b(R\d{2,4})\b", re.IGNORECASE)

# CO-PO mapping table cell: digits 0-3
_MAPPING_VALUE = re.compile(r"^[0-3]$")


@dataclass
class ParsedTopic:
    name: str
    order: int = 0


@dataclass
class ParsedUnit:
    number: int
    name: str
    hours: int = 8
    co_mapping: list[str] = field(default_factory=list)
    topics: list[ParsedTopic] = field(default_factory=list)


@dataclass
class ParsedOutcome:
    co_number: str    # "CO1"
    description: str
    bloom_level: str | None = None


@dataclass
class ParsedBook:
    title: str
    author: str
    edition: str | None
    publisher: str | None
    book_type: str = "textbook"   # "textbook" | "reference"


@dataclass
class ParsedMapping:
    co_number: str
    po_number: str
    value: int


@dataclass
class ParsedSyllabus:
    course_name: str | None = None
    course_code: str | None = None
    regulation: str | None = None
    credits: float | None = None
    semester: str | None = None
    prerequisites: list[str] = field(default_factory=list)
    units: list[ParsedUnit] = field(default_factory=list)
    outcomes: list[ParsedOutcome] = field(default_factory=list)
    textbooks: list[ParsedBook] = field(default_factory=list)
    mappings: list[ParsedMapping] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_bloom_level(text: str) -> str | None:
    text_lower = text.lower()
    for level in ("create", "evaluate", "analyze", "apply", "understand", "remember"):
        if level in text_lower:
            return level.capitalize()
    return None


def _parse_book_line(line: str) -> ParsedBook | None:
    """
    Attempt to split 'Title, Author, Edition, Publisher' from a single line.
    Many formats exist; this handles the most common comma/dash delimited styles.
    """
    line = line.strip().lstrip("0123456789.)- ")
    if len(line) < 10:
        return None
    parts = [p.strip() for p in re.split(r",\s*(?=[A-Z])", line)]
    title = parts[0] if parts else line
    author = parts[1] if len(parts) > 1 else "Unknown"
    edition = None
    publisher = None
    for p in parts[2:]:
        p_lower = p.lower()
        if "edition" in p_lower or re.search(r"\d+(st|nd|rd|th)", p_lower):
            edition = p
        elif any(pub in p_lower for pub in ["press", "publication", "pearson", "mcgraw",
                                             "oxford", "wiley", "tata", "prentice"]):
            publisher = p
    return ParsedBook(title=title, author=author, edition=edition, publisher=publisher)


# ── Main parser ───────────────────────────────────────────────────────────────

class SyllabusParser:
    """
    Stateful, rule-based syllabus parser.
    Call parse(text) → ParsedSyllabus.
    """

    def parse(self, raw_text: str, filename: str = "") -> ParsedSyllabus:
        text = clean_text(raw_text)
        lines = text.splitlines()

        result = ParsedSyllabus()
        self._extract_metadata(text, result, filename)
        self._extract_units(lines, result)
        self._extract_outcomes(lines, result)
        self._extract_books(lines, result)
        self._extract_prerequisites(lines, result)
        self._extract_mapping(lines, result)

        logger.info(
            "Parsed syllabus '%s': %d units, %d COs, %d books",
            filename,
            len(result.units),
            len(result.outcomes),
            len(result.textbooks),
        )
        return result

    # ── Metadata ──────────────────────────────────────────────────────────────

    def _extract_metadata(self, text: str, result: ParsedSyllabus, filename: str) -> None:
        # Course code
        m = _COURSE_CODE.search(text[:500])
        if m:
            result.course_code = m.group(1).upper()

        # Regulation
        m = _REGULATION.search(text[:500])
        if m:
            result.regulation = m.group(1).upper()

        # Credits
        m = _CREDITS.search(text[:1000])
        if m:
            try:
                result.credits = float(m.group(1))
            except ValueError:
                pass

        # Semester
        m = _SEMESTER.search(text[:500])
        if m:
            result.semester = m.group(1)

        # Course name: try to grab the first meaningful line
        first_lines = [l.strip() for l in text.splitlines()[:10] if l.strip()]
        for line in first_lines:
            if len(line) > 6 and not _COURSE_CODE.match(line):
                result.course_name = line
                break

        # Override with filename hint if name not found
        if not result.course_name and filename:
            stem = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
            result.course_name = stem

    # ── Units ─────────────────────────────────────────────────────────────────

    def _extract_units(self, lines: list[str], result: ParsedSyllabus) -> None:
        units: list[ParsedUnit] = []
        current_unit: ParsedUnit | None = None
        topic_order = 0

        for line in lines:
            m = _UNIT_HEADER.match(line.strip())
            if m:
                unit_num_raw = m.group(1)
                unit_title = (m.group(2) or "").strip()
                num = normalize_unit_number(unit_num_raw)
                if num is None:
                    continue
                current_unit = ParsedUnit(number=num, name=unit_title or f"Unit {num}")
                topic_order = 0
                # Extract hours from the same line
                h = _HOURS_PATTERN.search(line)
                if h:
                    current_unit.hours = int(h.group(1))
                units.append(current_unit)
                continue

            if current_unit is None:
                continue

            stripped = line.strip()
            if not stripped:
                continue

            # Skip section headers
            if _CO_SECTION_HEADER.search(stripped) or _TEXTBOOK_SECTION.search(stripped):
                current_unit = None
                continue

            # Detect hours on a standalone line
            h = _HOURS_PATTERN.fullmatch(stripped)
            if h:
                current_unit.hours = int(h.group(1))
                continue

            # Topic bullet / numbered list item
            topic_name = re.sub(r"^[\d]+[.)]\s*", "", stripped)
            topic_name = re.sub(r"^[-•*]\s*", "", topic_name).strip()
            if len(topic_name) > 3:
                current_unit.topics.append(ParsedTopic(name=topic_name, order=topic_order))
                topic_order += 1

        result.units = units

    # ── Course Outcomes ───────────────────────────────────────────────────────

    def _extract_outcomes(self, lines: list[str], result: ParsedSyllabus) -> None:
        outcomes: list[ParsedOutcome] = []
        in_section = False

        for line in lines:
            stripped = line.strip()
            if _CO_SECTION_HEADER.search(stripped):
                in_section = True
                continue

            if in_section:
                # End of section heuristic
                if stripped == "" and outcomes:
                    break
                if _UNIT_HEADER.match(stripped) or _TEXTBOOK_SECTION.search(stripped):
                    break

            m = _CO_LINE.match(stripped)
            if m:
                co_num = f"CO{m.group(1)}"
                desc = m.group(2).strip()
                outcomes.append(ParsedOutcome(
                    co_number=co_num,
                    description=desc,
                    bloom_level=_detect_bloom_level(desc),
                ))
                in_section = True  # start collecting even without explicit header

        result.outcomes = outcomes

    # ── Books ─────────────────────────────────────────────────────────────────

    def _extract_books(self, lines: list[str], result: ParsedSyllabus) -> None:
        books: list[ParsedBook] = []
        current_type = "textbook"
        in_section = False

        for line in lines:
            stripped = line.strip()

            if _TEXTBOOK_SECTION.search(stripped):
                in_section = True
                if re.search(r"REFERENCE", stripped, re.IGNORECASE):
                    current_type = "reference"
                else:
                    current_type = "textbook"
                continue

            if in_section and re.search(r"REFERENCE\s+BOOKS?", stripped, re.IGNORECASE):
                current_type = "reference"
                continue

            if in_section and stripped:
                book = _parse_book_line(stripped)
                if book:
                    book.book_type = current_type
                    books.append(book)

            # End heuristic: two consecutive blank lines or new section keyword
            if in_section and _UNIT_HEADER.match(stripped):
                in_section = False

        result.textbooks = books

    # ── Prerequisites ─────────────────────────────────────────────────────────

    def _extract_prerequisites(self, lines: list[str], result: ParsedSyllabus) -> None:
        prereqs: list[str] = []
        found = False
        for line in lines:
            stripped = line.strip()
            if _PREREQ_SECTION.search(stripped):
                found = True
                # prereqs sometimes on same line after the header
                rest = _PREREQ_SECTION.sub("", stripped).strip(": ")
                if rest:
                    prereqs.extend([p.strip() for p in re.split(r"[,;/]", rest) if p.strip()])
                continue
            if found:
                if not stripped:
                    break
                if _UNIT_HEADER.match(stripped):
                    break
                prereqs.extend([p.strip() for p in re.split(r"[,;]", stripped) if p.strip()])
        result.prerequisites = prereqs

    # ── CO-PO Mapping ─────────────────────────────────────────────────────────

    def _extract_mapping(self, lines: list[str], result: ParsedSyllabus) -> None:
        mappings: list[ParsedMapping] = []
        in_section = False
        header_cols: list[str] = []

        for line in lines:
            stripped = line.strip()
            if re.search(r"CO.?PO|CO.?PSO|PROGRAM\s+OUTCOME", stripped, re.IGNORECASE):
                in_section = True
                continue

            if not in_section:
                continue

            cells = re.split(r"\s{2,}|\t", stripped)
            cells = [c.strip() for c in cells if c.strip()]

            if not cells:
                continue

            # Header row: PO1 PO2 ... PSO1 ...
            if re.match(r"^PO\d", cells[0], re.IGNORECASE):
                header_cols = cells
                continue
            if re.match(r"^CO\d", cells[0], re.IGNORECASE) and header_cols:
                co = cells[0].upper()
                for i, val in enumerate(cells[1:]):
                    if i < len(header_cols) and _MAPPING_VALUE.match(val):
                        mappings.append(ParsedMapping(
                            co_number=co,
                            po_number=header_cols[i].upper(),
                            value=int(val),
                        ))

        result.mappings = mappings


# Module-level singleton
parser = SyllabusParser()
