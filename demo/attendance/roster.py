"""Roster: the course student list, loaded from a CSV file."""
import csv
import io

from .student import Student, normalize_phone

MAX_STUDENTS = 2000

NAME_HEADERS = {"name", "full name", "student name"}
PHONE_HEADERS = {"phone number", "phone", "phone_number", "phonenumber", "mobile"}


class RosterError(Exception):
    """The file cannot be used at all (for example a missing column)."""


def _decode(data):
    if isinstance(data, str):
        return data
    for encoding in ("utf-8-sig", "cp1255"):  # cp1255 = Hebrew Windows files
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RosterError("The file could not be read. Save it as a CSV (UTF-8) file.")


def _delimiter(text):
    first_line = text.splitlines()[0] if text.splitlines() else ""
    counts = {d: first_line.count(d) for d in (",", ";", "\t")}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


class Roster:
    def __init__(self):
        self.students = []
        self.warnings = []
        self._by_phone = {}

    def __len__(self):
        return len(self.students)

    @property
    def has_problems(self):
        return bool(self.warnings)

    def load(self, source):
        """
        Read a CSV file (bytes or text) with the columns Name and Phone number.
        Raises RosterError if the file cannot be used. Problems in single rows
        (empty name, bad phone number, the same phone number twice) are added
        to `warnings`, and those rows are not loaded.
        """
        text = _decode(source)
        if not text.strip():
            raise RosterError("The file is empty.")
        reader = csv.reader(io.StringIO(text), delimiter=_delimiter(text))
        rows = list(reader)
        header = [cell.strip().lower() for cell in rows[0]]
        name_col = next((i for i, h in enumerate(header) if h in NAME_HEADERS), None)
        phone_col = next((i for i, h in enumerate(header) if h in PHONE_HEADERS), None)
        if name_col is None or phone_col is None:
            raise RosterError("The file must have the columns Name and Phone number.")
        if len(rows) - 1 > MAX_STUDENTS:
            raise RosterError("The file has too many rows (the limit is %d)." % MAX_STUDENTS)

        students, warnings, by_phone, first_row = [], [], {}, {}
        for number, row in enumerate(rows[1:], start=2):  # row 1 is the header
            if not any(cell.strip() for cell in row):
                continue
            name = row[name_col].strip() if len(row) > name_col else ""
            phone = normalize_phone(row[phone_col]) if len(row) > phone_col else None
            if not name:
                warnings.append("Row %d: the name is empty." % number)
            elif phone is None:
                warnings.append("Row %d: the phone number is missing or not valid." % number)
            elif phone in by_phone:
                warnings.append(
                    "Rows %d and %d have the same phone number." % (first_row[phone], number)
                )
            else:
                student = Student(name=name, phone_number=phone)
                students.append(student)
                by_phone[phone] = student
                first_row[phone] = number

        self.students, self.warnings, self._by_phone = students, warnings, by_phone
        return self

    def find_by_phone(self, phone):
        """The student with this phone number, or None ("not found")."""
        return self._by_phone.get(normalize_phone(phone))
