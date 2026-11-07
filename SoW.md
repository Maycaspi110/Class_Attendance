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
| 9 | Working attendance demo | Smartphone web app |
| 10 | 10-minute demo in class | Live demo |
| 11 | Conclusion | Document |

## 3. Scope

**Included (implemented in the demo):**
- Course roster, so only registered students can check in
- Changing code (every 30-60 seconds), also shown as a QR code
- Location check: within about 150 m of the classroom; far students are flagged, not rejected
- CSV spreadsheet for the lecturer (Present, Flagged, Absent)

**Design only (not implemented):**
- Real-time student comments
- Lecturer polls
- ML summary of the class video
- LLM homework review

**Not included:**
- Integration with Moodle, Zoom or personal information systems
- A system that is 100% cheat-proof (known limitations are documented)

## 4. Decisions so far

These come from the tools report:
- Typed code that changes, plus QR code (tested on iPhone and Android)
- GPS (browser geolocation) for the distance check
- GitHub Pages for HTTPS hosting
- CSV file for the lecturer's spreadsheet
- Bluetooth rejected (not supported on iPhone)

## 5. Work plan

1. Finish the tools report (GPS and IP tests in class)
2. Write the SRS, then use cases
3. Design the components, class and sequence diagrams
4. Write the testing strategy
5. Build the attendance demo (reusing existing code from the test pages)
6. Run the demo in class and write the conclusion

## 6. Assumptions and risks

- **GPS accuracy indoors varies.** Mitigation: a wide radius (about 150 m) and a flag for the lecturer.
- **A code can be photographed and shared.** Mitigation: the code changes quickly, the location check, and the lecturer flag.
- **Classroom internet may be weak.** Mitigation: test the demo in the classroom before the presentation.
- **Time is limited.** Mitigation: implement only attendance; keep everything else as design.
