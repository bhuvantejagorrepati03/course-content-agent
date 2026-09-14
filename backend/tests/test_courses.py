"""Tests for course endpoints."""
import pytest


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_courses(client):
    r = client.get("/api/courses")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 5


def test_get_course_by_id(client):
    # Get all courses first
    courses = client.get("/api/courses").json()["data"]
    first_id = courses[0]["id"]

    r = client.get(f"/api/courses/{first_id}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "course_name" in data
    assert "units" in data


def test_get_course_not_found(client):
    r = client.get("/api/courses/99999")
    assert r.status_code == 404


def test_search_courses(client):
    r = client.get("/api/courses?search=Data")
    assert r.status_code == 200
    data = r.json()["data"]
    assert any("Data" in c["course_name"] for c in data)


def test_filter_by_program(client):
    r = client.get("/api/courses?program=B.Tech CSE")
    assert r.status_code == 200
    data = r.json()["data"]
    for c in data:
        assert c["program"] == "B.Tech CSE"


def test_get_units(client):
    courses = client.get("/api/courses").json()["data"]
    cs201 = next(c for c in courses if c["course_code"] == "CS201")
    r = client.get(f"/api/courses/{cs201['id']}/units")
    assert r.status_code == 200
    units = r.json()["data"]
    assert len(units) == 5
    assert units[0]["unit_number"] == 1


def test_get_outcomes(client):
    courses = client.get("/api/courses").json()["data"]
    cs201 = next(c for c in courses if c["course_code"] == "CS201")
    r = client.get(f"/api/courses/{cs201['id']}/outcomes")
    assert r.status_code == 200
    cos = r.json()["data"]
    assert len(cos) == 4
    assert cos[0]["co_number"] == "CO1"


def test_get_textbooks(client):
    courses = client.get("/api/courses").json()["data"]
    cs201 = next(c for c in courses if c["course_code"] == "CS201")
    r = client.get(f"/api/courses/{cs201['id']}/textbooks")
    assert r.status_code == 200
    books = r.json()["data"]
    assert len(books) >= 2


def test_get_mapping(client):
    courses = client.get("/api/courses").json()["data"]
    cs201 = next(c for c in courses if c["course_code"] == "CS201")
    r = client.get(f"/api/courses/{cs201['id']}/mapping")
    assert r.status_code == 200
    matrix = r.json()["data"]["matrix"]
    assert len(matrix) == 4   # CO1–CO4
    assert "PO1" in matrix[0]["values"]


def test_get_summary(client):
    courses = client.get("/api/courses").json()["data"]
    cs201 = next(c for c in courses if c["course_code"] == "CS201")
    r = client.get(f"/api/courses/{cs201['id']}/summary")
    assert r.status_code == 200
    summary = r.json()["data"]
    assert summary["total_units"] == 5
    assert summary["total_outcomes"] == 4
