# Demo Script (10 minutes)

**Project:** Class Attendance & Teaching Tool
**Team:** May Caspi and Haim Barabi
**Related documents:** README, Use Cases, Testing Strategy

The demo runs on the Render address, from a phone for the students and a laptop for the lecturer and the classroom screen.

## Before the demo (15 minutes before)

| # | Do | Why |
|---|----|-----|
| 1 | Open the site and wait until it loads | The free server sleeps and needs about a minute to wake up |
| 2 | Log in as the lecturer and upload the roster (`tests/attendance-sample.csv` columns are Email and Name; use the real class list) | The roster is lost when the server sleeps |
| 3 | Open the classroom screen page on the projector | It needs to be ready |
| 4 | Check that the lecturer's phone has Location on | The classroom location is taken from it |
| 5 | Have the files ready: a classroom photo, `tests/sample-transcript.vtt`, `tests/sample-homework-a.py`, `tests/sample-homework-b.py` | Used in steps 5-7 |
| 6 | Have 2-3 students ready with their phones | For the live check-in |
| 7 | Keep screenshots of each result (the `evidence` folder) | If the network or the AI does not work |

## The demo

| Time | What | What the audience sees |
|------|------|------------------------|
| 0:00 | **Problem** (30 s): attendance is slow, and the online tools are complicated | |
| 0:30 | **Start of class:** the lecturer presses "Start attendance" on the phone, inside the classroom | The classroom screen shows a code and a QR code that change every 30 seconds |
| 1:30 | **Check-in:** students scan the QR code or type the code, type their email, and press "I am here" | A confirmation on the phone, and the names appear on the lecturer page |
| 3:00 | **Photo count:** the lecturer uploads a photo of the classroom (card 4) | "48 people in the photo and N check-ins" and the warning or "close" message |
| 4:00 | **End of class:** "Start end-of-class check-in"; students check in again and write a comment | Late and "Left early" students are shown, and the comments appear |
| 5:30 | **Poll:** "Did you understand the lesson?" and the students answer | The results update on the lecturer page |
| 6:30 | **Spreadsheet:** download the CSV and open it in Excel | One row per student with the start and end check-in and the comment |
| 7:30 | **Class summary:** upload the 5 minute transcript (card 5) | A short summary that only the lecturer sees |
| 8:30 | **Homework:** a student opens the homework page and sends `sample-homework-a.py`; another student sends `sample-homework-b.py` | A review with a comparison to the other work. The student never sees the other work |
| 9:30 | **Limits** (30 s): the free AI has limits, email is the only identity, the photo count is only a warning | |

## If something fails

- **The AI shows an error:** read the message to the class (it says if it is a limit or the key), and show the saved screenshot.
- **The site is slow:** it is waking up. Wait a minute.
- **The location is rough:** the lecturer page shows a warning, and the demo goes on. Students far from the saved point are shown as Flagged.
- **A student cannot check in:** check that the email is in the roster.
