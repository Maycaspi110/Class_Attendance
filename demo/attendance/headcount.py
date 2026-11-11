"""Headcount: count the people in a photo of the classroom, and compare with the check-ins.

The count is a rough number from an AI vision model. It is only a warning for the
lecturer: it is never proof, and nobody is marked because of it. The photo is not
saved: it is sent for counting and then forgotten.
"""
import base64
import json
import math
import urllib.error
import urllib.request

MAX_PEOPLE = 1000

PROMPT = (
    "This is a photo of a classroom. Count how many people are visible in it. "
    "Count every person you can see, also people who are partly hidden. "
    "Do not try to identify anyone. Answer only with JSON: {\"count\": <whole number>}."
)


class HeadcountError(Exception):
    """The people could not be counted. The message is safe to show to the lecturer."""


def image_type(data):
    """The image type from the first bytes of the file (a real JPEG, PNG or WebP), or None."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _default_post(url, headers, body, timeout):
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read()


class GeminiCounter:
    """Counts people with the Google Gemini API (it has a free tier). The key comes from the server settings."""

    URL = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"

    def __init__(self, api_key, model="gemini-2.5-flash", http_post=None, timeout=45):
        self.api_key = api_key
        self.model = model
        self._post = http_post or _default_post
        self.timeout = timeout

    def count(self, image_bytes, mime_type):
        body = json.dumps(
            {
                "contents": [
                    {
                        "parts": [
                            {"text": PROMPT},
                            {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}},
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "OBJECT",
                        "properties": {"count": {"type": "INTEGER"}},
                        "required": ["count"],
                    },
                },
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        try:
            _status, raw = self._post(self.URL % self.model, headers, body, self.timeout)
        except urllib.error.HTTPError as error:
            raise HeadcountError(_http_message(error.code)) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise HeadcountError("The counting service did not answer. Try again in a minute.") from None
        return _parse_count(raw)


def _http_message(code):
    if code == 429:
        return "The free AI limit was reached for now. Wait a minute and try again."
    if code in (400, 403):
        return "The counting service refused the request. Check the GEMINI_API_KEY and the model name."
    if code == 404:
        return "The AI model was not found. Check the GEMINI_MODEL setting."
    return "The counting service had a problem (code %d). Try again." % code


def _parse_count(raw):
    try:
        reply = json.loads(raw)
        text = reply["candidates"][0]["content"]["parts"][0]["text"]
        count = json.loads(text)["count"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise HeadcountError("The AI answer was not clear. Try another photo.") from None
    if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= MAX_PEOPLE:
        raise HeadcountError("The AI answer was not clear. Try another photo.")
    return count


def compare(people, check_ins):
    """
    Compare the people in the photo with the number of check-ins.
    The count is rough, so a few missing people are normal (people hidden behind
    others, the lecturer in the photo). Only a bigger gap is a warning.
    """
    tolerance = max(2, math.ceil(0.15 * check_ins))
    gap = check_ins - people
    if gap > tolerance:
        level = "warning"
        text = (
            "%d check-ins but only %d people in the photo. Some students may have checked in without "
            "being in the room. This is a rough count, so please look yourself." % (check_ins, people)
        )
    elif -gap > tolerance:
        level = "info"
        text = "%d people in the photo and %d check-ins. Some people in the room did not check in." % (people, check_ins)
    else:
        level = "ok"
        text = "%d people in the photo and %d check-ins. The numbers are close." % (people, check_ins)
    return {"level": level, "gap": gap, "tolerance": tolerance, "message": text}
