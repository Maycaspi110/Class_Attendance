import pytest

from attendance.roster import Roster, RosterError
from attendance.student import Student, normalize_email

GOOD_CSV = (
    "Name,Email\n"
    "Dana Levi,dana.levi@example.com\n"
    "Noa Cohen,noa.cohen@example.com\n"
    "Ron Mizrahi,ron.mizrahi@example.com\n"
)


def test_load_a_good_file():
    roster = Roster().load(GOOD_CSV)
    assert len(roster) == 3
    assert not roster.has_problems


def test_missing_email_column_is_an_error():
    with pytest.raises(RosterError):
        Roster().load("Name,Phone number\nDana,0500000001\n")


def test_missing_name_column_is_an_error():
    with pytest.raises(RosterError):
        Roster().load("Email\ndana.levi@example.com\n")


def test_empty_file_is_an_error():
    with pytest.raises(RosterError):
        Roster().load("   \n")


def test_same_email_twice_gives_a_warning():
    roster = Roster().load(GOOD_CSV + "Another Student,dana.levi@example.com\n")
    assert len(roster) == 3  # the second row is not loaded
    assert roster.has_problems
    assert "same email" in roster.warnings[0]


def test_find_a_student():
    roster = Roster().load(GOOD_CSV)
    assert roster.find_by_email("noa.cohen@example.com") == Student("Noa Cohen", "noa.cohen@example.com")


def test_unknown_email_is_not_found():
    assert Roster().load(GOOD_CSV).find_by_email("nobody@example.com") is None


def test_find_ignores_capital_letters_and_spaces():
    roster = Roster().load(GOOD_CSV)
    assert roster.find_by_email("  Dana.Levi@EXAMPLE.com ").name == "Dana Levi"


def test_empty_name_and_bad_email_give_warnings():
    roster = Roster().load("Name,Email\n,dana.levi@example.com\nDana,abc\nNoa,noa.cohen@example.com\n")
    assert len(roster) == 1
    assert len(roster.warnings) == 2


def test_file_with_bom_and_semicolons():
    data = ("﻿Name;Email\nDana;dana.levi@example.com\n").encode("utf-8")
    assert len(Roster().load(data)) == 1


def test_hebrew_names_in_utf8_and_windows_hebrew_encoding():
    text = "Name,Email\nדנה לוי,dana.levi@example.com\n"
    assert Roster().load(text.encode("utf-8")).students[0].name == "דנה לוי"
    assert Roster().load(text.encode("cp1255")).students[0].name == "דנה לוי"


def test_blank_rows_are_ignored():
    roster = Roster().load("Name,Email\n\nDana,dana.levi@example.com\n,\n")
    assert len(roster) == 1
    assert not roster.has_problems


def test_too_many_rows_is_an_error():
    rows = "".join("S%d,s%d@example.com\n" % (i, i) for i in range(2001))
    with pytest.raises(RosterError):
        Roster().load("Name,Email\n" + rows)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("dana.levi@example.com", "dana.levi@example.com"),
        ("  Dana.Levi@Example.COM ", "dana.levi@example.com"),
        ("dana.levi@example", None),
        ("dana levi@example.com", None),
        ("a@b@example.com", None),
        ("0500000001", None),
        ("abc", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_email(text, expected):
    assert normalize_email(text) == expected


# ---- a real-life file: extra columns, Hebrew headers, first and last names ----


def test_other_columns_such_as_an_id_number_are_ignored_and_never_kept():
    text = "Name,ID,Email\nDana Levi,123456782,dana.levi@example.com\n"
    roster = Roster().load(text)
    assert len(roster) == 1
    assert "123456782" not in repr(roster.students) + repr(roster.warnings)


def test_hebrew_column_names_are_understood():
    text = "שם,תעודת זהות,מייל\nדנה לוי,123456782,dana.levi@example.com\n"
    roster = Roster().load(text.encode("cp1255"))
    assert roster.students[0].name == "דנה לוי"
    assert roster.students[0].email == "dana.levi@example.com"


def test_first_and_last_name_columns_are_joined():
    text = "שם פרטי,שם משפחה,Email\nדנה,לוי,dana.levi@example.com\n"
    assert Roster().load(text).students[0].name == "דנה לוי"


def test_a_file_with_only_a_first_name_column_is_refused():
    with pytest.raises(RosterError):
        Roster().load("First name,Email\nDana,dana.levi@example.com\n")
