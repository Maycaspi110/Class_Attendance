"""CodeGenerator: the 4-digit code that changes every few seconds.

Same idea as the prototype page (tests/code-test.html): the code depends on
a secret and on the current time slot. Here it runs on the server, so the
secret is never sent to the browser. The hash is HMAC-SHA256, which is a
better choice than the small hash used in the prototype.
"""
import hashlib
import hmac

CURRENT = "current"
PREVIOUS = "previous"
INVALID = "invalid"

MIN_PERIOD_SECONDS = 10
MAX_PERIOD_SECONDS = 30


class CodeGenerator:
    def __init__(self, secret, period_seconds=20):
        if not secret:
            raise ValueError("The code secret must not be empty.")
        if not MIN_PERIOD_SECONDS <= period_seconds <= MAX_PERIOD_SECONDS:
            raise ValueError(
                "The code period must be between %d and %d seconds."
                % (MIN_PERIOD_SECONDS, MAX_PERIOD_SECONDS)
            )
        self._secret = secret.encode("utf-8")
        self.period_seconds = period_seconds

    def slot(self, now):
        """The number of the time slot that contains `now` (seconds)."""
        return int(now // self.period_seconds)

    def code_for_slot(self, slot):
        digest = hmac.new(self._secret, str(slot).encode("ascii"), hashlib.sha256).digest()
        number = int.from_bytes(digest[:8], "big") % 10000
        return "%04d" % number

    def current_code(self, now):
        return self.code_for_slot(self.slot(now))

    def seconds_left(self, now):
        """Whole seconds until the code changes (at least 1)."""
        left = self.period_seconds - (now % self.period_seconds)
        return max(1, int(left + 0.999999))

    def check_code(self, entry, now):
        """Return CURRENT, PREVIOUS or INVALID for the code a student typed."""
        entry = (entry or "").strip()
        if len(entry) != 4 or not entry.isdigit():
            return INVALID
        slot = self.slot(now)
        if hmac.compare_digest(entry, self.code_for_slot(slot)):
            return CURRENT
        if hmac.compare_digest(entry, self.code_for_slot(slot - 1)):
            return PREVIOUS
        return INVALID
