// Small helpers shared by all pages.
function $(id) { return document.getElementById(id); }

// Send a request to the server. Always gives back { status, data }.
function api(method, url, body, isForm) {
  var options = { method: method, headers: {}, credentials: "same-origin" };
  if (body !== undefined && body !== null) {
    if (isForm) { options.body = body; }
    else { options.headers["Content-Type"] = "application/json"; options.body = JSON.stringify(body); }
  }
  return fetch(url, options).then(function (response) {
    return response.json().catch(function () { return {}; }).then(function (data) {
      return { status: response.status, data: data };
    });
  }).catch(function () {
    return { status: 0, data: { ok: false, error: "No connection to the server. Check the network and try again." } };
  });
}

// Show a message in an element (textContent only, so names can never run as HTML).
function say(el, text, cls) {
  el.textContent = text;
  el.className = "msg " + (cls || "");
}

// Ask the phone for its location. callback(location or null, problemText or null).
function getLocation(callback) {
  if (!navigator.geolocation) { callback(null, "This browser cannot give the location."); return; }
  navigator.geolocation.getCurrentPosition(function (pos) {
    callback({ lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy }, null);
  }, function (err) {
    var texts = {
      1: "Location permission was not granted.",
      2: "Location is unavailable. Check that Location is turned on in the phone.",
      3: "Getting the location took too long."
    };
    callback(null, texts[err.code] || "Could not get the location.");
  }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 });
}

function clear(el) { while (el.firstChild) { el.removeChild(el.firstChild); } }

function add(parent, tag, text, cls) {
  var el = document.createElement(tag);
  if (text !== undefined && text !== null) { el.textContent = text; }
  if (cls) { el.className = cls; }
  parent.appendChild(el);
  return el;
}
