# Class Diagram and Sequence Diagrams

**Project:** Class Attendance & Teaching Tool
**Author:** May Caspi
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
    +publish(name, course, due, text)
    +published(assignment) Assignment
    +allPublished() List~Assignment~
    +save(assignment, email, text)
    +workOf(assignment, email) Work
    +count(assignment) int
    +reviewWait(assignment, email) int
    +texts(assignment) List~String~
    +reportTexts(assignment) List~String~
    +overview(assignment) Overview
    +comparison(assignment, email) Comparison
    +startComparison(assignment, email) int
    +report(assignment) Report
    +startReport(assignment) bool
    +finishReport(assignment, text)
  }
  class GeminiReviewer {
    +readAssignment(pdf) Assignment text and date
    +readWork(pdf) String
    +review(work) String
    +overview(works) String
    +compare(work, overview) String
    +report(assignmentText, works) String
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
| Student | A student: name and email. | FR-11 |
| Roster | The course student list. Loads it from a CSV file and finds a student by email. | FR-1, FR-11 |
| Session | One check-in round ("start" or "end" of the class): the classroom location, the start time and whether it is open or closed. | FR-2, FR-5, FR-18 |
| LessonEntry | One student in the whole lesson: the start record, the end record and the combined status (Present, Late, Left early, Flagged or Absent). | FR-6, FR-18 |
| CodeGenerator | Creates the 4-digit code for the current time slot (10-30 seconds) and tells if an entered code is the current one, the previous one or invalid. | FR-3, FR-4 |
| LocationChecker | Calculates the distance between the phone and the classroom, and decides if the location is good, far or too inaccurate. The allowed distance grows with the two accuracies (each up to 300 m). | FR-13, FR-14, FR-25 |
| AttendanceRecord | One check-in of one student in one round: status (Present or Flagged), time, distance, a note and the comment about the lesson. | FR-14, FR-16, FR-19 |
| AttendanceManager | The main logic. It checks the roster, the code and the location for each check-in, and keeps one record per student. | FR-11, FR-13, FR-14, FR-16, FR-24 |
| Poll | A quick poll: a question, answer options, and the counting of answers. | FR-8, FR-9 |
| PollAnswer | One answer of one student. A student can answer once. | FR-17 |
| CsvExporter | Builds the spreadsheet for the lecturer from the lesson entries. | FR-7 |
| GeminiCounter | Sends a photo to the AI and returns the number of people. The comparison with the check-ins is a separate function that gives ok, warning or information. | FR-20 |
| GeminiSummarizer | Sends the sound of a recording, or a YouTube link, to the AI and returns the summary. It runs in the background. | FR-21 |
| HomeworkStore | Keeps the published assignments (course, name, due date and the text read from the PDF), the work of each student for each assignment (in memory, with a limit), the class overview, the state of each comparison (once a day for each student), and the class report for the lecturer. | FR-22, FR-23, FR-27, FR-28 |
| GeminiReviewer | Asks the AI to read the PDF of an assignment (its text and its due date) or of a work (its text), for one review of a work, for one overview of all the works, for the comparison of a work with the overview, and for one report about all the works of an assignment. | FR-22, FR-23, FR-27, FR-28 |

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
  SP->>AM: checkIn(email, code, location, accuracy, comment)
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

## 6. Sequence diagram: homework review and the comparison with the class

This scenario is use case UC-8. The assignment was published by the lecturer (section 8). The review comes first. The comparison opens when enough works exist.

```mermaid
sequenceDiagram
  actor St as Student
  participant HP as Homework page
  participant R as Roster
  participant HS as Homework store
  participant RV as Reviewer
  participant AI as AI service (Gemini)

  St->>HP: Email, the assignment chosen from the list, and the PDF of the work
  HP->>R: findByEmail(email)
  alt Email is not on the roster
    R-->>HP: Not found
    HP-->>St: Error: not on the roster
  else Email is on the roster
    HP->>RV: readWork(pdf)
    RV->>AI: The PDF
    AI-->>RV: The text of the work
    HP->>RV: review(work)
    RV->>AI: The work and the instructions
    AI-->>RV: The review text
    HP->>HS: Save the work
    HP-->>St: The review, and "N of 8 works" (the button is gray). A new review: after a day
  end

  Note over St,AI: Later, when 8 or more works exist
  St->>HP: Presses "Compare with the class"
  HP->>HS: Is there an overview, and is it new enough?
  opt No overview, or 5 or more new works since it was made
    HP->>RV: overview(all the works, each cut short)
    RV->>AI: The works and the instructions
    AI-->>RV: The class overview
    HP->>HS: Keep the overview
  end
  HP->>RV: compare(work, overview)
  RV->>AI: The overview and the work
  AI-->>RV: The comparison
  HP->>HS: Keep the result (once a day for each student)
  HP-->>St: Only the comparison (never other works or names)
```

## 7. Sequence diagram: the lecturer gets a summary of the class

This scenario is use case UC-7. The AI can take longer than the server allows for one request, so it works in the background and the page asks again.

```mermaid
sequenceDiagram
  actor Lec as Lecturer
  participant LP as Lecturer page
  participant SU as Summarizer
  participant AI as AI service (Gemini)

  Lec->>LP: Chooses a recording, presses Write the summary
  LP->>LP: Takes the sound out of the recording (16 kHz mono)
  LP->>SU: The sound
  SU-->>LP: Started (answered at once)
  SU->>AI: The sound and the instructions
  loop Every 3 seconds
    LP->>SU: Is it ready?
    SU-->>LP: Working
  end
  AI-->>SU: The summary text
  LP->>SU: Is it ready?
  SU-->>LP: The summary (or a clear error)
  LP-->>Lec: Shows the summary
```

## 8. Sequence diagram: the lecturer publishes an assignment

This scenario is use case UC-9. The students can choose the assignment only after it is published.

```mermaid
sequenceDiagram
  actor Lec as Lecturer
  participant LP as Lecturer page
  participant HS as Homework store
  participant RV as Reviewer
  participant AI as AI service (Gemini)

  Lec->>LP: Course, assignment name, due date and the PDF
  LP->>LP: Checks that the file is a PDF of 5 MB or less
  LP->>RV: readAssignment(pdf)
  RV->>AI: The PDF and the instructions
  AI-->>RV: The text of the assignment and the due date written in it
  alt The AI could not read the PDF
    LP-->>Lec: Error, nothing is published
  else The PDF was read
    LP->>HS: publish(name, course, due date, text)
    alt The date in the document is different or missing
      LP-->>Lec: Published, with a warning (the lecturer decides)
    else The dates are the same
      LP-->>Lec: Published
    end
  end
```

## 9. Sequence diagram: the lecturer gets a report about all the works

This scenario is use case UC-10. The AI can be slow, so it works in the background and the page asks again.

```mermaid
sequenceDiagram
  actor Lec as Lecturer
  participant LP as Lecturer page
  participant HS as Homework store
  participant RV as Reviewer
  participant AI as AI service (Gemini)

  Lec->>LP: Chooses the assignment, presses "Write the class report"
  LP->>HS: The due date has come? Are there works?
  alt Before the due date, or no works
    LP-->>Lec: The report opens on the due date, or an error
  else Allowed
    LP->>HS: startReport(assignment)
    LP-->>Lec: Working... (the page asks again every few seconds)
    LP->>RV: report(assignment text, all the works, each cut short)
    RV->>AI: The assignment and all the works, no names
    AI-->>RV: One report about the whole class
    LP->>HS: finishReport(text)
    Lec->>LP: The page asks again
    LP-->>Lec: The report (only the lecturer sees it)
  end
```
