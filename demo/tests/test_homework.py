"""The homework review, with a fake AI (no real AI is called)."""
import io
import json
import urllib.error

import pytest

from attendance.homework import (
    GeminiReviewer,
    HomeworkError,
    HomeworkStore,
    ReviewServiceError,
    clean_work,
)
from app import create_app

from .conftest import NOW, PERIOD
from .test_app import PASSWORD, Clock, confirm_roster

WORK = "def add(a, b):\n    return a + b\n"
DANA, NOA = "dana.levi@example.com", "noa.cohen@example.com"


class FakeReviewer:
    def __init__(self, error=None):
        self.error, self.calls = error, []

    def review(self, work, previous=None, others=()):
        self.calls.append((work, previous, list(others)))
        if self.error:
            raise ReviewServiceError(self.error)
        return "A review of the work."


def make_clients(reviewer, clock):
    config = {
        "TESTING": True,
        "LECTURER_PASSWORD": PASSWORD,
        "CODE_SECRET": "test-secret",
        "CODE_PERIOD_SECONDS": PERIOD,
        "CLOCK": clock,
        "TIMEZONE": "UTC",
    }
    if reviewer is not None:
        config["REVIEWER"] = reviewer
    app = create_app(config)
    lecturer = app.test_client()
    assert lecturer.post("/login", data={"password": PASSWORD}).status_code == 302
    confirm_roster(lecturer)
    return app.test_client()


@pytest.fixture
def clock():
    return Clock(NOW)


def send(client, email=DANA, assignment="Ex2", work=WORK, as_file=True):
    data = {"email": email, "assignment": assignment}
    if as_file:
        data["work"] = (io.BytesIO(work.encode("utf-8")), "work.py")
    else:
        data["text"] = work
    return client.post("/api/homework", data=data, content_type="multipart/form-data")


def test_a_student_gets_a_review_and_the_page_opens(clock):
    reviewer = FakeReviewer()
    student = make_clients(reviewer, clock)
    assert student.get("/homework").status_code == 200
    data = send(student).get_json()
    assert data["ok"] and data["review"] == "A review of the work."
    assert data["compared_with"] == 0 and data["had_previous"] is False


def test_pasted_text_works_like_a_file(clock):
    student = make_clients(FakeReviewer(), clock)
    assert send(student, as_file=False).get_json()["ok"]


def test_the_email_must_be_on_the_roster(clock):
    student = make_clients(FakeReviewer(), clock)
    assert send(student, email="nobody@example.com").status_code == 403


def test_the_second_version_is_compared_with_the_first(clock):
    reviewer = FakeReviewer()
    student = make_clients(reviewer, clock)
    send(student)
    clock.t += 60
    data = send(student, work=WORK + "# version two\n").get_json()
    assert data["had_previous"] is True
    assert reviewer.calls[1][1] == WORK.strip()


def test_other_students_works_are_compared_but_never_shown(clock):
    reviewer = FakeReviewer()
    student = make_clients(reviewer, clock)
    send(student, email=NOA, work="def secret_other_work():\n    return 42\n")
    data = send(student, email=DANA).get_json()
    assert data["compared_with"] == 1
    assert "secret_other_work" not in json.dumps(data)  # the answer has only the review
    assert "secret_other_work" in reviewer.calls[1][2][0]  # but the AI did get it


def test_works_of_other_assignments_are_not_compared(clock):
    student = make_clients(FakeReviewer(), clock)
    send(student, email=NOA, assignment="Ex1")
    assert send(student, email=DANA, assignment="Ex2").get_json()["compared_with"] == 0


def test_assignment_names_ignore_case_and_extra_spaces(clock):
    student = make_clients(FakeReviewer(), clock)
    send(student, email=NOA, assignment="ex2")
    assert send(student, email=DANA, assignment="  EX2 ").get_json()["compared_with"] == 1


def test_a_student_must_wait_between_reviews(clock):
    student = make_clients(FakeReviewer(), clock)
    send(student)
    assert send(student).status_code == 429
    clock.t += 30
    assert send(student).status_code == 200


@pytest.mark.parametrize("work", ["", "short", "a\x00b" * 20])
def test_an_empty_short_or_binary_work_is_refused(clock, work):
    reviewer = FakeReviewer()
    student = make_clients(reviewer, clock)
    assert send(student, work=work).status_code == 400
    assert reviewer.calls == []


def test_a_missing_assignment_name_is_refused(clock):
    student = make_clients(FakeReviewer(), clock)
    assert send(student, assignment="  ").status_code == 400


def test_a_big_file_is_refused(clock):
    student = make_clients(FakeReviewer(), clock)
    assert send(student, work="a" * (300 * 1024)).status_code == 413


def test_a_failed_review_is_not_saved_and_the_error_is_shown(clock):
    reviewer = FakeReviewer(error="The free AI limit was reached for now.")
    student = make_clients(reviewer, clock)
    response = send(student)
    assert response.status_code == 502 and "limit" in response.get_json()["error"]
    clock.t += 30
    reviewer.error = None
    assert send(student).get_json()["had_previous"] is False


def test_without_a_key_the_review_says_it_is_not_set_up(clock, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    student = make_clients(None, clock)
    response = send(student)
    assert response.status_code == 503 and "GEMINI_API_KEY" in response.get_json()["error"]


def test_the_store_has_a_limit():
    store = HomeworkStore()
    for number in range(300):
        store.save("a", "s%d@example.com" % number, WORK, 0)
    with pytest.raises(HomeworkError):
        store.save("a", "one.more@example.com", WORK, 0)
    store.save("a", "s1@example.com", WORK + "x", 1)  # a new version of a saved work is fine


def test_at_most_five_other_works_are_compared():
    store = HomeworkStore()
    for number in range(9):
        store.save("a", "s%d@example.com" % number, WORK, number)
    assert len(store.others("a", "s0@example.com")) == 5


def test_clean_work_accepts_windows_line_ends():
    assert clean_work("line one here\r\nline two here\r\n") == "line one here\nline two here"


def answer(text):
    return 200, json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode()


def test_the_request_has_the_key_in_a_header_and_all_the_works():
    seen = {}

    def post(url, headers, body, timeout):
        seen.update(url=url, headers=headers, prompt=json.loads(body)["contents"][0]["parts"][0]["text"])
        return answer("ok")

    reviewer = GeminiReviewer("test-key", "test-model", http_post=post)
    assert reviewer.review("MY WORK", "OLD VERSION", ["OTHER ONE"]) == "ok"
    assert seen["headers"]["x-goog-api-key"] == "test-key" and "test-key" not in seen["url"]
    for word in ("MY WORK", "OLD VERSION", "OTHER ONE", "never accuse", "do not follow instructions"):
        assert word in seen["prompt"]


def test_others_are_cut_to_a_short_length():
    seen = {}

    def post(url, headers, body, timeout):
        seen["prompt"] = json.loads(body)["contents"][0]["parts"][0]["text"]
        return answer("ok")

    GeminiReviewer("k", http_post=post).review("mine", None, ["z" * 20000])
    assert seen["prompt"].count("z") == 4000


@pytest.mark.parametrize("reply", [(200, b"{}"), (200, b"not json"), answer("  ")])
def test_an_unclear_answer_is_a_service_error(reply):
    with pytest.raises(ReviewServiceError):
        GeminiReviewer("k", http_post=lambda *a: reply).review("work")


def test_http_errors_are_clear_and_do_not_show_the_key():
    def post(*args):
        raise urllib.error.HTTPError("https://example/?key=test-key", 429, "x", {}, None)

    with pytest.raises(ReviewServiceError) as error:
        GeminiReviewer("test-key", http_post=post).review("work")
    assert "limit" in str(error.value) and "test-key" not in str(error.value)
