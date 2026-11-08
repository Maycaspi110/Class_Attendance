"""Student: a name and a phone number (the phone number is the identity)."""
import re
from dataclasses import dataclass


def normalize_phone(text):
    """
    Turn a phone number into one standard form, or return None if it is not
    a usable number. Spaces, dashes, dots and brackets are removed, and an
    Israeli international prefix (+972 / 972) becomes a leading 0.
    """
    if text is None:
        return None
    text = str(text).strip()
    text = re.sub(r"[\s\-\.\(\)]", "", text)
    if text.startswith("+"):
        text = text[1:]
    if not text.isdigit():
        return None
    if text.startswith("972") and len(text) >= 11:
        text = "0" + text[3:]
    if not 9 <= len(text) <= 15:
        return None
    return text


@dataclass(frozen=True)
class Student:
    name: str
    phone_number: str
