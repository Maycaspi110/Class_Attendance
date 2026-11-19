"""LocationChecker: is the student close enough to the classroom?

The distance formula is the same one used in tests/location-test.html
(great-circle distance between two GPS points).
"""
import math
from collections import namedtuple

GOOD = "good"
FAR = "far"
INACCURATE = "inaccurate"

EARTH_RADIUS_METERS = 6371000

# A rough location (Wi-Fi or cell tower, for example on a laptop) can be wrong by hundreds of meters.
# The check allows for this: the two accuracies are added to the allowed radius, but only up to this much each.
MAX_ALLOWANCE_METERS = 300

# distance_meters is None when the phone gave no usable location.
LocationResult = namedtuple("LocationResult", ["status", "distance_meters"])


def valid_point(lat, lon):
    """True if lat and lon are real numbers inside the allowed ranges."""
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return False
    if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


class LocationChecker:
    def __init__(self, allowed_radius_meters=150, max_accuracy_meters=200):
        """
        allowed_radius_meters: how far from the classroom a student may be.
        max_accuracy_meters: a phone that reports a worse accuracy than this
            is treated as "inaccurate". The final value is chosen after the
            tests in class (see the SRS, open points).
        """
        self.allowed_radius_meters = allowed_radius_meters
        self.max_accuracy_meters = max_accuracy_meters

    @staticmethod
    def distance(a, b):
        """Distance in whole meters between two (lat, lon) points."""
        lat1, lon1 = map(math.radians, a)
        lat2, lon2 = map(math.radians, b)
        d_lat = lat2 - lat1
        d_lon = lon2 - lon1
        h = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
        return int(round(2 * EARTH_RADIUS_METERS * math.asin(math.sqrt(h))))

    def accuracy_ok(self, accuracy):
        try:
            accuracy = float(accuracy)
        except (TypeError, ValueError):
            return False
        return 0 <= accuracy <= self.max_accuracy_meters

    @staticmethod
    def _allowance(accuracy):
        """How many meters of doubt a location with this accuracy adds to the allowed distance."""
        try:
            return max(0.0, min(float(accuracy), MAX_ALLOWANCE_METERS))
        except (TypeError, ValueError):
            return 0.0

    def check(self, location, accuracy, classroom_location, classroom_accuracy=0):
        """
        location: (lat, lon) of the phone, or None if the phone gave nothing.
        accuracy: the accuracy in meters reported by the phone.
        classroom_location: (lat, lon) saved when the session started.
        classroom_accuracy: how exact the lecturer's location was (meters).
        """
        if location is None or not valid_point(*location):
            return LocationResult(INACCURATE, None)
        point = (float(location[0]), float(location[1]))
        distance = self.distance(point, classroom_location)
        if not self.accuracy_ok(accuracy):
            return LocationResult(INACCURATE, distance)
        if distance > self.allowed_radius_meters + self._allowance(accuracy) + self._allowance(classroom_accuracy):
            return LocationResult(FAR, distance)
        return LocationResult(GOOD, distance)
