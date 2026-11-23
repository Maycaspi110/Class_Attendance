# Conclusion

**Project:** Class Attendance & Teaching Tool
**Author:** May Caspi
**Related documents:** README, SoW, SRS, Testing Strategy

The demo runs at https://class-attendance-ogqg.onrender.com (a free server: the first visit after a pause takes about a minute).

## What I built

A web app that students open on their own phones, with nothing to install. It runs on a free Render server, and the AI features use the free Google Gemini service.

| # | Feature in the assignment | What I built | Status |
|---|---------------------------|---------------|--------|
| 1 | Attendance, photo count and a spreadsheet (the main feature) | A roster, a code and QR code that change, a location check, two check-ins (start and end of class) and a CSV file. A photo of the classroom is counted by AI and compared with the check-ins | Works. The photo count was tried with a real photo |
| 2 | Student comments | A comment box in the end-of-class check-in. The comments appear for the lecturer and in the CSV | Works |
| 3 | Lecturer polls | A question with 2-6 options, answered from the phones, with a ready "Did you understand the lesson?" question | Works |
| 4 | AI summary of the class | The lecturer uploads a recording (or a public YouTube link). The browser takes out the sound, and the AI writes a summary that only the lecturer sees | Works. Tried with a real 2 minute screen recording |
| 5 | Homework review and comparison | A student sends a work and gets an AI review, once a day, and a new version replaces the old one. From 8 works the student can compare their work with a general overview of the class, once a day. No one sees another work. The lecturer publishes the assignment (PDF and due date) and on the due date gets one report about the whole class | Works |

## How I checked it

- 384 automated tests (pytest) for the classes, the pages and the errors. The AI is replaced by a fake one in the tests.
- Manual tests: the changing code and the QR code on an iPhone and an Android device, GPS in the classroom and the library, the CSV in Excel, the website on phones through Render, and the AI photo count.

## What I learned

- **A design that can be built.** Each feature was kept small (KISS), and every idea that was too big for the time was dropped: students uploading their own summaries, and polls sent by email.
- **Real life is different from the plan.** The university Wi-Fi blocked traffic between phones and a laptop, so I moved to a Render server. The AI model I first chose was replaced by Google, so the model name is now a setting. A screen recording was 141 MB, so the browser takes out only the sound (3.7 MB), and a slow AI answer runs in the background. The indoor GPS accuracy is often rough, so a rough location for the lecturer is accepted, and far students are flagged, not rejected.
- **AI is a help, not a judge.** The photo count and the homework comparison are only warnings and advice. Nobody is marked because of them.

## Known limits

- Nothing is 100% cheat-proof. A code can be shared with a friend during its short validity.
- Email is the only identity (also on the homework page), so someone who knows a classmate's email can use it. A real system needs a login.
- The demo keeps its data in memory, and it is lost when the free server sleeps (about 15 minutes without use).
- Photos, the sound of recordings and works are sent to Google. The demo uses sample data, and the terms of the free tier should be checked before real use.
- The free AI has request limits, and a request can fail or be slow.

## Next steps (if the project continues)

- A real database and a proper login for students.
- A paid hosting plan that does not sleep.
- Comments during the class (today a comment is written in the end check-in only).
- Polls sent by email (left out on purpose, to keep the demo small).
- Checking the privacy terms and moving to a paid AI plan.
