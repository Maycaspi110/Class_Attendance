"""Shared test helpers. All students, numbers and places are made up."""
import pytest

from attendance.attendance_manager import AttendanceManager
from attendance.code_generator import CodeGenerator
from attendance.location_checker import LocationChecker
from attendance.roster import Roster

PERIOD = 20
NOW = 1_000_000 * PERIOD + 5  # a moment inside a time slot
CLASSROOM = (32.1000, 35.2000)
NEAR = (32.1009, 35.2000)  # about 100 m from the classroom
FAR_AWAY = (32.1090, 35.2000)  # about 1 km from the classroom

ROSTER_CSV = (
    "Name,Email\n"
    "Dana Levi,dana.levi@example.com\n"
    "Noa Cohen,noa.cohen@example.com\n"
    "Ron Mizrahi,ron.mizrahi@example.com\n"
    "Lior Peretz,lior.peretz@example.com\n"
)


@pytest.fixture
def roster():
    return Roster().load(ROSTER_CSV)


@pytest.fixture
def code_generator():
    return CodeGenerator("test-secret", PERIOD)


@pytest.fixture
def manager(roster, code_generator):
    return AttendanceManager(roster, code_generator, LocationChecker(150, 200))


@pytest.fixture
def open_manager(manager):
    """A manager with an open session at the made-up classroom."""
    manager.start_session(CLASSROOM, 10, now=NOW)
    return manager
