# Attendance demo

A small web app for taking attendance in class. Students use their own phone and a code that changes every few seconds. The lecturer gets a spreadsheet. The lecturer can also ask a quick poll.

It follows the design documents in the main folder: `SRS.md`, `use-cases.md`, `components.md`, `diagrams.md` and `testing-strategy.md`.

## What it does

- **Lecturer page** (`/lecturer`, needs a password): upload the roster, start and end attendance, see Present / Flagged / Absent, download the CSV, run a poll.
- **Classroom screen** (`/screen`, needs the same password): shows the 4-digit code and a QR code. They change every 10-30 seconds (default 20).
- **Student page** (`/checkin`): the code (typed, or filled in by the QR code) + email + the phone location. Students can also answer the poll here.

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

### Try it with a phone on the same Wi-Fi

Add `HOST` before you start the server:

```n$env:HOST = "0.0.0.0"
```n
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
| `MAX_ACCURACY_METERS` | A phone that reports a worse accuracy is treated as "inaccurate" (Flagged). The final value is decided after the tests in class. | `200` |
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
| Start Command | `gunicorn wsgi:app --workers 1 --threads 8 --bind 0.0.0.0:$PORT` |
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
