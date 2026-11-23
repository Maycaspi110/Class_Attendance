# Use Cases

**Project:** Class Attendance & Teaching Tool
**Author:** May Caspi
**Related documents:** SoW, SRS

Each use case is a short story of how a user does one thing with the system. Attendance is the main feature (UC-1 to UC-4). The photo count (UC-5), the poll (UC-6), the class summary (UC-7), the homework review (UC-8), publishing an assignment (UC-9) and the homework report for the lecturer (UC-10) are extra features. All of them are implemented in the demo.

## UC-1: Lecturer uploads the course roster

**Story:** As a lecturer, I want to upload my student list, so that only registered students can check in.

- **Actor:** Lecturer
- **Before:** The lecturer opened the lecturer page.
- **Main flow:**
  1. The lecturer chooses a CSV file with the students' names and emails.
  2. The system reads the file and shows how many students it found.
  3. The lecturer confirms.
  4. The system saves the roster.
- **Other cases:**
  - The file is missing the name or email column: the system shows an error and asks for another file.
  - The same email appears twice: the system shows a warning and the lecturer fixes the file.
- **After:** The roster is saved and ready for a session.
- **Related requirements:** FR-1

## UC-2: Lecturer starts and ends an attendance session

**Story:** As a lecturer, I want to start attendance with one press in the classroom, so that students can check in without me doing anything else.

- **Actor:** Lecturer
- **Before:** A roster was uploaded. The lecturer is in the classroom and allows location on their phone.
- **Main flow:**
  1. The lecturer presses "Start" on their phone.
  2. The system takes the phone location and saves it as the classroom location.
  3. The system opens the session and shows a page for the classroom screen with a 4-digit code and a QR code.
  4. The code changes every 10-30 seconds.
  5. The lecturer presses "End". The system stops accepting check-ins.
  6. At the end of the class the lecturer presses "Start end-of-class check-in", and the students check in again. This is a second round of the same lesson.
- **Other cases:**
  - The location is blocked or too inaccurate: the system tells the lecturer and asks to try again.
- **After:** The session is open (or closed) and the results are available.
- **Related requirements:** FR-2, FR-3, FR-4, FR-5, FR-18, FR-25

## UC-3: Student checks in

**Story:** As a student, I want to mark that I am in class from my phone, so that the lecturer knows I was here.

- **Actor:** Student
- **Before:** A session is open. The student has a phone with a browser.
- **Main flow:**
  1. The student scans the QR code from the classroom screen, or opens the check-in page and types the code.
  2. The student types their email.
  3. The student allows location when the phone asks.
  4. The student presses "I am here".
  5. The system checks three things: the email is on the roster, the code is the current or the previous one, and the phone is within about 150 m of the classroom.
  6. The system records the student for this round and shows a confirmation. In the end-of-class round the student can also write a short comment about the lesson (up to 300 characters).
- **Other cases:**
  - The email is not on the roster: the system shows an error.
  - The code is wrong or expired: the system shows an error and the student can try again with the new code.
  - The code is valid but the location is far, missing or too inaccurate: the system records the student as Flagged and tells the student that the lecturer will review it. The student is not rejected.
  - The student already checked in: the system says so and does not create a second record.
- **After:** The student has one record per round (start and end): Present or Flagged. Together they give the lesson status: Present (both rounds), Late (only the end round), Left early (only the start round) or Absent.
- **Related requirements:** FR-10 to FR-16, FR-19, FR-24

## UC-4: Lecturer reviews the results and downloads the spreadsheet

**Story:** As a lecturer, I want to see who was in class and get a spreadsheet, so that I can keep the attendance record.

- **Actor:** Lecturer
- **Before:** A session was started.
- **Main flow:**
  1. The lecturer opens the results page.
  2. The system shows the students in groups: Present, Late, Left early, Flagged and Absent, and the comments about the lesson.
  3. The lecturer looks at the Flagged students (for example a valid code but a far location) and decides what to do with them.
  4. The lecturer downloads the CSV file.
- **Other cases:**
  - Nobody checked in: all students appear as Absent.
- **After:** The lecturer has a CSV file with the columns Email, Name, Status, Start check-in, End check-in, Distance from classroom (m), Note and Comment.
- **Related requirements:** FR-6, FR-7

## UC-5: Lecturer checks the number of people with a photo

**Story:** As a lecturer, I want to photograph the classroom and compare the number of people with the check-ins, so that I can notice check-ins from students who are not in the room.

- **Actor:** Lecturer
- **Before:** A check-in is open.
- **Main flow:**
  1. The lecturer takes or chooses a photo of the classroom and presses "Count the people".
  2. The system sends the photo to an AI, which returns the number of people. The photo is not saved.
  3. The system compares the number with the check-ins and shows a message: the numbers are close, or there are many more check-ins than people (a warning), or more people than check-ins.
- **Other cases:**
  - The file is not a real photo, or it is too big: the system shows an error.
  - The AI service is not available or its limit was reached: the system shows a clear message.
- **After:** The lecturer sees the count. It is a rough number and only a warning: nobody is marked because of it.
- **Related requirements:** FR-20

## UC-6: Lecturer runs a poll

**Story:** As a lecturer, I want to ask a quick question during the lesson or at its end, so that I can see if the students understood.

- **Actor:** Lecturer, Student
- **Main flow:**
  1. The lecturer writes a question with answer options (or uses the ready question "Did you understand the lesson?") and opens the poll.
  2. Each student sees the poll on their phone and answers once.
  3. The lecturer sees the results as they come in.
- **Related requirements:** FR-8, FR-9, FR-17

## UC-7: Lecturer gets a summary of the class

**Story:** As a lecturer, I want a short summary of my class from its recording, so that I can see what was covered.

- **Actor:** Lecturer
- **Main flow:**
  1. The lecturer chooses a recording of the class (a screen recording or a Zoom recording, up to about 7 minutes), or pastes a link to a public YouTube video.
  2. For a recording, the browser takes the sound out of it. This keeps the upload small, even if the video is 100 MB or more.
  3. The system sends the sound (or the link) to an AI. The AI works in the background, and the page shows the progress.
  4. The system shows the summary: main topics, key points, students' questions and tasks. Only the lecturer can see it.
- **Other cases:** the recording has no sound, is too long, is not a recording, or the AI is not available or too slow: the system shows a clear error.
- **After:** The recording is not saved. The summary stays in memory until the next lesson starts.
- **Related requirements:** FR-21

## UC-8: Student gets a review of homework and compares it with the class

**Story:** As a student, I want a detailed review of my homework, and to see how it compares with the rest of the class, so that I can improve it before I submit it.

- **Actor:** Student
- **Before:** The student is on the roster. The lecturer published the assignment (UC-9).
- **Main flow:**
  1. The student opens the homework page, types their email, chooses the assignment from the list that the lecturer published, and uploads a text or code file (or pastes the text).
  2. The system sends the work to an AI. The student gets a review: summary, strengths, problems and suggestions. The page says when a new review is possible: once a day for each assignment.
  3. The page shows how many students sent their work, for example "5 of 8". Until 8 students did, the comparison button is gray.
  4. When 8 or more students sent their work, the button opens. The student presses it.
  5. The AI makes one general overview of all the works of the assignment (only what several works share), and compares the work of the student with it: how close it is to the general direction, what is different, and how to improve. The student reads the result.
- **Other cases:**
  - The email is not on the roster, or the work is empty or not a text file: the system shows an error.
  - The student sends a work again on the same day: the system says how long to wait. After a day, a new version replaces the old one and gets a new review.
  - The AI is not available: a clear error, and the student can try the comparison again.
- **After:** The work stays in memory for the overview. The student can compare once a day. The student never sees another student's work or name.
- **Related requirements:** FR-22, FR-23

## UC-9: Lecturer publishes an assignment

**Story:** As a lecturer, I want to publish an assignment with its due date, so that the students choose it from a list and the system knows what the assignment asks for.

- **Actor:** Lecturer
- **Before:** The lecturer is logged in.
- **Main flow:**
  1. The lecturer opens the "Publish an assignment" tile and writes the course name and the assignment name.
  2. The lecturer chooses the due date and uploads the PDF of the assignment.
  3. The AI reads the PDF and checks the due date written inside it against the chosen date.
  4. The page says that the assignment is published. If the dates differ, or the document has no date, the page shows a warning.
- **Other cases:**
  - The file is not a PDF, is too large (over 5 MB), or has no readable text: the system shows an error.
  - The date in the document is different: it is only a warning. The lecturer can publish again with a fixed date.
  - The AI is not available: a clear error, and nothing is published.
- **After:** The assignment appears in the list on the student homework page (course, name and due date, never the text). The text read from the PDF is kept for the class report.
- **Related requirements:** FR-27

## UC-10: Lecturer gets a report about all the works of an assignment

**Story:** As a lecturer, I want one report about all the works of an assignment on the due date, so that I can see if the class understood the assignment and what to explain again.

- **Actor:** Lecturer
- **Before:** The lecturer published the assignment (UC-9). Students sent works for it (UC-8).
- **Main flow:**
  1. The lecturer opens the "Homework report" tile and chooses the assignment from the list. The page shows the due date and how many students sent a work.
  2. Until the due date, the button is gray.
  3. On the due date, the lecturer presses "Write the class report".
  4. The AI reads all the works together with the text of the assignment, and writes one report: do the works match the assignment, which mistakes repeat or what was not clear, what was interesting or special, and what to explain again. It can take a few minutes.
  5. The lecturer reads the report. Only the lecturer sees it.
- **Other cases:**
  - Before the due date: the page says when the report opens.
  - No student sent a work: the system shows an error.
  - The AI is not available: a clear error, the old report stays, and the lecturer can try again.
- **After:** The report is kept in memory until the server restarts. It does not name any student and does not describe works one by one.
- **Related requirements:** FR-28
