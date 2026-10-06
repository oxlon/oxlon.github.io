/* util.js — shared helpers of the Risk paneli (no framework). Data: window.RISK.<bundle>.<output file stem> = compact
   table {c, r, p?, pc?}; U.T('<stem>') returns rows as objects. Number format: Azerbaijani (decimal comma). */
(function () {
  'use strict';
  var U = window.U = {};
  var R = window.RISK = window.RISK || {};
  U.YEARS = [2026, 2027, 2028, 2029, 2030];
  U.$ = function (s, r) { return (r || document).querySelector(s); };
  U.$$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  U.esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  U.isNum = function (v) { return typeof v === 'number' && isFinite(v); };
  U.nf = function (v, dec) {
    if (!U.isNum(v)) return '—';
    if (dec == null) dec = Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 10 ? 1 : Math.abs(v) >= 0.1 ? 2 : Math.abs(v) === 0 ? 0 : 3;
    var s = Math.abs(v).toFixed(dec), p = s.split('.');
    p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return (v < 0 && Number(s) !== 0 ? '−' : '') + p[0] + (p[1] ? ',' + p[1] : '');
  };
  U.sg = function (v, dec) { return U.isNum(v) ? (v > 0 && Number(Math.abs(v).toFixed(dec == null ? 2 : dec)) !== 0 ? '+' : '') + U.nf(v, dec) : '—'; };
  U.pct = function (p, dec) { return U.isNum(p) ? U.nf(p * 100, dec == null ? (p < 0.01 && p > 0 ? 2 : 0) : dec) + ' %' : '—'; };
  U.pf = function (p) { return !U.isNum(p) ? '—' : p < 0.001 ? '<0,001' : U.nf(p, 3); };
  U.sig = function (v) { if (!U.isNum(v)) return '—'; var a = Math.abs(v); return U.nf(v, a >= 100 ? 1 : a >= 1 ? 2 : a >= 0.01 ? 3 : 4); };
  U.parseNum = function (v) {
    var s = String(v == null ? '' : v).trim().replace(/[\s   ]/g, '').replace(/[−–]/g, '-');
    if (s === '') return null;
    var c = s.lastIndexOf(','), d = s.lastIndexOf('.');
    if (c >= 0 && d >= 0) s = c > d ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
    else if (c >= 0) s = s.replace(',', '.');
    var x = Number(s); return isFinite(x) ? x : null;
  };
  U.fold = function (s) { return String(s).toLocaleLowerCase('az').replace(/i̇/g, 'i').replace(/[ıİ]/g, 'i').replace(/ə/g, 'e').replace(/ö/g, 'o').replace(/ü/g, 'u').replace(/ğ/g, 'g').replace(/ş/g, 's').replace(/ç/g, 'c'); };
  U.ls = function (k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { return null; } return null; };
  U.toast = function (m) { var t = U.$('#toast'); if (!t) return; t.textContent = m; t.hidden = false; clearTimeout(U.toast.t); U.toast.t = setTimeout(function () { t.hidden = true; }, 3600); };
  U.debounce = function (fn, ms) { var t; return function () { var a = arguments; clearTimeout(t); t = setTimeout(function () { fn.apply(null, a); }, ms || 250); }; };
  U.enc = function (id) { return encodeURIComponent(id); };
  U.uniq = function (a) { var s = {}, o = []; a.forEach(function (x) { var k = String(x); if (!s[k]) { s[k] = 1; o.push(x); } }); return o; };
  U.by = function (rows, k) { var o = {}; rows.forEach(function (r) { (o[r[k]] = o[r[k]] || []).push(r); }); return o; };
  U.sum = function (a) { return a.reduce(function (s, x) { return s + (U.isNum(x) ? x : 0); }, 0); };
  U.ids = function (s) { return String(s || '').split(/[;,]\s*/).map(function (x) { return x.trim(); }).filter(Boolean); };

  // ---- data access ---------------------------------------------------------
  var CACHE = {};
  U.raw = function (stem) { for (var b in R) { if (R[b] && R[b][stem] !== undefined) return R[b][stem]; } return null; };
  U.T = function (stem) {
    if (CACHE[stem]) return CACHE[stem];
    var t = U.raw(stem); if (!t || !t.c) return [];
    var pc = {}; (t.pc || []).forEach(function (c) { pc[c] = 1; });
    var rows = t.r.map(function (r) { var o = {}; t.c.forEach(function (c, i) { var v = r[i]; o[c] = pc[c] && v != null ? t.p[v] : v; }); return o; });
    CACHE[stem] = rows; return rows;
  };
  U.has = function (stem) { return !!U.raw(stem); };
  U.META = (R.core || {})._meta || { stamp: {}, run: {} };
  var LOADED = {};
  U.loadScript = function (src) {
    if (LOADED[src]) return LOADED[src];
    LOADED[src] = new Promise(function (ok, bad) {
      var el = document.createElement('script'); el.src = src; el.onload = function () { ok(); };
      el.onerror = function () { delete LOADED[src]; bad(new Error('Fayl yüklənmədi: ' + src)); }; document.head.appendChild(el);
    });
    return LOADED[src];
  };
  /* lazy bundles (plain <script> injection — works from file://) */
  U.lazy = function (b) { return R[b] ? Promise.resolve() : U.loadScript('data/' + b + '.js'); };
  U.need = function (bundles, el, fn) {
    var miss = bundles.filter(function (b) { return !R[b]; });
    if (!miss.length) return fn();
    var tok = U.navTok;
    el.innerHTML = '<div class="card pad muted">Məlumat yüklənir… (' + miss.map(function (b) { return 'data/' + b + '.js'; }).join(', ') + ')</div>';
    Promise.all(miss.map(U.lazy)).then(function () { if (tok === U.navTok) { el.innerHTML = ''; fn(); } }, function (e) { el.innerHTML = '<div class="card pad"><b>Məlumat faylı yüklənmədi.</b><p class="small muted">' + U.esc(e.message) + '</p></div>'; });
  };
  U.navTok = 0;

  // ---- small UI pieces -----------------------------------------------------
  var IC = {
    home: '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/>',
    list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    pulse: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    fan: '<path d="M3 20c6 0 8-10 18-14"/><path d="M3 20c7 0 10-5 18-6" opacity=".6"/><path d="M3 20c7 0 11 0 18 2" opacity=".35"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    scale: '<path d="M4 20 20 4M4 20h6M4 20v-6"/><circle cx="17" cy="17" r="3"/>',
    bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    tool: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    grid: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    check: '<path d="m4 12 5 5L20 6"/>',
    doc: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5Z"/><path d="M4 19a2 2 0 0 1 2-2h13"/>',
    warn: '<path d="M10.3 3.9 2.5 17.4a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4.5M12 17.2h.01"/>',
    dl: '<path d="M12 3v11"/><path d="M7.5 10 12 14.5 16.5 10"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>',
    play: '<path d="M7 4v16l13-8z"/>'
  };
  U.icon = function (n, sz) { return '<svg' + (sz ? ' width="' + sz + '" height="' + sz + '"' : '') + ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (IC[n] || '') + '</svg>'; };
  U.seg = function (id, opts, on) {
    return '<div class="seg" id="' + id + '" role="group">' + opts.map(function (o) { return '<button type="button" data-v="' + U.esc(o[0]) + '" class="' + (String(o[0]) === String(on) ? 'on' : '') + '">' + U.esc(o[1]) + '</button>'; }).join('') + '</div>';
  };
  U.opt = function (v, lab, on) { return '<option value="' + U.esc(v) + '"' + (String(v) === String(on) ? ' selected' : '') + '>' + U.esc(lab) + '</option>'; };
  U.sel = function (id, opts, on, cls) { return '<select id="' + id + '" class="btn sm ' + (cls || '') + '">' + opts.map(function (o) { return U.opt(o[0], o[1], on); }).join('') + '</select>'; };
  U.help = function (t) { return ' <span class="help" title="' + U.esc(t) + '">?</span>'; };
  U.sec = function (title, note, body, id) { return '<section class="sec"' + (id ? ' id="' + id + '"' : '') + '><div class="sec-h"><h2>' + title + '</h2>' + (note ? '<p>' + note + '</p>' : '') + '</div>' + body + '</section>'; };
  U.head = function (eyebrow, title, lead) { return '<div class="eyebrow">' + eyebrow + '</div><h1 class="h1" style="margin-top:4px">' + title + '</h1>' + (lead ? '<p class="lead">' + lead + '</p>' : ''); };
  U.subtabs = function (base, list, cur) {
    return '<nav class="sectabs subnav" aria-label="Alt bölmələr">' + list.map(function (t) { return '<a class="stab' + (t[0] === cur ? ' on' : '') + '" href="#/' + base + (t[0] ? '/' + t[0] : '') + '">' + U.esc(t[1]) + '</a>'; }).join('') + '</nav>';
  };
  var PR = { 'yüksək': 'bad', 'orta': 'warn', 'aşağı': 'acc' };
  U.prio = function (p) { return p ? '<span class="chip ' + (PR[p] || '') + '">' + U.esc(p) + '</span>' : ''; };
  U.sigchip = function (s) {
    var t = String(s || ''), c = /xəbərdarlıq|qırmızı|keçmədi|yüksək|mənfi|xeta|xəta/.test(t) ? 'bad' : /diqqət|sarı|izləmə|köhnəl|orta|qismən/.test(t) ? 'warn' : /normal|yaşıl|keçdi|ok|təzə|canlı|əlverişli|aşağı/.test(t) ? 'acc' : '';
    return t ? '<span class="chip ' + c + '">' + U.esc(t) + '</span>' : '';
  };
  U.score = function (s) { var c = s >= 12 ? '#B3261E' : s >= 6 ? '#C77700' : '#1E7B4F'; return '<b class="tnum" style="color:' + c + '">' + U.nf(s, 0) + '</b>'; };
  U.FAM = { MAL: 'Maliyyə və əmtəə bazarları', XSI: 'Xarici iqtisadi və siyasi mühit', TEB: 'Təbii fəlakətlər', DAX: 'Daxili makroiqtisadi nəticələr', SEK: 'Sektor və bazar strukturu' };
  U.FAMC = { MAL: '#1F6FB2', XSI: '#6A3FB5', TEB: '#1E7B4F', DAX: '#B3261E', SEK: '#8A5300' };
  U.fam = function (f) { return '<span class="chip" style="background:' + (U.FAMC[f] || '#738190') + '1A;color:' + (U.FAMC[f] || '#455463') + '" title="' + U.esc(U.FAM[f] || '') + '">' + U.esc(f) + '</span>'; };
})();
