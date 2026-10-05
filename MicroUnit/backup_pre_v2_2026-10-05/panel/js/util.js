/* util.js — shared helpers for the Mikro Model İş paneli (no framework, no network). */
(function () {
  'use strict';
  var U = window.U = {};
  var M = window.MICRO;
  U.YEARS = [2026, 2027, 2028, 2029, 2030];
  U.SC = ['B', 'A', 'R'];
  U.SCN = { B: 'Əsas', A: 'Mənfi', R: 'İslahat' };
  U.SCC = { B: '#0E6F7C', A: '#B3261E', R: '#1F6FB2' };
  U.SCD = { B: 'solid', A: 'dash', R: 'dot' };
  U.$ = function (s, r) { return (r || document).querySelector(s); };
  U.$$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  U.esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  U.isNum = function (v) { return typeof v === 'number' && isFinite(v); };
  U.nf = function (v, dec) {
    if (!U.isNum(v)) return '—';
    var s = Math.abs(v).toFixed(dec), p = s.split('.');
    p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return (v < 0 && Number(s) !== 0 ? '−' : '') + p[0] + (p[1] ? ',' + p[1] : '');
  };
  U.sg = function (v, dec) { return U.isNum(v) ? (v > 0 && Number(Math.abs(v).toFixed(dec)) !== 0 ? '+' : '') + U.nf(v, dec) : '—'; };
  U.fold = function (s) { return String(s).toLocaleLowerCase('az').replace(/i̇/g, 'i').replace(/[ıİ]/g, 'i').replace(/ə/g, 'e').replace(/ö/g, 'o').replace(/ü/g, 'u').replace(/ğ/g, 'g').replace(/ş/g, 's').replace(/ç/g, 'c'); };
  U.ls = function (k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  U.toast = function (m) { var t = U.$('#toast'); t.textContent = m; t.hidden = false; clearTimeout(U.toast.t); U.toast.t = setTimeout(function () { t.hidden = true; }, 2600); };
  var IC = {
    home: '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/>',
    chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    table: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
    flask: '<path d="M9.5 3h5"/><path d="M10.5 3v6.2L5.2 18a2 2 0 0 0 1.7 3h10.2a2 2 0 0 0 1.7-3l-5.3-8.8V3"/>',
    book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5Z"/><path d="M4 19a2 2 0 0 1 2-2h13"/>',
    layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/>',
    warn: '<path d="M10.3 3.9 2.5 17.4a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4.5M12 17.2h.01"/>',
    dl: '<path d="M12 3v11"/><path d="M7.5 10 12 14.5 16.5 10"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>'
  };
  U.icon = function (n) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (IC[n] || '') + '</svg>'; };

  // ---- series index -------------------------------------------------------
  U.S = M.S;
  U.byId = {};
  U.S.forEach(function (s, i) { s.n = i; U.byId[s.i] = s; });
  U.fr = function (code) { return U.S.filter(function (s) { return s.f === code; }); };
  U.groups = function (code) { var o = [], seen = {}; U.fr(code).forEach(function (s) { if (!seen[s.g]) { seen[s.g] = 1; o.push(s.g); } }); return o; };
  U.label = function (s) { return s.e + (s.v ? ' · ' + s.v : ''); };
  U.dec = function (s) { return s.d; };
  U.gdec = function (s) { return s.k === 'rate' ? 2 : 1; };
  U.gunit = function (s) { return s.k === 'rate' ? 'f.b.' : '%'; };
  U.scOf = function (s) { var sc = U.scen(); return s.s[sc] ? sc : 'B'; };
  U.scens = function (s) { return U.SC.filter(function (k) { return s.s[k]; }); };
  U.cagr = function (s, k) {
    var v = s.s[k]; if (!v || !U.isNum(v[4])) return null;
    if (s.k === 'rate') return U.isNum(s.b) ? (v[4] - s.b) : null;
    return U.isNum(s.b) && s.b > 0 && v[4] > 0 ? (Math.pow(v[4] / s.b, 1 / 5) - 1) * 100 : null;
  };
  U.lastHist = function (s) { return s.h && s.h.length ? s.h[s.h.length - 1] : null; };

  // ---- global scenario ----------------------------------------------------
  var SCEN = (/[?&]scen=(B|A|R|all)/.exec(location.search) || [])[1] || U.ls('mikroPanel.scen') || 'B';
  U.scen = function () { return SCEN === 'all' ? 'B' : SCEN; };
  U.scenRaw = function () { return SCEN; };
  U.setScen = function (k) { SCEN = k; U.ls('mikroPanel.scen', k); if (U.onScen) U.onScen(); };

  // ---- sparkline (history + forecast for the active scenario) -------------
  U.spark = function (s, W, H) {
    W = W || 220; H = H || 40;
    var k = U.scOf(s), hv = (s.h || []).slice(-10), pts = hv.map(function (p) { return [p[0], p[1]]; });
    if (U.isNum(s.b) && (!pts.length || pts[pts.length - 1][0] !== 2025)) pts.push([2025, s.b]);
    U.YEARS.forEach(function (y, i) { if (U.isNum(s.s[k][i])) pts.push([y, s.s[k][i]]); });
    if (pts.length < 2) return '';
    var x0 = pts[0][0], x1 = 2030, lo = Infinity, hi = -Infinity;
    pts.forEach(function (p) { lo = Math.min(lo, p[1]); hi = Math.max(hi, p[1]); });
    if (hi === lo) { hi += 1; lo -= 1; }
    var X = function (y) { return 3 + (y - x0) * (W - 8) / (x1 - x0 || 1); }, Y = function (v) { return 4 + (H - 8) * (1 - (v - lo) / (hi - lo)); };
    var fx = X(2025.5), hp = pts.filter(function (p) { return p[0] <= 2025; }), fp = pts.filter(function (p) { return p[0] >= 2025; });
    var line = function (a, c, w, d) { return '<polyline fill="none" stroke="' + c + '" stroke-width="' + w + '"' + (d ? ' stroke-dasharray="3 2"' : '') + ' stroke-linejoin="round" points="' + a.map(function (p) { return X(p[0]).toFixed(1) + ',' + Y(p[1]).toFixed(1); }).join(' ') + '"/>'; };
    var L = fp.length ? fp[fp.length - 1] : hp[hp.length - 1];
    return '<svg class="spark" viewBox="0 0 ' + W + ' ' + H + '" aria-hidden="true"><rect x="' + fx + '" y="0" width="' + (W - fx) + '" height="' + H + '" fill="#F2F7FB"/>' +
      (hp.length > 1 ? line(hp, '#738190', 1.5) : '') + (fp.length > 1 ? line(fp, U.SCC[k], 2) : '') +
      '<circle cx="' + X(L[0]).toFixed(1) + '" cy="' + Y(L[1]).toFixed(1) + '" r="3" fill="' + U.SCC[k] + '" stroke="#fff" stroke-width="1.5"/></svg>';
  };
  U.trend = function (v) { return !U.isNum(v) ? 'flat' : v > 0.005 ? 'up' : v < -0.005 ? 'down' : 'flat'; };
  U.heat = function (v, cap) {
    if (!U.isNum(v)) return '';
    var a = Math.min(Math.abs(v) / (cap || 8), 1) * 0.55 + 0.06;
    return 'background:' + (v >= 0 ? 'rgba(30,123,79,' : 'rgba(179,38,30,') + a.toFixed(2) + ')';
  };
})();
