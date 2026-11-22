# Sample homework (Ex2): a third way to write the same task
students = []


def add_student(name):
    students.append(name)


def count_students():
    return len(students)


add_student("Dana")
add_student("Noa")
add_student("Ron")
print(count_students())
