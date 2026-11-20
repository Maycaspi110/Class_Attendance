# Class Diagram and Sequence Diagrams

**Project:** Class Attendance & Teaching Tool
**Team:** May Caspi and Haim Barabi
**Related documents:** SRS, Use Cases, Software Components

This document goes one level below the components. The class diagram shows the main classes of the demo, what each one holds and does, and how they are connected. The sequence diagrams show the important scenarios step by step, in time order.

## 1. Class diagram

```mermaid
classDiagram
  class Student {
    +String name
    +String email
  }
  class Roster {
    +List~Student~ students
    +load(csvFile)
    +findByEmail(email) Student
  }
  class Session {
    +Location classroomLocation
    +int classroomAccuracy
    +DateTime startTime
    +String round
    +String status
    +start(location, accuracy)
    +end()
    +isOpen() boolean
  }
  class CodeGenerator {
    +int periodSeconds
    +currentCode(now) String
    +checkCode(entry, now) CodeResult
  }
  class LocationChecker {
    +int allowedRadiusMeters
    +distance(a, b) int
    +check(location, accuracy, classroomLocation, classroomAccuracy) LocationResult
  }
  class AttendanceRecord {
    +Student student
    +String status
    +DateTime checkInTime
    +int distanceMeters
    +String note
    +String comment
  }
  class LessonEntry {
    +Student student
    +String status
    +AttendanceRecord start
    +AttendanceRecord end
  }
  class AttendanceManager {
    +startSession(location, accuracy, round)
    +checkIn(email, code, location, accuracy, comment) AttendanceRecord
    +lessonEntries() List~LessonEntry~
  }
  class Poll {
    +String question
    +List~String~ options
    +open()
    +close()
    +counts() Map
  }
  class PollAnswer {
    +Student student
    +String option
  }
  class CsvExporter {
    +export(entries) File
  }
  class GeminiCounter {
    +count(image, type) int
  }
  class GeminiSummarizer {
    +summarizeMedia(sound, type) String
    +summarizeVideo(youtubeLink) String
  }
  class HomeworkStore {
    +save(assignment, email, text)
    +previous(assignment, email) Submission
    +others(assignment, email) List~Submission~
  }
  class GeminiReviewer {
    +review(work, previous, others) String
  }

  Roster "1" o-- "*" Student
  Session "1" *-- "*" AttendanceRecord
  AttendanceRecord --> Student
  AttendanceManager --> Roster
  AttendanceManager --> Session
  AttendanceManager --> CodeGenerator
  AttendanceManager --> LocationChecker
  Poll "1" *-- "*" PollAnswer
  PollAnswer --> Student
  CsvExporter --> LessonEntry
  AttendanceManager --> LessonEntry
  LessonEntry --> AttendanceRecord
  HomeworkStore --> Student
  GeminiReviewer --> HomeworkStore
```

### What each class is for

| Class | Purpose | Related requirements |
|-------|---------|----------------------|
| Student | A student: name and email. | identify by email |
| Roster | The course student list. Loads it from a CSV file and finds a student by email. | upload the roster, identify by email |
| Session | One check-in round ("start" or "end" of the class): the classroom location, the start time and whether it is open or closed. | FR-2, FR-5, FR-18 |
| LessonEntry | One student in the whole lesson: the start record, the end record and the combined status (Present, Late, Left early, Flagged or Absent). | FR-6, FR-18 |
| CodeGenerator | Creates the 4-digit code for the current time slot (10-30 seconds) and tells if an entered code is the current one, the previous one or invalid. | changing code, current and previous code |
| LocationChecker | Calculates the distance between the phone and the classroom, and decides if the location is good, far or too inaccurate. The allowed distance grows with the two accuracies (each up to 300 m). | distance check, flag |
| AttendanceRecord | One check-in of one student in one round: status (Present or Flagged), time, distance, a note and the comment about the lesson. | flag, one record per student, FR-19 |
| AttendanceManager | The main logic. It checks the roster, the code and the location for each check-in, and keeps one record per student. | roster, code and location checks, one record per student |
| Poll | A quick poll: a question, answer options, and the counting of answers. | create a poll, see the results |
| PollAnswer | One answer of one student. A student can answer once. | answer a poll once |
| CsvExporter | Builds the spreadsheet for the lecturer from the lesson entries. | download the CSV |
| GeminiCounter | Sends a photo to the AI and returns the number of people. The comparison with the check-ins is a separate function that gives ok, warning or information. | FR-20 |
| GeminiSummarizer | Sends the sound of a recording, or a YouTube link, to the AI and returns the summary. It runs in the background. | FR-21 |
| HomeworkStore | Keeps the latest work of each student for each assignment (in memory, with a limit), and gives the previous work and up to 5 works of other students. | FR-22, FR-23 |
| GeminiReviewer | Sends the work, the previous version and the other works to the AI and returns the review. | FR-22, FR-23 |

Notes:
- **Absent** is not saved. A student is Absent when they are on the roster and have no attendance record in the session.
- The AI classes call the Google Gemini service. In the tests they are replaced by fake classes, so no real AI is called.

## 2. Sequence diagram: a student checks in

This is the main scenario (use case UC-3). It shows the checks in order: roster, code, location.

```mermaid
sequenceDiagram
  actor St as Student
  participant SP as Student page
  participant AM as Attendance manager
  participant R as Roster
  participant CG as Code generator
  participant LC as Location checker
  participant DB as Storage

  St->>SP: Types email and code, allows location
  SP->>AM: checkIn(email, code, location, accuracy)
  AM->>R: findByEmail(email)
  R-->>AM: Student or not found
  alt Email is not on the roster
    AM-->>SP: Error: not on the roster
  else Email is on the roster
    AM->>CG: checkCode(code, now)
    CG-->>AM: current, previous or invalid
    alt Code is invalid
      AM-->>SP: Error: wrong or expired code
    else Code is valid
      AM->>LC: check(location, accuracy, classroomLocation, classroomAccuracy)
      LC-->>AM: Distance and result (good, far or inaccurate)
      Note over AM: Good location gives Present. Far, missing or inaccurate location gives Flagged. If the student already has a record, the manager answers "already recorded" and saves nothing.
      AM->>DB: Save attendance record
      AM-->>SP: Check-in received
    end
  end
  SP-->>St: Shows the message
```

## 3. Sequence diagram: the lecturer starts a session

This scenario is use case UC-2. It shows how the classroom location is saved and how the classroom screen gets the code.

```mermaid
sequenceDiagram
  actor Lec as Lecturer
  participant LP as Lecturer page
  participant AM as Attendance manager
  participant DB as Storage
  participant CS as Classroom screen page
  participant CG as Code generator

  Lec->>LP: Presses Start (location allowed)
  LP->>AM: startSession(phone location)
  AM->>DB: Save new session with the classroom location
  AM-->>LP: Session is open
  CS->>CG: currentCode()
  CG-->>CS: Code and QR content
  loop Every 10-30 seconds
    CS->>CG: currentCode()
    CG-->>CS: New code and QR content
  end
  Lec->>LP: Presses End
  LP->>AM: endSession()
  AM->>DB: Mark the session as closed
```

## 4. Sequence diagram: the lecturer downloads the spreadsheet

This scenario is use case UC-4.

```mermaid
sequenceDiagram
  actor Lec as Lecturer
  participant LP as Lecturer page
  participant E as CSV exporter
  participant DB as Storage

  Lec->>LP: Presses Download CSV
  LP->>E: export(session)
  E->>DB: Read the roster and the attendance records
  DB-->>E: Students and records
  Note over E: Present and Flagged come from the records. Absent means on the roster with no record.
  E-->>LP: CSV file
  LP-->>Lec: File is downloaded
```

## 5. Sequence diagram: the lecturer counts the people in a photo

This scenario is use case UC-5.

```mermaid
sequenceDiagram
  actor Lec as Lecturer
  participant LP as Lecturer page
  participant HC as Headcounter
  participant AI as AI service (Gemini)

  Lec->>LP: Chooses a photo, presses Count the people
  LP->>LP: Makes the photo smaller
  LP->>HC: Photo
  HC->>HC: Checks that it is a real JPEG, PNG or WebP photo
  HC->>AI: Photo and the question "how many people?"
  AI-->>HC: A number
  Note over HC: The photo is forgotten. Only the number is kept.
  HC->>HC: Compares the number with the number of check-ins
  HC-->>LP: Message: close, warning or information
  LP-->>Lec: Shows the message
```

## 6. Sequence diagram: a student gets a homework review

This scenario is use case UC-8.

```mermaid
sequenceDiagram
  actor St as Student
  participant HP as Homework page
  participant R as Roster
  participant HS as Homework store
  participant RV as Reviewer
  participant AI as AI service (Gemini)

  St->>HP: Email, assignment name and the work
  HP->>R: findByEmail(email)
  alt Email is not on the roster
    R-->>HP: Not found
    HP-->>St: Error: not on the roster
  else Email is on the roster
    HP->>HS: Previous work of this student, and other students' works
    HS-->>HP: Previous work and up to 5 other works
    HP->>RV: review(work, previous, others)
    RV->>AI: The works and the instructions
    AI-->>RV: The review text
    HP->>HS: Save the work as the latest version
    HP-->>St: Only the review (never other students' works or names)
  end
```
