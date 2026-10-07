/* p_rep2.js — Hesabat qurucusu, part 2: global sections (KPI, validation, notes), the report model, the page (choices
   left, live preview right), templates (built-in + saved in this browser + JSON) and the exports: print → PDF, Excel
   (.xlsx: cover + one sheet per table), Word (.docx with chart PNGs) and CSV. Copied from the Risk paneli and adapted. */
(function () {
  'use strict';
  var U = window.U, R = U.REP, B = U.REPB;
  function tb(name, head, rows) { return { t: 'table', name: name, rows: [head].concat(rows) }; }
  var G = {
    kpi: function () { var st = null; try { st = JSON.parse(U.ls('policyPanel.kpi') || 'null'); } catch (e) { st = null; }
      var K = st && st.sel && st.sel.length >= 5 ? U.kpiRank(st).rows : U.T('P5_ranking');
      var out = [{ t: 'small', text: st && st.sel && st.sel.length >= 5 ? 'KPI seçimi: «KPI» bölməsində seçilmiş ' + st.sel.length + ' göstərici və çəkilər.' : 'KPI seçimi: standart (config/kpi.csv).' },
        tb('KPI reytinqi', ['Yer', 'Ssenari', 'Bal', 'Xərc, mln AZN', 'Bal / 1 mlrd AZN'], K.map(function (r) { return [r.rank, r.scenario_name, U.isNum(r.score) ? +r.score.toFixed(3) : '', U.isNum(r.cost_mln_azn) ? +r.cost_mln_azn.toFixed(0) : '', U.isNum(r.score_per_bn_azn) ? +r.score_per_bn_azn.toFixed(3) : '']; }))];
      if (R.charts) out.push({ t: 'chart', draw: function (el) { U.barH(el, K.map(function (r) { return r.scenario_name; }), K.map(function (r) { return r.score; }), 'çoxkriteriyalı bal (0–1)', { color: '#0E6F7C', h: 340 }); } });
      return out; },
    valid: function () { if (!window.POL.val) return []; return [{ t: 'small', text: 'NFR1: model ' + U.T('V_nfr1_events').length + ' tarixi siyasət hadisəsində faktla müqayisə edilib; tam sapma hesabatı — docs/Sapma_hesabati.md.' },
      tb('Tarixi validasiya — hökmlər', ['Hadisə', 'Tarix', 'Müqayisə', 'Uyğun', 'İstiqamət', 'Hökm'], U.T('V_nfr1_events').map(function (e) { return [e.event_name_az, e.event_date_az, e.n_comparisons, U.pct(e.share_ok, 0), U.pct(e.dir_hit_rate, 0), e.verdict_az]; }))]; },
    notes: function () { return R.notes ? [{ t: 'p', text: R.notes }] : []; }
  };
  var PER = ['summary', 'headline', 'macro', 'micro', 'sector', 'social', 'risk', 'mitig', 'methods'];
  U.repModel = function () {
    var st = U.META.stamp || {}, m = [{ t: 'title', text: R.title }, { t: 'small', text: 'MİİS §15.5.4 · Siyasət paneli · son hesablama ' + (st.date || '') + ' · MikroUnit vintajı ' + ((st.vintage || {}).micro_vintage || '—') + (R.author ? ' · ' + R.author : '') }];
    R.scen.forEach(function (sc) {
      if (!U.scen(sc)) return;
      var secs = PER.filter(function (k) { return R.sections.indexOf(k) >= 0; });
      if (!secs.length) return;
      m.push({ t: 'h1', text: U.sname(sc) });
      secs.forEach(function (k) { var b = B[k](sc); if (b.length) { m.push({ t: 'h2', text: (U.SECS.filter(function (s) { return s[0] === k; })[0] || [k, k])[1] }); m.push.apply(m, b); } });
    });
    ['kpi', 'valid', 'notes'].filter(function (k) { return R.sections.indexOf(k) >= 0; }).forEach(function (k) { var b = G[k](); if (b.length) { m.push({ t: 'h1', text: (U.SECS.filter(function (s) { return s[0] === k; })[0])[1] }); m.push.apply(m, b); } });
    return m;
  };
  function chk(attr, v, on, lab) { return '<label class="ck"><input type="checkbox" data-' + attr + '="' + U.esc(v) + '"' + (on ? ' checked' : '') + '> ' + U.esc(lab) + '</label>'; }
  function side() {
    var saved = []; try { saved = JSON.parse(U.ls('policyPanel.repTpl') || '[]'); } catch (e) { saved = []; }
    return '<div class="card pad rside"><h3>Şablon</h3><div class="toolbar" style="margin:4px 0"><button class="btn sm' + (R.tpl === 'rehberlik' ? ' pri' : '') + '" data-tpl="rehberlik">Rəhbərlik üçün qısa hesabat</button><button class="btn sm' + (R.tpl === 'analitik' ? ' pri' : '') + '" data-tpl="analitik">Analitik hesabat</button></div>' +
      (saved.length ? '<div class="chips">' + saved.map(function (s, i) { return '<span><button class="btn sm ghost" data-st="' + i + '">' + U.esc(s.title) + '</button><button class="btn sm ghost" data-sd="' + i + '" title="Sil">✕</button></span>'; }).join('') + '</div>' : '') +
      '<div class="form"><label>Başlıq<input id="rp-title" value="' + U.esc(R.title) + '"></label><label>Müəllif<input id="rp-au" value="' + U.esc(R.author) + '"></label></div>' +
      '<h3>Ssenarilər</h3><div class="chips" style="flex-direction:column;align-items:flex-start">' + U.official().map(function (s) { return chk('sc', s.id, R.scen.indexOf(s.id) >= 0, s.name); }).join('') + '</div>' +
      '<h3>Bölmələr</h3><div class="chips">' + U.SECS.map(function (s) { return chk('sec', s[0], R.sections.indexOf(s[0]) >= 0, s[1]); }).join('') + '</div>' +
      '<h3>Müddətlər</h3><div class="chips">' + U.HZ.map(function (h) { return chk('hz', h[0], R.hz.indexOf(h[0]) >= 0, h[1]); }).join('') + chk('ch', '1', R.charts, 'qrafiklər') + '</div>' +
      '<h3>Qeydlər</h3><div class="form"><textarea id="rp-notes" rows="4">' + U.esc(R.notes) + '</textarea></div>' +
      '<div class="toolbar"><button class="btn sm" id="rp-save">Şablonu saxla</button><button class="btn sm ghost" id="rp-exp">Şablon JSON</button><label class="btn sm ghost">JSON idxal<input type="file" id="rp-imp" accept=".json" hidden></label></div></div>';
  }
  function preview() {
    var m = U.repModel(), charts = [], h = '<div class="rdoc" id="rep-doc">';
    m.forEach(function (b, i) {
      if (b.t === 'title') h += '<div class="r-title">' + U.esc(b.text) + '</div>'; else if (b.t === 'small') h += '<p class="r-small">' + U.esc(b.text) + '</p>';
      else if (b.t === 'h1') h += '<h2 class="r-h1">' + U.esc(b.text) + '</h2>'; else if (b.t === 'h2') h += '<h3 class="r-h2">' + U.esc(b.text) + '</h3>'; else if (b.t === 'p') h += '<p>' + U.esc(b.text) + '</p>';
      else if (b.t === 'chart') { h += '<div class="r-chart" id="rch-' + i + '"></div>'; charts.push([i, b]); }
      else if (b.t === 'table') h += '<div class="itbl-wrap"><table class="rtbl"><thead><tr>' + b.rows[0].map(function (c) { return '<th>' + U.esc(c) + '</th>'; }).join('') + '</tr></thead><tbody>' + b.rows.slice(1).map(function (r) { return '<tr>' + r.map(function (c) { return U.isNum(c) ? '<td class="n">' + (c === Math.round(c) ? (c >= 1900 && c <= 2100 ? c : U.nf(c, 0)) : U.nf(c)) + '</td>' : '<td>' + U.esc(c) + '</td>'; }).join('') + '</tr>'; }).join('') + (b.rows.length < 2 ? '<tr><td class="muted">sətir yoxdur</td></tr>' : '') + '</tbody></table></div>';
    });
    return { html: h + '</div>', charts: charts, model: m };
  }
  function draw(v) { var p = preview(); U.$('#rep-prev', v).innerHTML = p.html; p.charts.forEach(function (c) { c[1].draw(U.$('#rch-' + c[0], v)); }); }
  function fname(ext) { return (R.title || 'hesabat').replace(/[^\wəöüğışçİƏÖÜĞIŞÇ\-]+/g, '_').slice(0, 60) + '_' + String((U.META.stamp || {}).date || '').slice(0, 10) + '.' + ext; }
  var X = U.REPX = {};
  X.xlsx = function () {
    var m = U.repModel(), used = {}, st = U.META.stamp || {}, sh = [{ name: 'Məlumat', rows: [['Hesabat', R.title], ['Son hesablama', st.date], ['MikroUnit vintajı', (st.vintage || {}).micro_vintage || ''], ['Müəllif', R.author], ['Ssenarilər', R.scen.map(U.sname).join('; ')], ['Bölmələr', R.sections.join(', ')], ['Mənbə', 'PolicyUnit/output, möhür ' + st.md5]].concat(m.filter(function (b) { return b.t === 'p' || b.t === 'small'; }).map(function (b) { return ['Mətn', b.text]; })), widths: [22, 120], freeze: 0 }];
    m.filter(function (b) { return b.t === 'table'; }).forEach(function (b) { var nm = b.name.replace(/[\[\]:*?\/\\]/g, ' ').slice(0, 28), k = nm, i = 2; while (used[k]) k = nm.slice(0, 26) + ' ' + i++; used[k] = 1; sh.push({ name: k, rows: b.rows, widths: b.rows[0].map(function (c, j) { return j < 2 ? 30 : 14; }) }); });
    return Promise.resolve(U.xlsx(sh));
  };
  X.csv = function () { var rows = [['Cədvəl', 'Sütunlar…']]; U.repModel().filter(function (b) { return b.t === 'table'; }).forEach(function (b) { b.rows.forEach(function (r, i) { rows.push([b.name + (i ? '' : ' (başlıq)')].concat(r)); }); }); return Promise.resolve(new Blob([U.csvOf(rows)], { type: 'text/csv' })); };
  X.docx = function () {
    var p = preview(), host = document.createElement('div'); host.style.cssText = 'position:absolute;left:-9999px;width:900px'; document.body.appendChild(host); host.innerHTML = p.html;
    var jobs = p.charts.map(function (c) { var el = host.querySelector('#rch-' + c[0]); c[1].draw(el); return window.Plotly && el.data ? window.Plotly.toImage(el, { format: 'png', width: 900, height: 360 }).catch(function () { return null; }) : Promise.resolve(null); });
    return Promise.all(jobs).then(function (imgs) {
      var k = 0, blocks = [];
      p.model.forEach(function (b) { if (b.t === 'chart') { var im = imgs[k++]; if (im) blocks.push({ t: 'img', png: U.dataUrlBytes(im), w: 900, h: 360 }); } else if (b.t === 'table') blocks.push({ t: 'table', rows: b.rows.map(function (r) { return r.map(function (c) { return c === '' ? '—' : c; }); }) }); else blocks.push(b); });
      host.remove();
      return U.docx(blocks, { title: R.title, author: R.author || 'Siyasət paneli' });
    });
  };
  X.save = function (kind) { U.toast('Fayl hazırlanır…'); return X[kind]().then(function (b) { U.download(fname(kind), b); U.toast(kind.toUpperCase() + ' faylı hazırdır'); }, function (e) { U.toast('Xəta: ' + e.message); }); };
  X.print = function () { var els = U.$$('#rep-prev .r-chart'); document.body.classList.add('print-report'); var done = function () { document.body.classList.remove('print-report'); window.removeEventListener('afterprint', done); els.forEach(function (el) { try { window.Plotly.relayout(el, { width: null, autosize: true }); } catch (e) { /* ignore */ } }); };
    window.addEventListener('afterprint', done); Promise.all(els.map(function (el) { return el.data ? window.Plotly.relayout(el, { width: 660, autosize: false }) : null; })).catch(function () { return null; }).then(function () { setTimeout(function () { window.print(); setTimeout(done, 1500); }, 60); }); };
  U.pages.hesabat = function (v) {
    v.innerHTML = U.head('NFR3 — qrafiklər, cədvəllər və qısa izahlar', 'Hesabat qurucusu', 'Siyasət təsiri hesabatı: şablonu seçin (və ya ssenariləri, bölmələri, müddətləri özünüz seçin) — sağda canlı görünüş. İxrac: PDF (brauzerin çap pəncərəsi), Excel, Word (qrafiklərlə), CSV.') +
      '<div class="toolbar"><button class="btn" id="rx-print">Çap / PDF</button><button class="btn pri" id="rx-xlsx">Excel (.xlsx)</button><button class="btn pri" id="rx-docx">Word (.docx)</button><button class="btn" id="rx-csv">CSV</button></div>' +
      '<div class="rep-layout"><div id="rep-side">' + side() + '</div><div class="card rprev" id="rep-prev"></div></div>';
    U.need(['eff', 'io', 'soc', 'risk', 'cmp', 'val'], U.$('#rep-prev', v), function () { draw(v); });
    var upd = function () { U.repSave(); draw(v); };
    v.onchange = function (e) { var t = e.target, d = t.dataset;
      var tog = function (arr, x) { var i = arr.indexOf(x); if (t.checked && i < 0) arr.push(x); if (!t.checked && i >= 0) arr.splice(i, 1); };
      if (d.sec) tog(R.sections, d.sec); else if (d.sc) tog(R.scen, d.sc); else if (d.hz) { tog(R.hz, d.hz); R.hz.sort(function (a, b) { return ['qısa', 'orta', 'uzun'].indexOf(a) - ['qısa', 'orta', 'uzun'].indexOf(b); }); } else if (d.ch) R.charts = t.checked;
      else if (t.id === 'rp-title') R.title = t.value; else if (t.id === 'rp-au') R.author = t.value; else if (t.id === 'rp-notes') R.notes = t.value;
      else if (t.id === 'rp-imp' && t.files[0]) { var fr = new FileReader(); fr.onload = function () { try { var j = JSON.parse(fr.result); Object.keys(j).forEach(function (k) { R[k] = j[k]; }); U.repSave(); U.route(true); } catch (er) { U.toast('JSON oxunmadı'); } }; fr.readAsText(t.files[0]); return; }
      R.tpl = ''; upd(); };
    v.onclick = function (e) { var t = e.target.closest('button'); if (!t) return; var saved = []; try { saved = JSON.parse(U.ls('policyPanel.repTpl') || '[]'); } catch (er) { saved = []; }
      if (t.dataset.tpl) { U.repApply(t.dataset.tpl); U.route(true); return; }
      if (t.dataset.st != null) { var s = saved[+t.dataset.st]; Object.keys(s).forEach(function (k) { R[k] = s[k]; }); U.repSave(); U.route(true); return; }
      if (t.dataset.sd != null) { saved.splice(+t.dataset.sd, 1); U.ls('policyPanel.repTpl', JSON.stringify(saved)); U.route(true); return; }
      var id = t.id;
      if (id === 'rp-save') { saved.push(JSON.parse(JSON.stringify(R))); U.ls('policyPanel.repTpl', JSON.stringify(saved)); U.toast('Şablon saxlanıldı'); U.route(true); }
      else if (id === 'rp-exp') U.download('hesabat_sablonu.json', new Blob([JSON.stringify(R, null, 1)], { type: 'application/json' }));
      else if (id === 'rx-print') X.print(); else if (id === 'rx-xlsx') X.save('xlsx'); else if (id === 'rx-docx') X.save('docx'); else if (id === 'rx-csv') X.save('csv');
    };
  };
})();
