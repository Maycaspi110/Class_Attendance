# Software Components

**Project:** Class Attendance & Teaching Tool
**Author:** May Caspi
**Related documents:** SRS, Use Cases

This document lists the main parts of the software, what each part does, and which parts talk to each other. It does not describe code. Classes and sequences are in the next document.

## 1. Overview

The system has two sides:

- **Pages in the browser** (what people see): the lecturer page, the classroom screen page, the student page and the homework page. All of them open in a normal phone or computer browser, with nothing to install.
- **Server** (what works behind the scenes): it creates the codes, checks every check-in, keeps the data, creates the spreadsheet and talks to the AI service.

```mermaid
flowchart LR
  subgraph Browser["Pages in the browser"]
    L["Lecturer page"]
    C["Classroom screen page"]
    S["Student page"]
    H["Homework page"]
  end
  subgraph Server["Server"]
    A["Attendance manager"]
    G["Code generator"]
    LC["Location checker"]
    P["Poll manager"]
    E["CSV exporter"]
    HC["Headcounter"]
    SU["Summarizer"]
    HW["Homework reviewer"]
  end
  D[("Storage")]
  AI(["AI service: Google Gemini"])

  L --> A
  L --> P
  L --> E
  C --> G
  S --> A
  S --> P
  A --> G
  A --> LC
  A --> D
  P --> D
  E --> D
  L --> HC
  L --> SU
  H --> HW
  HC --> AI
  SU --> AI
  HW --> AI
  HW --> D
```

## 2. Components

### Pages in the browser

| Component | What it does | Used by | Related requirements |
|-----------|--------------|---------|--------------|
| Home page and menus | A first page with two tiles (student or lecturer), a student menu (check-in, homework) and a lecturer menu with six tiles (roster, attendance, classroom screen, photo count, class summary, poll). The lecturer menu needs the password, and each of its tiles opens only its own part of the lecturer page (for example only the roster). The design uses blue, white, purple and gray. | Everyone | FR-10, FR-22 |
| Lecturer page | Uploads the roster, starts and ends the start and end check-ins, shows the results and the comments, uploads the classroom photo, uploads a class recording (or a YouTube link) and shows the summary, downloads the CSV, creates a poll and shows its results. | Lecturer | FR-1 to FR-9, FR-18, FR-20, FR-21 |
| Classroom screen page | Shows the current 4-digit code and the QR code, and updates them when the code changes. | Classroom screen | show the code and QR |
| Student page | The student enters an email and a code (or arrives from the QR code), allows location, writes a comment in the end check-in, sees a confirmation or an error, and answers a poll. | Student | FR-10 to FR-17, FR-19 |
| Homework page | The student enters an email, chooses the assignment from the list and sends the PDF of the work with one button, and asks for the AI review with another button. | Student | FR-22, FR-23 |

### Server

| Component | What it does | Related requirements |
|-----------|--------------|--------------|
| Code generator | Creates the 4-digit code for the current time slot (10-30 seconds) and tells whether a code is the current or the previous one. | FR-3, FR-4 |
| Location checker | Calculates the distance between the student's phone and the classroom location. The allowed distance is the radius plus the accuracy of the student's location and of the lecturer's location (each up to 300 m). A location worse than the accuracy limit, or missing, is "inaccurate". | FR-13, FR-14, FR-25 |
| Attendance manager | The main logic. For each check-in it checks the roster, the code and the location, and records Present or Flagged, for the start or the end round. It combines the two rounds into the lesson status (Present, Late, Left early, Flagged, Absent) and keeps the comments. | FR-1 to FR-7, FR-11 to FR-16, FR-18, FR-19 |
| Poll manager | Saves a poll, receives one answer per student and counts the answers. | FR-8, FR-9, FR-17 |
| CSV exporter | Builds the spreadsheet for the lecturer (Email, Name, Status, Start check-in, End check-in, Distance from classroom, Note, Comment). | FR-7 |
| Headcounter | Sends the classroom photo to the AI service, gets the number of people, and compares it with the number of check-ins (ok, warning or information). The photo is not saved. | FR-20 |
| Summarizer | Receives the sound of a class recording (the browser takes it out of the video) or a YouTube link, asks the AI service for a summary in the background, and keeps the result. Only the lecturer gets it. | FR-21 |
| Homework reviewer | (Also keeps the published assignments with their due date and text, reads the PDF of an assignment with the AI, and writes, on the due date, one report for the lecturer about all the works together, without names.) Keeps the work of each student for each assignment. Gives a review of a work (once a day for each student and assignment; a new version replaces the old one). When enough works exist, it asks the AI service for one general overview of all the works (made again only after 5 new works) and compares the work of a student with that overview, once a day. | FR-22, FR-23 |

### External service

| Component | What it does |
|-----------|--------------|
| AI service (Google Gemini) | Counts the people in a photo, summarizes a class recording and reviews homework. It is used on the free tier. The server calls it with a key that is kept only in the server settings, and the browser never gets the key. |

### Storage

| Component | What it does |
|-----------|--------------|
| Storage | Keeps the roster, the sessions (with the classroom location), the check-ins, the comments, the poll answers, the summary and the homework works. In a real system this is a database, so the lecturer uploads the roster once for the course. In the demo it is kept in memory. |

## 3. How the components work together

- **Starting a session:** the lecturer page sends the phone location to the attendance manager, which saves it as the classroom location and starts the session. The classroom screen page asks the code generator for the current code and shows it.
- **A student check-in:** the student page sends the email, the code and the phone location to the attendance manager. The attendance manager asks the code generator if the code is valid, asks the location checker for the distance, looks up the roster in the storage, and saves the result.
- **Getting the spreadsheet:** the lecturer page asks the CSV exporter, which reads the results from the storage and returns a CSV file.
- **A poll:** the lecturer page sends the question to the poll manager. Students answer through the student page, and the answers are saved in the storage.
- **Photo count:** the lecturer page sends the photo to the headcounter, which gets the number from the AI service and compares it with the number of check-ins.
- **Class summary:** the lecturer page takes the sound out of the recording and sends it to the summarizer, which gets the summary from the AI service in the background. The page asks every few seconds until it is ready. Only the lecturer page can read it.
- **Homework:** the homework page sends the PDF to the homework reviewer, which gets the text from the AI service and saves the work. A second button asks the reviewer for one review of the saved work from the AI service (once a day). When enough works exist, the comparison button asks the reviewer for the class overview (made again after 5 new works or a day) and for the comparison of one work with it. The page asks every few seconds until the answer is ready. The lecturer first publishes the assignment: the reviewer sends the PDF to the AI, which returns the text and the due date written in the document, and the page warns if it is not the chosen date. The students choose from the list of published assignments. On the due date the lecturer page asks the reviewer for one report about all the works of the assignment (together, no names) and shows it only to the lecturer.

## 4. Notes

- **AI:** the AI answers are a help and can be wrong. The photo count is a warning, and the homework review is advice.
- **Demo:** for the demo the server can be small, and the exact technology is chosen in the implementation step.
- **Known limit:** the codes are created and checked on the server, so the browser never gets the secret. A code can still be photographed and sent to a friend during its short validity.
