# Statement of Work (SoW)

**Project:** Class Attendance & Teaching Tool
**Course:** Introduction to Software Engineering, Ariel University
**Author:** May Caspi

## 1. Purpose

Build a simple web app for teaching in class that works on students' own smartphones, with nothing to install. The main goal is **automatic attendance**: the lecturer starts a session, students check in with a changing code, and the lecturer gets a spreadsheet.

## 2. Deliverables (the 12 steps of the assignment)

| Step | Deliverable | Status |
|------|-------------|--------|
| 1 | Repository and README: problem, goal, scope | Done |
| 2 | Submission through the form | By 25/11/2026 |
| 3 | Tools report: tools tested in real life | Done |
| 4 | This SoW | Done |
| 5 | SRS: functional and non-functional requirements | Done |
| 6 | Use cases | Done |
| 7 | Software components | Done |
| 8 | Class and sequence diagrams | Done |
| 9 | Testing strategy | Done |
| 10 | Working demo: attendance, comments, photo count, polls, class summary and homework review (a smartphone web app) | Done |
| 11 | 10-minute demo in class | In class |
| 12 | Conclusion | Written, to be completed after the demo |

## 3. Scope

**Included (implemented in the demo):**

Attendance:
- Course roster, so only registered students can check in
- Changing code (every 10-30 seconds), also shown as a QR code
- Location check: within about 150 m of the classroom; students who are far are flagged, not rejected
- Two check-ins (start and end of class): Present, Late, Left early, Flagged, Absent
- CSV spreadsheet for the lecturer, with the comments
- Student comments about the lesson, at the end check-in
- Photo count: an AI counts the people in a photo of the classroom, compared with the check-ins (a warning only)

Lecturer polls: a quick poll about the current material, answered from students' phones

Class summary: the lecturer uploads a short recording of the class (or pastes a public YouTube link), and an AI writes a summary that only the lecturer sees. The sound is taken out of the recording in the browser, so only the sound is sent

Homework review: a student (identified by email) sends a work and gets an AI review (once a day for each assignment). When at least 8 students sent their work, each can compare their work with a general overview of all the works, once a day (anonymous: no one sees another work). On the due date the lecturer gets one AI report about all the works together

AI service: Google Gemini on the free tier, called from the server. The students' phones never get the key.

**Not included:**
- Comments during the class: a student writes a comment (up to 300 characters) in the end check-in only
- Students uploading their own class summaries (dropped)
- Polls sent by email
- Integration with Moodle, Zoom or personal information systems
- A system that is 100% cheat-proof (known limitations are documented)

## 4. Decisions so far

These come from the tools report:
- A typed code that changes, plus a QR code (tested on iPhone and Android)
- Render (a free web service) for the demo: it gives an HTTPS address that phones can reach. GitHub Pages was only used for the early test pages
- Google Gemini (free tier) for the AI features, called from the server
- CSV file for the lecturer's spreadsheet
- GPS (browser geolocation) for the distance check. The allowed distance is the radius (about 150 m) plus the accuracy of the two locations, so a laptop is not flagged because of a rough Wi-Fi location
- Bluetooth rejected (not supported on iPhone)

## 5. Work plan

1. Finish the tools report (done)
2. Write the SRS, then the use cases (done)
3. Design the components, class diagrams and sequence diagrams (done)
4. Write the testing strategy (done)
5. Build the demo (done): attendance, comments, photo count, polls, class summary and homework review
6. Run the demo in class and write the conclusion (the conclusion is written, the demo is in class)

## 6. Who does what

May Caspi prepares all the deliverables: the documents, the design, the code and the demo.

## 7. Assumptions and risks

- **GPS accuracy indoors varies.** Mitigation: a wide radius (about 150 m) and a flag for the lecturer.
- **A code can be photographed and shared.** Mitigation: the code changes quickly, the location check, and the flag for the lecturer.
- **Classroom internet may be weak.** Mitigation: test the demo in the classroom before the presentation.
- **The free AI has limits and can be slow.** Mitigation: short waits between requests, clear error messages, and a short recording (2-5 minutes) for the demo.
- **Privacy:** photos, the sound of recordings and works are sent to Google. Mitigation: nothing is saved except the short results in memory, and the demo uses sample data.
- **Email is the only identity** for the homework page, so a student could send a work in another student's name. Known limitation of the demo.
- **The free server sleeps**, and the data in memory is lost. Mitigation: open the site a few minutes before the demo and upload the roster again.
- **Time is limited.** Mitigation: keep each feature simple (KISS).
