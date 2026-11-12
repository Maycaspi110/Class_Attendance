"""AttendanceManager: the main logic of a check-in.

For every check-in the order of the checks follows the sequence diagram in
diagrams.md: session open, roster, code, location, then save one record.
"""
import threading
import time
from datetime import datetime

from . import location_checker as lc
from .attendance_record import ABSENT, FLAGGED, PRESENT, AttendanceRecord, LessonEntry, lesson_status
from .code_generator import INVALID
from .session import END_ROUND, START_ROUND, Session

MAX_COMMENT_LENGTH = 300
MAX_LECTURER_ACCURACY_METERS = 3000

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
        self.session = None  # the current round (the last one that was started)
        self.rounds = {}  # round name -> Session, for the lesson that is running
        self._wrong_codes = {}  # email -> list of times of wrong codes
        self._lock = threading.RLock()

    # ---- the lecturer side -------------------------------------------------

    def start_session(self, location, accuracy, now=None, round_name=START_ROUND):
        """
        Open a check-in round. The lecturer's phone location is the classroom.
        A "start" round begins a new lesson. An "end" round is added to the same lesson.
        """
        now = time.time() if now is None else now
        with self._lock:
            if round_name not in (START_ROUND, END_ROUND):
                raise SessionError("Unknown check-in round.")
            if self.session is not None and self.session.is_open():
                raise SessionError("A check-in is already open. End it first.")
            if len(self.roster) == 0:
                raise SessionError("Upload and confirm the roster before starting a session.")
            if location is None or not lc.valid_point(*location):
                raise SessionError("The phone location is missing. Allow location and try again.")
            # The lecturer is trusted, so a rough indoor location (Wi-Fi or cell tower) is accepted.
            # Only a hopeless one is refused. Students are still checked with the strict accuracy.
            try:
                rough = 0 <= float(accuracy) <= MAX_LECTURER_ACCURACY_METERS
            except (TypeError, ValueError):
                rough = False
            if not rough:
                raise SessionError("The phone location is too inaccurate. Try again outdoors or near a window.")
            session = Session(round_name)
            session.start(location, self._datetime(now))
            if round_name == START_ROUND:
                self.rounds = {}
            self.rounds[round_name] = session
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

    def check_in(self, email, code, location, accuracy, now=None, comment=""):
        """
        Check in one student. Returns the saved AttendanceRecord, or raises
        CheckInError with a clear message for the student.
        A comment about the lesson is kept only in the end-of-class round.
        """
        now = time.time() if now is None else now
        with self._lock:
            session = self.session
            if session is None or not session.is_open():
                raise CheckInError("session_closed", "There is no open attendance session now.")

            student = self.roster.find_by_email(email)
            if student is None:
                raise CheckInError("not_on_roster", "This email is not on the roster.")

            self._check_not_locked(student.email, now)
            if self.code_generator.check_code(code, now) == INVALID:
                self._remember_wrong_code(student.email, now)
                raise CheckInError(
                    "bad_code",
                    "Wrong or expired code. Look at the classroom screen and try again.",
                )

            result = self.location_checker.check(location, accuracy, session.classroom_location)

            existing = session.record_for(student.email)
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
                comment=self._clean_comment(comment) if session.round == END_ROUND else "",
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
            recorded = {r.student.email for r in records}
            return {
                PRESENT: [r for r in records if r.status == PRESENT],
                FLAGGED: [r for r in records if r.status == FLAGGED],
                ABSENT: [s for s in self.roster.students if s.email not in recorded],
            }

    def lesson_entries(self):
        """
        Every student of the roster with the status for the whole lesson.
        Present = both check-ins, Late = only the end, Left early = only the start.
        Flagged (location problem) is shown first. Without an end round it is the start status.
        """
        with self._lock:
            start = self.rounds.get(START_ROUND)
            end = self.rounds.get(END_ROUND)
            end_finished = end is not None and not end.is_open()
            entries = []
            for student in self.roster.students:
                start_record = start.record_for(student.email) if start else None
                end_record = end.record_for(student.email) if end else None
                status = lesson_status(start_record, end_record, end_finished)
                entries.append(LessonEntry(student, status, start_record, end_record))
            return entries

    def lesson_start_time(self):
        """When the first round of the lesson was started (for the file name), or None."""
        with self._lock:
            first = self.rounds.get(START_ROUND) or self.rounds.get(END_ROUND)
            return first.start_time if first else None

    # ---- helpers -----------------------------------------------------------

    @staticmethod
    def _clean_comment(comment):
        return " ".join(str(comment or "").split())[:MAX_COMMENT_LENGTH]

    def _datetime(self, now):
        return datetime.fromtimestamp(now, self.tz)

    def _check_not_locked(self, email, now):
        recent = [t for t in self._wrong_codes.get(email, []) if now - t < WRONG_CODE_WINDOW_SECONDS]
        self._wrong_codes[email] = recent
        if len(recent) >= MAX_WRONG_CODES:
            raise CheckInError(
                "too_many_attempts",
                "Too many wrong codes. Wait a minute and try again.",
            )

    def _remember_wrong_code(self, email, now):
        self._wrong_codes.setdefault(email, []).append(now)
