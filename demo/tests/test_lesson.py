"""The lesson has a start check-in and an end check-in; the status joins both."""
import csv
import io

import pytest

from attendance.attendance_manager import CheckInError, SessionError
from attendance.csv_exporter import BOM, CsvExporter
from attendance.session import END_ROUND, START_ROUND

from .conftest import CLASSROOM, FAR_AWAY, NEAR, NOW

DANA, NOA, RON, LIOR = (
    "dana.levi@example.com",
    "noa.cohen@example.com",
    "ron.mizrahi@example.com",
    "lior.peretz@example.com",
)


def code(manager, t):
    return manager.code_generator.current_code(t)


def run_start(manager, who, t=NOW):
    manager.start_session(CLASSROOM, 10, now=t)
    for email, point in who:
        manager.check_in(email, code(manager, t), point, 10, now=t)
    manager.end_session(now=t + 1)


def run_end(manager, who, t=NOW + 3000, comments=None):
    manager.start_session(CLASSROOM, 10, now=t, round_name=END_ROUND)
    for email, point in who:
        manager.check_in(email, code(manager, t), point, 10, now=t, comment=(comments or {}).get(email, ""))
    manager.end_session(now=t + 1)


def statuses(manager):
    return {e.student.email: e.status for e in manager.lesson_entries()}


def test_present_late_left_early_and_absent(manager):
    run_start(manager, [(DANA, NEAR), (NOA, NEAR)])
    run_end(manager, [(DANA, NEAR), (RON, NEAR)])
    assert statuses(manager) == {DANA: "Present", NOA: "Left early", RON: "Late", LIOR: "Absent"}


def test_without_an_end_round_the_status_is_the_start_status(manager):
    run_start(manager, [(DANA, NEAR), (NOA, FAR_AWAY)])
    assert statuses(manager) == {DANA: "Present", NOA: "Flagged", RON: "Absent", LIOR: "Absent"}


def test_while_the_end_round_is_open_nobody_is_left_early_yet(manager):
    run_start(manager, [(DANA, NEAR)])
    manager.start_session(CLASSROOM, 10, now=NOW + 3000, round_name=END_ROUND)
    assert statuses(manager)[DANA] == "Present"
    manager.check_in(NOA, code(manager, NOW + 3000), NEAR, 10, now=NOW + 3000)
    assert statuses(manager)[NOA] == "Late"


def test_a_far_location_in_any_round_is_flagged(manager):
    run_start(manager, [(DANA, NEAR)])
    run_end(manager, [(DANA, FAR_AWAY)])
    assert statuses(manager)[DANA] == "Flagged"


def test_a_new_start_round_begins_a_new_lesson(manager):
    run_start(manager, [(DANA, NEAR)])
    run_end(manager, [(DANA, NEAR)])
    run_start(manager, [(NOA, NEAR)], t=NOW + 9000)
    assert statuses(manager) == {DANA: "Absent", NOA: "Present", RON: "Absent", LIOR: "Absent"}
    assert END_ROUND not in manager.rounds and START_ROUND in manager.rounds


def test_a_student_can_check_in_once_in_each_round(manager):
    run_start(manager, [(DANA, NEAR)])
    manager.start_session(CLASSROOM, 10, now=NOW + 3000, round_name=END_ROUND)
    manager.check_in(DANA, code(manager, NOW + 3000), NEAR, 10, now=NOW + 3000)
    with pytest.raises(CheckInError) as error:
        manager.check_in(DANA, code(manager, NOW + 3000), NEAR, 10, now=NOW + 3000)
    assert error.value.reason == "already_recorded"


def test_a_round_cannot_start_while_another_is_open(manager):
    manager.start_session(CLASSROOM, 10, now=NOW)
    with pytest.raises(SessionError):
        manager.start_session(CLASSROOM, 10, now=NOW + 5, round_name=END_ROUND)


def test_unknown_round_name_is_refused(manager):
    with pytest.raises(SessionError):
        manager.start_session(CLASSROOM, 10, now=NOW, round_name="middle")


def test_comment_is_kept_only_in_the_end_round(manager):
    manager.start_session(CLASSROOM, 10, now=NOW)
    record = manager.check_in(DANA, code(manager, NOW), NEAR, 10, now=NOW, comment="hello")
    assert record.comment == ""
    manager.end_session(now=NOW + 1)
    run_end(manager, [(DANA, NEAR)], comments={DANA: "The lesson was great"})
    entry = next(e for e in manager.lesson_entries() if e.student.email == DANA)
    assert entry.comment == "The lesson was great"


def test_comment_is_cleaned_and_shortened(manager):
    run_end(manager, [(DANA, NEAR)], comments={DANA: "  too   many\n spaces " + "x" * 400})
    comment = next(e for e in manager.lesson_entries() if e.student.email == DANA).comment
    assert comment.startswith("too many spaces x") and len(comment) == 300


def test_csv_has_both_times_and_the_comment(manager):
    run_start(manager, [(DANA, NEAR)])
    run_end(manager, [(DANA, NEAR), (RON, NEAR)], comments={RON: "=1+1"})
    text = CsvExporter().export(manager.lesson_entries()).decode("utf-8")
    rows = {r[0]: r for r in csv.reader(io.StringIO(text[len(BOM):]))}
    assert rows[DANA][2:5] == ["Present", rows[DANA][3], rows[DANA][4]] and rows[DANA][3] and rows[DANA][4]
    assert rows[RON][2] == "Late" and rows[RON][3] == "" and rows[RON][4] != ""
    assert rows[RON][7] == "'=1+1"  # a comment that looks like a formula is made safe
