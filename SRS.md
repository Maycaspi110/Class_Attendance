# Software Requirements Specification (SRS)

**Project:** Class Attendance & Teaching Tool
**Team:** May Caspi and Haim Barabi
**Related documents:** README, SoW, tools report

## 1. Purpose and scope

This document lists what the system must do (functional requirements) and how it must behave (non-functional requirements). The main feature is automatic attendance. Lecturer polls are also implemented in the demo. Student comments and the class summary are design only and are not covered by requirements here.

## 2. Users

| User | Description |
|------|-------------|
| Lecturer | Runs the session in class, uses a phone and the classroom screen, and receives the attendance spreadsheet. |
| Student | Uses a personal smartphone browser to check in and to answer polls. |

## 3. Functional requirements

FR = Functional Requirement (what the system does). NFR = Non-functional Requirement (how the system behaves).

### 3.1 Lecturer

| Req. no. | Requirement |
|----------|-------------|
| FR-1 | The lecturer shall be able to upload the course roster (name and phone number for each student). |
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
| FR-11 | The student shall identify with a phone number. Only phone numbers on the roster are accepted. |
| FR-12 | The student shall be able to enter the code by typing it or by scanning the QR code. |
| FR-13 | The system shall ask for the phone location and check that the student is within the allowed distance from the classroom (default: about 150 m). |
| FR-14 | If the code is valid but the location is far, missing or too inaccurate, the student shall be marked Flagged for the lecturer, not rejected. |
| FR-15 | The system shall show the student a clear message: check-in received, or the reason it failed (wrong or expired code, phone number not on the roster). |
| FR-16 | A student shall have only one attendance record per session. Checking in again shall not create a duplicate. |
| FR-17 | The student shall be able to answer an open poll once. |

## 4. Non-functional requirements

| Req. no. | Requirement |
|----------|-------------|
| NFR-1 | **Simple:** a student can check in in a few taps, in about 30 seconds or less. |
| NFR-2 | **No installation:** it works in a regular browser on iPhone and Android. |
| NFR-3 | **Secure connection:** the pages are served over HTTPS only, because browsers give the location only over HTTPS. |
| NFR-4 | **Privacy:** the system keeps only the data it needs (roster, check-ins, poll answers). The location is used only to check the distance. |
| NFR-5 | **Reliable in class:** it works over the classroom network, and the previous code is still accepted for a short time after the code changes. |
| NFR-6 | **Honest limits:** the system does not claim to be fully cheat-proof, and its known limitations are documented. |

## 5. Constraints and assumptions

- Students have a smartphone with a browser and allow location access.
- GPS accuracy inside a building can be lower than outdoors. The radius is wide on purpose, and far or inaccurate locations are flagged for the lecturer to decide.
- The demo uses made-up students and phone numbers.
- In the prototype the secret used to create the code is visible in the browser. A real system would create the codes on a server.
- Not included: Moodle or Zoom integration, LLM homework review, comments and class summary (design only).

## 6. Open points

- Roster file format (planned: CSV).
- Final values for the code period (10-30 seconds) and the radius, to be confirmed after the tests in class.
