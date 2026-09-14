"""Tests for the AI chat endpoint."""
import pytest


def _get_cs201_id(client) -> int:
    courses = client.get("/api/courses").json()["data"]
    cs201 = next(c for c in courses if c["course_code"] == "CS201")
    return cs201["id"]


def test_chat_unit_topics(client):
    course_id = _get_cs201_id(client)
    r = client.post("/api/chat", json={"course_id": course_id, "message": "What are the topics in Unit 3?"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["answer"]
    assert "Tree" in data["answer"] or "tree" in data["answer"]
    assert isinstance(data["citations"], list)


def test_chat_textbooks(client):
    course_id = _get_cs201_id(client)
    r = client.post("/api/chat", json={"course_id": course_id, "message": "What textbooks are prescribed?"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "Reema Thareja" in data["answer"] or "Weiss" in data["answer"]


def test_chat_course_outcomes(client):
    course_id = _get_cs201_id(client)
    r = client.post("/api/chat", json={"course_id": course_id, "message": "List all course outcomes"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "CO1" in data["answer"]


def test_chat_summary(client):
    course_id = _get_cs201_id(client)
    r = client.post("/api/chat", json={"course_id": course_id, "message": "Give me a summary of this course"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["answer"]
    assert len(data["suggested_questions"]) > 0


def test_chat_empty_message(client):
    course_id = _get_cs201_id(client)
    r = client.post("/api/chat", json={"course_id": course_id, "message": "   "})
    assert r.status_code == 400


def test_chat_invalid_course(client):
    r = client.post("/api/chat", json={"course_id": 99999, "message": "Hello"})
    assert r.status_code == 404


def test_chat_no_course_id(client):
    """Should fall back to first available course."""
    r = client.post("/api/chat", json={"message": "What are the topics in Unit 1?"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["answer"]


def test_chat_citations_present(client):
    course_id = _get_cs201_id(client)
    r = client.post("/api/chat", json={"course_id": course_id, "message": "What are the topics in Unit 3?"})
    data = r.json()["data"]
    citations = data["citations"]
    assert isinstance(citations, list)
    if citations:
        assert "filename" in citations[0]
