/* pyworker.js — Web Worker of the in-browser backend (identical in the three panels). Loads Pyodide (pinned version
   from cdn.jsdelivr.net), the NumPy / pandas / SciPy packages and the unit's Python bundle (panel/py/*_bundle.zip),
   then answers {method, path, body} with the JSON the local API would return (panel/py/<unit>_web.py → handle).
   Downloads are cached by the browser (HTTP cache); the bundle URL carries its md5, so a new build is fetched once. */
'use strict';
var py = null, handle = null, bytes = 0;
var realFetch = self.fetch.bind(self);
self.fetch = function (u, o) {
  return realFetch(u, o).then(function (r) {
    bytes += +(r.headers.get('content-length') || 0);
    self.postMessage({ type: 'bytes', bytes: bytes, file: String(u).split('?')[0].split('/').pop() });
    return r;
  });
};
function stage(t) { self.postMessage({ type: 'stage', text: t, bytes: bytes }); }
async function init(m) {
  var t0 = performance.now();
  stage('Pyodide ' + m.pyodide + ' yüklənir…');
  importScripts(m.cdn + 'pyodide.js');
  py = await self.loadPyodide({ indexURL: m.cdn });
  stage('Python paketləri yüklənir: ' + m.packages.join(', '));
  await py.loadPackage(m.packages, { messageCallback: function () {}, errorCallback: function (e) { stage('xəbərdarlıq: ' + e); } });
  stage('Model paketi yüklənir…');
  var r = await self.fetch(m.zipUrl);
  if (!r.ok) throw new Error('model paketi tapılmadı (HTTP ' + r.status + ')');
  py.unpackArchive(await r.arrayBuffer(), 'zip', { extractDir: m.root });
  stage('Model modulları idxal olunur…');
  var sys = py.pyimport('sys');
  sys.dont_write_bytecode = true;
  sys.path.insert(0, m.root + '/' + m.pypath);
  handle = py.pyimport(m.entry).handle;
  return { seconds: (performance.now() - t0) / 1000, bytes: bytes };
}
self.onmessage = async function (ev) {
  var m = ev.data;
  try {
    if (m.cmd === 'init') {
      var r = await init(m.meta);
      self.postMessage({ type: 'ready', id: m.id, seconds: r.seconds, bytes: r.bytes });
    } else if (m.cmd === 'req') {
      var t0 = performance.now();
      var out = handle(m.method, m.path, m.body == null ? '' : JSON.stringify(m.body));
      self.postMessage({ type: 'res', id: m.id, json: String(out), seconds: (performance.now() - t0) / 1000 });
    }
  } catch (e) {
    self.postMessage({ type: 'err', id: m.id, message: String((e && e.message) || e).slice(-1500) });
  }
};
