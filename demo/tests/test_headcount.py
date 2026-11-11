"""Counting the people in a photo: the Gemini answer, the errors and the comparison."""
import base64
import json
import urllib.error

import pytest

from attendance.headcount import GeminiCounter, HeadcountError, compare, image_type

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 20


def answer(count_text):
    body = {"candidates": [{"content": {"parts": [{"text": count_text}]}}]}
    return 200, json.dumps(body).encode()


def counter_with(post):
    return GeminiCounter("test-key", "test-model", http_post=post)


def test_the_count_is_read_from_the_answer():
    assert counter_with(lambda *a: answer('{"count": 23}')).count(JPEG, "image/jpeg") == 23


def test_the_request_has_the_key_in_a_header_and_the_photo_inside():
    seen = {}

    def post(url, headers, body, timeout):
        seen.update(url=url, headers=headers, body=json.loads(body))
        return answer('{"count": 1}')

    counter_with(post).count(JPEG, "image/jpeg")
    assert seen["headers"]["x-goog-api-key"] == "test-key"
    assert "test-key" not in seen["url"]  # the key is never in the address
    assert "test-model" in seen["url"]
    part = seen["body"]["contents"][0]["parts"][1]["inline_data"]
    assert part["mime_type"] == "image/jpeg" and base64.b64decode(part["data"]) == JPEG


@pytest.mark.parametrize(
    "text", ["not json", '{"count": "many"}', '{"count": -3}', '{"count": 5000}', '{"count": true}', "{}"]
)
def test_an_unclear_answer_is_an_error(text):
    with pytest.raises(HeadcountError):
        counter_with(lambda *a: answer(text)).count(JPEG, "image/jpeg")


def test_an_empty_reply_is_an_error():
    with pytest.raises(HeadcountError):
        counter_with(lambda *a: (200, b"{}")).count(JPEG, "image/jpeg")


@pytest.mark.parametrize("code, word", [(429, "limit"), (403, "GEMINI_API_KEY"), (404, "GEMINI_MODEL"), (500, "500")])
def test_http_errors_give_a_clear_message_without_the_key(code, word):
    def post(*args):
        raise urllib.error.HTTPError("https://example/?key=test-key", code, "x", {}, None)

    with pytest.raises(HeadcountError) as error:
        counter_with(post).count(JPEG, "image/jpeg")
    assert word in str(error.value) and "test-key" not in str(error.value)


def test_no_network_is_an_error():
    def post(*args):
        raise urllib.error.URLError("down")

    with pytest.raises(HeadcountError):
        counter_with(post).count(JPEG, "image/jpeg")


def test_image_type_is_read_from_the_bytes_not_the_name():
    assert image_type(JPEG) == "image/jpeg"
    assert image_type(b"\x89PNG\r\n\x1a\n....") == "image/png"
    assert image_type(b"RIFF1234WEBPxxxx") == "image/webp"
    assert image_type(b"<html>not an image</html>") is None
    assert image_type(b"") is None


def test_close_numbers_are_ok():
    assert compare(20, 21)["level"] == "ok"
    assert compare(20, 20)["gap"] == 0


def test_many_more_check_ins_than_people_is_a_warning():
    result = compare(20, 40)
    assert result["level"] == "warning" and result["gap"] == 20
    assert "rough" in result["message"]


def test_a_small_class_has_a_minimum_tolerance():
    assert compare(3, 5)["level"] == "ok"  # a gap of 2 is normal
    assert compare(3, 6)["level"] == "warning"


def test_more_people_than_check_ins_is_only_information():
    assert compare(30, 10)["level"] == "info"
