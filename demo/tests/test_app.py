"""Integration tests: whole flows through the web app (made-up students only)."""
import csv
import io
import re

import pytest

from app import create_app

from .conftest import CLASSROOM, FAR_AWAY, NEAR, NOW, PERIOD, ROSTER_CSV

PASSWORD = "test-password"


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


@pytest.fixture
def clock():
    return Clock(NOW)


@pytest.fixture
def app(clock):
    return create_app(
        {
            "TESTING": True,
            "LECTURER_PASSWORD": PASSWORD,
            "CODE_SECRET": "test-secret",
            "CODE_PERIOD_SECONDS": PERIOD,
            "CLOCK": clock,
            "TIMEZONE": "UTC",
        }
    )


@pytest.fixture
def student(app):
    """A client with no login, like a student's phone."""
    return app.test_client()


@pytest.fixture
def lecturer(app):
    client = app.test_client()
    response = client.post("/login", data={"password": PASSWORD})
    assert response.status_code == 302
    return client


def upload_roster(client, text=ROSTER_CSV):
    preview = client.post(
        "/api/roster/preview",
        data={"file": (io.BytesIO(text.encode("utf-8")), "roster.csv")},
        content_type="multipart/form-data",
    )
    return preview


def confirm_roster(client, text=ROSTER_CSV):
    assert upload_roster(client, text).get_json()["can_confirm"]
    return client.post("/api/roster/confirm")


def start_session(client, point=CLASSROOM, accuracy=10):
    return client.post("/api/session/start", json={"lat": point[0], "lon": point[1], "accuracy": accuracy})


def check_in(client, phone, code, point=NEAR, accuracy=10):
    body = {"phone": phone, "code": code}
    if point is not None:
        body.update(lat=point[0], lon=point[1], accuracy=accuracy)
    return client.post("/api/checkin", json=body)


def screen_code(lecturer):
    data = lecturer.get("/api/code").get_json()
    assert data["open"]
    return data["code"]


def results(lecturer):
    return lecturer.get("/api/results").get_json()


# ---- the lecturer password -----------------------------------------------------


@pytest.mark.parametrize("path", ["/lecturer", "/screen"])
def test_lecturer_pages_need_the_password(student, path):
    response = student.get(path)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/api/code"),
        ("get", "/api/results"),
        ("get", "/api/state"),
        ("get", "/api/session/csv"),
        ("post", "/api/session/start"),
        ("post", "/api/session/end"),
        ("post", "/api/roster/preview"),
        ("post", "/api/roster/confirm"),
        ("post", "/api/poll"),
        ("post", "/api/poll/close"),
        ("get", "/api/poll/results"),
    ],
)
def test_lecturer_api_needs_the_password(student, method, path):
    assert getattr(student, method)(path).status_code == 401


def test_wrong_password_is_refused(student):
    response = student.post("/login", data={"password": "nope"})
    assert response.status_code == 401
    assert student.get("/lecturer").status_code == 302


def test_right_password_opens_the_lecturer_page(lecturer):
    assert lecturer.get("/lecturer").status_code == 200
    assert lecturer.get("/screen").status_code == 200


def test_login_does_not_redirect_to_other_sites(student):
    response = student.post("/login?next=https://evil.example/", data={"password": PASSWORD})
    assert response.headers["Location"].endswith("/lecturer")


def test_too_many_wrong_passwords_are_blocked(student):
    for _ in range(10):
        assert student.post("/login", data={"password": "nope"}).status_code == 401
    response = student.post("/login", data={"password": PASSWORD})
    assert response.status_code == 401  # blocked even with the right password


def test_logout_closes_the_lecturer_pages(lecturer):
    lecturer.get("/logout")
    assert lecturer.get("/lecturer").status_code == 302


def test_student_page_is_public_and_has_security_headers(student):
    response = student.get("/checkin")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


# ---- the roster ------------------------------------------------------------------


def test_roster_preview_then_confirm(lecturer):
    preview = upload_roster(lecturer).get_json()
    assert preview["count"] == 4 and preview["can_confirm"]
    assert lecturer.get("/api/state").get_json()["roster_count"] == 0  # not saved yet
    assert lecturer.post("/api/roster/confirm").get_json()["count"] == 4
    assert lecturer.get("/api/state").get_json()["roster_count"] == 4


def test_roster_with_a_repeated_number_cannot_be_confirmed(lecturer):
    preview = upload_roster(lecturer, ROSTER_CSV + "Copy,0500000001\n").get_json()
    assert preview["warnings"] and not preview["can_confirm"]
    assert lecturer.post("/api/roster/confirm").status_code == 400


def test_roster_without_the_phone_column_is_refused(lecturer):
    response = upload_roster(lecturer, "Name,Email\nDana,d@example.com\n")
    assert response.status_code == 400
    assert "Phone number" in response.get_json()["error"]


def test_roster_upload_without_a_file_is_refused(lecturer):
    assert lecturer.post("/api/roster/preview").status_code == 400


def test_the_roster_cannot_change_during_a_session(lecturer):
    confirm_roster(lecturer)
    start_session(lecturer)
    upload_roster(lecturer)
    assert lecturer.post("/api/roster/confirm").status_code == 409


# ---- the attendance session -------------------------------------------------------


def test_cannot_start_a_session_without_a_roster(lecturer):
    response = start_session(lecturer)
    assert response.status_code == 400
    assert "roster" in response.get_json()["error"]


def test_cannot_start_with_a_bad_location(lecturer):
    confirm_roster(lecturer)
    assert lecturer.post("/api/session/start", json={}).status_code == 400
    assert start_session(lecturer, accuracy=5000).status_code == 400


def test_cannot_start_a_second_session_while_one_is_open(lecturer):
    confirm_roster(lecturer)
    assert start_session(lecturer).status_code == 200
    assert start_session(lecturer).status_code == 409


def test_the_screen_shows_no_code_before_the_session(lecturer):
    confirm_roster(lecturer)
    assert lecturer.get("/api/code").get_json()["open"] is False


def test_the_screen_gets_a_four_digit_code_and_a_link(lecturer):
    confirm_roster(lecturer)
    start_session(lecturer)
    data = lecturer.get("/api/code").get_json()
    assert re.fullmatch(r"\d{4}", data["code"])
    assert data["link"].endswith("/checkin?code=" + data["code"])
    assert 1 <= data["seconds_left"] <= PERIOD


def test_full_attendance_flow(lecturer, student):
    """Roster, session, three check-ins (near, far, wrong code), end, CSV."""
    confirm_roster(lecturer)
    assert start_session(lecturer).status_code == 200
    code = screen_code(lecturer)

    near = check_in(student, "0500000001", code, NEAR)
    far = check_in(student, "0500000002", code, FAR_AWAY)
    wrong = check_in(student, "0500000003", "0000" if code != "0000" else "1111", NEAR)

    assert near.get_json()["status"] == "Present"
    assert far.get_json()["status"] == "Flagged"
    assert wrong.status_code == 400 and wrong.get_json()["reason"] == "bad_code"

    data = results(lecturer)
    assert [r["name"] for r in data["present"]] == ["Dana Levi"]
    assert [r["name"] for r in data["flagged"]] == ["Noa Cohen"]
    assert [s["name"] for s in data["absent"]] == ["Ron Mizrahi", "Lior Peretz"]

    assert lecturer.post("/api/session/end").status_code == 200
    late = check_in(student, "0500000004", code, NEAR)
    assert late.status_code == 400 and late.get_json()["reason"] == "session_closed"

    response = lecturer.get("/api/session/csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    assert response.data.startswith(b"\xef\xbb\xbf")
    rows = list(csv.reader(io.StringIO(response.data.decode("utf-8-sig"))))
    assert rows[0][:3] == ["Phone number", "Name", "Status"]
    statuses = {r[0]: r[2] for r in rows[1:]}
    assert statuses == {
        "0500000001": "Present",
        "0500000002": "Flagged",
        "0500000003": "Absent",
        "0500000004": "Absent",
    }


def test_changing_code_previous_is_accepted_older_is_not(lecturer, student, clock):
    confirm_roster(lecturer)
    start_session(lecturer)
    first_code = screen_code(lecturer)

    clock.t = NOW + PERIOD  # the code changed once
    assert screen_code(lecturer) != first_code
    accepted = check_in(student, "0500000001", first_code)
    assert accepted.status_code == 200

    clock.t = NOW + 2 * PERIOD  # the code changed twice
    rejected = check_in(student, "0500000002", first_code)
    assert rejected.status_code == 400 and rejected.get_json()["reason"] == "bad_code"


def test_check_in_twice_gives_already_recorded(lecturer, student):
    confirm_roster(lecturer)
    start_session(lecturer)
    code = screen_code(lecturer)
    assert check_in(student, "0500000001", code).status_code == 200
    again = check_in(student, "0500000001", code)
    assert again.status_code == 409 and again.get_json()["reason"] == "already_recorded"
    assert again.get_json()["record_status"] == "Present"
    assert len(results(lecturer)["present"]) == 1


def test_unknown_phone_number_is_refused(lecturer, student):
    confirm_roster(lecturer)
    start_session(lecturer)
    response = check_in(student, "0509999999", screen_code(lecturer))
    assert response.status_code == 400 and response.get_json()["reason"] == "not_on_roster"


def test_check_in_without_location_is_flagged(lecturer, student):
    confirm_roster(lecturer)
    start_session(lecturer)
    response = check_in(student, "0500000001", screen_code(lecturer), point=None)
    assert response.get_json()["status"] == "Flagged"


@pytest.mark.parametrize("body", [None, [], "text", {"phone": "0500000001"}])
def test_strange_check_in_requests_do_not_crash(lecturer, student, body):
    confirm_roster(lecturer)
    start_session(lecturer)
    response = student.post("/api/checkin", json=body)
    assert response.status_code == 400


def test_nonsense_location_values_are_flagged_not_crashing(lecturer, student):
    confirm_roster(lecturer)
    start_session(lecturer)
    code = screen_code(lecturer)
    response = student.post(
        "/api/checkin",
        json={"phone": "0500000001", "code": code, "lat": "x", "lon": True, "accuracy": float("nan")},
    )
    assert response.status_code == 200 and response.get_json()["status"] == "Flagged"


def test_names_with_html_are_returned_as_plain_text(lecturer):
    confirm_roster(lecturer, 'Name,Phone number\n"<b>Dana</b>",0500000001\n')
    data = results(lecturer)
    assert data["absent"][0]["name"] == "<b>Dana</b>"  # the page shows it with textContent


# ---- polls --------------------------------------------------------------------------


def create_poll(lecturer):
    return lecturer.post("/api/poll", json={"question": "Did you understand?", "options": ["Yes", "A little", "No"]})


def test_poll_flow(lecturer, student):
    confirm_roster(lecturer)
    assert student.get("/api/poll/current").get_json()["open"] is False
    assert create_poll(lecturer).status_code == 200

    current = student.get("/api/poll/current").get_json()
    assert current["open"] and current["options"] == ["Yes", "A little", "No"]

    def answer(phone, option):
        return student.post("/api/poll/answer", json={"id": current["id"], "phone": phone, "option": option})

    assert answer("0500000001", "Yes").status_code == 200
    assert answer("0500000002", "Yes").status_code == 200
    assert answer("0500000003", "No").status_code == 200
    assert answer("0500000001", "No").status_code == 409  # one answer only

    shown = lecturer.get("/api/poll/results").get_json()["poll"]
    assert shown["counts"] == [2, 0, 1] and shown["total"] == 3

    assert lecturer.post("/api/poll/close").status_code == 200
    assert student.get("/api/poll/current").get_json()["open"] is False
    assert answer("0500000004", "Yes").status_code == 400  # closed


def test_poll_answer_needs_a_roster_phone_number(lecturer, student):
    confirm_roster(lecturer)
    create_poll(lecturer)
    current = student.get("/api/poll/current").get_json()
    response = student.post("/api/poll/answer", json={"id": current["id"], "phone": "0509999999", "option": "Yes"})
    assert response.status_code == 403


def test_students_do_not_get_the_counts_while_the_poll_is_open(lecturer, student):
    confirm_roster(lecturer)
    create_poll(lecturer)
    assert "counts" not in student.get("/api/poll/current").get_json()


def test_a_new_poll_replaces_the_old_one(lecturer, student):
    confirm_roster(lecturer)
    create_poll(lecturer)
    old_id = student.get("/api/poll/current").get_json()["id"]
    lecturer.post("/api/poll", json={"question": "Next?", "options": ["A", "B"]})
    response = student.post("/api/poll/answer", json={"id": old_id, "phone": "0500000001", "option": "Yes"})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "body",
    [{}, {"question": "Q?", "options": ["only one"]}, {"question": "", "options": ["A", "B"]}, {"question": "Q?", "options": "AB"}],
)
def test_bad_polls_are_refused(lecturer, body):
    assert lecturer.post("/api/poll", json=body).status_code == 400
