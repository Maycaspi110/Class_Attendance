# Attendance demo

A small web app for taking attendance in class. Students use their own phone and a code that changes every few seconds. The lecturer gets a spreadsheet. The lecturer can also ask a quick poll.

It follows the design documents in the main folder: `SRS.md`, `use-cases.md`, `components.md`, `diagrams.md` and `testing-strategy.md`.

## What it does

- **Lecturer page** (`/lecturer`, needs a password): upload the roster, start and end attendance, see Present / Flagged / Absent, download the CSV, run a poll.
- **Classroom screen** (`/screen`, needs the same password): shows the 4-digit code and a QR code. They change every 10-30 seconds (default 20).
- **Student page** (`/checkin`): email + code (typed, or arriving from the QR code) + the phone location. Students can also answer the poll here.

Checks for every check-in: the email is on the roster, the code is the current or the previous one, and the phone is within the allowed distance (default 150 m). If the code is right but the location is far, missing or too inaccurate, the student is **Flagged** for the lecturer. It is not rejected.

## Run it on your computer

You need Python 3.10 or newer. Open PowerShell in the `demo` folder:

```
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

$env:LECTURER_PASSWORD = "choose-a-password"
$env:CODE_SECRET = "choose-a-long-random-text"
.\.venv\Scripts\python.exe app.py
```

Then open <http://localhost:5000/lecturer> and log in.

Try it: on the lecturer page choose `sample-roster.csv` (made-up students), press **Check the file**, then **Confirm**. Press **Start attendance**, then **Open the classroom screen**. On a second browser tab open <http://localhost:5000/checkin>, type `dana.levi@example.com` and the code from the screen.

Hint: if the virtual environment is inside OneDrive, OneDrive will upload it. It is better to keep the project outside OneDrive when you work on it.

## Environment variables

| Name | What it is | Default |
|------|------------|---------|
| `LECTURER_PASSWORD` | The password for `/lecturer` and `/screen`. | If missing, a random password is printed when the server starts. |
| `CODE_SECRET` | The secret used to create the codes. Use a long random text. | A development value (do not use it on a public server). |
| `CODE_PERIOD_SECONDS` | How often the code changes (10 to 30). | `20` |
| `ALLOWED_RADIUS_METERS` | How far from the classroom a student may be. | `150` |
| `MAX_ACCURACY_METERS` | A phone that reports a worse accuracy is treated as "inaccurate" (Flagged). The final value is decided after the tests in class. | `200` |
| `TIMEZONE` | The time zone of the check-in times in the CSV. | `Asia/Jerusalem` |
| `PORT` | The port of the server. | `5000` |
| `HOST` | The address to listen on. Use `0.0.0.0` to reach it from other devices. | `127.0.0.1` |
| `PUBLIC_URL` | The public address of the site, used inside the QR code link (for example `https://example.com`). If missing, the address of the request is used. | not set |
| `SECRET_KEY` | Signs the login cookie. If missing, a random one is made at every start. | random |
| `SECURE_COOKIES` | Set to `1` when the site runs over HTTPS. | not set |
| `TRUST_PROXY` | Set to `1` when the site is behind a hosting proxy that sets the `X-Forwarded-*` headers. | not set |

## The CSV files

**Roster you upload** needs a name and an email for every student, for example:

```
Name,Email
Dana Levi,dana.levi@example.com
```

Other columns (for example an ID number) are ignored: they are never read or kept. These column names are understood: `Name` / `שם` / `שם מלא`, or `First name` + `Last name` / `שם פרטי` + `שם משפחה`; and `Email` / `מייל` / `אימייל`. Capital letters and spaces in an email do not matter. A file with a repeated email is refused until you fix it. Files saved from Excel in Hebrew are read correctly.

**Results you download** have the columns: Email, Name, Status, Check-in time, Distance from classroom (m), Note. The file is saved as UTF-8 with a BOM, so Excel shows Hebrew names correctly.

## Run the tests

```
.\.venv\Scripts\python.exe -m pytest
```

The tests follow `testing-strategy.md`: unit tests for each class, and integration tests for the full attendance flow, the changing code and the poll. They use made-up students only. The acceptance tests in the classroom are done by hand.

## Good to know

- **Everything is kept in memory.** There is no database. When the server restarts, the roster, the sessions and the polls are lost. Download the CSV before you stop the server.
- **Run one server process only.** The data lives inside the process, so do not start several workers.
- **Location needs HTTPS.** Phones give the location only to `https://` pages (and to `localhost`). Over plain `http://` on the local network, students will be Flagged because the phone gives no location.
- **No real student data in the repository, and no ID numbers anywhere.** Use made-up data in files that are committed. Keep real lists outside the repository, or name them `real-*.csv`, which git ignores here.
- **Known limit:** a student can send the code to a friend who is not in the class. This is why the code changes quickly and the location check and the lecturer flag exist.
- A student who types 5 wrong codes in a row must wait a minute. This stops guessing of the 4-digit code.

## Files

| Path | What it is |
|------|------------|
| `app.py` | The Flask app: pages and API |
| `attendance/` | The classes from the class diagram (Roster, CodeGenerator, LocationChecker, AttendanceManager, Poll, CsvExporter...) |
| `templates/`, `static/` | The pages. `static/qrcode.js` is the open-source qrcode-generator library (MIT license) |
| `tests/` | The automatic tests (pytest) |
| `sample-roster.csv` | A roster with made-up students |
