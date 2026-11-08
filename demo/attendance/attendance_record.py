"""AttendanceRecord: one check-in of one student."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .student import Student

PRESENT = "Present"
FLAGGED = "Flagged"
ABSENT = "Absent"  # never saved in a record: absent = on the roster, no record

SAVED_STATUSES = (PRESENT, FLAGGED)


@dataclass(frozen=True)
class AttendanceRecord:
    student: Student
    status: str
    check_in_time: datetime
    distance_meters: Optional[int] = None
    note: str = ""

    def __post_init__(self):
        if self.status not in SAVED_STATUSES:
            raise ValueError("A record status must be Present or Flagged, not %r." % (self.status,))
