"""The web app: Flask pages and a small JSON API.

Pages:   /checkin (students), /lecturer and /screen (need the lecturer password)
All data is kept in memory (no database), so it is lost when the server restarts.
"""
import hmac
import math
import os
import secrets
import socket
import threading
import time
from datetime import datetime
from functools import wraps
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session as login_session,
    url_for,
)

from attendance.attendance_manager import AttendanceManager, CheckInError, SessionError
from attendance.attendance_record import ABSENT, FLAGGED, LATE, LEFT_EARLY, PRESENT
from attendance.code_generator import CodeGenerator
from attendance.headcount import GeminiCounter, HeadcountError, compare, image_type
from attendance.homework import (
    GeminiReviewer,
    HomeworkError,
    HomeworkStore,
    ReviewServiceError,
    clean_name,
    clean_work,
)
from attendance.summary import (
    MAX_MEDIA_BYTES,
    GeminiSummarizer,
    SummaryError,
    clean_transcript,
    media_type,
    youtube_link,
)
from attendance.csv_exporter import CsvExporter
from attendance.location_checker import LocationChecker, valid_point
from attendance.poll import Poll, PollError
from attendance.roster import Roster, RosterError
from attendance.session import END_ROUND, START_ROUND

DEFAULT_DEV_CODE_SECRET = "dev-only-secret-change-me"
MAX_LOGIN_FAILURES = 10
LOGIN_WINDOW_SECONDS = 300
MAX_PHOTO_BYTES = 6 * 1024 * 1024
MAX_TRANSCRIPT_BYTES = 1024 * 1024
MAX_HOMEWORK_BYTES = 200 * 1024


class DemoState:
    """Everything the demo remembers while the server runs."""

    def __init__(self, manager):
        self.manager = manager
        self.exporter = CsvExporter()
        self.pending_roster = None
        self.poll = None
        self.poll_id = 0
        self.counter = None  # counts the people in a photo (None = not set up)
        self.headcounts = []  # the photo counts of this lesson (the photos are never kept)
        self.summarizer = None  # writes the lesson summary (None = not set up)
        self.summary = None  # the summary of this lesson, only for the lecturer
        self.summary_working = False  # the AI is writing a summary right now
        self.summary_error = None  # why the last summary failed
        self.reviewer = None  # writes the homework review (None = not set up)
        self.homework = HomeworkStore()
        self.login_failures = {}  # ip -> list of times


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        raise SystemExit("The environment variable %s must be a whole number." % name)


def _lan_ip():
    """The address of this computer on the local network (for phones on the same Wi-Fi)."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))  # nothing is sent: it only picks the network card
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


def _number(value):
    """A real finite number from JSON, or None (booleans are not numbers)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        LECTURER_PASSWORD=os.environ.get("LECTURER_PASSWORD"),
        CODE_SECRET=os.environ.get("CODE_SECRET"),
        CODE_PERIOD_SECONDS=_env_int("CODE_PERIOD_SECONDS", 20),
        ALLOWED_RADIUS_METERS=_env_int("ALLOWED_RADIUS_METERS", 150),
        MAX_ACCURACY_METERS=_env_int("MAX_ACCURACY_METERS", 1000),
        TIMEZONE=os.environ.get("TIMEZONE", "Asia/Jerusalem"),
        # RENDER_EXTERNAL_URL is set by the Render hosting service itself.
        PUBLIC_URL=os.environ.get("PUBLIC_URL") or os.environ.get("RENDER_EXTERNAL_URL"),
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SECURE_COOKIES") == "1",
        PERMANENT_SESSION_LIFETIME=8 * 3600,
        MAX_CONTENT_LENGTH=512 * 1024,
        CLOCK=time.time,
    )
    if test_config:
        app.config.update(test_config)

    # On a real server (Render sets RENDER; or set REQUIRE_SECRETS=1) the app refuses to
    # start without its own password and secret. The development fallbacks below are
    # only for running on your own computer.
    if os.environ.get("REQUIRE_SECRETS") == "1" or os.environ.get("RENDER"):
        missing = [n for n in ("LECTURER_PASSWORD", "CODE_SECRET") if not app.config[n]]
        if missing:
            raise RuntimeError("Set these environment variables before starting: " + ", ".join(missing))

    if not app.config["LECTURER_PASSWORD"]:
        # No password was set: make a random one so the lecturer pages are never open.
        app.config["LECTURER_PASSWORD"] = secrets.token_urlsafe(9)
        print("LECTURER_PASSWORD is not set. For this run the password is: %s" % app.config["LECTURER_PASSWORD"])
    if not app.config["CODE_SECRET"]:
        app.config["CODE_SECRET"] = DEFAULT_DEV_CODE_SECRET
        print("CODE_SECRET is not set. Using a development value: do not do this on a public server.")

    if os.environ.get("TRUST_PROXY") == "1":  # behind a hosting proxy that sets X-Forwarded-*
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    manager = AttendanceManager(
        Roster(),
        CodeGenerator(app.config["CODE_SECRET"], app.config["CODE_PERIOD_SECONDS"]),
        LocationChecker(app.config["ALLOWED_RADIUS_METERS"], app.config["MAX_ACCURACY_METERS"]),
        tz=ZoneInfo(app.config["TIMEZONE"]),
    )
    state = DemoState(manager)
    app.extensions["demo"] = state
    if app.config.get("HEADCOUNTER") is not None:  # tests give a fake counter
        state.counter = app.config["HEADCOUNTER"]
    elif os.environ.get("GEMINI_API_KEY"):
        state.counter = GeminiCounter(
            os.environ["GEMINI_API_KEY"], os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
        )
    if app.config.get("SUMMARIZER") is not None:  # tests give a fake summarizer
        state.summarizer = app.config["SUMMARIZER"]
    elif os.environ.get("GEMINI_API_KEY"):
        state.summarizer = GeminiSummarizer(
            os.environ["GEMINI_API_KEY"], os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
        )

    if app.config.get("REVIEWER") is not None:  # tests give a fake reviewer
        state.reviewer = app.config["REVIEWER"]
    elif os.environ.get("GEMINI_API_KEY"):
        state.reviewer = GeminiReviewer(
            os.environ["GEMINI_API_KEY"], os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
        )

    def now():
        return app.config["CLOCK"]()

    def fail(message, status=400, **extra):
        return jsonify(ok=False, error=message, message=message, **extra), status

    # ---- security headers -----------------------------------------------

    @app.after_request
    def add_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'"
        )
        if request.path.startswith("/api/") or request.path in ("/lecturer", "/screen", "/login"):
            response.headers["Cache-Control"] = "no-store"
        return response

    # ---- the lecturer password ------------------------------------------

    def lecturer_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if login_session.get("lecturer"):
                return view(*args, **kwargs)
            if request.path.startswith("/api/"):
                return fail("Please log in again.", 401)
            return redirect(url_for("login", next=request.path))

        return wrapped

    def safe_next(target):
        return target if target in ("/lecturer", "/screen") else "/lecturer"

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            ip = request.remote_addr or "?"
            recent = [t for t in state.login_failures.get(ip, []) if now() - t < LOGIN_WINDOW_SECONDS]
            state.login_failures[ip] = recent
            given = (request.form.get("password") or "").encode("utf-8")
            expected = app.config["LECTURER_PASSWORD"].encode("utf-8")
            if len(recent) >= MAX_LOGIN_FAILURES:
                error = "Too many attempts. Wait a few minutes."
            elif hmac.compare_digest(given, expected):
                login_session.clear()
                login_session["lecturer"] = True
                login_session.permanent = True
                return redirect(safe_next(request.args.get("next")))
            else:
                recent.append(now())
                error = "Wrong password."
        return render_template("login.html", error=error), (401 if error else 200)

    @app.route("/logout")
    def logout():
        login_session.clear()
        return redirect(url_for("login"))

    # ---- pages ------------------------------------------------------------

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/checkin")
    def checkin():
        return render_template("checkin.html")

    @app.route("/homework")
    def homework_page():
        return render_template("homework.html")

    @app.route("/lecturer")
    @lecturer_required
    def lecturer():
        return render_template("lecturer.html", version=(os.environ.get("RENDER_GIT_COMMIT") or "local")[:7])

    @app.route("/screen")
    @lecturer_required
    def screen():
        return render_template("screen.html")

    # ---- lecturer API: roster --------------------------------------------

    @app.route("/api/roster/preview", methods=["POST"])
    @lecturer_required
    def roster_preview():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return fail("Choose a CSV file first.")
        candidate = Roster()
        try:
            candidate.load(upload.read())
        except RosterError as error:
            return fail(str(error))
        state.pending_roster = candidate
        return jsonify(
            ok=True,
            count=len(candidate),
            warnings=candidate.warnings[:20],
            can_confirm=len(candidate) > 0 and not candidate.has_problems,
        )

    @app.route("/api/roster/confirm", methods=["POST"])
    @lecturer_required
    def roster_confirm():
        pending = state.pending_roster
        if pending is None:
            return fail("Choose a file first.")
        if pending.has_problems or len(pending) == 0:
            return fail("Fix the problems in the file and choose it again.")
        session = manager.session
        if session is not None and session.is_open():
            return fail("End the attendance session before changing the roster.", 409)
        manager.roster = pending
        state.pending_roster = None
        return jsonify(ok=True, count=len(pending))

    # ---- lecturer API: session and results -------------------------------

    def person(student):
        return {"name": student.name, "email": student.email}

    def clock(record):
        return None if record is None else record.check_in_time.strftime("%H:%M")

    def entry_json(entry):
        data = person(entry.student)
        data.update(
            time=clock(entry.start) or clock(entry.end),
            start_time=clock(entry.start),
            end_time=clock(entry.end),
            distance=entry.distance_meters,
            note=entry.note,
            comment=entry.comment,
        )
        return data

    @app.route("/api/state")
    @lecturer_required
    def lecturer_state():
        session = manager.session
        return jsonify(
            ok=True,
            roster_count=len(manager.roster),
            session_open=bool(session and session.is_open()),
            has_session=session is not None,
            round=session.round if session is not None else None,
            has_start=START_ROUND in manager.rounds,
            has_end=END_ROUND in manager.rounds,
            period=manager.code_generator.period_seconds,
            radius=manager.location_checker.allowed_radius_meters,
        )

    @app.route("/api/session/start", methods=["POST"])
    @lecturer_required
    def session_start():
        session = manager.session
        if session is not None and session.is_open():
            return fail("A session is already open. End it first.", 409)
        data = request.get_json(silent=True) or {}
        lat, lon, accuracy = _number(data.get("lat")), _number(data.get("lon")), _number(data.get("accuracy"))
        location = (lat, lon) if lat is not None and lon is not None and valid_point(lat, lon) else None
        round_name = END_ROUND if data.get("round") == END_ROUND else START_ROUND
        try:
            manager.start_session(location, accuracy, now=now(), round_name=round_name)
        except SessionError as error:
            return fail(str(error))
        if round_name == START_ROUND:
            state.headcounts = []  # a new lesson
            state.summary = None
        return jsonify(ok=True)

    @app.route("/api/session/end", methods=["POST"])
    @lecturer_required
    def session_end():
        try:
            manager.end_session(now=now())
        except SessionError as error:
            return fail(str(error), 409)
        return jsonify(ok=True)

    @app.route("/api/results")
    @lecturer_required
    def results():
        entries = manager.lesson_entries()
        session = manager.session

        def group(status):
            return [entry_json(e) for e in entries if e.status == status]

        return jsonify(
            ok=True,
            session_open=bool(session and session.is_open()),
            has_session=session is not None,
            has_end=END_ROUND in manager.rounds,
            present=group(PRESENT),
            late=group(LATE),
            left_early=group(LEFT_EARLY),
            flagged=group(FLAGGED),
            absent=[person(e.student) for e in entries if e.status == ABSENT],
            comments=[
                {"name": e.student.name, "comment": e.comment} for e in entries if e.comment
            ],
            headcounts=state.headcounts,
            headcount_ready=state.counter is not None,
        )

    @app.route("/api/headcount", methods=["POST"])
    @lecturer_required
    def headcount():
        """Count the people in a classroom photo and compare with the check-ins. The photo is not saved."""
        request.max_content_length = MAX_PHOTO_BYTES  # a photo is bigger than a roster file
        if state.counter is None:
            return fail("The AI counting is not set up. Add GEMINI_API_KEY in the server settings.", 503)
        session = manager.session
        if session is None:
            return fail("Start a check-in first, then take the photo.", 409)
        photo = request.files.get("photo")
        if photo is None:
            return fail("Choose a photo first.")
        data = photo.read(MAX_PHOTO_BYTES + 1)
        if len(data) > MAX_PHOTO_BYTES:
            return fail("The photo is too large.", 413)
        mime_type = image_type(data)
        if mime_type is None:
            return fail("The file must be a JPEG, PNG or WebP photo.")
        try:
            people = state.counter.count(data, mime_type)
        except HeadcountError as error:
            return fail(str(error), 502)
        entry = {
            "round": session.round,
            "people": people,
            "check_ins": len(session.records),
            "time": datetime.fromtimestamp(now(), manager.tz).strftime("%H:%M"),
        }
        entry.update(compare(people, entry["check_ins"]))
        state.headcounts.append(entry)
        return jsonify(ok=True, **entry)

    @app.route("/api/summary", methods=["GET"])
    @lecturer_required
    def summary_get():
        return jsonify(
            ok=True,
            summary=state.summary,
            ready=state.summarizer is not None,
            working=state.summary_working,
            error=state.summary_error,
        )

    @app.route("/api/summary", methods=["POST"])
    @lecturer_required
    def summary_create():
        """Summarize the transcript of the class. Only the lecturer can do this and see the result."""
        request.max_content_length = MAX_MEDIA_BYTES + 1024 * 1024  # room for a recording
        if state.summarizer is None:
            return fail("The AI summary is not set up. Add GEMINI_API_KEY in the server settings.", 503)
        link = str(request.form.get("video_url") or "").strip()[:300]
        transcript = request.files.get("transcript")
        media = request.files.get("media")
        has_transcript = transcript is not None and bool(transcript.filename)
        has_media = media is not None and bool(media.filename)
        if has_transcript:
            raw = transcript.read(MAX_TRANSCRIPT_BYTES + 1)
            if len(raw) > MAX_TRANSCRIPT_BYTES:
                return fail("The transcript file is too large.", 413)
            text = clean_transcript(raw.decode("utf-8-sig", errors="replace"))
            if len(text) < 20:
                return fail("The transcript is empty or too short to summarize.")
            work = lambda: state.summarizer.summarize(text)  # noqa: E731
        elif has_media:
            data = media.read(MAX_MEDIA_BYTES + 1)
            if len(data) > MAX_MEDIA_BYTES:
                return fail("The recording is too large. The limit is 14 MB: record fewer minutes.", 413)
            mime_type = media_type(data)
            if mime_type is None:
                return fail("The file must be an MP4, WebM, MP3, M4A or WAV recording.")
            work = lambda: state.summarizer.summarize_media(data, mime_type)  # noqa: E731
        elif link:
            video = youtube_link(link)
            if video is None:
                return fail("Paste a link to a public YouTube video.")
            work = lambda: state.summarizer.summarize_video(video)  # noqa: E731
        else:
            return fail("Choose a transcript or a recording, or paste a YouTube link.")
        if state.summary_working:
            return fail("A summary is already being written. Wait for it to finish.", 409)

        def run():
            """Ask the AI. A recording can take longer than the server allows for one request."""
            try:
                text_result = work()
            except SummaryError as error:
                state.summary_error = str(error)
            except Exception:  # never leave the page waiting forever
                app.logger.exception("The summary failed")
                state.summary_error = "Something went wrong while writing the summary. Try again."
            else:
                state.summary = {
                    "text": text_result,
                    "time": datetime.fromtimestamp(now(), manager.tz).strftime("%H:%M"),
                }
            finally:
                state.summary_working = False

        state.summary_working, state.summary_error = True, None
        if app.config.get("SUMMARY_IN_BACKGROUND", not app.testing):
            threading.Thread(target=run, daemon=True).start()
            return jsonify(ok=True, working=True), 202
        run()  # in the tests the answer is ready at once
        if state.summary_error:
            return fail(state.summary_error, 502)
        return jsonify(ok=True, summary=state.summary)

    @app.route("/api/session/csv")
    @lecturer_required
    def session_csv():
        started = manager.lesson_start_time()
        if started is None:
            return fail("There is no session yet.", 404)
        filename = "attendance-%s.csv" % started.strftime("%Y-%m-%d-%H%M")
        return Response(
            state.exporter.export(manager.lesson_entries()),
            mimetype="text/csv",
            headers={"Content-Disposition": 'attachment; filename="%s"' % filename},
        )

    # ---- the classroom screen --------------------------------------------

    def public_base():
        """
        The address that students' phones can open. PUBLIC_URL wins. If the
        lecturer opened the site as "localhost", a phone could not use that
        address, so the address of this computer on the local network is used.
        """
        if app.config["PUBLIC_URL"]:
            return app.config["PUBLIC_URL"].rstrip("/")
        host, _, port = request.host.partition(":")
        if host in ("localhost", "127.0.0.1") and _lan_ip():
            return "http://%s:%s" % (_lan_ip(), port or "80")
        return request.host_url.rstrip("/")

    @app.route("/api/code")
    @lecturer_required
    def current_code():
        session = manager.session
        if session is None or not session.is_open():
            return jsonify(ok=True, open=False)
        t = now()
        code = manager.code_generator.current_code(t)
        base = public_base()
        return jsonify(
            ok=True,
            open=True,
            round=session.round,
            code=code,
            seconds_left=manager.code_generator.seconds_left(t),
            period=manager.code_generator.period_seconds,
            page="%s/checkin" % base,
            link="%s/checkin?code=%s" % (base, code),
        )

    # ---- the student API --------------------------------------------------

    @app.route("/api/round")
    def current_round():
        """Which check-in is open now ("start" or "end"). The student page shows the comment box only for "end"."""
        session = manager.session
        if session is None or not session.is_open():
            return jsonify(ok=True, open=False, round=None)
        return jsonify(ok=True, open=True, round=session.round)

    @app.route("/api/checkin", methods=["POST"])
    def api_checkin():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return fail("The request is not valid.")
        email = str(data.get("email") or "")[:254]
        code = str(data.get("code") or "")[:10]
        lat, lon = _number(data.get("lat")), _number(data.get("lon"))
        location = (lat, lon) if lat is not None and lon is not None and valid_point(lat, lon) else None
        accuracy = _number(data.get("accuracy"))
        comment = str(data.get("comment") or "")[:1000]
        try:
            record = manager.check_in(email, code, location, accuracy, now=now(), comment=comment)
        except CheckInError as error:
            extra = {"reason": error.reason}
            if error.record is not None:
                extra["record_status"] = error.record.status
            status = 409 if error.reason == "already_recorded" else 400
            if error.reason == "too_many_attempts":
                status = 429
            return fail(error.message, status, **extra)
        if record.status == PRESENT:
            message = "Check-in received. You are marked Present."
        else:
            message = "Check-in received. The lecturer will review your location."
        return jsonify(ok=True, status=record.status, message=message, name=record.student.name)

    # ---- polls --------------------------------------------------------------

    def poll_json(poll):
        counts = poll.counts()
        return {
            "question": poll.question,
            "options": poll.options,
            "counts": [counts[o] for o in poll.options],
            "total": poll.total_answers,
            "open": poll.is_open,
        }

    @app.route("/api/poll", methods=["POST"])
    @lecturer_required
    def poll_create():
        data = request.get_json(silent=True) or {}
        options = data.get("options")
        if not isinstance(options, list):
            return fail("Write the answer options.")
        try:
            poll = Poll(str(data.get("question") or ""), [str(o) for o in options][:10])
        except PollError as error:
            return fail(str(error))
        state.poll = poll
        state.poll_id += 1
        return jsonify(ok=True, poll=poll_json(poll))

    @app.route("/api/poll/close", methods=["POST"])
    @lecturer_required
    def poll_close():
        if state.poll is None:
            return fail("There is no poll.", 404)
        state.poll.close()
        return jsonify(ok=True)

    @app.route("/api/poll/results")
    @lecturer_required
    def poll_results():
        if state.poll is None:
            return jsonify(ok=True, exists=False)
        return jsonify(ok=True, exists=True, poll=poll_json(state.poll))

    @app.route("/api/poll/current")
    def poll_current():
        poll = state.poll
        if poll is None or not poll.is_open:
            return jsonify(ok=True, open=False)
        return jsonify(ok=True, open=True, id=state.poll_id, question=poll.question, options=poll.options)

    @app.route("/api/poll/answer", methods=["POST"])
    def poll_answer():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return fail("The request is not valid.")
        poll = state.poll
        if poll is None or data.get("id") != state.poll_id:
            return fail("This poll is no longer available.", 404)
        student = manager.roster.find_by_email(str(data.get("email") or "")[:254])
        if student is None:
            return fail("This email is not on the roster.", 403)
        try:
            poll.answer(student, str(data.get("option") or ""))
        except PollError as error:
            return fail(str(error), 409 if "already" in str(error) else 400)
        return jsonify(ok=True, message="Thank you. Your answer was received.")

    @app.route("/api/homework", methods=["POST"])
    def homework_review():
        """A student sends a work and gets an AI review. Identified by the roster email, like the check-in."""
        request.max_content_length = MAX_HOMEWORK_BYTES + 4096
        if state.reviewer is None:
            return fail("The AI review is not set up. Add GEMINI_API_KEY in the server settings.", 503)
        student = manager.roster.find_by_email(str(request.form.get("email") or "")[:254])
        if student is None:
            return fail("This email is not on the roster.", 403)
        assignment = clean_name(request.form.get("assignment"))
        if not assignment:
            return fail("Write the name of the assignment.")
        upload = request.files.get("work")
        if upload is not None and upload.filename:
            raw = upload.read(MAX_HOMEWORK_BYTES + 1)
            if len(raw) > MAX_HOMEWORK_BYTES:
                return fail("The file is too large (the limit is 200 KB).", 413)
            raw_text = raw.decode("utf-8-sig", errors="replace")
        else:
            raw_text = str(request.form.get("text") or "")[:MAX_HOMEWORK_BYTES]
        try:
            text = clean_work(raw_text)
            state.homework.check_wait(student.email, now())
            previous = state.homework.previous(assignment, student.email)
            others = state.homework.others(assignment, student.email)
            review = state.reviewer.review(text, previous.text if previous else None, [w.text for w in others])
            state.homework.save(assignment, student.email, text, now())
        except ReviewServiceError as error:
            return fail(str(error), 502)
        except HomeworkError as error:
            return fail(str(error), 429 if "wait" in str(error) else 400)
        return jsonify(ok=True, review=review, compared_with=len(others), had_previous=previous is not None)

    @app.errorhandler(500)
    def server_error(_error):
        if request.path.startswith("/api/"):
            return fail("Something went wrong on the server. Try again.", 500)
        return "Something went wrong on the server.", 500

    @app.errorhandler(413)
    def too_large(_error):
        return fail("The file is too large.", 413)

    return app


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = _env_int("PORT", 5000)
    if host == "0.0.0.0":
        print("Phones on the same Wi-Fi can open: http://%s:%d/checkin" % (_lan_ip() or "<this computer>", port))
    else:
        print("Only this computer can open the site. To let phones in, set HOST=0.0.0.0")
    create_app().run(host=host, port=port, debug=False)
