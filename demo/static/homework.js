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

  function filled() { return $("email").value.trim() && $("assignment").value.trim(); }

  function showStatus(d) {
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
      say(statusEl, "This is your comparison with the class (you can do it once).", "ok");
      $("comparetext").textContent = c.text;
      $("comparetext").hidden = false;
      return;
    }
    var count = d.count + " of " + d.needed + " students sent their work.";
    if (!d.reviewed) {
      say(statusEl, count + " Send your work first, then the comparison can open.", "");
    } else if (!d.unlocked) {
      say(statusEl, count + " The comparison opens when " + d.needed + " students sent their work.", "");
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
  $("assignment").addEventListener("change", refreshStatus);

  $("form").addEventListener("submit", function (event) {
    event.preventDefault();
    var file = $("work").files[0];
    var text = $("text").value;
    if (!file && !text.trim()) { say(msg, "Choose a file or paste your work.", "bad"); return; }
    var form = fields();
    if (file) { form.append("work", file, file.name); } else { form.append("text", text); }
    var button = $("send");
    button.disabled = true;
    say(msg, "Writing the review... this can take up to a minute.", "");
    api("POST", "/api/homework", form, true).then(function (result) {
      button.disabled = false;
      var d = result.data;
      if (!d.ok) { say(msg, d.error || "Could not write the review (server answer " + result.status + "). Try again in a minute.", "bad"); refreshStatus(); return; }
      try { localStorage.setItem("attendance_email", $("email").value.trim()); } catch (e) { /* not important */ }
      say(msg, "The review is ready. You got your one review for this assignment.", "ok");
      $("review").textContent = d.review;
      $("resultbox").hidden = false;
      $("resultbox").scrollIntoView();
      showStatus(d);
      schedulePoll(15000);
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

  if (filled()) { refreshStatus(); }
})();
