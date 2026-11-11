"""Session: one attendance session (the classroom location, times, records)."""
from datetime import datetime

OPEN = "open"
CLOSED = "closed"


START_ROUND = "start"  # the check-in at the beginning of the class
END_ROUND = "end"  # the check-in at the end of the class


class Session:
    """One check-in round. A lesson has a start round and, if the lecturer wants, an end round."""

    def __init__(self, round_name=START_ROUND):
        self.round = round_name
        self.classroom_location = None  # (lat, lon)
        self.start_time = None
        self.end_time = None
        self.status = CLOSED
        self._records = {}  # email -> AttendanceRecord, in check-in order

    def start(self, location, start_time=None):
        """Open the session. `location` is the lecturer's phone (lat, lon)."""
        self.classroom_location = (float(location[0]), float(location[1]))
        self.start_time = start_time or datetime.now()
        self.end_time = None
        self.status = OPEN
        self._records = {}

    def end(self, end_time=None):
        self.status = CLOSED
        self.end_time = end_time or datetime.now()

    def is_open(self):
        return self.status == OPEN

    def record_for(self, email):
        return self._records.get(email)

    def add_record(self, record):
        """Save a record. Only one record per student is allowed."""
        email = record.student.email
        if email in self._records:
            raise ValueError("This student already has a record in this session.")
        self._records[email] = record

    @property
    def records(self):
        return list(self._records.values())
