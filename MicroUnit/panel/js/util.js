/* util.js — shared helpers of the Mikro Model İş paneli v2 (no framework). Series are keyed by stable ids fr<k>:<code>. */
(function () {
  'use strict';
  var U = window.U = {};
  var M = window.MICRO;
  U.YEARS = [2026, 2027, 2028, 2029, 2030];
  U.SC = ['B', 'A', 'R'];
  U.SCN = { B: 'Əsas', A: 'Mənfi', R: 'İslahat', C: 'Xüsusi' };
  U.SCL = { B: 'Baseline', A: 'Adverse', R: 'Reform' };
  U.SCK = { Baseline: 'B', Adverse: 'A', Reform: 'R' };
  U.SCC = { B: '#0E6F7C', A: '#B3261E', R: '#1F6FB2', C: '#E07B00' };
  U.SCD = { B: 'solid', A: 'dash', R: 'dot', C: 'solid' };
  U.$ = function (s, r) { return (r || document).querySelector(s); };
  U.$$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  U.esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  U.isNum = function (v) { return typeof v === 'number' && isFinite(v); };
  U.nf = function (v, dec) {
    if (!U.isNum(v)) return '—';
    if (dec == null) dec = Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 10 ? 1 : Math.abs(v) >= 0.1 ? 2 : 3;
    var s = Math.abs(v).toFixed(dec), p = s.split('.');
    p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return (v < 0 && Number(s) !== 0 ? '−' : '') + p[0] + (p[1] ? ',' + p[1] : '');
  };
  U.sg = function (v, dec) { return U.isNum(v) ? (v > 0 && Number(Math.abs(v).toFixed(dec)) !== 0 ? '+' : '') + U.nf(v, dec) : '—'; };
  U.pf = function (p) { return !U.isNum(p) ? '—' : p < 0.001 ? '<0,001' : U.nf(p, 3); };
  /* numbers in input fields: decimal comma, `sig` significant digits (full value in data-v / tooltip); parse accepts
     "1,5", "1.5", "1 234,5", "1,234.5", "−0,2" */
  U.inFmt = function (v, sig) {
    var x = Number(v); if (v === null || v === '' || !isFinite(x)) return '';
    x = +x.toPrecision(sig || 5);
    return String(x).replace('.', ',');
  };
  U.inFull = function (v) { var x = Number(v); return v === null || v === '' || !isFinite(x) ? '' : String(+x.toPrecision(12)).replace('.', ','); };
  U.parseNum = function (v) {
    var s = String(v == null ? '' : v).trim().replace(/[\s\u00a0\u2009\u202f]/g, '').replace(/[−–]/g, '-');
    if (s === '') return null;
    var c = s.lastIndexOf(','), d = s.lastIndexOf('.');
    if (c >= 0 && d >= 0) s = c > d ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
    else if (c >= 0) s = s.split(',').length > 2 ? s.replace(/,/g, '') : s.replace(',', '.');
    return Number(s);
  };
  U.sig = function (v) { if (!U.isNum(v)) return '—'; var a = Math.abs(v); return U.nf(v, a >= 100 ? 1 : a >= 1 ? 3 : a >= 0.01 ? 4 : 6); };
  U.fold = function (s) { return String(s).toLocaleLowerCase('az').replace(/i̇/g, 'i').replace(/[ıİ]/g, 'i').replace(/ə/g, 'e').replace(/ö/g, 'o').replace(/ü/g, 'u').replace(/ğ/g, 'g').replace(/ş/g, 's').replace(/ç/g, 'c'); };
  U.ls = function (k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { return null; } return null; };
  U.toast = function (m) { var t = U.$('#toast'); t.textContent = m; t.hidden = false; clearTimeout(U.toast.t); U.toast.t = setTimeout(function () { t.hidden = true; }, 3200); };
  U.debounce = function (fn, ms) { var t; return function () { var a = arguments; clearTimeout(t); t = setTimeout(function () { fn.apply(null, a); }, ms || 250); }; };
  U.enc = function (id) { return encodeURIComponent(id); };
  var IC = {
    home: '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/>',
    sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    table: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
    flask: '<path d="M9.5 3h5"/><path d="M10.5 3v6.2L5.2 18a2 2 0 0 0 1.7 3h10.2a2 2 0 0 0 1.7-3l-5.3-8.8V3"/>',
    book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5Z"/><path d="M4 19a2 2 0 0 1 2-2h13"/>',
    doc: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    warn: '<path d="M10.3 3.9 2.5 17.4a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4.5M12 17.2h.01"/>',
    fx: '<path d="M4 20c4 0 4-16 8-16M3 11h9M14 9l6 8M20 9l-6 8"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    dl: '<path d="M12 3v11"/><path d="M7.5 10 12 14.5 16.5 10"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>'
  };
  U.icon = function (n, sz) { return '<svg' + (sz ? ' width="' + sz + '" height="' + sz + '"' : '') + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (IC[n] || '') + '</svg>'; };

  // ---- series index -------------------------------------------------------
  U.S = M.S;
  U.byId = {};
  U.S.forEach(function (s, i) { s.n = i; U.byId[s.i] = s; });
  U.META = M.META;
  U.frOf = function (code) { return U.META.frs.filter(function (f) { return f.c === code || f.slug === code; })[0]; };
  U.fr = function (code) { return U.S.filter(function (s) { return s.f === code; }); };
  U.groups = function (code) { return U.META.groups[code] || []; };
  U.members = function (code, g) { return U.S.filter(function (s) { return s.f === code && s.g === g; }); };
  U.isRate = function (s) { return s.k === 'rate' || s.k === 'share'; };
  U.gdec = function (s) { return U.isRate(s) ? 2 : 1; };
  U.gunit = function (s) { return U.isRate(s) ? 'f.b.' : '%'; };
  U.scens = function (s) { return U.SC.filter(function (k) { return s.s && s.s[k]; }); };
  U.scOf = function (s) { var k = U.scen(); return s.s && s.s[k] ? k : 'B'; };
  U.b25 = function (s, k) { return s.b25 && U.isNum(s.b25[k]) ? s.b25[k] : s.b; };
  U.cagr = function (s, k) {
    var v = s.s && s.s[k], b = U.b25(s, k); if (!v || !U.isNum(v[4]) || !U.isNum(b)) return null;
    if (U.isRate(s)) return v[4] - b;
    return b > 0 && v[4] > 0 ? (Math.pow(v[4] / b, 1 / 5) - 1) * 100 : null;
  };
  U.lastHist = function (s) { var h = (s.h || []).filter(function (p) { return p[0] <= 2025; }); return h.length ? h[h.length - 1] : null; };
  U.lab25 = function (s) { return s.nc ? '2025 · qiym.' : (U.lastHist(s) && U.lastHist(s)[0] === 2025 ? '2025 · faktiki' : '2025'); };
  U.href = function (s) { return '#/' + s.f.toLowerCase() + '/c/' + U.enc(s.i); };
  U.label = function (s) { return s.e; };

  // ---- global scenario ----------------------------------------------------
  var SCEN = (/[?&]scen=(B|A|R|all)/.exec(location.search) || [])[1] || U.ls('mikroPanel.scen') || 'B';
  U.scen = function () { return SCEN === 'all' ? 'B' : SCEN; };
  U.scenRaw = function () { return SCEN; };
  U.setScen = function (k) { SCEN = k; U.ls('mikroPanel.scen', k); if (U.onScen) U.onScen(); };

  // ---- lazy bundles (work from file:// too: plain <script> injection) ----
  var LOADED = {};
  U.loadScript = function (src) {
    if (LOADED[src]) return LOADED[src];
    LOADED[src] = new Promise(function (ok, bad) {
      var el = document.createElement('script'); el.src = src; el.onload = function () { ok(); };
      el.onerror = function () { delete LOADED[src]; bad(new Error('Fayl yüklənmədi: ' + src)); }; document.head.appendChild(el);
    });
    return LOADED[src];
  };
  U.trend = function (v) { return !U.isNum(v) ? 'flat' : v > 0.005 ? 'up' : v < -0.005 ? 'down' : 'flat'; };
  U.heat = function (v, cap) {
    if (!U.isNum(v)) return '';
    var a = Math.min(Math.abs(v) / (cap || 8), 1) * 0.55 + 0.06;
    return 'background:' + (v >= 0 ? 'rgba(30,123,79,' : 'rgba(179,38,30,') + a.toFixed(2) + ')';
  };
  U.seg = function (id, opts, on) {
    return '<div class="seg" id="' + id + '" role="group">' + opts.map(function (o) { return '<button type="button" data-v="' + U.esc(o[0]) + '" class="' + (String(o[0]) === String(on) ? 'on' : '') + '">' + U.esc(o[1]) + '</button>'; }).join('') + '</div>';
  };
  U.opt = function (v, lab, on) { return '<option value="' + U.esc(v) + '"' + (String(v) === String(on) ? ' selected' : '') + '>' + U.esc(lab) + '</option>'; };
})();
