# Testing Strategy

**Project:** Class Attendance & Teaching Tool
**Author:** May Caspi
**Related documents:** SRS, Use Cases, Software Components, Class and Sequence Diagrams

The tests follow the classes of the class diagram. The automated tests are written with pytest (329 pass). The numbers (radius, limits) are in the SRS.

## 1. Approach

| Level | What is tested | How |
|-------|----------------|-----|
| Unit | Each class alone | Automated, in `demo/tests` |
| Integration | A full flow through several classes and pages | Automated, with made-up students |
| Acceptance | The real system, real phones, the real AI | By hand, with a checklist |

Every test has an input and an expected result. The automated tests use made-up students and **never call the real AI**: a fake counter, summarizer and reviewer are used. The real AI is checked by hand.

## 2. Unit tests by class

| Class | What is tested | Test file |
|-------|----------------|-----------|
| Roster | A good file, a missing column, extra columns ignored (no ID number kept), a repeated email, finding a student, an unknown email | `test_roster.py` |
| CodeGenerator | Same code in one time slot, always 4 digits, a new code in the next slot, current / previous / invalid | `test_code_generator.py` |
| LocationChecker | Distance (0 and about 100 m), near / far / inaccurate / no location, rough readings of the same place are good, the two accuracies are added up to 300 m each, a far place stays far, a good GPS keeps the radius tight | `test_location_checker.py` |
| Session | Start with a location, the two rounds of one lesson, only one round open, end | `test_session.py` |
| AttendanceManager | Present and Flagged check-ins, a wrong or old code, not on the roster, one record per student, a closed session, the lesson status (Present, Late, Left early, Flagged wins), the 300 character comment, 5 wrong codes lock | `test_attendance_manager.py`, `test_lesson.py` |
| AttendanceRecord | Saved values, only Present or Flagged | `test_attendance_record.py` |
| Poll, PollAnswer | Counting, one answer per student, a closed poll | `test_poll.py` |
| CsvExporter | The columns, Present / Flagged / Absent rows, text that starts with `=` is made safe | `test_csv_exporter.py` |
| Headcount | The count is read from the AI answer, unclear answers, the key is never in the address or in an error, the file type is read from its bytes, ok / warning / info comparison | `test_headcount.py`, `test_headcount_app.py` |
| Summarizer | Recording type from the bytes, only YouTube links, the size limit, the work in the background, only the lecturer can see the summary, clear errors | `test_summary.py` |
| Homework review | A review, not on the roster, the previous version, other works compared but never shown, the limits (5 works, 200 KB), the wait between reviews, a failed review is not saved | `test_homework.py` |
| App and pages | A lecturer location worse than 500 m is refused, the first page has two tiles, each menu has its own tiles and links back, the lecturer menu needs the password, each tile shows only its own part, the login returns only to our own pages | `test_app.py` |

## 3. Integration tests

| Test | Flow | Expected result |
|------|------|-----------------|
| Full attendance | Roster, start, three students (near, far, wrong code), end, export | Present, Flagged and Absent are right in the CSV; the wrong code has no record |
| Changing code | Wait for the code to change, then check in with the old and the new code | The previous code is accepted, an older one is not |
| Two rounds | Start round, end round, comments, export | Present, Late, Left early, Absent and the comments are right |
| Poll | Create, three answers, close | The counts are right |

## 4. Acceptance tests in the classroom

By hand, with real phones (iPhone and Android).

| Test | Expected result |
|------|-----------------|
| Open the student page on several phones | It opens over HTTPS and asks for the location |
| Typed code and QR code | The check-in is received |
| Location blocked, or a check-in from another place | The student is Flagged |
| An old code from a photo | The code is rejected |
| About 10 students check in together | All check-ins are recorded |
| Download the CSV and open it in Excel | The data is correct |
| Photo count with the class photo from the lecturer | A number close to the real count, and a clear message |
| Class summary with a recording of about 2 minutes | The browser sends only the sound, and a summary appears for the lecturer only |
| Homework review with two works of one assignment | The second review compares with the first |
| Many AI requests in a short time | A clear message that the limit was reached |
| The site after 15 minutes of no use | It wakes up in about a minute; the roster is uploaded again |

## 5. Pass criteria and status

- All unit and integration tests pass: **329 pass**.
- Each acceptance test passes, or the failure is written down with a decision. Known limits (for example a code sent to a friend) are not failures.
- **Done by hand:** the changing code and the QR code on an iPhone and an Android device, GPS in the classroom and the library, the CSV in Excel, the pages on phones through Render, the photo count, the class summary with a 2 minute recording, the homework review, and a check-in from a laptop.
- **Evidence:** the `evidence` folder has the pytest output and screenshots (photo count, results, poll, and the first code and QR tests).
- **Not done yet:** many phones at once in the real classroom, and the demo in class.
- **Not tested:** the quality of the AI answers (only that they are shown and the errors are clear), Moodle and Zoom, and polls sent by email (not included).
