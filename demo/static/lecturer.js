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
      var roundName = d.round === "end" ? "end of class" : "start of class";
      pill.textContent = d.session_open ? "open - " + roundName : "closed";
      pill.className = "pill " + (d.session_open ? "open" : "closed");
      $("startsession").hidden = d.session_open;
      $("startend").hidden = d.session_open || !d.has_start || d.has_end;
      $("endsession").hidden = !d.session_open;
      $("downloadcsv").disabled = !d.has_session;
    });
  }

  function startRound(button, round) {
    button.disabled = true;
    say(sessionMsg, "Getting the location... tap Allow if the phone asks.", "");
    getLocation(function (location, problem) {
      if (!location) {
        button.disabled = false;
        say(sessionMsg, problem + " Allow location and try again.", "bad");
        return;
      }
      var body = { lat: location.lat, lon: location.lon, accuracy: location.accuracy, round: round };
      api("POST", "/api/session/start", body).then(function (result) {
        button.disabled = false;
        if (needLogin(result)) { return; }
        if (result.data.ok) {
          say(sessionMsg, round === "end"
            ? "The end-of-class check-in is open. Show the classroom screen again. Students can write a comment."
            : "Attendance is open. Show the classroom screen to the students.", "ok");
        } else {
          say(sessionMsg, result.data.error, "bad");
        }
        refreshState(); refreshResults();
      });
    });
  }

  $("startsession").addEventListener("click", function () { startRound($("startsession"), "start"); });
  $("startend").addEventListener("click", function () { startRound($("startend"), "end"); });

  $("endsession").addEventListener("click", function () {
    api("POST", "/api/session/end").then(function (result) {
      if (needLogin(result)) { return; }
      say(sessionMsg, result.data.ok ? "This check-in is closed." : result.data.error, result.data.ok ? "ok" : "bad");
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
      $("counts").textContent = "Present: " + d.present.length
        + (d.has_end ? "   Late: " + d.late.length + "   Left early: " + d.left_early.length : "")
        + "   Flagged: " + d.flagged.length + "   Absent: " + d.absent.length;
      function times(r) {
        var t = r.start_time && r.end_time ? r.start_time + " / " + r.end_time : r.time;
        return t + (r.distance === null ? "" : " - " + r.distance + " m");
      }
      $("grouplate").hidden = $("groupleft").hidden = !d.has_end;
      fillList("listlate", d.late, times);
      fillList("listleft", d.left_early, times);
      $("groupcomments").hidden = !d.comments.length;
      fillList("listcomments", d.comments.map(function (c) { return { name: c.name, text: c.comment }; }), function (c) { return c.text; });
      fillList("listpresent", d.present, times);
      fillList("listflagged", d.flagged, function (r) { return times(r) + (r.note ? " - " + r.note : ""); });
      fillList("listabsent", d.absent, function (s) { return s.email; });
      showHeadcounts(d);
    });
  }

  // ---- photo count ----
  var photoMsg = $("photomsg");

  // A phone photo can be several MB. It is shrunk here, so it is sent fast and the AI needs less.
  function shrink(file) {
    if (!window.createImageBitmap) { return Promise.resolve(file); }
    return createImageBitmap(file).then(function (bitmap) {
      var scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
      var canvas = document.createElement("canvas");
      canvas.width = Math.round(bitmap.width * scale);
      canvas.height = Math.round(bitmap.height * scale);
      canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
      return new Promise(function (resolve) {
        canvas.toBlob(function (blob) { resolve(blob || file); }, "image/jpeg", 0.85);
      });
    }).catch(function () { return file; });
  }

  $("countphoto").addEventListener("click", function () {
    var file = $("photofile").files[0];
    if (!file) { say(photoMsg, "Choose or take a photo first.", "bad"); return; }
    var button = $("countphoto");
    button.disabled = true;
    say(photoMsg, "Counting... this can take up to a minute.", "");
    shrink(file).then(function (photo) {
      var form = new FormData();
      form.append("photo", photo, "classroom.jpg");
      return api("POST", "/api/headcount", form, true);
    }).then(function (result) {
      button.disabled = false;
      if (needLogin(result)) { return; }
      var d = result.data;
      if (d.ok) {
        say(photoMsg, d.message, d.level === "warning" ? "warn" : (d.level === "ok" ? "ok" : ""));
        $("photofile").value = "";
      } else {
        say(photoMsg, d.error || "Could not count the people.", "bad");
      }
      refreshResults();
    });
  });

  function showHeadcounts(d) {
    $("headcountoff").hidden = d.headcount_ready;
    var body = $("listheadcounts");
    clear(body);
    d.headcounts.forEach(function (h) {
      var row = add(body, "tr");
      add(row, "td", h.time + " (" + (h.round === "end" ? "end" : "start") + ")");
      add(row, "td", "Photo: " + h.people + ", check-ins: " + h.check_ins, h.level === "warning" ? "warn" : "muted");
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
