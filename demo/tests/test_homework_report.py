"""The report for the lecturer: all the works of an assignment together, on the due date, with a fake AI."""
import json
import time

import pytest

from attendance.homework import MAX_REPORT_WORK_CHARS, GeminiReviewer, HomeworkStore, ReviewServiceError
from app import create_app

from .conftest import NOW, PERIOD
from .test_app import PASSWORD, Clock, confirm_roster
from .test_homework import BIG_ROSTER, FakeReviewer, answer, prompt_of, send, send_many

TASK = "Write a program that adds two numbers and prints the result."
DAY = 24 * 3600


class ReportReviewer(FakeReviewer):
    def __init__(self, error=None):
        super().__init__(error)
        self.reports = []

    def report(self, request, works):
        self.reports.append((request, list(works)))
        self._fail()
        return "A report about the whole class %d" % len(self.reports)


@pytest.fixture
def clock():
    return Clock(NOW)


def make_pair(reviewer, clock, background=False):
    """A lecturer and a student on the same server."""
    config = {
        "TESTING": True,
        "LECTURER_PASSWORD": PASSWORD,
        "CODE_SECRET": "test-secret",
        "CODE_PERIOD_SECONDS": PERIOD,
        "CLOCK": clock,
        "TIMEZONE": "UTC",
        "HOMEWORK_COOLDOWN_SECONDS": 0,
    }
    if reviewer is not None:
        config["REVIEWER"] = reviewer
    if background:
        config["HOMEWORK_IN_BACKGROUND"] = True
    app = create_app(config)
    lecturer, student = app.test_client(), app.test_client()
    assert lecturer.post("/login", data={"password": PASSWORD}).status_code == 302
    confirm_roster(lecturer, BIG_ROSTER)
    return lecturer, student


def due_date(clock, days=0):
    return time.strftime("%Y-%m-%d", time.gmtime(clock.t + days * DAY))


def make_report(lecturer, clock, assignment="Ex2", task=TASK, days=0):
    return lecturer.post(
        "/api/homework/report",
        data={"assignment": assignment, "request": task, "due": due_date(clock, days)},
        content_type="multipart/form-data",
    )


def test_the_report_needs_the_lecturer_password(clock):
    _lecturer, student = make_pair(ReportReviewer(), clock)
    assert student.get("/api/homework/assignments").status_code == 401
    assert student.get("/api/homework/report", query_string={"assignment": "Ex2"}).status_code == 401
    assert make_report(student, clock).status_code == 401


def test_on_the_due_date_the_report_reads_all_the_works_together(clock):
    reviewer = ReportReviewer()
    lecturer, student = make_pair(reviewer, clock)
    send_many(student, 4)
    answer_ = make_report(lecturer, clock)
    data = answer_.get_json()
    assert answer_.status_code == 200 and data["report"]["state"] == "done"
    assert data["report"]["text"] == "A report about the whole class 1" and data["count"] == 4
    request, works = reviewer.reports[0]
    assert request == TASK and len(works) == 4
    assert len(reviewer.reports) == 1 and not reviewer.compares  # one call for the whole class


def test_before_the_due_date_the_report_is_refused(clock):
    reviewer = ReportReviewer()
    lecturer, student = make_pair(reviewer, clock)
    send_many(student, 2)
    refused = make_report(lecturer, clock, days=3)
    assert refused.status_code == 409 and "due date" in refused.get_json()["error"]
    assert reviewer.reports == []
    clock.t += 3 * DAY  # the due date came
    assert make_report(lecturer, clock, days=0).status_code == 200


def test_the_report_is_refused_without_works_task_or_date(clock):
    lecturer, student = make_pair(ReportReviewer(), clock)
    assert make_report(lecturer, clock).status_code == 409  # no works yet
    send_many(student, 1)
    assert make_report(lecturer, clock, task="short").status_code == 400
    assert make_report(lecturer, clock, assignment="  ").status_code == 400
    bad_date = lecturer.post(
        "/api/homework/report",
        data={"assignment": "Ex2", "request": TASK, "due": "tomorrow"},
        content_type="multipart/form-data",
    )
    assert bad_date.status_code == 400


def test_without_a_key_the_report_says_it_is_not_set_up(clock, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    lecturer, _student = make_pair(None, clock)
    refused = make_report(lecturer, clock)
    assert refused.status_code == 503 and "GEMINI_API_KEY" in refused.get_json()["error"]
    assert lecturer.get("/api/homework/assignments").get_json()["ready"] is False


def test_the_list_of_assignments_has_names_and_counts_but_no_students(clock):
    lecturer, student = make_pair(ReportReviewer(), clock)
    send_many(student, 3, assignment="Ex2")
    send_many(student, 1, assignment="Ex3")
    data = lecturer.get("/api/homework/assignments").get_json()
    assert data["assignments"] == [{"name": "Ex2", "count": 3}, {"name": "Ex3", "count": 1}]
    assert "@" not in json.dumps(data)


def test_the_report_can_be_read_again_and_made_again_with_more_works(clock):
    reviewer = ReportReviewer()
    lecturer, student = make_pair(reviewer, clock)
    send_many(student, 2)
    make_report(lecturer, clock)
    again = lecturer.get("/api/homework/report", query_string={"assignment": "ex2"}).get_json()
    assert again["report"]["text"].endswith("1") and again["count"] == 2
    send_many(student, 3)
    second = make_report(lecturer, clock).get_json()
    assert second["report"]["text"].endswith("2") and len(reviewer.reports[1][1]) == 3


def test_a_failed_report_keeps_the_old_one_and_can_be_tried_again(clock):
    reviewer = ReportReviewer()
    lecturer, student = make_pair(reviewer, clock)
    send_many(student, 2)
    assert make_report(lecturer, clock).status_code == 200
    reviewer.error = "The AI is busy."
    failed = make_report(lecturer, clock)
    assert failed.status_code == 502 and "busy" in failed.get_json()["error"]
    state = lecturer.get("/api/homework/report", query_string={"assignment": "Ex2"}).get_json()["report"]
    assert state["state"] == "error" and state["text"].endswith("1")  # the good report is still there
    reviewer.error = None
    assert make_report(lecturer, clock).status_code == 200


def test_a_crash_does_not_leave_the_report_waiting(clock):
    class Crashing(ReportReviewer):
        def report(self, request, works):
            raise RuntimeError("boom")

    lecturer, student = make_pair(Crashing(), clock)
    send_many(student, 1)
    failed = make_report(lecturer, clock)
    assert failed.status_code == 502
    assert lecturer.get("/api/homework/report", query_string={"assignment": "Ex2"}).get_json()["report"]["state"] == "error"


def test_a_slow_ai_answers_at_once_and_the_page_asks_again(clock):
    class Slow(ReportReviewer):
        def report(self, request, works):
            time.sleep(0.3)
            return super().report(request, works)

    lecturer, student = make_pair(Slow(), clock, background=True)
    send_many(student, 2)
    started = make_report(lecturer, clock)
    assert started.status_code == 202 and started.get_json()["working"] is True
    assert make_report(lecturer, clock).status_code == 409  # one report at a time
    for _ in range(50):
        state = lecturer.get("/api/homework/report", query_string={"assignment": "Ex2"}).get_json()["report"]
        if state["state"] != "working":
            break
        time.sleep(0.1)
    assert state["state"] == "done"


def test_the_store_lists_works_without_names_and_cuts_each_work():
    store = HomeworkStore()
    store.save("Ex2", "a@example.com", "x" * (MAX_REPORT_WORK_CHARS + 500), 1)
    store.save("Ex2", "b@example.com", "second work", 2)
    texts = store.report_texts("EX2")
    assert len(texts) == 2 and len(texts[0]) == MAX_REPORT_WORK_CHARS and texts[1] == "second work"


def test_the_report_request_has_the_assignment_all_the_works_and_no_names():
    seen = {}

    def post(url, headers, body, timeout):
        seen.update(prompt=prompt_of(body), timeout=timeout)
        return answer("the report")

    text = GeminiReviewer("k", http_post=post, timeout=60).report("THE TASK TEXT", ["FIRST WORK", "SECOND WORK"])
    prompt = seen["prompt"]
    assert text == "the report" and "THE TASK TEXT" in prompt and "FIRST WORK" in prompt and "SECOND WORK" in prompt
    assert "match what the assignment asks for" in prompt and "mistakes that repeat" in prompt.lower()
    assert "interesting or special" in prompt.lower() and "not about every work one by one" in prompt
    assert "do not mention names" in prompt and "@" not in prompt
    assert seen["timeout"] > 60  # the AI may take its time


def test_a_long_report_is_not_cut_like_a_short_review():
    long_text = "word " * 2000
    text = GeminiReviewer("k", http_post=lambda *a: answer(long_text)).report("task text here", ["work"])
    assert len(text) > 8000


def test_an_unclear_answer_for_the_report_is_a_service_error():
    with pytest.raises(ReviewServiceError):
        GeminiReviewer("k", http_post=lambda *a: (200, b"{}")).report("task text here", ["work"])
