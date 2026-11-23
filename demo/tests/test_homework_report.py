"""Publishing an assignment (PDF, due date) and the report for the lecturer, with a fake AI."""
import base64
import io
import json
import time

import pytest

from attendance.homework import (
    MAX_ASSIGNMENT_PDF_BYTES,
    MAX_REPORT_WORK_CHARS,
    GeminiReviewer,
    HomeworkError,
    HomeworkStore,
    ReviewServiceError,
)
from app import create_app

from .conftest import NOW, PERIOD
from .test_app import PASSWORD, Clock, confirm_roster
from .test_homework import BIG_ROSTER, PDF, FakeReviewer, answer, prompt_of, publish, send_many

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


def date_of(clock, days=0):
    return time.strftime("%Y-%m-%d", time.gmtime(clock.t + days * DAY))


def make_pair(reviewer, clock, background=False):
    """A lecturer and a student on the same server. "Ex2" is due today, "Later" in 3 days, "Empty" today."""
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
    if reviewer is not None:
        for name, days in (("Ex2", 0), ("Later", 3), ("Empty", 0)):
            assert publish(lecturer, name, due=date_of(clock, days)).status_code == 200
    return lecturer, student


def make_report(lecturer, assignment="Ex2"):
    return lecturer.post("/api/homework/report", data={"assignment": assignment}, content_type="multipart/form-data")


def get_report(lecturer, assignment="Ex2"):
    return lecturer.get("/api/homework/report", query_string={"assignment": assignment}).get_json()


# ---- publishing an assignment ----

def test_publishing_needs_the_lecturer_password(clock):
    _lecturer, student = make_pair(ReportReviewer(), clock)
    assert publish(student, "Ex5").status_code == 401
    assert student.get("/api/homework/assignments").status_code == 401
    assert student.get("/api/homework/report", query_string={"assignment": "Ex2"}).status_code == 401
    assert make_report(student).status_code == 401


def test_the_lecturer_publishes_a_pdf_and_the_ai_reads_it(clock):
    reviewer = ReportReviewer()
    lecturer, _student = make_pair(reviewer, clock)
    data = publish(lecturer, "Ex5", due=date_of(clock, 7), course="Algorithms", pdf=PDF + b"more").get_json()
    assert data["ok"] and data["assignment"]["name"] == "Ex5" and data["assignment"]["course"] == "Algorithms"
    assert reviewer.pdfs[-1] == PDF + b"more"  # the AI got the file itself
    listed = lecturer.get("/api/homework/assignments").get_json()["assignments"]
    assert [a["name"] for a in listed] == ["Empty", "Ex2", "Later", "Ex5"]  # the nearest due date first


def test_the_ai_checks_the_due_date_in_the_document(clock):
    reviewer = ReportReviewer()
    lecturer, _student = make_pair(reviewer, clock)
    chosen = date_of(clock, 5)
    reviewer.found_due = chosen
    assert publish(lecturer, "Ex5", due=chosen).get_json()["warning"] is None
    reviewer.found_due = date_of(clock, 9)
    different = publish(lecturer, "Ex5", due=chosen).get_json()
    assert different["ok"] and different["found_due"] == reviewer.found_due
    assert reviewer.found_due in different["warning"] and chosen in different["warning"]
    reviewer.found_due = None
    missing = publish(lecturer, "Ex5", due=chosen).get_json()
    assert missing["ok"] and "did not find a due date" in missing["warning"]  # a warning only: it is still published


def test_publishing_again_with_the_same_name_fixes_the_date(clock):
    lecturer, _student = make_pair(ReportReviewer(), clock)
    publish(lecturer, "ex2", due=date_of(clock, 10))
    listed = lecturer.get("/api/homework/assignments").get_json()["assignments"]
    assert [a["due"] for a in listed if a["name"].lower() == "ex2"] == [date_of(clock, 10)] and len(listed) == 3


@pytest.mark.parametrize(
    "fields",
    [{"course": ""}, {"name": "  "}, {"due": "tomorrow"}, {"due": ""}],
)
def test_publishing_without_the_needed_fields_is_refused(clock, fields):
    lecturer, _student = make_pair(ReportReviewer(), clock)
    data = {"course": "OOP", "name": "Ex5", "due": date_of(clock, 1), "file": (io.BytesIO(PDF), "a.pdf")}
    data.update(fields)
    response = lecturer.post("/api/assignments", data=data, content_type="multipart/form-data")
    assert response.status_code == 400


def test_publishing_needs_a_real_pdf_that_is_not_too_big(clock):
    lecturer, _student = make_pair(ReportReviewer(), clock)
    assert publish(lecturer, "Ex5", pdf=b"just some text").status_code == 400
    no_file = lecturer.post(
        "/api/assignments", data={"course": "OOP", "name": "Ex5", "due": date_of(clock, 1)}, content_type="multipart/form-data"
    )
    assert no_file.status_code == 400 and "PDF" in no_file.get_json()["error"]
    assert publish(lecturer, "Ex5", pdf=b"%PDF-1.4" + b"x" * MAX_ASSIGNMENT_PDF_BYTES).status_code == 413


def test_a_pdf_without_readable_text_is_refused(clock):
    reviewer = ReportReviewer()
    lecturer, _student = make_pair(reviewer, clock)
    reviewer.task = "short"
    response = publish(lecturer, "Ex5")
    assert response.status_code == 400 and "could not read text" in response.get_json()["error"]


def test_publishing_without_a_key_says_it_is_not_set_up(clock, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    lecturer, _student = make_pair(None, clock)
    refused = publish(lecturer, "Ex5")
    assert refused.status_code == 503 and "GEMINI_API_KEY" in refused.get_json()["error"]
    assert lecturer.get("/api/homework/assignments").get_json()["ready"] is False


def test_an_ai_failure_while_reading_the_pdf_is_a_clear_error(clock):
    reviewer = ReportReviewer()
    lecturer, _student = make_pair(reviewer, clock)

    def broken(pdf):
        raise ReviewServiceError("The AI is busy.")

    reviewer.read_assignment = broken
    failed = publish(lecturer, "Ex5")
    assert failed.status_code == 502 and "busy" in failed.get_json()["error"]
    assert "Ex5" not in json.dumps(lecturer.get("/api/homework/assignments").get_json())  # nothing was published


# ---- the report ----

def test_on_the_due_date_the_report_reads_all_the_works_together(clock):
    reviewer = ReportReviewer()
    lecturer, student = make_pair(reviewer, clock)
    send_many(student, 4)
    response = make_report(lecturer)
    data = response.get_json()
    assert response.status_code == 200 and data["report"]["state"] == "done" and data["count"] == 4
    assert data["report"]["text"] == "A report about the whole class 1"
    request, works = reviewer.reports[0]
    assert request == reviewer.task and len(works) == 4  # the text the AI read from the PDF, and every work
    assert len(reviewer.reports) == 1 and not reviewer.compares  # one call for the whole class


def test_before_the_due_date_the_report_is_closed(clock):
    reviewer = ReportReviewer()
    lecturer, student = make_pair(reviewer, clock)
    send_many(student, 2, assignment="Later")
    assert get_report(lecturer, "Later")["opens"] is False
    refused = make_report(lecturer, "Later")
    assert refused.status_code == 409 and date_of(clock, 3) in refused.get_json()["error"]
    assert reviewer.reports == []
    clock.t += 3 * DAY  # the due date came
    assert get_report(lecturer, "Later")["opens"] is True and make_report(lecturer, "Later").status_code == 200


def test_the_report_needs_a_published_assignment_with_works(clock):
    lecturer, _student = make_pair(ReportReviewer(), clock)
    assert make_report(lecturer, "Empty").status_code == 409  # nobody sent a work
    assert make_report(lecturer, "Nope").status_code == 404
    assert make_report(lecturer, "  ").status_code == 404
    assert lecturer.get("/api/homework/report", query_string={"assignment": "Nope"}).status_code == 404


def test_without_a_key_the_report_says_it_is_not_set_up(clock, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    lecturer, _student = make_pair(None, clock)
    assert make_report(lecturer).status_code == 503


def test_the_list_for_the_lecturer_has_counts_but_no_students(clock):
    lecturer, student = make_pair(ReportReviewer(), clock)
    send_many(student, 3)
    data = lecturer.get("/api/homework/assignments").get_json()
    by_name = {a["name"]: a for a in data["assignments"]}
    assert by_name["Ex2"]["count"] == 3 and by_name["Ex2"]["opens"] is True and by_name["Later"]["opens"] is False
    assert "@" not in json.dumps(data)


def test_the_report_can_be_read_again_and_made_again_with_more_works(clock):
    reviewer = ReportReviewer()
    lecturer, student = make_pair(reviewer, clock)
    send_many(student, 2)
    make_report(lecturer)
    again = get_report(lecturer, "ex2")
    assert again["report"]["text"].endswith("1") and again["count"] == 2
    send_many(student, 3)
    second = make_report(lecturer).get_json()
    assert second["report"]["text"].endswith("2") and len(reviewer.reports[1][1]) == 3


def test_a_failed_report_keeps_the_old_one_and_can_be_tried_again(clock):
    reviewer = ReportReviewer()
    lecturer, student = make_pair(reviewer, clock)
    send_many(student, 2)
    assert make_report(lecturer).status_code == 200
    reviewer.error = "The AI is busy."
    failed = make_report(lecturer)
    assert failed.status_code == 502 and "busy" in failed.get_json()["error"]
    state = get_report(lecturer)["report"]
    assert state["state"] == "error" and state["text"].endswith("1")  # the good report is still there
    reviewer.error = None
    assert make_report(lecturer).status_code == 200


def test_a_crash_does_not_leave_the_report_waiting(clock):
    class Crashing(ReportReviewer):
        def report(self, request, works):
            raise RuntimeError("boom")

    lecturer, student = make_pair(Crashing(), clock)
    send_many(student, 1)
    assert make_report(lecturer).status_code == 502
    assert get_report(lecturer)["report"]["state"] == "error"


def test_a_slow_ai_answers_at_once_and_the_page_asks_again(clock):
    class Slow(ReportReviewer):
        def report(self, request, works):
            time.sleep(0.3)
            return super().report(request, works)

    lecturer, student = make_pair(Slow(), clock, background=True)
    send_many(student, 2)
    started = make_report(lecturer)
    assert started.status_code == 202 and started.get_json()["working"] is True
    assert make_report(lecturer).status_code == 409  # one report at a time
    for _ in range(50):
        state = get_report(lecturer)["report"]
        if state["state"] != "working":
            break
        time.sleep(0.1)
    assert state["state"] == "done"


# ---- the store and the AI requests ----

def test_the_store_lists_works_without_names_and_cuts_each_work():
    store = HomeworkStore()
    store.save("Ex2", "a@example.com", "x" * (MAX_REPORT_WORK_CHARS + 500), 1)
    store.save("Ex2", "b@example.com", "second work", 2)
    texts = store.report_texts("EX2")
    assert len(texts) == 2 and len(texts[0]) == MAX_REPORT_WORK_CHARS and texts[1] == "second work"


def test_the_store_has_a_limit_of_published_assignments():
    store = HomeworkStore()
    for n in range(30):
        store.publish("Ex%d" % n, "OOP", "2030-01-01", "text", 0)
    store.publish("Ex3", "OOP", "2031-01-01", "text", 0)  # the same name again is fine
    with pytest.raises(HomeworkError, match="limit"):
        store.publish("Ex99", "OOP", "2030-01-01", "text", 0)


def test_the_pdf_request_has_the_file_inside_and_asks_for_json_with_the_date():
    seen = {}

    def post(url, headers, body, timeout):
        seen.update(body=json.loads(body), timeout=timeout)
        return answer(json.dumps({"text": "Write a program.", "due_date": "2026-11-25"}))

    info = GeminiReviewer("k", http_post=post).read_assignment(b"%PDF-1.4 hello")
    assert info == {"text": "Write a program.", "due": "2026-11-25"}
    parts = seen["body"]["contents"][0]["parts"]
    assert parts[0]["inline_data"]["mime_type"] == "application/pdf"
    assert base64.b64decode(parts[0]["inline_data"]["data"]) == b"%PDF-1.4 hello"
    assert "day first" in parts[1]["text"] and seen["body"]["generationConfig"]["responseMimeType"] == "application/json"


@pytest.mark.parametrize("due", ["", "next week", "31/11/2026", "2026-13-40"])
def test_an_unclear_date_from_the_ai_means_no_date(due):
    reply = answer(json.dumps({"text": "Write a program.", "due_date": due}))
    assert GeminiReviewer("k", http_post=lambda *a: reply).read_assignment(b"%PDF-1")["due"] is None


@pytest.mark.parametrize("reply", [(200, b"{}"), (200, b"not json"), answer("not json"), answer(json.dumps({"x": 1}))])
def test_an_unclear_answer_for_the_pdf_is_a_service_error(reply):
    with pytest.raises(ReviewServiceError):
        GeminiReviewer("k", http_post=lambda *a: reply).read_assignment(b"%PDF-1")


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


def test_every_ai_request_asks_for_plain_text_without_markdown():
    prompts = []

    def post(url, headers, body, timeout):
        prompts.append(prompt_of(body))
        return answer("ok")

    reviewer = GeminiReviewer("k", http_post=post)
    reviewer.review("work")
    reviewer.overview(["work"])
    reviewer.compare("work", "overview")
    reviewer.report("task text here", ["work"])
    assert len(prompts) == 4 and all("plain text only" in p and "no LaTeX" in p for p in prompts)
