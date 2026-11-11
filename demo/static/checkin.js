// The student page: check in, and answer a poll.
(function () {
  var emailEl = $("email"), codeEl = $("code"), sendEl = $("send"), msgEl = $("msg");

  function store(key, value) { try { localStorage.setItem(key, value); } catch (e) {} }
  function load(key) { try { return localStorage.getItem(key) || ""; } catch (e) { return ""; } }

  emailEl.value = load("attendance_email");
  // Arrived from the QR code: the code is already known, so the code field is hidden.
  var fromLink = new URLSearchParams(window.location.search).get("code");
  if (fromLink && /^\d{4}$/.test(fromLink)) {
    codeEl.value = fromLink;
    $("codefield").hidden = true;
    $("fromqr").hidden = false;
  }
  $("typecode").addEventListener("click", function () {
    codeEl.value = "";
    $("fromqr").hidden = true;
    $("codefield").hidden = false;
    codeEl.focus();
  });

  // The comment box is shown only while the end-of-class check-in is open.
  var commentEl = $("comment");
  function checkRound() {
    api("GET", "/api/round").then(function (result) {
      $("commentfield").hidden = !(result.data && result.data.round === "end");
    });
  }
  checkRound();
  setInterval(checkRound, 5000);

  codeEl.addEventListener("input", function () { codeEl.value = codeEl.value.replace(/\D/g, "").slice(0, 4); });

  $("form").addEventListener("submit", function (event) {
    event.preventDefault();
    var email = emailEl.value.trim(), code = codeEl.value.trim();
    if (!email) { say(msgEl, "Type your email.", "bad"); return; }
    if (!/^\d{4}$/.test(code)) { say(msgEl, "Type the 4-digit code from the classroom screen.", "bad"); return; }
    store("attendance_email", email);
    sendEl.disabled = true;
    say(msgEl, "Getting your location... tap Allow if the phone asks.", "");

    getLocation(function (location, problem) {
      var body = { email: email, code: code };
      if (!$("commentfield").hidden && commentEl.value.trim()) { body.comment = commentEl.value.trim(); }
      if (location) { body.lat = location.lat; body.lon = location.lon; body.accuracy = location.accuracy; }
      say(msgEl, "Sending...", "");
      api("POST", "/api/checkin", body).then(function (result) {
        sendEl.disabled = false;
        var data = result.data;
        if (data.ok) {
          var text = data.message;
          if (problem) { text += " (" + problem + ")"; }
          say(msgEl, (data.name ? data.name + ": " : "") + text, data.status === "Present" ? "ok" : "warn");
        } else if (data.reason === "already_recorded") {
          say(msgEl, data.message + " Status: " + (data.record_status || "recorded") + ".", "warn");
        } else {
          say(msgEl, data.message || data.error || "Something went wrong. Try again.", "bad");
        }
      });
    });
  });

  // ---- the poll ----
  var pollBox = $("pollbox"), pollMsg = $("pollmsg"), shownId = null;

  function answered(id) { return load("attendance_poll_" + id) === "1"; }

  function showPoll(poll) {
    shownId = poll.id;
    $("pollquestion").textContent = poll.question;
    var box = $("polloptions");
    clear(box);
    say(pollMsg, "", "");
    poll.options.forEach(function (option) {
      var button = add(box, "button", option, "poll-option");
      button.type = "button";
      button.addEventListener("click", function () { sendAnswer(poll.id, option); });
    });
    pollBox.hidden = false;
  }

  function sendAnswer(id, option) {
    var email = emailEl.value.trim();
    if (!email) { say(pollMsg, "Type your email above first.", "bad"); return; }
    api("POST", "/api/poll/answer", { id: id, email: email, option: option }).then(function (result) {
      var data = result.data;
      if (data.ok) {
        store("attendance_poll_" + id, "1");
        clear($("polloptions"));
        say(pollMsg, data.message, "ok");
      } else {
        if (result.status === 409) { store("attendance_poll_" + id, "1"); clear($("polloptions")); }
        say(pollMsg, data.message || data.error || "Could not send the answer.", "bad");
      }
    });
  }

  function checkPoll() {
    api("GET", "/api/poll/current").then(function (result) {
      var data = result.data;
      if (!data.open) { pollBox.hidden = true; shownId = null; return; }
      if (answered(data.id)) { if (shownId !== data.id) { pollBox.hidden = true; } return; }
      if (shownId !== data.id) { showPoll(data); }
    });
  }
  checkPoll();
  setInterval(checkPoll, 5000);
})();
