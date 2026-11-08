import csv
import io

from attendance.attendance_manager import AttendanceManager
from attendance.csv_exporter import BOM, COLUMNS, CsvExporter
from attendance.location_checker import LocationChecker
from attendance.roster import Roster

from .conftest import FAR_AWAY, NEAR, NOW


def rows_of(data):
    text = data.decode("utf-8")
    assert text.startswith(BOM)
    return list(csv.reader(io.StringIO(text[len(BOM):])))


def test_first_row_has_the_right_columns(open_manager):
    data = CsvExporter(open_manager.roster).export(open_manager.session)
    assert rows_of(data)[0] == [
        "Phone number",
        "Name",
        "Status",
        "Check-in time",
        "Distance from classroom (m)",
        "Note",
    ]
    assert COLUMNS == rows_of(data)[0]


def test_file_starts_with_the_utf8_bom_for_excel(open_manager):
    data = CsvExporter(open_manager.roster).export(open_manager.session)
    assert data.startswith(b"\xef\xbb\xbf")


def test_present_and_flagged_appear_with_the_right_status(open_manager):
    code = open_manager.code_generator.current_code(NOW)
    open_manager.check_in("0500000001", code, NEAR, 10, now=NOW)
    open_manager.check_in("0500000002", code, FAR_AWAY, 10, now=NOW)
    rows = {r[0]: r for r in rows_of(CsvExporter(open_manager.roster).export(open_manager.session))[1:]}
    assert rows["0500000001"][2] == "Present"
    assert rows["0500000001"][4] != ""
    assert rows["0500000002"][2] == "Flagged"
    assert "far" in rows["0500000002"][5]


def test_a_student_with_no_record_is_absent(open_manager):
    rows = {r[0]: r for r in rows_of(CsvExporter(open_manager.roster).export(open_manager.session))[1:]}
    assert len(rows) == 4
    assert rows["0500000003"][2:] == ["Absent", "", "", ""]


def test_rows_follow_the_roster_order(open_manager):
    names = [r[1] for r in rows_of(CsvExporter(open_manager.roster).export(open_manager.session))[1:]]
    assert names == ["Dana Levi", "Noa Cohen", "Ron Mizrahi", "Lior Peretz"]


def test_without_a_session_everyone_is_absent(roster):
    rows = rows_of(CsvExporter(roster).export(None))[1:]
    assert [r[2] for r in rows] == ["Absent"] * 4


def test_hebrew_names_are_kept(code_generator):
    roster = Roster().load("Name,Phone number\nדנה לוי,0500000001\n")
    manager = AttendanceManager(roster, code_generator, LocationChecker())
    manager.start_session((32.1, 35.2), 10, now=NOW)
    data = CsvExporter(roster).export(manager.session)
    assert rows_of(data)[1][1] == "דנה לוי"


def test_names_that_look_like_formulas_are_made_safe(code_generator):
    roster = Roster().load('Name,Phone number\n"=1+1",0500000001\n')
    manager = AttendanceManager(roster, code_generator, LocationChecker())
    manager.start_session((32.1, 35.2), 10, now=NOW)
    data = CsvExporter(roster).export(manager.session)
    assert rows_of(data)[1][1] == "'=1+1"
