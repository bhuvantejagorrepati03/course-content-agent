"""Tests for syllabus upload endpoint and parser utilities."""
import io
import pytest


def test_upload_invalid_type(client):
    r = client.post(
        "/api/syllabus/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert r.status_code == 415


def test_upload_empty_file(client):
    r = client.post(
        "/api/syllabus/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert r.status_code == 400


def test_upload_pdf(client):
    # Minimal valid PDF bytes (not actually parseable but accepted by file type check)
    fake_pdf = b"%PDF-1.4 fake content for testing upload endpoint"
    r = client.post(
        "/api/syllabus/upload",
        files={"file": ("test_syllabus.pdf", fake_pdf, "application/pdf")},
    )
    # Should be accepted (202) or possibly fail at extraction — both are valid
    assert r.status_code in (200, 202, 422)


def test_document_not_found(client):
    r = client.get("/api/syllabus/99999")
    assert r.status_code == 404


def test_document_status_not_found(client):
    r = client.get("/api/syllabus/99999/status")
    assert r.status_code == 404


# ── Parser unit tests ─────────────────────────────────────────────────────────

def test_parser_extracts_units():
    from app.services.syllabus_parser import parser

    sample = """CS201 Data Structures R23
UNIT I Introduction to Data Structures
Arrays, Linked Lists, Abstract Data Types
Applications of Arrays

UNIT II Stacks and Queues
Stack ADT, Queue ADT, Circular Queue

COURSE OUTCOMES
CO1: Understand fundamental data structure concepts.
CO2: Analyze and implement linear data structures.

TEXT BOOKS
Data Structures Using C, Reema Thareja, 2nd Edition, Oxford University Press
"""
    result = parser.parse(sample, "test.pdf")
    assert len(result.units) == 2
    assert result.units[0].number == 1
    assert result.units[1].number == 2
    assert len(result.units[0].topics) >= 2
    assert len(result.outcomes) == 2
    assert result.outcomes[0].co_number == "CO1"


def test_parser_handles_roman_units():
    from app.services.syllabus_parser import parser

    sample = """UNIT III Trees
Binary Trees, BST, AVL Trees
"""
    result = parser.parse(sample, "test.pdf")
    assert len(result.units) == 1
    assert result.units[0].number == 3


def test_text_cleaner():
    from app.utils.text_cleaner import clean_text, normalize_unit_number

    dirty = "Hello\u00a0World\u2019s  \n\n\n  test"
    cleaned = clean_text(dirty)
    assert "\u00a0" not in cleaned
    assert "  " not in cleaned

    assert normalize_unit_number("III") == 3
    assert normalize_unit_number("3") == 3
    assert normalize_unit_number("THREE") == 3
