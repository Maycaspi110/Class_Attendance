# Testing Strategy

**Project:** Class Attendance & Teaching Tool
**Team:** May Caspi and Haim Barabi
**Related documents:** SRS, Use Cases, Software Components, Class and Sequence Diagrams

This document says how we will check that the demo works. It is a plan: the tests are run after the demo is built. The tests follow the classes from the class diagram.

## 1. Approach

We test on three levels:

| Level | What is tested | How |
|-------|----------------|-----|
| Unit tests | Each class alone (for example the code generator, the location checker). | Automated: small test programs that run on a computer in a few seconds. |
| Integration tests | A full flow through several classes (for example a check-in from start to finish). | Automated, with made-up students. |
| Acceptance tests | The real system in the real classroom, with real phones. | Manual: a checklist that we go through together. |

Every test has an input and an expected result. A test passes only if the result is the same as expected.

The tests use made-up students and emails.

## 2. Unit tests by class

### Roster

| Test | Input | Expected result |
|------|-------|-----------------|
| Load a good file | CSV with 3 students | 3 students are loaded |
| Missing column | CSV without the email column | An error is shown |
| Other columns | CSV with an extra ID number column | The ID number is ignored and not kept |
| Same email twice | CSV with a repeated email | A warning is shown |
| Find a student | An email on the roster | The student is returned |
| Unknown email | An email not on the roster | "Not found" |

### CodeGenerator

| Test | Input | Expected result |
|------|-------|-----------------|
| Same time slot | Two requests inside the same slot | The same 4-digit code |
| Format | Many different times | The code is always 4 digits |
| Code changes | Times in different slots | The code is different in the next slot |
| Current code | The code of the current slot | "current" |
| Previous code | The code of the previous slot | "previous" |
| Old code | The code from two slots ago | "invalid" |
| Wrong code | A random wrong code | "invalid" |

### LocationChecker

| Test | Input | Expected result |
|------|-------|-----------------|
| Same point | Phone at the classroom location | Distance 0 |
| Known distance | Two points about 100 m apart | Distance is about 100 m |
| Near | Distance inside the radius (150 m), good accuracy | "good" |
| Far | Distance outside the radius | "far" |
| Inaccurate | Accuracy worse than the allowed limit (the limit is set after the tests in class) | "inaccurate" |
| No location | The phone gave no location | "inaccurate" (treated as missing) |

### Session

| Test | Input | Expected result |
|------|-------|-----------------|
| Start | Start with a classroom location | The session is open and the location is saved |
| End | End an open session | The session is closed |

### AttendanceManager

| Test | Input | Expected result |
|------|-------|-----------------|
| Good check-in | Number on the roster, valid code, near | One record: Present |
| Far location | Number on the roster, valid code, far | One record: Flagged |
| No location | Number on the roster, valid code, no location | One record: Flagged |
| Wrong code | Number on the roster, wrong code | An error, no record |
| Previous code | Number on the roster, the previous code | One record: Present |
| Not on the roster | Unknown number, valid code | An error, no record |
| Checking in twice | The same student sends two check-ins | "Already recorded", still one record |
| Closed session | A check-in after the session ended | The check-in is not accepted |

### AttendanceRecord

| Test | Input | Expected result |
|------|-------|-----------------|
| Saved values | A record with a student, time and distance | The same values are read back |
| Allowed status | Status "Present" or "Flagged" | Accepted |
| Other status | Any other text | Not accepted |

### Poll and PollAnswer

| Test | Input | Expected result |
|------|-------|-----------------|
| Counting | 3 students answer: 2 choose A, 1 chooses B | A = 2, B = 1 |
| One answer | The same student answers twice | Only one answer is counted |
| Closed poll | An answer after the poll was closed | Not accepted |

### CsvExporter

| Test | Input | Expected result |
|------|-------|-----------------|
| Columns | Any session | The first row has: Email, Name, Status, Check-in time, Distance from classroom (m), Note |
| Present and Flagged | A session with one Present and one Flagged | Both appear with the right status |
| Absent | A student on the roster with no record | The student appears as Absent |
| Opens in a spreadsheet | The file is opened in Excel | Every column is in its own column |

## 3. Integration tests

| Test | Flow | Expected result |
|------|------|-----------------|
| Full attendance | Upload a roster, start a session, three students check in (near, far, wrong code), end the session, export | Present, Flagged and Absent are correct in the CSV; the wrong code has no record |
| Changing code | Start a session, wait for the code to change, check in with the old and the new code | The previous code is accepted for a short time, an older code is not |
| Poll | Create a poll, three students answer, close, see the results | The counts are right |

## 4. Acceptance tests in the classroom

These are done by hand, in the real classroom, with real phones (iPhone and Android), before the demo.

| Test | How | Expected result |
|------|-----|-----------------|
| The page opens | Open the student page on several phones | The page opens over HTTPS and the phone asks for the location |
| Typed code | A student types the code and an email | Check-in is received |
| QR code | A student scans the QR code from the classroom screen | The page opens and the check-in is received |
| Location blocked | A student refuses the location permission | The student is recorded as Flagged |
| Outside the class | A student checks in with a real code from another place (for example the library) | The student is recorded as Flagged |
| Old code | A student uses a code from a photo taken a minute ago | The code is rejected |
| Same name | Two students with the same name and different emails check in | Both appear in the CSV as separate students |
| Many phones at once | About 10 students check in together | All check-ins are recorded |
| Spreadsheet | The lecturer downloads the CSV and opens it in Excel | The file opens and the data is correct |
| Poll | The lecturer creates a poll and students answer | The results are shown |
| Weak network | A check-in on a slow connection | The student gets a clear message, success or failure |

## 5. Pass criteria

- All unit and integration tests pass.
- All acceptance tests pass, or each failure is written down with the reason and a decision.
- Known limits are documented and are not counted as failures. For example, a student can send the code to a friend who is not in the class.

## 6. What is not tested

- Student comments and the class summary (design only).
- Moodle and Zoom integration (not included).
