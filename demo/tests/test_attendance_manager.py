import pytest

from attendance.attendance_manager import (
    MAX_WRONG_CODES,
    AttendanceManager,
    CheckInError,
    SessionError,
)
from attendance.attendance_record import ABSENT, FLAGGED, PRESENT
from attendance.location_checker import LocationChecker
from attendance.roster import Roster

from .conftest import CLASSROOM, FAR_AWAY, NEAR, NOW, PERIOD


def good_code(manager, now=NOW):
    return manager.code_generator.current_code(now)


def wrong_code(manager, now=NOW):
    valid = {good_code(manager, now), good_code(manager, now - PERIOD)}
    return next(c for c in ("0000", "1111", "2222", "3333") if c not in valid)


# ---- starting and ending a session -----------------------------------------


def test_start_stores_the_classroom_location(manager):
    session = manager.start_session(CLASSROOM, 10, now=NOW)
    assert session.is_open()
    assert session.classroom_location == CLASSROOM


def test_start_needs_a_roster(code_generator):
    manager = AttendanceManager(Roster(), code_generator, LocationChecker())
    with pytest.raises(SessionError):
        manager.start_session(CLASSROOM, 10, now=NOW)


@pytest.mark.parametrize("location, accuracy", [(None, 10), (CLASSROOM, 5000), (CLASSROOM, None)])
def test_start_needs_a_good_location(manager, location, accuracy):
    with pytest.raises(SessionError):
        manager.start_session(location, accuracy, now=NOW)
    assert manager.session is None


def test_end_closes_the_session(open_manager):
    open_manager.end_session(now=NOW + 60)
    assert not open_manager.session.is_open()


def test_end_without_an_open_session_is_an_error(manager):
    with pytest.raises(SessionError):
        manager.end_session()


# ---- the check-in ---------------------------------------------------------


def test_good_check_in_is_present(open_manager):
    record = open_manager.check_in("0500000001", good_code(open_manager), NEAR, 10, now=NOW)
    assert record.status == PRESENT
    assert record.student.name == "Dana Levi"
    assert 95 <= record.distance_meters <= 105
    assert len(open_manager.results()) == 1


def test_far_location_is_flagged(open_manager):
    record = open_manager.check_in("0500000001", good_code(open_manager), FAR_AWAY, 10, now=NOW)
    assert record.status == FLAGGED
    assert "far" in record.note
    assert len(open_manager.results()) == 1


def test_no_location_is_flagged(open_manager):
    record = open_manager.check_in("0500000001", good_code(open_manager), None, None, now=NOW)
    assert record.status == FLAGGED
    assert record.distance_meters is None
    assert "missing" in record.note


def test_inaccurate_location_is_flagged(open_manager):
    record = open_manager.check_in("0500000001", good_code(open_manager), NEAR, 900, now=NOW)
    assert record.status == FLAGGED


def test_wrong_code_is_an_error_and_has_no_record(open_manager):
    with pytest.raises(CheckInError) as error:
        open_manager.check_in("0500000001", wrong_code(open_manager), NEAR, 10, now=NOW)
    assert error.value.reason == "bad_code"
    assert open_manager.results() == []


def test_previous_code_is_accepted(open_manager):
    later = NOW + PERIOD  # the code changed once since the lecturer's screen showed it
    previous = good_code(open_manager, NOW)
    record = open_manager.check_in("0500000001", previous, NEAR, 10, now=later)
    assert record.status == PRESENT


def test_code_from_two_slots_ago_is_rejected(open_manager):
    later = NOW + 2 * PERIOD
    with pytest.raises(CheckInError) as error:
        open_manager.check_in("0500000001", good_code(open_manager, NOW), NEAR, 10, now=later)
    assert error.value.reason == "bad_code"


def test_phone_number_not_on_the_roster_is_an_error(open_manager):
    with pytest.raises(CheckInError) as error:
        open_manager.check_in("0509999999", good_code(open_manager), NEAR, 10, now=NOW)
    assert error.value.reason == "not_on_roster"
    assert open_manager.results() == []


def test_phone_number_can_be_written_in_another_way(open_manager):
    record = open_manager.check_in("050-000-0001", good_code(open_manager), NEAR, 10, now=NOW)
    assert record.student.phone_number == "0500000001"


def test_checking_in_twice_keeps_one_record(open_manager):
    code = good_code(open_manager)
    first = open_manager.check_in("0500000001", code, NEAR, 10, now=NOW)
    with pytest.raises(CheckInError) as error:
        open_manager.check_in("0500000001", code, FAR_AWAY, 10, now=NOW)
    assert error.value.reason == "already_recorded"
    assert error.value.record == first
    assert open_manager.results() == [first]


def test_check_in_after_the_session_ended_is_not_accepted(open_manager):
    open_manager.end_session(now=NOW + 5)
    with pytest.raises(CheckInError) as error:
        open_manager.check_in("0500000001", good_code(open_manager), NEAR, 10, now=NOW + 5)
    assert error.value.reason == "session_closed"


def test_check_in_before_any_session_is_not_accepted(manager):
    with pytest.raises(CheckInError) as error:
        manager.check_in("0500000001", "1234", NEAR, 10, now=NOW)
    assert error.value.reason == "session_closed"


def test_too_many_wrong_codes_in_a_row_are_blocked(open_manager):
    for _ in range(MAX_WRONG_CODES):
        with pytest.raises(CheckInError) as error:
            open_manager.check_in("0500000001", wrong_code(open_manager), NEAR, 10, now=NOW)
        assert error.value.reason == "bad_code"
    # Even the right code is refused for a short time.
    with pytest.raises(CheckInError) as error:
        open_manager.check_in("0500000001", good_code(open_manager), NEAR, 10, now=NOW + 1)
    assert error.value.reason == "too_many_attempts"
    # After a minute the student can try again.
    later = NOW + 61
    record = open_manager.check_in("0500000001", good_code(open_manager, later), NEAR, 10, now=later)
    assert record.status == PRESENT


def test_wrong_codes_of_one_student_do_not_block_another(open_manager):
    for _ in range(MAX_WRONG_CODES):
        with pytest.raises(CheckInError):
            open_manager.check_in("0500000001", wrong_code(open_manager), NEAR, 10, now=NOW)
    record = open_manager.check_in("0500000002", good_code(open_manager), NEAR, 10, now=NOW)
    assert record.status == PRESENT


# ---- results ---------------------------------------------------------------


def test_results_without_a_session_are_empty(manager):
    assert manager.results() == []
    groups = manager.grouped_results()
    assert groups[PRESENT] == [] and groups[FLAGGED] == []
    assert len(groups[ABSENT]) == 4


def test_grouped_results_present_flagged_and_absent(open_manager):
    code = good_code(open_manager)
    open_manager.check_in("0500000001", code, NEAR, 10, now=NOW)
    open_manager.check_in("0500000002", code, FAR_AWAY, 10, now=NOW)
    groups = open_manager.grouped_results()
    assert [r.student.name for r in groups[PRESENT]] == ["Dana Levi"]
    assert [r.student.name for r in groups[FLAGGED]] == ["Noa Cohen"]
    assert [s.name for s in groups[ABSENT]] == ["Ron Mizrahi", "Lior Peretz"]


def test_starting_a_new_session_forgets_the_old_one(open_manager):
    open_manager.check_in("0500000001", good_code(open_manager), NEAR, 10, now=NOW)
    open_manager.start_session(CLASSROOM, 10, now=NOW + 100)
    assert open_manager.results() == []
