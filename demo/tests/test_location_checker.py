import pytest

from attendance.location_checker import FAR, GOOD, INACCURATE, LocationChecker, valid_point

# A made-up classroom point.
CLASSROOM = (32.1000, 35.2000)
# 0.0009 degrees of latitude is about 100 meters.
ABOUT_100M = (32.1009, 35.2000)
ABOUT_1KM = (32.1090, 35.2000)


@pytest.fixture
def checker():
    return LocationChecker(allowed_radius_meters=150, max_accuracy_meters=200)


def test_same_point_has_distance_zero(checker):
    assert checker.distance(CLASSROOM, CLASSROOM) == 0


def test_known_distance_is_about_100_meters(checker):
    assert 95 <= checker.distance(CLASSROOM, ABOUT_100M) <= 105


def test_distance_is_the_same_in_both_directions(checker):
    assert checker.distance(CLASSROOM, ABOUT_1KM) == checker.distance(ABOUT_1KM, CLASSROOM)


def test_near_with_good_accuracy_is_good(checker):
    result = checker.check(ABOUT_100M, 15, CLASSROOM)
    assert result.status == GOOD
    assert 95 <= result.distance_meters <= 105


def test_far_is_far(checker):
    result = checker.check(ABOUT_1KM, 15, CLASSROOM)
    assert result.status == FAR
    assert result.distance_meters > 900


def test_exactly_at_the_radius_is_good():
    checker = LocationChecker(allowed_radius_meters=100, max_accuracy_meters=200)
    distance = checker.distance(CLASSROOM, ABOUT_100M)
    checker.allowed_radius_meters = distance
    assert checker.check(ABOUT_100M, 10, CLASSROOM).status == GOOD


def test_bad_accuracy_is_inaccurate(checker):
    result = checker.check(CLASSROOM, 500, CLASSROOM)
    assert result.status == INACCURATE
    assert result.distance_meters == 0


@pytest.mark.parametrize("accuracy", [None, "abc", -5])
def test_missing_or_strange_accuracy_is_inaccurate(checker, accuracy):
    assert checker.check(CLASSROOM, accuracy, CLASSROOM).status == INACCURATE


def test_no_location_is_inaccurate_without_distance(checker):
    result = checker.check(None, 10, CLASSROOM)
    assert result.status == INACCURATE
    assert result.distance_meters is None


@pytest.mark.parametrize("point", [(200, 10), (10, 400), (float("nan"), 5), ("x", "y")])
def test_impossible_location_is_inaccurate(checker, point):
    result = checker.check(point, 10, CLASSROOM)
    assert result.status == INACCURATE
    assert result.distance_meters is None


def test_valid_point():
    assert valid_point(32.1, 35.2)
    assert valid_point("32.1", "35.2")
    assert not valid_point(91, 0)
    assert not valid_point(0, 181)
    assert not valid_point(None, None)
