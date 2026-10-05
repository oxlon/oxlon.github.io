/* report3.js — Hesabat qurucusu, part 3: exports of the report model — print-ready HTML (→ PDF via the browser),
   Excel (.xlsx: Məlumat, Proqnoz (uzun), Proqnoz (geniş), Tənliklər, Fərziyyələr), Word (.docx with chart PNGs) and CSV. */
(function () {
  'use strict';
  var U = window.U, R = U.R;
  var REP = U.REP = {};
  function fname(ext) { return (R.title || 'hesabat').replace(/[^\wəöüğışçİƏÖÜĞIŞÇ\-]+/g, '_').slice(0, 60) + '.' + ext; }
  REP.long = function (m) {
    var rows = [['FR', 'İdentifikator', 'Qrup', 'Komponent', 'Vahid', 'Ssenari', 'İl', 'Dəyər', 'Növ']];
    m.items.forEach(function (it) { var s = it.s; it.rows.forEach(function (r) { r.vals.forEach(function (c, i) { var y = m.years[i];
      rows.push([s.f, s.i, s.g, s.e, s.u, r.lab, y, U.isNum(c.v) ? c.v : null, y > 2025 ? 'proqnoz' : (c.imp ? 'doldurulmuş (interpolyasiya)' : (y === 2025 && s.nc ? 'cari qiymətləndirmə' : 'faktiki'))]); }); }); });
    return rows;
  };
  REP.wide = function (m) {
    var rows = [['FR', 'İdentifikator', 'Komponent', 'Vahid', 'Ssenari'].concat(m.years)];
    m.items.forEach(function (it) { var s = it.s; it.rows.forEach(function (r) { rows.push([s.f, s.i, s.e, s.u, r.lab].concat(r.vals.map(function (c) { return U.isNum(c.v) ? c.v : null; }))); }); });
    return rows;
  };
  REP.eqRows = function (m) {
    var rows = [['Komponent', 'Tənlik', 'Ad', 'Üsul', 'n', 'R²', 'Düzəldilmiş R²', 'DW', 'Kointeqrasiya p', 'Theil U (təsadüfi gəzişmə)', 'Theil U (sabit artım)', 'Dayanıqlıq hökmü', 'Uğursuz testlər']];
    m.items.forEach(function (it) { it.eqs.forEach(function (e) { rows.push([it.s.i, e.id, e.t, e.est, e.n, e.r2, e.r2a, e.dw, e.cp, e.urw, e.uc, e.v || '', e.ft || '']); }); });
    return rows;
  };
  REP.cover = function (m) {
    return [['Mikro Model — hesabat'], ['Başlıq', m.title], ['Tarix', m.date], ['Müəllif', R.author || ''], ['Tələblər', R.frs.join(', ')],
      ['Ssenarilər', m.cols.map(function (c) { return c.lab; }).join('; ')], ['İllər', R.y0 + '–' + R.y1], ['Komponentlər', m.items.length],
      ['Qeydlər', R.notes || ''], ['Mənbə', 'MicroUnit/output, möhür ' + U.META.stamp.md5 + ' (' + U.META.stamp.date + ')'],
      ['İzah', '2025-dən sonrakı illər proqnozdur. «Növ» sütunu: faktiki, cari qiymətləndirmə, doldurulmuş (interpolyasiya), proqnoz.']];
  };
  REP.xlsx = function () {
    var m = U.rModel(), sh = [{ name: 'Məlumat', rows: REP.cover(m), widths: [18, 90], hdr: 1, freeze: 0 },
      { name: 'Proqnoz (uzun)', rows: REP.long(m), widths: [6, 26, 30, 44, 16, 24, 6, 14, 22] },
      { name: 'Proqnoz (geniş)', rows: REP.wide(m), widths: [6, 26, 44, 16, 24].concat(m.years.map(function () { return 11; })) }];
    if (R.blocks.eq) sh.push({ name: 'Tənliklər', rows: REP.eqRows(m), widths: [24, 26, 50, 22, 6, 8, 8, 8, 10, 12, 12, 14, 40] });
    if (R.blocks.asm) sh.push({ name: 'Fərziyyələr', rows: [['Ssenari', 'Modul', 'Fərziyyə', 'Vahid'].concat(U.YEARS)].concat(U.rAssumptions()), widths: [24, 8, 50, 18, 11, 11, 11, 11, 11] });
    return Promise.resolve(U.xlsx(sh));
  };
  REP.csv = function () { return Promise.resolve(new Blob([U.csvOf(REP.long(U.rModel()))], { type: 'text/csv' })); };
  REP.docx = function () {
    var m = U.rModel(), blocks = [{ t: 'title', text: m.title }, { t: 'small', text: 'İqtisadiyyat Nazirliyi · Mikro Model (MİİS §15.5.2) · ' + m.date + (R.author ? ' · ' + R.author : '') },
      { t: 'p', text: 'Tələblər: ' + R.frs.join(', ') + '. Ssenarilər: ' + m.cols.map(function (c) { return c.lab; }).join(', ') + '. İllər: ' + R.y0 + '–' + R.y1 + '. 2025-dən sonrakı illər proqnozdur.' }];
    var jobs = [];
    if (R.blocks.chart && window.Plotly) {
      if (!U.$('#rch-0')) { var p = U.$('#rep-prev'); if (!p) { p = document.createElement('div'); p.id = 'rep-prev'; p.style.cssText = 'position:absolute;left:-9999px;width:900px'; document.body.appendChild(p); } p.innerHTML = U.rPreview(); U.rCharts(); }
      m.items.forEach(function (it, i) { var el = U.$('#rch-' + i); jobs.push(el && el.data ? window.Plotly.toImage(el, { format: 'png', width: 900, height: 380 }).catch(function () { return null; }) : Promise.resolve(null)); });
    }
    return Promise.all(jobs).then(function (imgs) {
      var lastF = null;
      m.items.forEach(function (it, i) {
        var s = it.s;
        if (s.f !== lastF) { lastF = s.f; blocks.push({ t: 'h1', text: s.f + ' — ' + U.frOf(s.f).full }); }
        blocks.push({ t: 'h2', text: s.e + ' (' + s.u + ')' });
        if (imgs[i]) blocks.push({ t: 'img', png: U.dataUrlBytes(imgs[i]), w: 900, h: 380 });
        if (R.blocks.tbl) blocks.push({ t: 'table', rows: [['Ssenari'].concat(m.years.map(String))].concat(it.rows.map(function (r) { return [r.lab].concat(r.vals.map(function (c) { return U.isNum(c.v) ? c.v : '—'; })); })) });
        if (R.blocks.eq && it.eqs.length) blocks.push({ t: 'table', rows: [['Tənlik', 'Üsul', 'n', 'R²', 'DW', 'Theil U', 'Dayanıqlıq']].concat(it.eqs.map(function (e) {
          return [e.t + ' (' + e.id + ')', e.est, e.n == null ? '—' : String(e.n), U.isNum(e.r2) ? U.nf(e.r2, 3) : '—', U.isNum(e.dw) ? U.nf(e.dw, 2) : '—', U.isNum(e.urw) ? U.nf(e.urw, 2) : '—', (e.v || '—') + (R.blocks.rob && e.ft ? ' — ' + e.ft : '')]; })) });
      });
      if (R.blocks.asm) { var a = U.rAssumptions(); if (a.length) { blocks.push({ t: 'h1', text: 'Fərziyyələr' }); blocks.push({ t: 'table', rows: [['Ssenari', 'Modul', 'Fərziyyə', 'Vahid'].concat(U.YEARS.map(String))].concat(a.map(function (r) { return r.map(function (x) { return x == null ? '' : x; }); })) }); } }
      if (R.blocks.notes && R.notes) { blocks.push({ t: 'h1', text: 'Qeydlər' }); R.notes.split(/\n+/).forEach(function (p) { blocks.push({ t: 'p', text: p }); }); }
      blocks.push({ t: 'small', text: 'Mənbə: modulların çıxış faylları, möhür ' + U.META.stamp.md5 + ' (' + U.META.stamp.date + ').' });
      return U.docx(blocks, { title: m.title, author: R.author });
    });
  };
  REP.save = function (kind) {
    U.toast('Fayl hazırlanır…');
    return REP[kind]().then(function (b) { U.download(fname(kind), b); U.toast(kind.toUpperCase() + ' faylı hazırdır'); }, function (e) { U.toast('Xəta: ' + e.message); });
  };
  REP.b64 = function (kind) { return REP[kind]().then(U.blobB64); };
  U.rPrint = function () {
    // charts are drawn for the (wider) screen preview; at A4/Letter width they would be clipped on the right
    var P = window.Plotly, els = [].slice.call(document.querySelectorAll('#rep-prev .r-chart')).filter(function (el) { return P && el.data && el.layout; });
    document.body.classList.add('print-report');
    var done = function () {
      document.body.classList.remove('print-report'); window.removeEventListener('afterprint', done);
      els.forEach(function (el) { try { P.relayout(el, { width: null, autosize: true }); } catch (e) { /* ignore */ } });
    };
    window.addEventListener('afterprint', done);
    Promise.all(els.map(function (el) { return P.relayout(el, { width: 660, autosize: false }); })).catch(function () { return null; }).then(function () {
      setTimeout(function () { window.print(); setTimeout(done, 1500); }, 60);
    });
  };
})();
