"""CsvExporter: the attendance spreadsheet for the lecturer."""
import csv
import io

COLUMNS = [
    "Email",
    "Name",
    "Status",
    "Start check-in",
    "End check-in",
    "Distance from classroom (m)",
    "Note",
    "Comment",
]

BOM = "﻿"  # lets Excel open the file as UTF-8 (so Hebrew names look right)
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def _safe(text):
    """A cell that starts with = + - @ could run as a formula in Excel."""
    text = "" if text is None else str(text)
    return "'" + text if text.startswith(_FORMULA_START) else text


def _time(record):
    return "" if record is None else record.check_in_time.strftime("%H:%M")


class CsvExporter:
    def export(self, entries):
        """
        The CSV file as bytes (UTF-8 with BOM). `entries` are the LessonEntry
        objects of the manager: every student of the roster has one row.
        """
        out = io.StringIO()
        out.write(BOM)
        writer = csv.writer(out)
        writer.writerow(COLUMNS)
        for entry in entries:
            distance = entry.distance_meters
            writer.writerow(
                [
                    entry.student.email,
                    _safe(entry.student.name),
                    entry.status,
                    _time(entry.start),
                    _time(entry.end),
                    "" if distance is None else distance,
                    _safe(entry.note),
                    _safe(entry.comment),
                ]
            )
        return out.getvalue().encode("utf-8")
