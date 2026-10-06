/* tables.js — generic full tables: sortable columns, text filter, "show more", CSV and Excel export, row links.
   U.dt(id, rows, cols, opt) returns HTML; the view's delegated handlers (U.dtBind) do the rest. cols: [{k, l, f(v,row),
   n (numeric), d (decimals), p (probability), t (title)}]; omitted → every column of the rows with U.colLabel(). */
(function () {
  'use strict';
  var U = window.U;
  U.DT = {};
  var PAGE = 200, YR = { il: 1, year: 1, ufuq: 1, hedef_il: 1, baseline_year: 1, orijin: 1, reference_year: 1 };
  U.colLabel = function (k) { var L = U.COLS || {}; if (L[k]) return L[k]; var s = String(k).replace(/_/g, ' '); return s.charAt(0).toUpperCase() + s.slice(1); };
  function auto(rows) {
    var ks = []; rows.slice(0, 50).forEach(function (r) { Object.keys(r).forEach(function (k) { if (ks.indexOf(k) < 0) ks.push(k); }); });
    return ks.map(function (k) { var n = rows.some(function (r) { return U.isNum(r[k]); }) && rows.every(function (r) { return r[k] == null || U.isNum(r[k]) || typeof r[k] === 'boolean'; }); return { k: k, l: U.colLabel(k), n: n }; });
  }
  U.VMAP = { baxis: { baseline: 'baza mərkəzli', live: 'canlı' }, gosterici: { g: 'qeyri-neft artımı', cpi: 'inflyasiya', fis: 'büdcə balansı', brent: 'Brent' }, kind: { g: 'qeyri-neft artımı', cpi: 'inflyasiya', fis: 'büdcə balansı' } };
  function vmap(c, v) { var m = U.VMAP[c.k]; return m && typeof v === 'string' && m[v] ? m[v] : v; }
  U.flat = function (v) {
    if (v == null) return '';
    if (U.isNum(v)) return U.nf(v);
    if (Array.isArray(v)) return v.map(U.flat).join('; ');
    if (typeof v === 'object' && v.label != null) return v.label + ': ' + Object.keys(v).filter(function (k) { return k !== 'label'; }).map(function (k) { return U.flat(v[k]); }).join(', ');
    if (typeof v === 'object') return Object.keys(v).map(function (k) { return (U.COLS && U.COLS[k] || k) + ' ' + U.flat(v[k]); }).join(', ');
    return String(v);
  };
  U.fmtCell = function (c, v, row) {
    if (c.f) return c.f(v, row);
    v = vmap(c, v);
    if (v == null || v === '') return '<span class="muted">—</span>';
    if (typeof v === 'boolean') return v ? 'bəli' : 'xeyr';
    if (typeof v === 'object') return U.esc(U.flat(v));
    if (U.isNum(v)) return c.p ? U.pct(v, c.d) : YR[c.k] && v >= 1900 && v <= 2100 && v === Math.round(v) ? String(v) : U.nf(v, c.d == null && v === Math.round(v) ? 0 : c.d);
    var s = String(v);
    return s.length > 160 && !c.full ? '<span title="' + U.esc(s) + '">' + U.esc(s.slice(0, 158)) + '…</span>' : U.esc(s);
  };
  function txt(c, v) { v = vmap(c, v); if (v == null) return ''; if (typeof v === 'object') return JSON.stringify(v); if (typeof v === 'boolean') return v ? 'bəli' : 'xeyr'; return v; }
  function view(id) {
    var T = U.DT[id], q = U.fold(T.q || '').trim().split(/\s+/).filter(Boolean), rows = T.rows;
    if (q.length) rows = rows.filter(function (r) { var s = U.fold(T.cols.map(function (c) { return r[c.k]; }).join(' ')); return q.every(function (w) { return s.indexOf(w) >= 0; }); });
    if (T.sort) {
      var k = T.sort[0], dir = T.sort[1];
      rows = rows.slice().sort(function (a, b) { var x = a[k], y = b[k]; if (x == null) return 1; if (y == null) return -1; return (U.isNum(x) && U.isNum(y) ? x - y : String(x).localeCompare(String(y), 'az')) * dir; });
    }
    return rows;
  }
  function body(id) {
    var T = U.DT[id], rows = view(id), shown = rows.slice(0, T.lim);
    var h = shown.map(function (r, i) {
      var href = T.opt.href ? T.opt.href(r) : null, cls = (T.opt.rowCls ? T.opt.rowCls(r) : '') + (href || T.opt.onRow ? ' click' : '');
      return '<tr class="' + cls + '"' + (href ? ' data-href="' + U.esc(href) + '"' : '') + ' data-i="' + i + '">' + T.cols.map(function (c) { var h0 = U.fmtCell(c, r[c.k], r); return '<td class="' + (c.n ? 'n' : 'lab0') + (c.cls ? ' ' + c.cls : '') + '">' + (c.n ? h0 : '<div class="cw">' + h0 + '</div>') + '</td>'; }).join('') + '</tr>';
    }).join('');
    if (!rows.length) h = '<tr><td colspan="' + T.cols.length + '" class="muted">Sətir yoxdur</td></tr>';
    T.cur = shown;
    return { h: h, n: rows.length, more: rows.length > shown.length };
  }
  U.dt = function (id, rows, cols, opt) {
    opt = opt || {};
    rows = rows || [];
    if (!Array.isArray(rows)) rows = Object.keys(rows).map(function (k) { var v = rows[k]; return v && typeof v === 'object' && !Array.isArray(v) ? Object.assign({ acar: k }, v) : { acar: k, deyer: Array.isArray(v) ? v.join('; ') : v }; });
    cols = cols || auto(rows);
    cols.forEach(function (c) { if (c.n || c.cls) return; var m = 0; rows.slice(0, 60).forEach(function (r) { var v = r[c.k]; if (typeof v === 'string' && v.length > m) m = v.length; }); if (m > 60) c.cls = 'lw'; else if (m <= 16) c.cls = 'sw'; });
    var prev = U.DT[id];
    U.DT[id] = { rows: rows, cols: cols, opt: opt, q: prev ? prev.q : '', sort: prev ? prev.sort : opt.sort || null, lim: opt.lim || PAGE };
    var b = body(id);
    return '<div class="dt card" data-dt="' + id + '">' +
      (opt.title || !opt.bare ? '<div class="dt-bar">' + (opt.title ? '<b>' + opt.title + '</b>' : '') + '<span class="muted small dt-n">' + U.nf(b.n, 0) + ' sətir</span>' +
        '<span class="dt-tools">' + (rows.length > 8 ? '<input type="search" class="dt-q" placeholder="süz…" value="' + U.esc(U.DT[id].q) + '" aria-label="Cədvəli süz">' : '') +
        '<button type="button" class="btn sm ghost dt-csv" title="CSV kimi yüklə">CSV</button><button type="button" class="btn sm ghost dt-xlsx" title="Excel kimi yüklə">Excel</button></span></div>' : '') +
      (opt.note ? '<p class="small muted dt-note">' + opt.note + '</p>' : '') +
      '<div class="itbl-wrap"' + (opt.maxh != null ? ' style="max-height:' + (opt.maxh ? opt.maxh + 'px' : 'none') + '"' : '') + '><table class="itbl dtt"><thead><tr>' + cols.map(function (c) {
        var s = U.DT[id].sort, on = s && s[0] === c.k;
        return '<th class="' + (c.n ? '' : 'l') + ' sortable" data-k="' + U.esc(c.k) + '"' + (c.t ? ' title="' + U.esc(c.t) + '"' : '') + '>' + U.esc(c.l) + (on ? (s[1] > 0 ? ' ▲' : ' ▼') : '') + '</th>'; }).join('') +
      '</tr></thead><tbody>' + b.h + '</tbody></table></div>' +
      '<div class="dt-more"' + (b.more ? '' : ' hidden') + '><button type="button" class="btn sm dt-mo">Daha çox göstər</button> <button type="button" class="btn sm ghost dt-all">Hamısını göstər</button></div></div>';
  };
  function rerender(box) {
    var id = box.getAttribute('data-dt'), b = body(id);
    U.$('tbody', box).innerHTML = b.h; var n = U.$('.dt-n', box); if (n) n.textContent = U.nf(b.n, 0) + ' sətir';
    U.$('.dt-more', box).hidden = !b.more;
    U.$$('th.sortable', box).forEach(function (th) { var k = th.getAttribute('data-k'), s = U.DT[id].sort, c = U.DT[id].cols.filter(function (x) { return x.k === k; })[0]; th.innerHTML = U.esc(c.l) + (s && s[0] === k ? (s[1] > 0 ? ' ▲' : ' ▼') : ''); });
  }
  U.dtRows = function (id) {
    var T = U.DT[id]; if (!T) return [];
    return [T.cols.map(function (c) { return c.l; })].concat(view(id).map(function (r) { return T.cols.map(function (c) { return c.csv ? c.csv(r[c.k], r) : txt(c, r[c.k]); }); }));
  };
  U.dtBind = function (root) {
    root.addEventListener('click', function (e) {
      var box = e.target.closest('[data-dt]'); if (!box) return;
      var id = box.getAttribute('data-dt'), T = U.DT[id]; if (!T) return;
      var th = e.target.closest('th.sortable');
      if (th) { var k = th.getAttribute('data-k'); T.sort = T.sort && T.sort[0] === k ? (T.sort[1] > 0 ? [k, -1] : null) : [k, 1]; rerender(box); return; }
      if (e.target.closest('.dt-csv')) { U.download((T.opt.file || id) + '.csv', new Blob([U.csvOf(U.dtRows(id))], { type: 'text/csv' })); return; }
      if (e.target.closest('.dt-xlsx')) { U.download((T.opt.file || id) + '.xlsx', U.xlsx([{ name: (T.opt.sheet || T.opt.file || id).slice(0, 31), rows: U.dtRows(id) }])); return; }
      if (e.target.closest('.dt-mo')) { T.lim += PAGE * 2; rerender(box); return; }
      if (e.target.closest('.dt-all')) { T.lim = 1e9; rerender(box); return; }
      var tr = e.target.closest('tr[data-i]');
      if (tr && !e.target.closest('a,button,input,select')) {
        var r = T.cur[+tr.getAttribute('data-i')];
        if (T.opt.onRow) T.opt.onRow(r, tr); else if (tr.getAttribute('data-href')) location.hash = tr.getAttribute('data-href');
      }
    });
    root.addEventListener('input', U.debounce(function (e) {
      var q = e.target.closest && e.target.closest('.dt-q'); if (!q) return;
      var box = q.closest('[data-dt]'), T = U.DT[box.getAttribute('data-dt')]; T.q = q.value; T.lim = T.opt.lim || PAGE; rerender(box);
    }, 180));
  };
  U.csvOf = function (rows) {
    return '﻿' + rows.map(function (r) { return r.map(function (x) { var t = x == null ? '' : U.isNum(x) ? String(x).replace('.', ',') : String(x); return /[";\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t; }).join(';'); }).join('\r\n');
  };
  U.download = function (name, blob) {
    if (blob && typeof blob.then === 'function') return blob.then(function (b) { U.download(name, b); }, function (e) { U.toast('Xəta: ' + e.message); });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 800);
  };
  /* key–value list */
  U.kv = function (pairs) { return '<table class="itbl kv"><tbody>' + pairs.filter(function (p) { return p && p[1] != null && p[1] !== ''; }).map(function (p) { return '<tr><td class="lab">' + U.esc(p[0]) + '</td><td style="white-space:normal">' + p[1] + '</td></tr>'; }).join('') + '</tbody></table>'; };
})();
