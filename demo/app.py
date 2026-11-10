"""The web app: Flask pages and a small JSON API.

Pages:   /checkin (students), /lecturer and /screen (need the lecturer password)
All data is kept in memory (no database), so it is lost when the server restarts.
"""
import hmac
import math
import os
import secrets
import socket
import time
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
from attendance.attendance_record import ABSENT, FLAGGED, PRESENT
from attendance.code_generator import CodeGenerator
from attendance.csv_exporter import CsvExporter
from attendance.location_checker import LocationChecker, valid_point
from attendance.poll import Poll, PollError
from attendance.roster import Roster, RosterError

DEFAULT_DEV_CODE_SECRET = "dev-only-secret-change-me"
MAX_LOGIN_FAILURES = 10
LOGIN_WINDOW_SECONDS = 300


class DemoState:
    """Everything the demo remembers while the server runs."""

    def __init__(self, manager):
        self.manager = manager
        self.exporter = CsvExporter(manager.roster)
        self.pending_roster = None
        self.poll = None
        self.poll_id = 0
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
        MAX_ACCURACY_METERS=_env_int("MAX_ACCURACY_METERS", 200),
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
        return redirect(url_for("checkin"))

    @app.route("/checkin")
    def checkin():
        return render_template("checkin.html")

    @app.route("/lecturer")
    @lecturer_required
    def lecturer():
        return render_template("lecturer.html")

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
        state.exporter = CsvExporter(pending)
        state.pending_roster = None
        return jsonify(ok=True, count=len(pending))

    # ---- lecturer API: session and results -------------------------------

    def person(student):
        return {"name": student.name, "email": student.email}

    def record_json(record):
        data = person(record.student)
        data.update(
            time=record.check_in_time.strftime("%H:%M"),
            distance=record.distance_meters,
            note=record.note,
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
        try:
            manager.start_session(location, accuracy, now=now())
        except SessionError as error:
            return fail(str(error))
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
        groups = manager.grouped_results()
        session = manager.session
        return jsonify(
            ok=True,
            session_open=bool(session and session.is_open()),
            has_session=session is not None,
            present=[record_json(r) for r in groups[PRESENT]],
            flagged=[record_json(r) for r in groups[FLAGGED]],
            absent=[person(s) for s in groups[ABSENT]],
        )

    @app.route("/api/session/csv")
    @lecturer_required
    def session_csv():
        session = manager.session
        if session is None:
            return fail("There is no session yet.", 404)
        filename = "attendance-%s.csv" % session.start_time.strftime("%Y-%m-%d-%H%M")
        return Response(
            state.exporter.export(session),
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
            code=code,
            seconds_left=manager.code_generator.seconds_left(t),
            period=manager.code_generator.period_seconds,
            page="%s/checkin" % base,
            link="%s/checkin?code=%s" % (base, code),
        )

    # ---- the student API --------------------------------------------------

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
        try:
            record = manager.check_in(email, code, location, accuracy, now=now())
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
