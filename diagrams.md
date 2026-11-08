# Class Diagram and Sequence Diagrams

**Project:** Class Attendance & Teaching Tool
**Team:** May Caspi and Haim Barabi
**Related documents:** SRS, Use Cases, Software Components

This document goes one level below the components. The class diagram shows the main classes of the demo, what each one holds and does, and how they are connected. The sequence diagrams show three important scenarios step by step, in time order.

## 1. Class diagram

```mermaid
classDiagram
  class Student {
    +String name
    +String phoneNumber
  }
  class Roster {
    +List~Student~ students
    +load(csvFile)
    +findByPhone(phone) Student
  }
  class Session {
    +Location classroomLocation
    +DateTime startTime
    +String status
    +start(location)
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
    +check(location, accuracy, classroomLocation) LocationResult
  }
  class AttendanceRecord {
    +Student student
    +String status
    +DateTime checkInTime
    +int distanceMeters
    +String note
  }
  class AttendanceManager {
    +checkIn(phone, code, location, accuracy) AttendanceRecord
    +results() List~AttendanceRecord~
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
    +export(session) File
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
  CsvExporter --> Session
  CsvExporter --> Roster
```

### What each class is for

| Class | Purpose | Related requirements |
|-------|---------|----------------------|
| Student | A student: name and phone number. | identify by phone number |
| Roster | The course student list. Loads it from a CSV file and finds a student by phone number. | upload the roster, identify by phone number |
| Session | One attendance session: the classroom location, the start time and whether it is open or closed. | start and end a session |
| CodeGenerator | Creates the 4-digit code for the current time slot (10-30 seconds) and tells if an entered code is the current one, the previous one or invalid. | changing code, current and previous code |
| LocationChecker | Calculates the distance between the phone and the classroom, and decides if the location is good, far or too inaccurate. | distance check, flag |
| AttendanceRecord | One check-in of one student: status (Present or Flagged), time, distance and a note. | flag, one record per student |
| AttendanceManager | The main logic. It checks the roster, the code and the location for each check-in, and keeps one record per student. | roster, code and location checks, one record per student |
| Poll | A quick poll: a question, answer options, and the counting of answers. | create a poll, see the results |
| PollAnswer | One answer of one student. A student can answer once. | answer a poll once |
| CsvExporter | Builds the spreadsheet for the lecturer. | download the CSV |

Notes:
- **Absent** is not saved. A student is Absent when they are on the roster and have no attendance record in the session.
- Student comments and the class summary are design only and are not in the class diagram.

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

  St->>SP: Types phone number and code, allows location
  SP->>AM: checkIn(phone, code, location, accuracy)
  AM->>R: findByPhone(phone)
  R-->>AM: Student or not found
  alt Phone number is not on the roster
    AM-->>SP: Error: not on the roster
  else Phone number is on the roster
    AM->>CG: checkCode(code, now)
    CG-->>AM: current, previous or invalid
    alt Code is invalid
      AM-->>SP: Error: wrong or expired code
    else Code is valid
      AM->>LC: check(location, accuracy, classroomLocation)
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
