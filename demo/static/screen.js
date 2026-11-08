// The classroom screen: shows the current code and the QR code, and updates them.
(function () {
  var shownLink = null;

  function drawQr(link) {
    var qr = qrcode(0, "M");
    qr.addData(link);
    qr.make();
    $("qr").innerHTML = qr.createSvgTag({ cellSize: 4, margin: 4, scalable: true });
  }

  function update() {
    api("GET", "/api/code").then(function (result) {
      if (result.status === 401) { window.location.href = "/login?next=/screen"; return; }
      var d = result.data;
      if (!d.ok || !d.open) {
        $("open").hidden = true;
        $("closed").hidden = false;
        shownLink = null;
        return;
      }
      $("closed").hidden = true;
      $("open").hidden = false;
      $("bigcode").textContent = d.code.split("").join(" ");
      if (d.link !== shownLink) { drawQr(d.link); shownLink = d.link; }
      $("page").textContent = d.page.replace(/^https?:\/\//, "");
      $("left").textContent = "The code changes in " + d.seconds_left + " seconds";
      $("fill").style.width = Math.round(100 * d.seconds_left / d.period) + "%";
    });
  }

  update();
  setInterval(update, 1000);
})();
