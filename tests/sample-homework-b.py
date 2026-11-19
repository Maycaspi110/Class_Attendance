# Sample homework (Ex2): the same task, written in a different way
class Student:
    def __init__(self, name, email):
        self.name = name
        self.email = email


class Course:
    def __init__(self, name):
        self.name = name
        self._students = {}

    def add_student(self, student):
        if student.email in self._students:
            raise ValueError("The student is already in the course")
        self._students[student.email] = student

    def count(self):
        return len(self._students)


course = Course("Software Engineering")
course.add_student(Student("Dana", "dana.levi@example.com"))
print(course.count())
