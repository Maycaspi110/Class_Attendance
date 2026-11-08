"""Session: one attendance session (the classroom location, times, records)."""
from datetime import datetime

OPEN = "open"
CLOSED = "closed"


class Session:
    def __init__(self):
        self.classroom_location = None  # (lat, lon)
        self.start_time = None
        self.end_time = None
        self.status = CLOSED
        self._records = {}  # phone number -> AttendanceRecord, in check-in order

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

    def record_for(self, phone_number):
        return self._records.get(phone_number)

    def add_record(self, record):
        """Save a record. Only one record per student is allowed."""
        phone = record.student.phone_number
        if phone in self._records:
            raise ValueError("This student already has a record in this session.")
        self._records[phone] = record

    @property
    def records(self):
        return list(self._records.values())
