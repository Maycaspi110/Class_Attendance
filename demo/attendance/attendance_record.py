"""AttendanceRecord: one check-in of one student. LessonEntry: one student in the whole lesson."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .student import Student

PRESENT = "Present"
FLAGGED = "Flagged"
ABSENT = "Absent"  # never saved in a record: absent = on the roster, no record
LATE = "Late"  # lesson status: checked in only at the end of the class
LEFT_EARLY = "Left early"  # lesson status: checked in only at the start of the class

SAVED_STATUSES = (PRESENT, FLAGGED)


@dataclass(frozen=True)
class AttendanceRecord:
    student: Student
    status: str
    check_in_time: datetime
    distance_meters: Optional[int] = None
    note: str = ""
    comment: str = ""  # the student's comment about the lesson (end-of-class check-in only)

    def __post_init__(self):
        if self.status not in SAVED_STATUSES:
            raise ValueError("A record status must be Present or Flagged, not %r." % (self.status,))


def lesson_status(start_record, end_record, end_finished):
    """
    The status of one student in the whole lesson.
    A far or unclear location (Flagged) always wins, so the lecturer sees it.
    Without a finished end-of-class check-in, the status is the one of the start check-in.
    """
    records = [r for r in (start_record, end_record) if r is not None]
    if not records:
        return ABSENT
    if any(r.status == FLAGGED for r in records):
        return FLAGGED
    if start_record is not None and end_record is not None:
        return PRESENT
    if start_record is not None:
        return LEFT_EARLY if end_finished else PRESENT  # the end check-in may still come
    return LATE


@dataclass(frozen=True)
class LessonEntry:
    """One roster student with the status for the whole lesson and the two (optional) records."""

    student: Student
    status: str
    start: Optional[AttendanceRecord] = None
    end: Optional[AttendanceRecord] = None

    @property
    def distance_meters(self):
        first = self.start or self.end
        return None if first is None else first.distance_meters

    @property
    def note(self):
        notes = [r.note for r in (self.start, self.end) if r is not None and r.note]
        if len(notes) == 2 and notes[0] != notes[1]:
            return "Start: %s; End: %s" % (notes[0], notes[1])
        return notes[0] if notes else ""

    @property
    def comment(self):
        return self.end.comment if self.end is not None else ""
