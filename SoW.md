# Statement of Work (SoW)

**Project:** Class Attendance & Teaching Tool
**Course:** Introduction to Software Engineering, Ariel University
**Team:** May Caspi and Haim Barabi

## 1. Purpose

Build a simple web app for teaching in class that works on students' own smartphones, with nothing to install. The main goal is **automatic attendance**: the lecturer starts a session, students check in with a changing code, and the lecturer gets a spreadsheet.

## 2. What we will deliver

| # | Deliverable | Form |
|---|-------------|------|
| 1 | README: problem, goal, scope | Document (done) |
| 2 | Tools report: tools tested in real life | Document (in progress) |
| 3 | This SoW | Document |
| 4 | SRS: functional and non-functional requirements | Document |
| 5 | Use cases | Document |
| 6 | Software components | Diagram + text |
| 7 | Class and sequence diagrams | Diagrams |
| 8 | Testing strategy | Document |
| 9 | Working demo: attendance and polls | Smartphone web app |
| 10 | 10-minute demo in class | Live demo |
| 11 | Conclusion | Document |

## 3. Scope

**Included (implemented in the demo):**

Attendance:
- Course roster, so only registered students can check in
- Changing code (every 10-30 seconds), also shown as a QR code
- Location check: within about 150 m of the classroom; students who are far are flagged, not rejected
- CSV spreadsheet for the lecturer (Present, Flagged, Absent)

Lecturer polls: a quick poll about the current material, answered from students' phones

**Design only (not implemented):**
- Student comments, suggestions and questions
- Class summary: students upload their own summaries, and an AI agent combines them into one PDF summary

**Not included:**
- LLM homework review
- Integration with Moodle, Zoom or personal information systems
- A system that is 100% cheat-proof (known limitations are documented)

## 4. Decisions so far

These come from the tools report:
- A typed code that changes, plus a QR code (tested on iPhone and Android)
- GitHub Pages for HTTPS hosting
- CSV file for the lecturer's spreadsheet
- GPS (browser geolocation) for the distance check: to be confirmed after the tests in class
- Bluetooth rejected (not supported on iPhone)

## 5. Work plan

1. Finish the tools report (GPS and IP tests in class)
2. Write the SRS, then the use cases
3. Design the components, class diagrams and sequence diagrams
4. Write the testing strategy
5. Build the demo: attendance and polls (reusing existing code from the test pages)
6. Run the demo in class and write the conclusion

## 6. Who does what

Each team member prepares their own version of each deliverable. Then we compare the two versions and combine them into the final one.

## 7. Assumptions and risks

- **GPS accuracy indoors varies.** Mitigation: a wide radius (about 150 m) and a flag for the lecturer.
- **A code can be photographed and shared.** Mitigation: the code changes quickly, the location check, and the flag for the lecturer.
- **Classroom internet may be weak.** Mitigation: test the demo in the classroom before the presentation.
- **Time is limited.** Mitigation: implement only attendance and polls; everything else stays as design.
