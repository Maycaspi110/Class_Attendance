// The homework page: send a work, show the AI review.
(function () {
  var msg = $("msg");

  try { var saved = localStorage.getItem("attendance_email"); if (saved) { $("email").value = saved; } } catch (e) { /* not important */ }

  $("form").addEventListener("submit", function (event) {
    event.preventDefault();
    var file = $("work").files[0];
    var text = $("text").value;
    if (!file && !text.trim()) { say(msg, "Choose a file or paste your work.", "bad"); return; }
    var form = new FormData();
    form.append("email", $("email").value);
    form.append("assignment", $("assignment").value);
    if (file) { form.append("work", file, file.name); } else { form.append("text", text); }
    var button = $("send");
    button.disabled = true;
    say(msg, "Writing the review... this can take up to a minute.", "");
    api("POST", "/api/homework", form, true).then(function (result) {
      button.disabled = false;
      var d = result.data;
      if (!d.ok) { say(msg, d.error || "Could not write the review.", "bad"); return; }
      try { localStorage.setItem("attendance_email", $("email").value.trim()); } catch (e) { /* not important */ }
      say(msg, "The review is ready.", "ok");
      var parts = [];
      parts.push(d.had_previous ? "Compared with your previous version." : "This is your first version.");
      parts.push(d.compared_with > 0
        ? "Compared with " + d.compared_with + " other work" + (d.compared_with === 1 ? "" : "s") + "."
        : "No other works to compare with yet.");
      $("meta").textContent = parts.join(" ");
      $("review").textContent = d.review;
      $("resultbox").hidden = false;
      $("resultbox").scrollIntoView();
    });
  });
})();
