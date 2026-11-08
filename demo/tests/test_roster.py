import pytest

from attendance.roster import Roster, RosterError
from attendance.student import Student, normalize_phone

GOOD_CSV = (
    "Name,Phone number\n"
    "Dana Levi,0500000001\n"
    "Noa Cohen,0500000002\n"
    "Ron Mizrahi,0500000003\n"
)


def test_load_a_good_file():
    roster = Roster().load(GOOD_CSV)
    assert len(roster) == 3
    assert not roster.has_problems


def test_missing_phone_column_is_an_error():
    with pytest.raises(RosterError):
        Roster().load("Name,Email\nDana,dana@example.com\n")


def test_missing_name_column_is_an_error():
    with pytest.raises(RosterError):
        Roster().load("Phone number\n0500000001\n")


def test_empty_file_is_an_error():
    with pytest.raises(RosterError):
        Roster().load("   \n")


def test_same_phone_number_twice_gives_a_warning():
    roster = Roster().load(GOOD_CSV + "Another Student,0500000001\n")
    assert len(roster) == 3  # the second row is not loaded
    assert roster.has_problems
    assert "same phone number" in roster.warnings[0]


def test_find_a_student():
    roster = Roster().load(GOOD_CSV)
    assert roster.find_by_phone("0500000002") == Student("Noa Cohen", "0500000002")


def test_unknown_number_is_not_found():
    assert Roster().load(GOOD_CSV).find_by_phone("0509999999") is None


def test_find_accepts_other_ways_to_write_the_number():
    roster = Roster().load(GOOD_CSV)
    assert roster.find_by_phone("050-000-0001").name == "Dana Levi"
    assert roster.find_by_phone("+972 50 000 0001").name == "Dana Levi"


def test_empty_name_and_bad_phone_give_warnings():
    roster = Roster().load("Name,Phone number\n,0500000001\nDana,abc\nNoa,0500000002\n")
    assert len(roster) == 1
    assert len(roster.warnings) == 2


def test_file_with_bom_and_semicolons():
    data = ("﻿Name;Phone number\nDana;0500000001\n").encode("utf-8")
    assert len(Roster().load(data)) == 1


def test_hebrew_names_in_utf8_and_windows_hebrew_encoding():
    text = "Name,Phone number\nדנה לוי,0500000001\n"
    assert Roster().load(text.encode("utf-8")).students[0].name == "דנה לוי"
    assert Roster().load(text.encode("cp1255")).students[0].name == "דנה לוי"


def test_blank_rows_are_ignored():
    roster = Roster().load("Name,Phone number\n\nDana,0500000001\n,\n")
    assert len(roster) == 1
    assert not roster.has_problems


def test_too_many_rows_is_an_error():
    rows = "".join("S%d,05%08d\n" % (i, i) for i in range(2001))
    with pytest.raises(RosterError):
        Roster().load("Name,Phone number\n" + rows)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("0500000001", "0500000001"),
        (" 050-000-0001 ", "0500000001"),
        ("+972500000001", "0500000001"),
        ("972500000001", "0500000001"),
        ("12345", None),
        ("abc", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_phone(text, expected):
    assert normalize_phone(text) == expected
