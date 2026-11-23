# Software Requirements Specification (SRS)

**Project:** Class Attendance & Teaching Tool
**Author:** May Caspi
**Related documents:** README, SoW, tools report

## 1. Purpose and scope

This document lists what the system must do (functional requirements) and how it must behave (non-functional requirements). The main feature is automatic attendance. Student comments, the photo count, lecturer polls, the class summary and the homework review are also implemented in the demo.

## 2. Users

| User | Description |
|------|-------------|
| Lecturer | Runs the session in class, uses a phone and the classroom screen, and receives the attendance spreadsheet. |
| Student | Uses a personal smartphone browser to check in, to comment, to answer polls and to send homework. |

## 3. Functional requirements

FR = Functional Requirement (what the system does). NFR = Non-functional Requirement (how the system behaves).

### 3.1 Lecturer

| Req. no. | Requirement |
|----------|-------------|
| FR-1 | The lecturer shall be able to upload the course roster (name and email for each student). The system shall keep the roster, so the lecturer uploads it once for the course. |
| FR-2 | The lecturer shall be able to start an attendance session. Starting the session stores the classroom location, taken from the lecturer's phone. |
| FR-3 | The system shall show a 4-digit code and a matching QR code on the classroom screen. The code shall change every 10-30 seconds. |
| FR-4 | The system shall accept the current code and the previous code. |
| FR-5 | The lecturer shall be able to end the session. After that, no more check-ins are accepted. |
| FR-6 | The lecturer shall be able to see who is Present, who is Flagged and who is Absent. |
| FR-7 | The lecturer shall be able to download the results as a CSV spreadsheet. |
| FR-8 | The lecturer shall be able to create a quick poll (a question with answer options). |
| FR-9 | The lecturer shall be able to see the poll results. |

### 3.2 Student

| Req. no. | Requirement |
|----------|-------------|
| FR-10 | The student shall be able to open the check-in page in a phone browser, without installing anything. |
| FR-11 | The student shall identify with an email address. Only emails on the roster are accepted. |
| FR-12 | The student shall be able to enter the code by typing it or by scanning the QR code. |
| FR-13 | The system shall ask for the phone location and check that the student is within the allowed distance from the classroom (default: about 150 m). |
| FR-14 | If the code is valid but the location is far, missing or too inaccurate (an accuracy worse than 1000 m), the student shall be marked Flagged for the lecturer, not rejected. |
| FR-15 | The system shall show the student a clear message: check-in received, or the reason it failed (wrong or expired code, email not on the roster). |
| FR-16 | A student shall have only one attendance record per session. Checking in again shall not create a duplicate. |
| FR-17 | The student shall be able to answer an open poll once. |
| FR-18 | The lecturer shall be able to open a second check-in at the end of the class. Students who checked in only at the start are shown as Left early, and students who checked in only at the end are shown as Late. |
| FR-19 | The student shall be able to write a short comment (up to 300 characters) in the end check-in. The lecturer sees the comments and they are in the CSV. |
| FR-20 | The lecturer shall be able to upload a photo of the classroom. The system counts the people with an AI and compares the number with the check-ins. The result is a warning only, and the photo is not saved. |
| FR-21 | The lecturer shall be able to upload a recording of the class (MP4, WebM, MP3, M4A or WAV, up to about 7 minutes, so at most 14 MB of sound) or paste a link to a public YouTube video, and get an AI summary. The sound is taken out of the recording in the browser. Only the lecturer can see the summary. |
| FR-22 | The student shall be able to send a homework (the PDF of the work, up to 5 MB; the AI reads the text from the PDF) with the roster email and choose the assignment from the list that the lecturer published, and get an AI review (summary, strengths, problems and suggestions) once a day for each assignment. A new version of the work replaces the old one, and can get a new review after a day. |
| FR-23 | When at least 8 students (a server setting) sent their work for the same assignment, each of them can compare their own work with the class, once a day. The AI makes one general overview of all the works (only what several works share, no details of a single work) and compares the work of the student with it. Before that the comparison is closed and shows how many works are missing. The student shall never see another student's work or name. |
| FR-24 | A student who types 5 wrong codes in a row shall wait one minute, to stop guessing of the 4-digit code. |
| FR-25 | The lecturer can start a check-in only if the accuracy of the lecturer's location is 500 m or better. |
| FR-26 | The lecturer pages (the menu, the roster, attendance and results, the photo count, the class summary, the poll, publishing assignments, the homework report and the classroom screen) shall need the lecturer password. The first page lets everyone choose student or lecturer, and each tile of the lecturer menu shows only its own part. |
| FR-27 | The lecturer shall be able to publish an assignment: the course name, the assignment name, the due date and the PDF of the assignment (up to 5 MB). The AI reads the PDF and checks that the due date inside the document is the date the lecturer chose. A different or missing date is a warning only, and the lecturer decides. Publishing the same name again fixes it. |
| FR-28 | On the due date of a published assignment (or later) the lecturer can ask for a class report. The AI reads all the works of the assignment together, with the text of the assignment, and writes one report for the lecturer: do the works match what the assignment asks for, which mistakes repeat or what was not clear, and what was interesting or special. The report is about the class, not about each student, and has no names. Only the lecturer can see it. Before the due date the button is closed. |

## 4. Non-functional requirements

| Req. no. | Requirement |
|----------|-------------|
| NFR-1 | **Simple:** a student can check in in a few taps, in about 30 seconds or less. |
| NFR-2 | **No installation:** it works in a regular browser on iPhone and Android. |
| NFR-3 | **Secure connection:** the pages are served over HTTPS only, because browsers give the location only over HTTPS. |
| NFR-4 | **Privacy:** the system keeps only the data it needs (roster, check-ins, poll answers). The location is used only to check the distance. |
| NFR-5 | **Reliable in class:** it works over the classroom network, and the previous code is still accepted for a short time after the code changes. |
| NFR-6 | **Honest limits:** the system does not claim to be fully cheat-proof, and its known limitations are documented. |
| NFR-7 | **AI service:** the AI key is kept only in the server settings, never in the code or the browser. AI errors are shown to the user as clear messages. |
| NFR-8 | **AI privacy:** photos, the sound of recordings and works are sent to the AI service only to get a result, and are not stored. Only the result is kept in memory. |

## 5. Constraints and assumptions

- Students have a smartphone with a browser and allow location access.
- GPS accuracy inside a building can be lower than outdoors, and a laptop guesses its location from the Wi-Fi. The radius is wide on purpose. The allowed distance is the radius plus the accuracy of the student's location and the accuracy of the lecturer's location (each counted up to 300 m), so one laptop is not flagged because of two rough readings. Far or inaccurate locations are flagged for the lecturer to decide.
- The demo uses made-up students and emails.
- The roster file may have other columns (for example an ID number). The system ignores them and does not keep them.
- In the demo app the codes are created and checked on the server, and the browser never gets the secret. (Only the early test page `tests/code-test.html` had the secret in the browser.)
- In the demo the data is kept in memory and is lost when the server restarts. A real system would keep it in a database.
- The homework review never shows another student's work or name. The comparison uses a general overview of all the works, which is told to describe only what several works share, so a single work should not be recognized. With few works this is not a guarantee.
- A firewall in front of the demo server (the hosting service) can stop an uploaded text that looks like an attack, for example a README with SQL words or a path such as `../../etc/passwd`. Then the lecturer or student sees only a 403 answer, and has to remove that text.
- The photo count is a rough number. It is a warning for the lecturer and nobody is marked because of it.
- The homework page identifies the student only by the roster email, like the check-in, so it can be misused. A real system would add a login.
- Not included: Moodle or Zoom integration, students uploading their own class summaries, polls sent by email.

## 6. Open points

- Roster file format (planned: CSV).
- Decided: the code period is 10-30 seconds (30 on the demo server) and the radius is 150 m by default, with the accuracy of the two locations added. Both can be set in the server settings.
