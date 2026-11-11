"""The photo count in the web app, with a fake counter (no real AI is called)."""
import io

import pytest

from attendance.headcount import HeadcountError
from app import create_app

from .conftest import NOW, PERIOD
from .test_app import PASSWORD, Clock, check_in, confirm_roster, results, screen_code, start_session

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 20


class FakeCounter:
    def __init__(self, people=0, error=None):
        self.people, self.error, self.calls = people, error, 0

    def count(self, data, mime_type):
        self.calls += 1
        if self.error:
            raise HeadcountError(self.error)
        return self.people


def make_clients(counter, clock):
    config = {
        "TESTING": True,
        "LECTURER_PASSWORD": PASSWORD,
        "CODE_SECRET": "test-secret",
        "CODE_PERIOD_SECONDS": PERIOD,
        "CLOCK": clock,
        "TIMEZONE": "UTC",
    }
    if counter is not None:
        config["HEADCOUNTER"] = counter
    app = create_app(config)
    lecturer = app.test_client()
    assert lecturer.post("/login", data={"password": PASSWORD}).status_code == 302
    return app.test_client(), lecturer


@pytest.fixture
def clock():
    return Clock(NOW)


def send_photo(client, data=JPEG, name="class.jpg"):
    return client.post(
        "/api/headcount", data={"photo": (io.BytesIO(data), name)}, content_type="multipart/form-data"
    )


def test_photo_count_is_compared_with_the_check_ins(clock):
    student, lecturer = make_clients(FakeCounter(people=1), clock)
    confirm_roster(lecturer)
    start_session(lecturer)
    code = screen_code(lecturer)
    for email in (
        "dana.levi@example.com",
        "noa.cohen@example.com",
        "ron.mizrahi@example.com",
        "lior.peretz@example.com",
    ):
        check_in(student, email, code)
    data = send_photo(lecturer).get_json()
    assert data["ok"] and data["people"] == 1 and data["check_ins"] == 4
    assert data["level"] == "warning" and data["round"] == "start"
    assert results(lecturer)["headcounts"][0]["people"] == 1
    assert results(lecturer)["headcount_ready"] is True


def test_photo_count_close_to_the_check_ins_is_ok(clock):
    student, lecturer = make_clients(FakeCounter(people=2), clock)
    confirm_roster(lecturer)
    start_session(lecturer)
    code = screen_code(lecturer)
    check_in(student, "dana.levi@example.com", code)
    check_in(student, "noa.cohen@example.com", code)
    assert send_photo(lecturer).get_json()["level"] == "ok"


def test_photo_count_needs_a_session_and_the_lecturer_login(clock):
    student, lecturer = make_clients(FakeCounter(people=3), clock)
    assert send_photo(student).status_code == 401
    assert send_photo(lecturer).status_code == 409  # no check-in was started yet


def test_photo_must_be_a_real_image(clock):
    counter = FakeCounter(people=3)
    _student, lecturer = make_clients(counter, clock)
    confirm_roster(lecturer)
    start_session(lecturer)
    response = send_photo(lecturer, data=b"<html>hello</html>", name="class.jpg")
    assert response.status_code == 400 and "JPEG" in response.get_json()["error"]
    assert counter.calls == 0  # nothing was sent to the AI
    assert lecturer.post("/api/headcount", data={}, content_type="multipart/form-data").status_code == 400


def test_a_big_photo_is_accepted_but_not_a_huge_one(clock):
    _student, lecturer = make_clients(FakeCounter(people=3), clock)
    confirm_roster(lecturer)
    start_session(lecturer)
    assert send_photo(lecturer, data=JPEG + b"0" * (3 * 1024 * 1024)).status_code == 200
    assert send_photo(lecturer, data=JPEG + b"0" * (7 * 1024 * 1024)).status_code == 413


def test_counting_service_errors_reach_the_lecturer(clock):
    _student, lecturer = make_clients(FakeCounter(error="The free AI limit was reached for now."), clock)
    confirm_roster(lecturer)
    start_session(lecturer)
    response = send_photo(lecturer)
    assert response.status_code == 502 and "limit" in response.get_json()["error"]


def test_without_a_key_counting_says_it_is_not_set_up(clock, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    _student, lecturer = make_clients(None, clock)
    confirm_roster(lecturer)
    start_session(lecturer)
    response = send_photo(lecturer)
    assert response.status_code == 503 and "GEMINI_API_KEY" in response.get_json()["error"]
    assert results(lecturer)["headcount_ready"] is False


def test_a_new_lesson_clears_the_photo_counts(clock):
    _student, lecturer = make_clients(FakeCounter(people=1), clock)
    confirm_roster(lecturer)
    start_session(lecturer)
    send_photo(lecturer)
    lecturer.post("/api/session/end")
    clock.t = NOW + 9000
    start_session(lecturer)
    assert results(lecturer)["headcounts"] == []
