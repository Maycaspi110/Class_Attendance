// The homework page: one review of a work, and the comparison with the class.
(function () {
  var msg = $("msg"), statusEl = $("comparestatus"), compareBtn = $("compare");
  var pollTimer = null;

  try { var saved = localStorage.getItem("attendance_email"); if (saved) { $("email").value = saved; } } catch (e) { /* not important */ }

  function fields() {
    var form = new FormData();
    form.append("email", $("email").value.trim());
    form.append("assignment", $("assignment").value.trim());
    return form;
  }

  // The assignments are chosen from the list the lecturer published.
  function loadAssignments() {
    api("GET", "/api/assignments").then(function (result) {
      var d = result.data, select = $("assignment");
      clear(select);
      if (!d || !d.ok || !d.assignments.length) {
        add(select, "option", "(no assignment yet)").value = "";
        say(msg, "The lecturer did not publish an assignment yet.", "bad");
        return;
      }
      add(select, "option", "Choose the assignment").value = "";
      d.assignments.forEach(function (a) {
        var option = add(select, "option", a.course + " - " + a.name + " (due " + a.due + ")");
        option.value = a.name;
      });
    });
  }

  function filled() { return $("email").value.trim() && $("assignment").value.trim(); }

  function waitText(seconds) {
    return seconds >= 5400 ? Math.round(seconds / 3600) + " hours" : Math.max(1, Math.round(seconds / 60)) + " minutes";
  }

  function showReview(d) {
    var rs = $("reviewstatus"), button = $("reviewbtn");
    $("reviewtext").hidden = !d.review;
    $("reviewtext").textContent = d.review || "";
    button.disabled = true;
    if (!d.submitted) {
      say(rs, "Send your work first, then you can ask for the review.", "");
    } else if (d.review_wait > 0) {
      say(rs, "You got your review. You can ask for another one in about " + waitText(d.review_wait) + " (for example after you send an improved version).", "ok");
    } else {
      say(rs, "Your work was sent. You can ask for the AI review now.", "");
      button.disabled = false;
    }
  }

  function showStatus(d) {
    showReview(d);
    var bar = $("comparebar");
    bar.max = d.needed;
    bar.value = Math.min(d.count, d.needed);
    var c = d.comparison;
    compareBtn.disabled = true;
    $("comparetext").hidden = true;
    if (c && c.state === "working") {
      say(statusEl, "The AI is comparing your work with the class... it can take a minute.", "");
      schedulePoll(3000);
      return;
    }
    if (c && c.state === "done") {
      $("comparetext").textContent = c.text;
      $("comparetext").hidden = false;
    }
    var count = d.count + " of " + d.needed + " students sent their work.";
    if (!d.submitted) {
      say(statusEl, count + " Send your work first, then the comparison can open.", "");
    } else if (!d.unlocked) {
      say(statusEl, count + " The comparison opens when " + d.needed + " students sent their work.", "");
    } else if (d.compare_wait > 0) {
      say(statusEl, count + " This is your comparison. You can compare again in about " + waitText(d.compare_wait) + " (for example after you improve your work).", "ok");
    } else {
      say(statusEl, count + " The comparison is open." + (c && c.state === "error" ? " The last try failed: " + c.error : ""), "ok");
      compareBtn.disabled = false;
    }
  }

  function schedulePoll(ms) {
    clearTimeout(pollTimer);
    pollTimer = setTimeout(refreshStatus, ms);
  }

  function refreshStatus() {
    if (!filled()) { return; }
    var q = "?email=" + encodeURIComponent($("email").value.trim()) + "&assignment=" + encodeURIComponent($("assignment").value.trim());
    api("GET", "/api/homework/status" + q).then(function (result) {
      var d = result.data;
      if (d && d.ok) { showStatus(d); schedulePoll(d.comparison && d.comparison.state === "working" ? 3000 : 15000); }
      else if (d && d.error) { compareBtn.disabled = true; say(statusEl, d.error, "bad"); }
    });
  }

  $("email").addEventListener("change", refreshStatus);
  $("assignment").addEventListener("change", function () {
    $("reviewtext").hidden = true;
    refreshStatus();
  });

  $("form").addEventListener("submit", function (event) {
    event.preventDefault();
    var file = $("work").files[0];
    if (!file) { say(msg, "Choose the PDF file of your work.", "bad"); return; }
    var form = fields();
    form.append("work", file, file.name);
    var button = $("send");
    button.disabled = true;
    say(msg, "Sending your work... the AI reads the PDF, this can take up to a minute.", "");
    api("POST", "/api/homework", form, true).then(function (result) {
      button.disabled = false;
      var d = result.data;
      if (!d.ok) { say(msg, d.error || "Could not send the work (server answer " + result.status + "). Try again in a minute.", "bad"); refreshStatus(); return; }
      try { localStorage.setItem("attendance_email", $("email").value.trim()); } catch (e) { /* not important */ }
      say(msg, "Your work was sent. Now you can ask for an AI review below.", "ok");
      showStatus(d);
      schedulePoll(15000);
    });
  });

  $("reviewbtn").addEventListener("click", function () {
    var button = $("reviewbtn");
    button.disabled = true;
    say($("reviewstatus"), "The AI is writing the review... this can take up to a minute.", "");
    api("POST", "/api/homework/review", fields(), true).then(function (result) {
      var d = result.data;
      if (d && d.ok) { showStatus(d); schedulePoll(15000); $("reviewtext").scrollIntoView(); return; }
      say($("reviewstatus"), (d && d.error) || "Could not write the review (server answer " + result.status + "). Try again in a minute.", "bad");
      refreshStatus();
    });
  });

  compareBtn.addEventListener("click", function () {
    compareBtn.disabled = true;
    say(statusEl, "Sending to the AI...", "");
    api("POST", "/api/homework/compare", fields(), true).then(function (result) {
      var d = result.data;
      if (d && d.ok && d.working) { schedulePoll(3000); return; }
      if (d && d.ok) { showStatus(d); return; }
      say(statusEl, (d && d.error) || "Could not compare (server answer " + result.status + "). Try again in a minute.", "bad");
      refreshStatus();
    });
  });

  loadAssignments();
})();
