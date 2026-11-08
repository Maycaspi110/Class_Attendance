"""Roster: the course student list, loaded from a CSV file.

The file needs a name and an email for every student. Any other column
(for example an ID number) is ignored: it is never read or kept.
"""
import csv
import io

from .student import Student, normalize_email

MAX_STUDENTS = 2000

NAME_HEADERS = {"name", "full name", "student name", "שם", "שם מלא", "שם התלמיד", "שם הסטודנט", "שם סטודנט", "שם תלמיד"}
FIRST_NAME_HEADERS = {"first name", "firstname", "שם פרטי"}
LAST_NAME_HEADERS = {"last name", "lastname", "family name", "surname", "שם משפחה"}
EMAIL_HEADERS = {
    "email", "e-mail", "mail", "email address",
    "מייל", "אימייל", "אי-מייל", "דוא\"ל", "דואל", "דואר אלקטרוני", "כתובת מייל", "כתובת דוא\"ל",
}


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


def _header(cell):
    return " ".join(cell.replace("﻿", "").replace("‏", "").replace("‎", "").strip().strip('"').lower().split())


def _find(header, names):
    return next((i for i, h in enumerate(header) if h in names), None)


class Roster:
    def __init__(self):
        self.students = []
        self.warnings = []
        self._by_email = {}

    def __len__(self):
        return len(self.students)

    @property
    def has_problems(self):
        return bool(self.warnings)

    def load(self, source):
        """
        Read a CSV file (bytes or text) with the columns Name and Email.
        Raises RosterError if the file cannot be used. Problems in single rows
        (empty name, bad email, the same email twice) are added to `warnings`,
        and those rows are not loaded.
        """
        text = _decode(source)
        if not text.strip():
            raise RosterError("The file is empty.")
        rows = list(csv.reader(io.StringIO(text), delimiter=_delimiter(text)))
        header = [_header(cell) for cell in rows[0]]
        email_col = _find(header, EMAIL_HEADERS)
        name_col = _find(header, NAME_HEADERS)
        first_col = _find(header, FIRST_NAME_HEADERS)
        last_col = _find(header, LAST_NAME_HEADERS)
        has_name = name_col is not None or (first_col is not None and last_col is not None)
        if email_col is None or not has_name:
            raise RosterError("The file must have the columns Name and Email.")
        if len(rows) - 1 > MAX_STUDENTS:
            raise RosterError("The file has too many rows (the limit is %d)." % MAX_STUDENTS)

        def cell(row, col):
            return row[col].strip() if col is not None and len(row) > col else ""

        students, warnings, by_email, first_row = [], [], {}, {}
        for number, row in enumerate(rows[1:], start=2):  # row 1 is the header
            if not any(c.strip() for c in row):
                continue
            if name_col is not None:
                name = cell(row, name_col)
            else:
                name = (cell(row, first_col) + " " + cell(row, last_col)).strip()
            email = normalize_email(cell(row, email_col))
            if not name:
                warnings.append("Row %d: the name is empty." % number)
            elif email is None:
                warnings.append("Row %d: the email is missing or not valid." % number)
            elif email in by_email:
                warnings.append("Rows %d and %d have the same email." % (first_row[email], number))
            else:
                student = Student(name=name, email=email)
                students.append(student)
                by_email[email] = student
                first_row[email] = number

        self.students, self.warnings, self._by_email = students, warnings, by_email
        return self

    def find_by_email(self, email):
        """The student with this email, or None ("not found")."""
        return self._by_email.get(normalize_email(email))
