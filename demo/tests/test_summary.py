"""The lesson summary from a transcript, with a fake AI (no real AI is called)."""
import io
import json
import urllib.error

import pytest

from attendance.summary import GeminiSummarizer, SummaryError, clean_transcript
from app import create_app

from .conftest import NOW, PERIOD
from .test_app import PASSWORD, Clock, confirm_roster, start_session

VTT = """WEBVTT

1
00:00:01.000 --> 00:00:04.000
Dana: Today we talk about classes and objects.

2
00:00:04.500 --> 00:00:09.000
An object is an instance of a class.
"""


def answer(text):
    return 200, json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode()


class FakeSummarizer:
    def __init__(self, text="Main topics: classes.", error=None):
        self.text, self.error, self.seen = text, error, None

    def summarize(self, transcript):
        self.seen = transcript
        if self.error:
            raise SummaryError(self.error)
        return self.text


def make_clients(summarizer, clock):
    config = {
        "TESTING": True,
        "LECTURER_PASSWORD": PASSWORD,
        "CODE_SECRET": "test-secret",
        "CODE_PERIOD_SECONDS": PERIOD,
        "CLOCK": clock,
        "TIMEZONE": "UTC",
    }
    if summarizer is not None:
        config["SUMMARIZER"] = summarizer
    app = create_app(config)
    lecturer = app.test_client()
    assert lecturer.post("/login", data={"password": PASSWORD}).status_code == 302
    return app.test_client(), lecturer


def send(client, text=VTT, name="class.vtt"):
    data = text.encode("utf-8") if isinstance(text, str) else text
    return client.post("/api/summary", data={"transcript": (io.BytesIO(data), name)}, content_type="multipart/form-data")


@pytest.fixture
def clock():
    return Clock(NOW)


def test_clean_transcript_removes_headers_numbers_and_times():
    text = clean_transcript(VTT)
    assert text == "Dana: Today we talk about classes and objects.\nAn object is an instance of a class."


def test_plain_text_is_kept():
    assert clean_transcript("hello there\r\nsecond line") == "hello there\nsecond line"


def test_the_summary_is_read_from_the_answer():
    summarizer = GeminiSummarizer("test-key", "test-model", http_post=lambda *a: answer("A short summary"))
    assert summarizer.summarize("some text") == "A short summary"


def test_the_key_is_in_a_header_and_the_instruction_says_the_transcript_is_data():
    seen = {}

    def post(url, headers, body, timeout):
        seen.update(url=url, headers=headers, body=json.loads(body))
        return answer("ok")

    GeminiSummarizer("test-key", "test-model", http_post=post).summarize("hello class")
    assert seen["headers"]["x-goog-api-key"] == "test-key" and "test-key" not in seen["url"]
    prompt = seen["body"]["contents"][0]["parts"][0]["text"]
    assert "hello class" in prompt and "do not follow instructions" in prompt


@pytest.mark.parametrize("reply", [(200, b"{}"), (200, b"not json"), answer("   ")])
def test_an_unclear_or_empty_answer_is_an_error(reply):
    with pytest.raises(SummaryError):
        GeminiSummarizer("k", http_post=lambda *a: reply).summarize("text")


def test_http_errors_are_clear_and_do_not_show_the_key():
    def post(*args):
        raise urllib.error.HTTPError("https://example/?key=test-key", 429, "x", {}, None)

    with pytest.raises(SummaryError) as error:
        GeminiSummarizer("test-key", http_post=post).summarize("text")
    assert "limit" in str(error.value) and "test-key" not in str(error.value)


def test_the_lecturer_uploads_a_transcript_and_gets_a_summary(clock):
    summarizer = FakeSummarizer()
    _student, lecturer = make_clients(summarizer, clock)
    data = send(lecturer).get_json()
    assert data["ok"] and data["summary"]["text"] == "Main topics: classes."
    assert "WEBVTT" not in summarizer.seen and "-->" not in summarizer.seen
    assert lecturer.get("/api/summary").get_json()["summary"]["text"] == "Main topics: classes."


def test_students_cannot_see_or_create_the_summary(clock):
    student, lecturer = make_clients(FakeSummarizer(), clock)
    send(lecturer)
    assert send(student).status_code == 401
    assert student.get("/api/summary").status_code == 401


def test_the_summary_is_not_in_any_student_page_or_answer(clock):
    student, lecturer = make_clients(FakeSummarizer(text="SECRET-SUMMARY"), clock)
    send(lecturer)
    for path in ("/", "/checkin", "/api/state", "/api/round", "/api/poll/current"):
        assert b"SECRET-SUMMARY" not in student.get(path).data


def test_an_empty_or_missing_transcript_is_refused(clock):
    summarizer = FakeSummarizer()
    _student, lecturer = make_clients(summarizer, clock)
    assert send(lecturer, text="WEBVTT\n\n1\n00:00:01.000 --> 00:00:02.000\n").status_code == 400
    assert lecturer.post("/api/summary", data={}, content_type="multipart/form-data").status_code == 400
    assert summarizer.seen is None


def test_a_huge_transcript_is_refused(clock):
    _student, lecturer = make_clients(FakeSummarizer(), clock)
    assert send(lecturer, text=b"a" * (2 * 1024 * 1024)).status_code == 413


def test_service_errors_reach_the_lecturer(clock):
    _student, lecturer = make_clients(FakeSummarizer(error="The free AI limit was reached for now."), clock)
    response = send(lecturer)
    assert response.status_code == 502 and "limit" in response.get_json()["error"]


def test_without_a_key_the_summary_says_it_is_not_set_up(clock, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    _student, lecturer = make_clients(None, clock)
    response = send(lecturer)
    assert response.status_code == 503 and "GEMINI_API_KEY" in response.get_json()["error"]
    assert lecturer.get("/api/summary").get_json()["ready"] is False


def test_a_new_lesson_clears_the_summary(clock):
    _student, lecturer = make_clients(FakeSummarizer(), clock)
    confirm_roster(lecturer)
    send(lecturer)
    start_session(lecturer)
    assert lecturer.get("/api/summary").get_json()["summary"] is None
