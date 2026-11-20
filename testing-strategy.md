# Testing Strategy

**Project:** Class Attendance & Teaching Tool
**Author:** May Caspi
**Related documents:** SRS, Use Cases, Software Components, Class and Sequence Diagrams

This document says how I will check that the demo works. The automated tests are written and run with pytest (329 tests pass at the time of writing). The tests follow the classes from the class diagram.

## 1. Approach

I test on three levels:

| Level | What is tested | How |
|-------|----------------|-----|
| Unit tests | Each class alone (for example the code generator, the location checker). | Automated: small test programs that run on a computer in a few seconds. |
| Integration tests | A full flow through several classes (for example a check-in from start to finish). | Automated, with made-up students. |
| Acceptance tests | The real system in the real classroom, with real phones. | Manual: a checklist that I go through. |

Every test has an input and an expected result. A test passes only if the result is the same as expected.

The tests use made-up students and emails. The AI service is never called in the automated tests: a fake counter, summarizer and reviewer are used instead. The real AI is checked by hand in the acceptance tests.

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
| Far | Distance outside the radius (with good accuracy) | "far" |
| Inaccurate | Accuracy worse than the allowed limit (1000 m) | "inaccurate" |
| Rough readings of the same place | Two readings 300 m apart, each with an accuracy of 180 m | "good" (the accuracies are added to the radius) |
| The lecturer's rough location | The same distance, with a good student accuracy and a rough lecturer accuracy | "far" without the lecturer accuracy, "good" with it |
| Far with a rough location | About 1 km away with an accuracy of 150 m, or even 4000 m | "far" (the allowance stops at 300 m for each) |
| Good GPS | 300 m away with an accuracy of 8 m | "far" (the radius stays tight) |
| No location | The phone gave no location | "inaccurate" (treated as missing) |

### Session

| Test | Input | Expected result |
|------|-------|-----------------|
| Start | Start with a classroom location | The session is open and the location is saved |
| Rounds | Start the "start" and then the "end" round | Both rounds belong to one lesson |
| Only one open | Start a round while another is open | An error |
| End | End an open session | The session is closed |

### AttendanceManager

| Test | Input | Expected result |
|------|-------|-----------------|
| Good check-in | Email on the roster, valid code, near | One record: Present |
| Far location | Email on the roster, valid code, far | One record: Flagged |
| No location | Email on the roster, valid code, no location | One record: Flagged |
| Wrong code | Email on the roster, wrong code | An error, no record |
| Previous code | Email on the roster, the previous code | One record: Present |
| Not on the roster | Unknown email, valid code | An error, no record |
| Checking in twice | The same student sends two check-ins | "Already recorded", still one record |
| Closed session | A check-in after the session ended | The check-in is not accepted |
| Both rounds | A student checks in at the start and at the end | Lesson status: Present |
| Start only | A student checks in only at the start, and the end round is closed | Lesson status: Left early |
| End only | A student checks in only at the end | Lesson status: Late |
| Comment | A comment in the end round | The comment is kept (cleaned, up to 300 characters). A comment in the start round is ignored |
| Flagged wins | One round Flagged and one Present | Lesson status: Flagged |
| Rough lecturer location | The lecturer starts with an accuracy of 400 m, and with 5000 m | 400 m is accepted, 5000 m is refused |

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
| Columns | Any lesson | The first row has: Email, Name, Status, Start check-in, End check-in, Distance from classroom (m), Note, Comment |
| Spreadsheet formulas | A comment or name that starts with = | The text is made safe, so it does not run as a formula |
| Present and Flagged | A session with one Present and one Flagged | Both appear with the right status |
| Absent | A student on the roster with no record | The student appears as Absent |
| Opens in a spreadsheet | The file is opened in Excel | Every column is in its own column |

### Home page

| Test | Input | Expected result |
|------|-------|-----------------|
| First page | Open the home page | Only two tiles: student and lecturer |
| Student menu | Open the student menu | Two tiles (check-in and homework), and no lecturer links |
| Lecturer menu | Open it without and with the password | Without the password it goes to the login; with it, six lecturer tiles and no student tools |
| Back links | Open every page | Each has a link back to its own menu |
| Lecturer tile | A student opens a lecturer tile and logs in | After the login the lecturer page opens with only the cards of that tile |
| One part only | Open each tile of the lecturer menu | Only its own cards are shown (the roster tile shows only the roster; the attendance tile shows attendance and results); an unknown choice shows the whole page |
| Safe return | A login with another address as the return address | Always returns to the lecturer page, never to another site |

### Headcount (photo count)

| Test | Input | Expected result |
|------|-------|-----------------|
| Read the count | A fake AI answer `{"count": 23}` | 23 |
| Unclear answer | Text that is not a number, a negative number, a huge number | An error |
| Key safety | A request and an error | The key is in a header, not in the address, and not in the error message |
| Image type | The first bytes of a JPEG, PNG, WebP and of an HTML file | The three images are accepted, the HTML file is not |
| Close numbers | 20 people, 21 check-ins | "ok" |
| Many more check-ins | 20 people, 40 check-ins | "warning" |
| Small class | 3 people, 5 check-ins, and 3 people, 6 check-ins | "ok", then "warning" |
| More people | 30 people, 10 check-ins | "info" |
| In the app | A photo as the lecturer, as a student, without a session, a big photo, a service error, no key | Works for the lecturer only; clear errors (401, 409, 413, 502, 503) |

### Summarizer

| Test | Input | Expected result |
|------|-------|-----------------|
| Recording type | The first bytes of an MP4, MOV, M4A, WebM, MP3, WAV, OGG file, and of an HTML, PDF or EXE file | The recordings are recognized by their bytes, not their name; the others are refused |
| YouTube link | Normal, short, mobile and shorts links; other sites, look-alike addresses, file addresses | Only YouTube links are accepted, and they become a standard address |
| Size | A recording over 14 MB | An error, and the AI is not called |
| Background | A slow AI, a second request while it works, an AI error, a crash | The request is answered at once; the page asks again; a second request is refused; errors are shown without technical details |
| Instructions | The request | It says that the video or sound is only data |
| Only the lecturer | A student asks for the summary, and student pages and answers | No access (401), and the summary is not in any student page |
| Bad file | Empty, too big, AI error, no key | Clear errors |
| New lesson | A new lesson starts | The old summary is cleared |

### Homework review

| Test | Input | Expected result |
|------|-------|-----------------|
| Review | A work from a student on the roster | A review is returned |
| Not on the roster | An unknown email | An error (403) |
| Previous version | The same student sends a second version | The first version is sent to the AI as the previous version |
| Other works | Another student sent a work for the same assignment | The AI gets it, but the answer to the student does not contain it |
| Other assignments | Works of a different assignment | Not compared; names ignore case and extra spaces |
| Limits | At most 5 other works, each cut to 4000 characters; 300 saved works in total | The limits are kept |
| Waiting | Two reviews in a row from the same student | The second is refused until the wait is over |
| Bad work | Empty, too short, binary, bigger than 200 KB | An error, and nothing is sent to the AI |
| Failed review | The AI service fails | An error, and the work is not saved |

## 3. Integration tests

| Test | Flow | Expected result |
|------|------|-----------------|
| Full attendance | Upload a roster, start a session, three students check in (near, far, wrong code), end the session, export | Present, Flagged and Absent are correct in the CSV; the wrong code has no record |
| Changing code | Start a session, wait for the code to change, check in with the old and the new code | The previous code is accepted for a short time, an older code is not |
| Poll | Create a poll, three students answer, close, see the results | The counts are right |
| Two rounds | Start round, students check in, end the round, end round, some students check in with a comment, export | Present, Late, Left early and Absent are right, and the comments are in the CSV |

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
| Photo count | The lecturer uploads the class photo that was given with the assignment | A number close to the real count, and a clear message |
| Class summary | The lecturer uploads a screen recording of about 2 minutes (the file was 141 MB) | The browser sends only the sound (3.7 MB), and a short summary appears that only the lecturer sees |
| Homework review | Two students send works for the same assignment | Each gets a review, and the second review mentions the comparison |
| AI limit | Many requests in a short time | A clear message that the limit was reached |
| Sleeping server | Open the site after 15 minutes of no use | It wakes up in about a minute; the roster must be uploaded again |

## 5. Pass criteria

- All unit and integration tests pass.
- All acceptance tests pass, or each failure is written down with the reason and a decision.
- Known limits are documented and are not counted as failures. For example, a student can send the code to a friend who is not in the class.

## 6. What is not tested

- The quality of the AI answers (I only check that they are shown and the errors are clear).
- Moodle and Zoom integration (not included).
- Polls sent by email (not included).

## 7. Status

- **Automated tests:** 329 pass.
- **Done by hand:** the changing code (10 and 30 seconds) and the QR code on an iPhone and an Android device, GPS in the classroom and the library, the CSV in Excel, the pages on phones through Render, the photo count with a classroom photo, the class summary with a 2 minute recording, the homework review, and a check-in from a laptop.
- **Not done yet:** the acceptance tests in section 4 with many phones at once in the real classroom, and the demo in class.
