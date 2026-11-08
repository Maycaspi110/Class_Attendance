from datetime import datetime

import pytest

from attendance.attendance_record import PRESENT, AttendanceRecord
from attendance.session import CLOSED, OPEN, Session
from attendance.student import Student

STUDENT = Student("Dana Levi", "0500000001")


def test_a_new_session_is_closed():
    assert not Session().is_open()


def test_start_opens_the_session_and_saves_the_location():
    session = Session()
    session.start((32.1, 35.2))
    assert session.is_open()
    assert session.status == OPEN
    assert session.classroom_location == (32.1, 35.2)
    assert session.start_time is not None


def test_end_closes_an_open_session():
    session = Session()
    session.start((32.1, 35.2))
    session.end()
    assert not session.is_open()
    assert session.status == CLOSED
    assert session.end_time is not None


def test_one_record_per_student():
    session = Session()
    session.start((32.1, 35.2))
    record = AttendanceRecord(STUDENT, PRESENT, datetime.now())
    session.add_record(record)
    with pytest.raises(ValueError):
        session.add_record(record)
    assert session.records == [record]
    assert session.record_for("0500000001") == record


def test_starting_again_clears_the_old_records():
    session = Session()
    session.start((32.1, 35.2))
    session.add_record(AttendanceRecord(STUDENT, PRESENT, datetime.now()))
    session.start((32.1, 35.2))
    assert session.records == []
