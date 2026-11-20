# Attendance demo

A small web app for teaching in class. Students use their own phone and a code that changes every few seconds. The lecturer gets a spreadsheet. The lecturer can also count the people in a photo, ask a quick poll and get an AI summary of the class, and students can get an AI review of their homework.

It follows the design documents in the main folder: `SRS.md`, `use-cases.md`, `components.md`, `diagrams.md` and `testing-strategy.md`.

## What it does

| Page | Address | Who | What |
|------|---------|-----|------|
| First page | `/` | everyone | Two tiles: student or lecturer |
| Student menu | `/student` | students | Two tiles: mark attendance, homework review |
| Check-in | `/checkin` | students | The code (typed, or filled in by the QR code) + email + the phone location. In the end check-in a short comment. Students also answer the poll here |
| Homework review | `/homework` | students | Send a work (text or code) and get an AI review |
| Lecturer menu | `/lecturer/menu` | lecturer (password) | Six tiles: roster, attendance and results, classroom screen, photo count, class summary, poll |
| Lecturer page | `/lecturer` | lecturer (password) | Each tile opens only its own part: roster upload, start and end check-ins, results and CSV, photo count, class summary, poll |
| Classroom screen | `/screen` | lecturer (password) | The 4-digit code and a QR code. They change every 10-30 seconds (default 20) |

Checks for every check-in: the email is on the roster, the code is the current or the previous one, and the phone is within the allowed distance (default 150 m, see "How the location check works"). If the code is right but the location is far, missing or too inaccurate, the student is **Flagged** for the lecturer. It is not rejected.

A lesson has two check-ins, at the start and at the end of the class. A student with both is Present, only the end is Late, only the start is Left early.

## How the location check works

- When the lecturer presses **Start**, the location of the lecturer's device becomes the classroom location, together with its accuracy. It is not fixed in the code, so the app works in any classroom. A lecturer location that is worse than 500 m is refused.
- A student's phone gives its location and an accuracy (a radius of doubt, in meters). The app calculates the distance between the two points (great-circle distance).
- A laptop has no GPS and guesses from the Wi-Fi, so it can be wrong by hundreds of meters. So the allowed distance is the radius (150 m) **plus** the two accuracies, each counted up to 300 m at most. With a phone with a good GPS the radius stays tight. A student about 1 km away is still Flagged.
- A student whose phone reports an accuracy worse than 1000 m, or gives no location, is Flagged as "location missing or too inaccurate".
- The location is only used for this check. A Flagged student is not rejected: the lecturer decides.

## AI features

All three use the Google Gemini API (free tier), called from the server. The key is only in the server settings (`GEMINI_API_KEY`), never in the code or the browser. Without the key the pages say the feature is not set up.

- **Photo count:** the browser shrinks the photo, the server checks that it is a real JPEG, PNG or WebP, and Gemini returns a number. The number is compared with the check-ins (a gap bigger than 15 percent, at least 2, is a warning). The photo is not saved. It is a rough count and only a warning.
- **Class summary:** the lecturer uploads a recording (MP4, WebM, MP3, M4A or WAV) or pastes a public YouTube link. For a recording the browser takes out the sound (16 kHz mono, about 2 MB per minute), so a 140 MB screen recording becomes about 4 MB. Gemini runs in the background and the page asks every 3 seconds until it is ready. Only the lecturer sees the summary.
- **Homework review:** the work, the student's previous version and up to 5 works of other students (cut to 4000 characters, anonymous) are sent to Gemini. The student only gets the review, never another student's work. At least 20 seconds between two reviews of the same student.

## Run it on your computer

You need Python 3.10 or newer. Open PowerShell in the `demo` folder:

```
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

$env:LECTURER_PASSWORD = "choose-a-password"
$env:CODE_SECRET = "choose-a-long-random-text"
.\.venv\Scripts\python.exe app.py
```

Then open <http://localhost:5000> and press **I am a lecturer**. Log in.

Try it: on the lecturer page choose `sample-roster.csv` (made-up students), press **Check the file**, then **Confirm**. Press **Start attendance**, then **Open the classroom screen**. On a second browser tab open <http://localhost:5000/checkin>, type `dana.levi@example.com` and the code from the screen.

### Try it with a phone on the same Wi-Fi

Add `HOST` before you start the server:

```
$env:HOST = "0.0.0.0"
```

The server prints the address for phones, for example `http://192.168.1.20:5000/checkin`. Open the lecturer page on the computer, open the classroom screen, and scan the QR code with the phone camera. The check-in page opens with the code already filled in, and the student only types an email. A student can also open the address shown on the classroom screen and type the code.

- Windows may ask about the firewall. Allow access, and also tick **Public networks** if your Wi-Fi is set to Public.
- Some Wi-Fi networks (for example in a university) do not let devices talk to each other. Then use the hotspot of a phone.
- Over plain `http` the phone does not share its location, so the student is Flagged. Real location checks need HTTPS.

Hint: if the virtual environment is inside OneDrive, OneDrive will upload it. It is better to keep the project outside OneDrive when you work on it.

## Environment variables

| Name | What it is | Default |
|------|------------|---------|
| `LECTURER_PASSWORD` | The password for `/lecturer` and `/screen`. | If missing, a random password is printed when the server starts. |
| `CODE_SECRET` | The secret used to create the codes. Use a long random text. | A development value (do not use it on a public server). |
| `CODE_PERIOD_SECONDS` | How often the code changes (10 to 30). | `20` |
| `ALLOWED_RADIUS_METERS` | How far from the classroom a student may be. | `150` |
| `MAX_ACCURACY_METERS` | A phone that reports a worse accuracy is treated as "inaccurate" (Flagged). | `1000` |
| `GEMINI_API_KEY` | The key of the Google Gemini API, for the photo count, the class summary and the homework review. Only in the server settings, never in a file. | not set (the AI features are off) |
| `GEMINI_MODEL` | The Gemini model name. Google replaces models over time, so it is a setting. | `gemini-3.5-flash-lite` |
| `TIMEZONE` | The time zone of the check-in times in the CSV. | `Asia/Jerusalem` |
| `PORT` | The port of the server. | `5000` |
| `HOST` | The address to listen on. Use `0.0.0.0` so that phones on the same Wi-Fi can reach the site. | `127.0.0.1` |
| `PUBLIC_URL` | The public address of the site, used inside the QR code link (for example `https://example.com`). If missing, the address of the request is used. When the lecturer opens the site as `localhost`, the address of the computer on the local network is used, so that a phone can open the link. | not set |
| `SECRET_KEY` | Signs the login cookie. If missing, a random one is made at every start. | random |
| `SECURE_COOKIES` | Set to `1` when the site runs over HTTPS. | not set |
| `TRUST_PROXY` | Set to `1` when the site is behind a hosting proxy that sets the `X-Forwarded-*` headers. | not set |
| `REQUIRE_SECRETS` | Set to `1` on a real server: the app then refuses to start if `LECTURER_PASSWORD` or `CODE_SECRET` is missing. (Render also turns this on by itself.) | not set |

## Deploy on Render

Render is a free hosting service. The demo must run on the internet, because the phones in class reach it over HTTPS. The demo runs as **one** process, because everything is kept in memory.

1. Create a free account at <https://render.com> (**Sign up with GitHub**).
2. Press **New** > **Web Service**, choose **Build and deploy from a Git repository**, and connect the repository `Class_Attendance`.
3. Fill in the form with exactly these values:

| Field | Value |
|-------|-------|
| Name | `class-attendance` (any name; it becomes part of the address) |
| Language | `Python 3` |
| Branch | `main` |
| Root Directory | `demo` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn wsgi:app --workers 1 --threads 8 --timeout 90 --bind 0.0.0.0:$PORT` |
| Instance Type | `Free` |

4. Under **Environment Variables**, add these (the values here are examples only, never use them as they are):

| Key | Example value | What it is |
|-----|---------------|------------|
| `PYTHON_VERSION` | `3.12.8` | The Python version |
| `LECTURER_PASSWORD` | `your-own-long-password` | The password of the lecturer page. Make it long and private. |
| `CODE_SECRET` | `a-random-text-of-30-letters-and-digits` | The secret that creates the codes. Random, and never shared. |
| `SECRET_KEY` | `another-random-text` | Signs the login cookie. Random. |
| `ALLOWED_RADIUS_METERS` | `100` | How far from the classroom a student may be |
| `CODE_PERIOD_SECONDS` | `30` | How often the code changes (10 to 30) |
| `TIMEZONE` | `Asia/Jerusalem` | The time zone of the times in the CSV |
| `SECURE_COOKIES` | `1` | The site uses HTTPS |
| `TRUST_PROXY` | `1` | Render puts a proxy in front of the app |
| `REQUIRE_SECRETS` | `1` | The app refuses to start if the password or the secret is missing |
| `GEMINI_API_KEY` | (your key from Google AI Studio) | Turns on the AI features. Paste it only here, never in a file or in a chat |

   You do not need `PUBLIC_URL`: Render gives the address to the app by itself.
5. Press **Create Web Service**. After a few minutes the log says the service is live, and the address is shown at the top: `https://class-attendance-xxxx.onrender.com`.
6. Open `https://.../lecturer` and log in. Then open `https://.../checkin` on a phone.

**Random values:** in PowerShell, this makes a random text of 32 letters and digits (run it once for each secret):

```
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
```

Do not write the password or the secrets in any file of the repository. The repository has a `render.yaml` file too (a "Blueprint"). It is an alternative to the form above: **New** > **Blueprint**. It asks for the password and the radius, and creates the other values by itself.

**Before the demo in class**
- **The free server falls asleep** after about 15 minutes without visits. The first visit after that takes **about one minute** while it wakes up. Open the site a few minutes before the demo, and open the classroom screen to keep it awake.
- **Everything is in memory.** When the server sleeps or restarts, the roster, the session and the results are gone. Upload the roster after the server is awake, and download the CSV before you stop.
- **Use a made-up roster** (`sample-roster.csv`). Do not put real student emails on a free public server.
- Location works here, because the site uses HTTPS.
- Known limit: while a session is open, the check-in page tells whether an email is on the roster. This is one more reason to use a made-up roster.
## The CSV files

**Roster you upload** needs a name and an email for every student, for example:

```
Name,Email
Dana Levi,dana.levi@example.com
```

Other columns (for example an ID number) are ignored: they are never read or kept. These column names are understood: `Name` / `שם` / `שם מלא`, or `First name` + `Last name` / `שם פרטי` + `שם משפחה`; and `Email` / `מייל` / `אימייל`. Capital letters and spaces in an email do not matter. A file with a repeated email is refused until you fix it. Files saved from Excel in Hebrew are read correctly.

**Results you download** have the columns: Email, Name, Status, Start check-in, End check-in, Distance from classroom (m), Note, Comment. The file is saved as UTF-8 with a BOM, so Excel shows Hebrew names correctly.

## Run the tests

```
.\.venv\Scripts\python.exe -m pytest
```

The tests follow `testing-strategy.md`: unit tests for each class, and integration tests for the full attendance flow, the two check-ins, the changing code, the poll and the pages. They use made-up students only, and a fake AI (no real AI is called). The acceptance tests with the real AI are done by hand. The acceptance tests in the classroom are done by hand.

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
| `attendance/` | The classes from the class diagram (Roster, CodeGenerator, LocationChecker, AttendanceManager, Poll, CsvExporter) and the AI helpers (`headcount.py`, `summary.py`, `homework.py`) |
| `templates/`, `static/` | The pages. `static/qrcode.js` is the open-source qrcode-generator library (MIT license) |
| `tests/` | The automatic tests (pytest) |
| `sample-roster.csv` | A roster with made-up students |
