// The lecturer page. All text from the server is shown with textContent.
(function () {
  function needLogin(result) {
    if (result.status === 401) { window.location.href = "/login?next=/lecturer"; return true; }
    return false;
  }

  // ---- roster ----
  var rosterMsg = $("rostermsg"), confirmBtn = $("rosterconfirm");

  $("rosterpreview").addEventListener("click", function () {
    var file = $("rosterfile").files[0];
    var list = $("rosterwarnings");
    clear(list); confirmBtn.hidden = true;
    if (!file) { say(rosterMsg, "Choose a CSV file first.", "bad"); return; }
    var form = new FormData();
    form.append("file", file);
    api("POST", "/api/roster/preview", form, true).then(function (result) {
      if (needLogin(result)) { return; }
      var data = result.data;
      if (!data.ok) { say(rosterMsg, data.error, "bad"); return; }
      data.warnings.forEach(function (w) { add(list, "li", w); });
      if (data.can_confirm) {
        say(rosterMsg, "The file has " + data.count + " students. Confirm to save it.", "ok");
        confirmBtn.hidden = false;
      } else {
        say(rosterMsg, "Fix these problems in the file and choose it again.", "bad");
      }
    });
  });

  confirmBtn.addEventListener("click", function () {
    api("POST", "/api/roster/confirm").then(function (result) {
      if (needLogin(result)) { return; }
      if (result.data.ok) {
        say(rosterMsg, "The roster was saved (" + result.data.count + " students).", "ok");
        confirmBtn.hidden = true; clear($("rosterwarnings"));
        refreshState(); refreshResults();
      } else {
        say(rosterMsg, result.data.error, "bad");
      }
    });
  });

  // ---- session ----
  var sessionMsg = $("sessionmsg");

  function refreshState() {
    api("GET", "/api/state").then(function (result) {
      if (needLogin(result) || !result.data.ok) { return; }
      var d = result.data;
      $("rostercount").textContent = d.roster_count ? "Saved roster: " + d.roster_count + " students." : "No roster saved yet.";
      var pill = $("sessionpill");
      pill.textContent = d.session_open ? "open" : "closed";
      pill.className = "pill " + (d.session_open ? "open" : "closed");
      $("startsession").hidden = d.session_open;
      $("endsession").hidden = !d.session_open;
      $("downloadcsv").disabled = !d.has_session;
    });
  }

  $("startsession").addEventListener("click", function () {
    var button = $("startsession");
    button.disabled = true;
    say(sessionMsg, "Getting the location... tap Allow if the phone asks.", "");
    getLocation(function (location, problem) {
      if (!location) {
        button.disabled = false;
        say(sessionMsg, problem + " Allow location and try again.", "bad");
        return;
      }
      api("POST", "/api/session/start", location).then(function (result) {
        button.disabled = false;
        if (needLogin(result)) { return; }
        if (result.data.ok) {
          say(sessionMsg, "Attendance is open. Show the classroom screen to the students.", "ok");
        } else {
          say(sessionMsg, result.data.error, "bad");
        }
        refreshState(); refreshResults();
      });
    });
  });

  $("endsession").addEventListener("click", function () {
    api("POST", "/api/session/end").then(function (result) {
      if (needLogin(result)) { return; }
      say(sessionMsg, result.data.ok ? "Attendance is closed." : result.data.error, result.data.ok ? "ok" : "bad");
      refreshState(); refreshResults();
    });
  });

  $("openscreen").addEventListener("click", function () { window.open("/screen", "_blank"); });
  $("downloadcsv").addEventListener("click", function () { window.location.href = "/api/session/csv"; });

  // ---- results ----
  function fillList(id, items, describe) {
    var body = $(id);
    clear(body);
    items.forEach(function (item) {
      var row = add(body, "tr");
      add(row, "td", item.name);
      add(row, "td", describe(item), "muted");
    });
    if (!items.length) { add(add(body, "tr"), "td", "-", "muted"); }
  }

  function refreshResults() {
    api("GET", "/api/results").then(function (result) {
      if (needLogin(result) || !result.data.ok) { return; }
      var d = result.data;
      $("counts").textContent = "Present: " + d.present.length + "   Flagged: " + d.flagged.length + "   Absent: " + d.absent.length;
      fillList("listpresent", d.present, function (r) { return r.time + (r.distance === null ? "" : " - " + r.distance + " m"); });
      fillList("listflagged", d.flagged, function (r) { return r.time + (r.distance === null ? "" : " - " + r.distance + " m") + (r.note ? " - " + r.note : ""); });
      fillList("listabsent", d.absent, function (s) { return s.email; });
    });
  }

  // ---- poll ----
  var pollMsg = $("pollmsg");

  $("createpoll").addEventListener("click", function () {
    var options = [].map.call(document.querySelectorAll(".pollopt"), function (el) { return el.value.trim(); }).filter(Boolean);
    api("POST", "/api/poll", { question: $("pollquestion").value, options: options }).then(function (result) {
      if (needLogin(result)) { return; }
      say(pollMsg, result.data.ok ? "The poll is open. Students see it on the check-in page." : result.data.error, result.data.ok ? "ok" : "bad");
      refreshPoll();
    });
  });

  $("closepoll").addEventListener("click", function () {
    api("POST", "/api/poll/close").then(function (result) {
      if (needLogin(result)) { return; }
      say(pollMsg, "The poll is closed.", "ok");
      refreshPoll();
    });
  });

  function refreshPoll() {
    api("GET", "/api/poll/results").then(function (result) {
      if (needLogin(result) || !result.data.ok) { return; }
      var box = $("pollresults");
      clear(box);
      if (!result.data.exists) { $("closepoll").hidden = true; return; }
      var poll = result.data.poll;
      $("closepoll").hidden = !poll.open;
      add(box, "p", poll.question + (poll.open ? "" : " (closed)"), "group-title");
      poll.options.forEach(function (option, i) {
        var count = poll.counts[i];
        var percent = poll.total ? Math.round(100 * count / poll.total) : 0;
        add(box, "div", option + ": " + count);
        var bar = add(box, "div", null, "bar");
        add(bar, "div").style.width = percent + "%";
      });
      add(box, "p", "Answers: " + poll.total, "muted");
    });
  }

  function refreshAll() { refreshState(); refreshResults(); refreshPoll(); }
  refreshAll();
  setInterval(function () { if (!document.hidden) { refreshAll(); } }, 4000);
})();
