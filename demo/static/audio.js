// Takes the sound out of a recording, in the browser. A screen recording can be 100 MB or more,
// but its sound is small: 16 kHz mono WAV is about 2 MB per minute. Only the sound is sent to the server.
function extractAudio(file) {
  var Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx || !window.OfflineAudioContext) {
    return Promise.reject(new Error("This browser cannot read the sound of a recording."));
  }
  return file.arrayBuffer().then(function (buffer) {
    var context = new Ctx();
    return context.decodeAudioData(buffer).then(function (audio) {
      context.close();
      return audio;
    });
  }).then(function (audio) {
    var rate = 16000;
    var offline = new OfflineAudioContext(1, Math.max(1, Math.ceil(audio.duration * rate)), rate);
    var source = offline.createBufferSource();
    source.buffer = audio;
    source.connect(offline.destination);
    source.start();
    return offline.startRendering();
  }).then(function (rendered) {
    return { blob: encodeWav(rendered.getChannelData(0), rendered.sampleRate), seconds: rendered.length / rendered.sampleRate };
  });
}

function encodeWav(samples, rate) {
  var bytes = new ArrayBuffer(44 + samples.length * 2);
  var view = new DataView(bytes);
  function text(offset, value) { for (var i = 0; i < value.length; i++) { view.setUint8(offset + i, value.charCodeAt(i)); } }
  text(0, "RIFF"); view.setUint32(4, 36 + samples.length * 2, true); text(8, "WAVE");
  text(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, rate, true); view.setUint32(28, rate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  text(36, "data"); view.setUint32(40, samples.length * 2, true);
  for (var i = 0; i < samples.length; i++) {
    var s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([bytes], { type: "audio/wav" });
}
