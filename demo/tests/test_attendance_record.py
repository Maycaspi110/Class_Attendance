from datetime import datetime

import pytest

from attendance.attendance_record import FLAGGED, PRESENT, AttendanceRecord
from attendance.student import Student

STUDENT = Student("Dana Levi", "0500000001")
WHEN = datetime(2026, 1, 1, 10, 2)


def test_saved_values_are_read_back():
    record = AttendanceRecord(STUDENT, PRESENT, WHEN, 12, "a note")
    assert record.student == STUDENT
    assert record.status == "Present"
    assert record.check_in_time == WHEN
    assert record.distance_meters == 12
    assert record.note == "a note"


@pytest.mark.parametrize("status", [PRESENT, FLAGGED])
def test_allowed_status_is_accepted(status):
    assert AttendanceRecord(STUDENT, status, WHEN).status == status


@pytest.mark.parametrize("status", ["Absent", "present", "", "Late"])
def test_other_status_is_not_accepted(status):
    with pytest.raises(ValueError):
        AttendanceRecord(STUDENT, status, WHEN)
