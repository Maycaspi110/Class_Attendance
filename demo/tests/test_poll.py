import pytest

from attendance.poll import Poll, PollAnswer, PollError
from attendance.student import Student

DANA = Student("Dana Levi", "0500000001")
NOA = Student("Noa Cohen", "0500000002")
RON = Student("Ron Mizrahi", "0500000003")


@pytest.fixture
def poll():
    return Poll("Did you understand the lesson?", ["Yes", "A little", "No"])


def test_counting_answers(poll):
    poll.answer(DANA, "Yes")
    poll.answer(NOA, "Yes")
    poll.answer(RON, "No")
    assert poll.counts() == {"Yes": 2, "A little": 0, "No": 1}
    assert poll.total_answers == 3


def test_a_student_can_answer_only_once(poll):
    poll.answer(DANA, "Yes")
    with pytest.raises(PollError):
        poll.answer(DANA, "No")
    assert poll.counts()["Yes"] == 1
    assert poll.counts()["No"] == 0
    assert poll.total_answers == 1


def test_answer_after_the_poll_was_closed_is_not_accepted(poll):
    poll.close()
    with pytest.raises(PollError):
        poll.answer(DANA, "Yes")
    assert poll.total_answers == 0


def test_a_closed_poll_can_be_opened_again(poll):
    poll.close()
    poll.open()
    poll.answer(DANA, "Yes")
    assert poll.total_answers == 1


def test_answer_must_be_one_of_the_options(poll):
    with pytest.raises(PollError):
        poll.answer(DANA, "Maybe")


def test_has_answered(poll):
    assert not poll.has_answered(DANA)
    poll.answer(DANA, "Yes")
    assert poll.has_answered(DANA)
    assert not poll.has_answered(NOA)


def test_poll_answer_holds_the_student_and_the_option():
    assert PollAnswer(DANA, "Yes") == PollAnswer(student=DANA, option="Yes")


def test_question_and_options_are_cleaned_up():
    poll = Poll("  Question?  ", [" A ", "", "B"])
    assert poll.question == "Question?"
    assert poll.options == ["A", "B"]


@pytest.mark.parametrize(
    "question, options",
    [
        ("", ["A", "B"]),
        ("Q?", ["A"]),
        ("Q?", []),
        ("Q?", ["A", "B", "C", "D", "E", "F", "G"]),
        ("Q?", ["A", "a"]),
        ("Q" * 201, ["A", "B"]),
        ("Q?", ["A", "B" * 81]),
    ],
)
def test_bad_polls_are_not_created(question, options):
    with pytest.raises(PollError):
        Poll(question, options)
