# Sample homework (Ex2): a class with a list of students
class Course:
    def __init__(self, name):
        self.name = name
        self.students = []

    def add_student(self, student):
        self.students.append(student)

    def count(self):
        return len(self.students)


course = Course("Software Engineering")
course.add_student("Dana")
course.add_student("Noa")
print(course.count())
