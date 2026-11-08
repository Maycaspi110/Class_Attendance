"""Student: a name and an email address (the email is the identity)."""
import re
from dataclasses import dataclass

_EMAIL = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")
MAX_EMAIL_LENGTH = 254


def normalize_email(text):
    """
    Turn an email address into one standard form (no spaces, lower case),
    or return None if it is not a usable address.
    """
    if text is None:
        return None
    text = str(text).strip().lower()
    if len(text) > MAX_EMAIL_LENGTH or not _EMAIL.match(text):
        return None
    return text


@dataclass(frozen=True)
class Student:
    name: str
    email: str
