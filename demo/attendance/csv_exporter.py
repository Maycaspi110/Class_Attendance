"""CsvExporter: the attendance spreadsheet for the lecturer."""
import csv
import io

from .attendance_record import ABSENT

COLUMNS = [
    "Email",
    "Name",
    "Status",
    "Check-in time",
    "Distance from classroom (m)",
    "Note",
]

BOM = "﻿"  # lets Excel open the file as UTF-8 (so Hebrew names look right)
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def _safe(text):
    """A cell that starts with = + - @ could run as a formula in Excel."""
    text = "" if text is None else str(text)
    return "'" + text if text.startswith(_FORMULA_START) else text


class CsvExporter:
    def __init__(self, roster):
        self.roster = roster

    def export(self, session):
        """
        The CSV file as bytes (UTF-8 with BOM). Every student of the roster
        has one row: Present or Flagged from the record, otherwise Absent.
        """
        out = io.StringIO()
        out.write(BOM)
        writer = csv.writer(out)
        writer.writerow(COLUMNS)
        for student in self.roster.students:
            record = session.record_for(student.email) if session else None
            if record is None:
                writer.writerow([student.email, _safe(student.name), ABSENT, "", "", ""])
            else:
                writer.writerow(
                    [
                        student.email,
                        _safe(student.name),
                        record.status,
                        record.check_in_time.strftime("%H:%M"),
                        "" if record.distance_meters is None else record.distance_meters,
                        _safe(record.note),
                    ]
                )
        return out.getvalue().encode("utf-8")
