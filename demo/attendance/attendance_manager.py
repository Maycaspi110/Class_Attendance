"""AttendanceManager: the main logic of a check-in.

For every check-in the order of the checks follows the sequence diagram in
diagrams.md: session open, roster, code, location, then save one record.
"""
import threading
import time
from datetime import datetime

from . import location_checker as lc
from .attendance_record import ABSENT, FLAGGED, PRESENT, AttendanceRecord
from .code_generator import INVALID
from .session import Session

# Extra protection: a code has only 10,000 possible values, so a student who
# types many wrong codes in a row has to wait a short time.
MAX_WRONG_CODES = 5
WRONG_CODE_WINDOW_SECONDS = 60


class CheckInError(Exception):
    """A check-in that is not accepted. `reason` is a short fixed word."""

    def __init__(self, reason, message, record=None):
        super().__init__(message)
        self.reason = reason
        self.message = message
        self.record = record  # the existing record, for "already_recorded"


class SessionError(Exception):
    """The session cannot be started (for example no roster)."""


class AttendanceManager:
    def __init__(self, roster, code_generator, location_checker, tz=None):
        self.roster = roster
        self.code_generator = code_generator
        self.location_checker = location_checker
        self.tz = tz  # time zone for the check-in times (None = this computer)
        self.session = None
        self._wrong_codes = {}  # phone number -> list of times of wrong codes
        self._lock = threading.RLock()

    # ---- the lecturer side -------------------------------------------------

    def start_session(self, location, accuracy, now=None):
        """Open a new session. The lecturer's phone location is the classroom."""
        now = time.time() if now is None else now
        with self._lock:
            if len(self.roster) == 0:
                raise SessionError("Upload and confirm the roster before starting a session.")
            if location is None or not lc.valid_point(*location):
                raise SessionError("The phone location is missing. Allow location and try again.")
            if not self.location_checker.accuracy_ok(accuracy):
                raise SessionError("The phone location is too inaccurate. Try again outdoors or near a window.")
            session = Session()
            session.start(location, self._datetime(now))
            self.session = session
            self._wrong_codes = {}
            return session

    def end_session(self, now=None):
        now = time.time() if now is None else now
        with self._lock:
            if self.session is None or not self.session.is_open():
                raise SessionError("There is no open session.")
            self.session.end(self._datetime(now))
            return self.session

    # ---- the student side --------------------------------------------------

    def check_in(self, phone, code, location, accuracy, now=None):
        """
        Check in one student. Returns the saved AttendanceRecord, or raises
        CheckInError with a clear message for the student.
        """
        now = time.time() if now is None else now
        with self._lock:
            session = self.session
            if session is None or not session.is_open():
                raise CheckInError("session_closed", "There is no open attendance session now.")

            student = self.roster.find_by_phone(phone)
            if student is None:
                raise CheckInError("not_on_roster", "This phone number is not on the roster.")

            self._check_not_locked(student.phone_number, now)
            if self.code_generator.check_code(code, now) == INVALID:
                self._remember_wrong_code(student.phone_number, now)
                raise CheckInError(
                    "bad_code",
                    "Wrong or expired code. Look at the classroom screen and try again.",
                )

            result = self.location_checker.check(location, accuracy, session.classroom_location)

            existing = session.record_for(student.phone_number)
            if existing is not None:
                raise CheckInError("already_recorded", "You are already recorded in this session.", existing)

            if result.status == lc.GOOD:
                status, note = PRESENT, ""
            elif result.status == lc.FAR:
                status, note = FLAGGED, "Valid code but location far from the classroom"
            else:
                status, note = FLAGGED, "Valid code but location missing or too inaccurate"

            record = AttendanceRecord(
                student=student,
                status=status,
                check_in_time=self._datetime(now),
                distance_meters=result.distance_meters,
                note=note,
            )
            session.add_record(record)
            return record

    # ---- results -----------------------------------------------------------

    def results(self):
        """All saved records of the current session, in check-in order."""
        with self._lock:
            return self.session.records if self.session else []

    def grouped_results(self):
        """
        The students in three groups. Absent is not saved: it means the
        student is on the roster and has no record in this session.
        """
        with self._lock:
            records = self.session.records if self.session else []
            recorded = {r.student.phone_number for r in records}
            return {
                PRESENT: [r for r in records if r.status == PRESENT],
                FLAGGED: [r for r in records if r.status == FLAGGED],
                ABSENT: [s for s in self.roster.students if s.phone_number not in recorded],
            }

    # ---- helpers -----------------------------------------------------------

    def _datetime(self, now):
        return datetime.fromtimestamp(now, self.tz)

    def _check_not_locked(self, phone, now):
        recent = [t for t in self._wrong_codes.get(phone, []) if now - t < WRONG_CODE_WINDOW_SECONDS]
        self._wrong_codes[phone] = recent
        if len(recent) >= MAX_WRONG_CODES:
            raise CheckInError(
                "too_many_attempts",
                "Too many wrong codes. Wait a minute and try again.",
            )

    def _remember_wrong_code(self, phone, now):
        self._wrong_codes.setdefault(phone, []).append(now)
