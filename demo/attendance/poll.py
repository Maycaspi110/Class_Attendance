"""Poll and PollAnswer: a quick question for the class."""
import threading
from collections import namedtuple

from .student import Student

MIN_OPTIONS = 2
MAX_OPTIONS = 6
MAX_QUESTION_LENGTH = 200
MAX_OPTION_LENGTH = 80

PollAnswer = namedtuple("PollAnswer", ["student", "option"])


class PollError(Exception):
    """The poll or the answer is not valid. The message is for the user."""


class Poll:
    def __init__(self, question, options):
        question = (question or "").strip()
        options = [(o or "").strip() for o in (options or [])]
        options = [o for o in options if o]
        if not question:
            raise PollError("Write a question.")
        if len(question) > MAX_QUESTION_LENGTH:
            raise PollError("The question is too long.")
        if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS:
            raise PollError("A poll needs between %d and %d answer options." % (MIN_OPTIONS, MAX_OPTIONS))
        if any(len(o) > MAX_OPTION_LENGTH for o in options):
            raise PollError("An answer option is too long.")
        if len({o.lower() for o in options}) != len(options):
            raise PollError("The answer options must be different from each other.")
        self.question = question
        self.options = options
        self.is_open = True
        self._answers = {}  # email -> PollAnswer
        self._lock = threading.Lock()

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def answer(self, student, option):
        """Save one answer. A student can answer once."""
        if not isinstance(student, Student):
            raise PollError("Unknown student.")
        with self._lock:
            if not self.is_open:
                raise PollError("This poll is closed.")
            if option not in self.options:
                raise PollError("Choose one of the answer options.")
            if student.email in self._answers:
                raise PollError("You already answered this poll.")
            self._answers[student.email] = PollAnswer(student, option)

    def has_answered(self, student):
        return student.email in self._answers

    def counts(self):
        """How many students chose each option (options with no answers show 0)."""
        with self._lock:
            result = {option: 0 for option in self.options}
            for answer in self._answers.values():
                result[answer.option] += 1
            return result

    @property
    def total_answers(self):
        return len(self._answers)
