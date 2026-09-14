"""Text cleaning utilities for extracted syllabus content."""
import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/newlines into single ones."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_control_characters(text: str) -> str:
    """Strip non-printable / control characters while keeping newlines and tabs."""
    return "".join(
        ch for ch in text
        if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t", "\r")
    )


def normalize_unicode(text: str) -> str:
    """Normalize unicode to NFC form and replace common ligatures."""
    text = unicodedata.normalize("NFC", text)
    replacements = {
        "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u00a0": " ", "\ufb01": "fi", "\ufb02": "fl",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def clean_text(text: str) -> str:
    """Full pipeline: unicode → control chars → whitespace."""
    text = normalize_unicode(text)
    text = remove_control_characters(text)
    text = normalize_whitespace(text)
    return text


def split_into_sentences(text: str) -> list[str]:
    """Rough sentence splitter (no heavy NLP dependency)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def extract_roman_numeral(text: str) -> int | None:
    """Convert Roman numerals I–X to integers."""
    mapping = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
               "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
    upper = text.strip().upper()
    return mapping.get(upper)


def normalize_unit_number(raw: str) -> int | None:
    """
    Accept various unit-number formats and return an int.
    E.g. '1', 'I', 'ONE' → 1
    """
    raw = raw.strip().upper()
    roman = extract_roman_numeral(raw)
    if roman is not None:
        return roman
    word_map = {
        "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
        "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10,
    }
    if raw in word_map:
        return word_map[raw]
    try:
        return int(raw)
    except ValueError:
        return None
