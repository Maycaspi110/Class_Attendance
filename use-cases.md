# Use Cases

**Project:** Class Attendance & Teaching Tool
**Team:** May Caspi and Haim Barabi
**Related documents:** SoW, SRS

Each use case is a short story of how a user does one thing with the system. Attendance is the main feature (UC-1 to UC-4). The poll (UC-5) is optional: the lecturer uses it only when needed. The class summary (UC-6) is design only.

## UC-1: Lecturer uploads the course roster

**Story:** As a lecturer, I want to upload my student list, so that only registered students can check in.

- **Actor:** Lecturer
- **Before:** The lecturer opened the lecturer page.
- **Main flow:**
  1. The lecturer chooses a CSV file with the students' names and phone numbers.
  2. The system reads the file and shows how many students it found.
  3. The lecturer confirms.
  4. The system saves the roster.
- **Other cases:**
  - The file is missing the name or phone number column: the system shows an error and asks for another file.
  - The same phone number appears twice: the system shows a warning and the lecturer fixes the file.
- **After:** The roster is saved and ready for a session.
- **Related requirements:** upload the roster

## UC-2: Lecturer starts and ends an attendance session

**Story:** As a lecturer, I want to start attendance with one press in the classroom, so that students can check in without me doing anything else.

- **Actor:** Lecturer
- **Before:** A roster was uploaded. The lecturer is in the classroom and allows location on their phone.
- **Main flow:**
  1. The lecturer presses "Start" on their phone.
  2. The system takes the phone location and saves it as the classroom location.
  3. The system opens the session and shows a page for the classroom screen with a 4-digit code and a QR code.
  4. The code changes every 10-30 seconds.
  5. When the class is over, the lecturer presses "End". The system stops accepting check-ins.
- **Other cases:**
  - The location is blocked or too inaccurate: the system tells the lecturer and asks to try again.
- **After:** The session is open (or closed) and the results are available.
- **Related requirements:** start a session, show the code and QR, accept the current and previous code, end a session

## UC-3: Student checks in

**Story:** As a student, I want to mark that I am in class from my phone, so that the lecturer knows I was here.

- **Actor:** Student
- **Before:** A session is open. The student has a phone with a browser.
- **Main flow:**
  1. The student scans the QR code from the classroom screen, or opens the check-in page and types the code.
  2. The student types their phone number.
  3. The student allows location when the phone asks.
  4. The student presses "I am here".
  5. The system checks three things: the phone number is on the roster, the code is the current or the previous one, and the phone is within about 150 m of the classroom.
  6. The system records the student as Present and shows a confirmation.
- **Other cases:**
  - The phone number is not on the roster: the system shows an error.
  - The code is wrong or expired: the system shows an error and the student can try again with the new code.
  - The code is valid but the location is far, missing or too inaccurate: the system records the student as Flagged and tells the student that the lecturer will review it. The student is not rejected.
  - The student already checked in: the system says so and does not create a second record.
- **After:** The student has one record in the session: Present or Flagged.
- **Related requirements:** check in from the phone: roster, code, location, flag, messages, one record per student

## UC-4: Lecturer reviews the results and downloads the spreadsheet

**Story:** As a lecturer, I want to see who was in class and get a spreadsheet, so that I can keep the attendance record.

- **Actor:** Lecturer
- **Before:** A session was started.
- **Main flow:**
  1. The lecturer opens the results page.
  2. The system shows the students in three groups: Present, Flagged and Absent.
  3. The lecturer looks at the Flagged students (for example a valid code but a far location) and decides what to do with them.
  4. The lecturer downloads the CSV file.
- **Other cases:**
  - Nobody checked in: all students appear as Absent.
- **After:** The lecturer has a CSV file with the columns Phone number, Name, Status, Check-in time, Distance from classroom (m) and Note.
- **Related requirements:** see the results, download the CSV

## UC-5: Lecturer runs a poll (optional)

**Story:** As a lecturer, I want to ask a quick question during the lesson, so that I can see if the students understood.

- **Actor:** Lecturer, Student
- **Main flow:**
  1. The lecturer writes a question with answer options and opens the poll.
  2. Each student sees the poll on their phone and answers once.
  3. The lecturer sees the results as they come in.
- **Related requirements:** create a poll, see the results, answer once

## UC-6: Class summary from student summaries (design only)

**Story:** As a student, I want one reliable summary of the lesson, so that I do not depend on my own notes only.

- **Actor:** Student
- **Idea:** After a lesson, students upload their own summaries. An AI agent compares all the summaries and creates one combined summary as a PDF. It keeps what the summaries agree on and marks the points where they differ.
- **Status:** Design only. It is not built in the demo.
- **Things to watch:** the AI can make mistakes, so the result must be shown as a draft; and students' notes are their own work, so uploading should be voluntary.
