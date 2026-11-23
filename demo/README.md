# Attendance demo

A small web app for teaching in class. Students use their own phone and a code that changes every few seconds. The lecturer gets a spreadsheet, can count the people in a photo, run a poll and get an AI summary of the class. Students get an AI review of their homework.

The design is in the main folder: `SRS.md`, `use-cases.md`, `components.md`, `diagrams.md`, `testing-strategy.md`. The numbers (radius, limits) are in the SRS.

**Live demo:** https://class-attendance-ogqg.onrender.com (the free server sleeps, the first visit takes about a minute)

## Pages

| Page | Address | Who |
|------|---------|-----|
| First page | `/` | everyone: student or lecturer |
| Student menu | `/student` | students: mark attendance, homework review |
| Check-in | `/checkin` | students: code (typed or from the QR code), email, location, a comment at the end, the poll |
| Homework review | `/homework` | students |
| Lecturer menu | `/lecturer/menu` | lecturer (password): six tiles, each opens only its own part of `/lecturer` |
| Classroom screen | `/screen` | lecturer (password): the code and the QR code |

A lesson has two check-ins (start and end of the class): both is Present, only the end is Late, only the start is Left early. A check-in is accepted when the email is on the roster and the code is the current or the previous one. A far, missing or inaccurate location makes the student **Flagged**: not rejected, the lecturer decides.

## How the location check works

- **Start** takes the lecturer's device location (and its accuracy) as the classroom location. It is not fixed in the code. An accuracy worse than 500 m is refused.
- The distance between the phone and the classroom is calculated (great-circle distance).
- A laptop guesses its location from the Wi-Fi and can be wrong by hundreds of meters, so the allowed distance is the radius (150 m) **plus** the two accuracies, each counted up to 300 m. With a good GPS the radius stays tight, and a place 1 km away is still Flagged.
- A student accuracy worse than 1000 m, or no location, is Flagged.

## AI features

The AI features use the Google Gemini API (free tier) from the server. The key is only in the server settings (`GEMINI_API_KEY`). Without it the pages say the feature is not set up.

- **Photo count:** the browser shrinks the photo, the server checks it is a real image, Gemini returns a number, and it is compared with the check-ins (a gap above max(2, 15 percent) is a warning). The photo is not saved.
- **Class summary:** a recording (MP4, WebM, MP3, M4A, WAV) or a public YouTube link. For a recording the browser takes out the sound (about 2 MB per minute), so a 140 MB screen recording is about 4 MB. The AI works in the background, and only the lecturer sees the summary.
  (The server also accepts a transcript text file for the summary, `.txt`, `.vtt` or `.srt`, but the page does not offer it.)
- **Homework review:** the student sends a PDF of the work, then asks for the review with a second button: one review per student and assignment each day (a new version replaces the old one). From `HOMEWORK_MIN_WORKS` works (default 8) a student can compare their work with the class, once a day: Gemini writes one general overview of all the works (only what several works share, made again after 5 new works) and compares the work with it. The student never sees another work. The comparison runs in the background.
- **Publish an assignment (lecturer):** course, name, due date and the PDF. Gemini reads the PDF and warns if the due date inside is not the chosen date. Students choose the assignment from a list.
- **Homework report (lecturer):** on the due date the lecturer chooses the assignment and presses one button. Gemini reads all the works together and writes one report: do they match the assignment, repeated mistakes, what was not clear, what was interesting. No names. It runs in the background and can take a few minutes.

## Run it on your computer

You need Python 3.10 or newer. In PowerShell, in the `demo` folder:

```
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:LECTURER_PASSWORD = "choose-a-password"
$env:CODE_SECRET = "choose-a-long-random-text"
.\.venv\Scripts\python.exe app.py
```

Open <http://localhost:5000>, press **I am a lecturer**, log in, upload `sample-roster.csv` (made-up students) in **Course roster**, and start attendance. In another tab open `/checkin` and use `dana.levi@example.com` with the code from the classroom screen.

To try it with a phone on the same Wi-Fi, set `$env:HOST = "0.0.0.0"` before you start. Allow the firewall question (also **Public networks**). Some networks (for example a university) do not let devices talk to each other: use a phone hotspot. Over plain `http` the phone gives no location, so students are Flagged.

## Settings (environment variables)

| Name | What it is | Default |
|------|------------|---------|
| `LECTURER_PASSWORD` | The password of the lecturer pages | a random one is printed at start |
| `CODE_SECRET` | The secret that creates the codes (long and random) | a development value |
| `CODE_PERIOD_SECONDS` | How often the code changes (10 to 30) | `20` |
| `ALLOWED_RADIUS_METERS` | The allowed distance from the classroom | `150` |
| `MAX_ACCURACY_METERS` | A student accuracy worse than this is "inaccurate" | `1000` |
| `GEMINI_API_KEY` | The key for the AI features (only here, never in a file) | not set |
| `HOMEWORK_MIN_WORKS` | How many works an assignment needs before the comparison opens | `8` |
| `HOMEWORK_COOLDOWN_SECONDS` | The time between two reviews (and two comparisons) of one student for one assignment. `0` means no limit | `86400` (a day) |
| `GEMINI_MODEL` | The Gemini model name (Google replaces models over time) | `gemini-3.5-flash-lite` |
| `TIMEZONE` | The time zone of the times in the CSV | `Asia/Jerusalem` |
| `SECRET_KEY`, `SECURE_COOKIES`, `TRUST_PROXY`, `REQUIRE_SECRETS` | Login cookie and hosting settings: `SECURE_COOKIES`, `TRUST_PROXY` and `REQUIRE_SECRETS` are `1` on Render | random / not set |
| `HOST`, `PORT`, `PUBLIC_URL` | Where the server listens, and the public address in the QR link | `127.0.0.1`, `5000`, the request address |

## Deploy on Render

The demo must be on the internet (HTTPS) for the phones. It runs as **one** process, because the data is in memory.

1. Create a free account at <https://render.com> (**Sign up with GitHub**).
2. **New** > **Web Service**, connect the repository `Class_Attendance`.
3. Use: Language `Python 3`, Branch `main`, Root Directory `demo`, Build Command `pip install -r requirements.txt`, Start Command `gunicorn wsgi:app --workers 1 --threads 8 --timeout 90 --bind 0.0.0.0:$PORT`, Instance Type `Free`.
4. Under **Environment Variables** add `PYTHON_VERSION` (`3.12.8`), `LECTURER_PASSWORD`, `CODE_SECRET`, `SECRET_KEY` (random values, never shared), `CODE_PERIOD_SECONDS` (`30`), `TIMEZONE`, `SECURE_COOKIES`, `TRUST_PROXY`, `REQUIRE_SECRETS` (`1`) and `GEMINI_API_KEY` (from Google AI Studio). A random text: `-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })`.
5. **Create Web Service**, wait until it is live, and open the address on a phone.

Never write the password, the secrets or the key in a file of the repository. `render.yaml` is an alternative (**New** > **Blueprint**).

**Before the demo:** the free server sleeps after about 15 minutes and needs about a minute to wake up, so open it a few minutes before. Everything is in memory: after a sleep the roster is gone, so upload it again, and download the CSV before you stop. Use a made-up roster on a public server. A host firewall can stop an uploaded text that looks like an attack (for example `../../etc/passwd` or SQL words in a README): the page then shows only 403.

## Files

| Path | What it is |
|------|------------|
| `app.py` | The Flask app: pages and API |
| `attendance/` | The classes of the class diagram, and the AI helpers `headcount.py`, `summary.py`, `homework.py` |
| `templates/`, `static/` | The pages (`static/qrcode.js` is the open-source qrcode-generator, MIT) |
| `tests/` | The automatic tests: `.\.venv\Scripts\python.exe -m pytest` (they use made-up students and a fake AI) |
| `sample-roster.csv` | A roster with made-up students |

**CSV files.** The roster needs a name and an email per student (`Name` / `שם`, `Email` / `אימייל`; other columns such as an ID are ignored and never kept; a repeated email is refused). The results CSV has: Email, Name, Status, Start check-in, End check-in, Distance from classroom (m), Note, Comment (UTF-8 with BOM, so Excel shows Hebrew).

**Good to know.** No database: restarting loses the data. Run one process only. Location needs HTTPS (or `localhost`). Real student lists stay outside the repository (or named `real-*.csv`, which git ignores). A student can send the code to a friend, which is why the code changes fast and the location and the flag exist. A student who types 5 wrong codes waits a minute.
