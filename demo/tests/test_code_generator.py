import pytest

from attendance.code_generator import CURRENT, INVALID, PREVIOUS, CodeGenerator

PERIOD = 20
T0 = 1_000_000 * PERIOD  # the start of a time slot


@pytest.fixture
def gen():
    return CodeGenerator("test-secret", PERIOD)


def test_same_time_slot_gives_the_same_code(gen):
    assert gen.current_code(T0 + 1) == gen.current_code(T0 + PERIOD - 1)


def test_code_is_always_four_digits(gen):
    for i in range(500):
        code = gen.current_code(T0 + i * PERIOD)
        assert len(code) == 4 and code.isdigit()


def test_code_changes_in_the_next_slot(gen):
    for i in range(50):
        now = T0 + i * PERIOD
        assert gen.current_code(now) != gen.current_code(now + PERIOD)


def test_current_code_is_current(gen):
    now = T0 + 5
    assert gen.check_code(gen.current_code(now), now) == CURRENT


def test_previous_code_is_previous(gen):
    now = T0 + PERIOD + 5
    previous = gen.current_code(now - PERIOD)
    assert gen.check_code(previous, now) == PREVIOUS


def test_code_from_two_slots_ago_is_invalid(gen):
    now = T0 + 2 * PERIOD + 5
    old = gen.current_code(now - 2 * PERIOD)
    assert old not in (gen.current_code(now), gen.current_code(now - PERIOD))
    assert gen.check_code(old, now) == INVALID


def test_wrong_code_is_invalid(gen):
    now = T0 + 5
    valid = {gen.current_code(now), gen.current_code(now - PERIOD)}
    wrong = next(c for c in ("0000", "1111", "2222", "3333") if c not in valid)
    assert gen.check_code(wrong, now) == INVALID


@pytest.mark.parametrize("entry", ["", "12", "12345", "abcd", "12 4", None])
def test_badly_formatted_entry_is_invalid(gen, entry):
    assert gen.check_code(entry, T0) == INVALID


def test_spaces_around_the_code_are_ignored(gen):
    now = T0 + 5
    assert gen.check_code("  " + gen.current_code(now) + " ", now) == CURRENT


def test_different_secret_gives_different_codes():
    a = CodeGenerator("secret-a", PERIOD)
    b = CodeGenerator("secret-b", PERIOD)
    same = sum(a.current_code(T0 + i * PERIOD) == b.current_code(T0 + i * PERIOD) for i in range(50))
    assert same < 5


def test_seconds_left(gen):
    assert gen.seconds_left(T0) == PERIOD
    assert gen.seconds_left(T0 + 5) == PERIOD - 5
    assert gen.seconds_left(T0 + PERIOD - 0.2) == 1


@pytest.mark.parametrize("period", [9, 31, 60])
def test_period_outside_10_to_30_is_rejected(period):
    with pytest.raises(ValueError):
        CodeGenerator("s", period)


def test_empty_secret_is_rejected():
    with pytest.raises(ValueError):
        CodeGenerator("", 20)
