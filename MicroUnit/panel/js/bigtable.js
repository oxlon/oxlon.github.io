/* bigtable.js — Proqnoz cədvəlləri: every component of every requirement in one filterable table (all scenarios),
   with CSV and Excel export of exactly the rows that pass the filters. */
(function () {
  'use strict';
  var U = window.U;
  var F = { fr: '', g: '', sc: '*', q: '', show: 'b', page: 0, imp: false }, PER = 150, ROWS = null;
  function all() {
    if (ROWS) return ROWS;
    ROWS = [];
    U.S.forEach(function (s) { U.scens(s).forEach(function (k) { ROWS.push({ s: s, k: k, t: U.fold([s.f, s.g, s.e, s.i, s.u].join(' ')) }); }); });
    return ROWS;
  }
  function filtered() {
    var w = U.fold(F.q.trim()).split(/\s+/).filter(Boolean);
    return all().filter(function (r) {
      return (!F.fr || r.s.f === F.fr) && (!F.g || r.s.g === F.g) && (F.sc === '*' || r.k === F.sc) && (!F.imp || r.s.im) &&
        w.every(function (x) { return r.t.indexOf(x) >= 0; });
    });
  }
  function exportRows(list) { return [U.HEAD].concat(list.map(function (r) { var s = r.s; return [s.f, s.i, s.g, s.e, s.u, U.SCN[r.k], U.b25(s, r.k)].concat(s.s[r.k], s.gr[r.k]); })); }
  U.pages.cedvel = function (v) {
    var frs = U.META.frs, groups = F.fr ? U.groups(F.fr) : [];
    if (F.g && groups.indexOf(F.g) < 0) F.g = '';
    var list = filtered(), pages = Math.max(1, Math.ceil(list.length / PER));
    if (F.page >= pages) F.page = 0;
    var vis = list.slice(F.page * PER, (F.page + 1) * PER), cols = F.show === 'b' ? ['l', 'g'] : [F.show];
    var h = '<div class="eyebrow">Açıq proqnoz</div><h1 class="h1" style="margin-top:4px">Proqnoz cədvəlləri, 2026–2030</h1>' +
      '<p class="lead">Altı tələbin hər komponenti — hər ssenari üçün ayrıca sətir, beş il, səviyyə və illik artım. Süzgəcdən keçən sətirlər CSV və Excel faylına yüklənir.</p>' +
      '<div class="toolbar"><input type="search" id="bt-q" placeholder="Axtar: komponent, qrup, vahid, id…" value="' + U.esc(F.q) + '">' +
      '<select id="bt-fr" class="btn sm">' + U.opt('', 'Bütün tələblər', F.fr) + frs.map(function (f) { return U.opt(f.c, f.c + ' · ' + f.t, F.fr); }).join('') + '</select>' +
      '<select id="bt-g" class="btn sm"' + (F.fr ? '' : ' disabled') + '>' + U.opt('', 'Bütün qruplar', F.g) + groups.map(function (g) { return U.opt(g, g, F.g); }).join('') + '</select>' +
      '<select id="bt-sc" class="btn sm">' + U.opt('*', 'Bütün ssenarilər', F.sc) + U.SC.map(function (k) { return U.opt(k, U.SCN[k], F.sc); }).join('') + '</select>' +
      U.seg('bt-show', [['l', 'Səviyyə'], ['g', 'İllik artım'], ['b', 'İkisi']], F.show) +
      '<label class="small"><input type="checkbox" id="bt-imp"' + (F.imp ? ' checked' : '') + '> yalnız doldurulmuş illəri olanlar</label>' +
      '<span style="margin-left:auto;display:flex;gap:8px"><button class="btn sm" id="bt-csv">CSV</button><button class="btn sm pri" id="bt-xlsx">Excel (.xlsx)</button></span></div>' +
      '<div class="small muted" style="margin-bottom:8px"><b class="tnum">' + U.nf(list.length, 0) + '</b> sətir (' + U.nf(all().length, 0) + ' cəmi) · səhifə ' + (F.page + 1) + ' / ' + pages + '</div>' +
      '<div class="card itbl-wrap"><table class="itbl"><thead><tr><th class="l">FR</th><th class="l">Komponent</th><th class="l">Vahid</th><th class="l">Ssenari</th><th>2025</th>';
    cols.forEach(function (c) { U.YEARS.forEach(function (y) { h += '<th class="fc">' + y + (c === 'g' ? '<span class="st">artım</span>' : '') + '</th>'; }); });
    h += '</tr></thead><tbody>';
    vis.forEach(function (r) {
      var s = r.s;
      h += '<tr data-id="' + U.esc(s.i) + '" class="click"><td>' + s.f + '</td><td class="lab">' + U.esc(s.e) + (s.im ? ' <span class="impdot" title="' + U.IMPLAB + '"></span>' : '') + '<div class="small muted">' + U.esc(s.g) + '</div></td>' +
        '<td class="small">' + U.esc(s.u) + '</td><td><span style="color:' + U.SCC[r.k] + ';font-weight:700">' + U.SCN[r.k] + '</span></td><td class="n">' + U.nf(U.b25(s, r.k), s.d) + '</td>';
      cols.forEach(function (c) {
        h += c === 'g' ? s.gr[r.k].map(function (x) { return '<td class="n fc dcell" style="' + U.heat(x, U.isRate(s) ? 1.5 : 8) + '">' + U.sg(x, U.gdec(s)) + '</td>'; }).join('')
          : s.s[r.k].map(function (x) { return '<td class="n fc">' + U.nf(x, s.d) + '</td>'; }).join('');
      });
      h += '</tr>';
    });
    h += '</tbody></table></div><div class="toolbar"><button class="btn sm" id="bt-prev"' + (F.page ? '' : ' disabled') + '>← Əvvəlki</button>' +
      '<button class="btn sm" id="bt-next"' + (F.page < pages - 1 ? '' : ' disabled') + '>Növbəti →</button><span class="small muted">Sətrə klikləyin — komponentin qrafiki, cədvəli və tənlikləri açılır. Artım: səviyyə göstəricilərində %, faiz və pay göstəricilərində faiz bəndi.</span></div>';
    v.innerHTML = h;
    var q = U.$('#bt-q'), re = function () { F.page = 0; U.route(true); };
    q.oninput = U.debounce(function () { F.q = q.value; var p = q.selectionStart; re(); var t = U.$('#bt-q'); t.focus(); t.setSelectionRange(p, p); }, 250);
    U.$('#bt-fr').onchange = function (e) { F.fr = e.target.value; F.g = ''; re(); };
    U.$('#bt-g').onchange = function (e) { F.g = e.target.value; re(); };
    U.$('#bt-sc').onchange = function (e) { F.sc = e.target.value; re(); };
    U.$('#bt-imp').onchange = function (e) { F.imp = e.target.checked; re(); };
    v.onclick = function (e) {
      var b = e.target.closest('#bt-show [data-v]'); if (b) { F.show = b.getAttribute('data-v'); U.route(true); return; }
      if (e.target.id === 'bt-prev') { F.page--; U.route(true); return; }
      if (e.target.id === 'bt-next') { F.page++; U.route(true); return; }
      if (e.target.id === 'bt-csv') { U.download('mikro_proqnoz_2026_2030.csv', new Blob([U.csvOf(exportRows(filtered()))], { type: 'text/csv' })); U.toast(U.nf(list.length, 0) + ' sətir CSV faylına yazıldı'); return; }
      if (e.target.id === 'bt-xlsx') { U.download('mikro_proqnoz_2026_2030.xlsx', U.xlsx([{ name: 'Proqnoz 2026-2030', rows: exportRows(filtered()), widths: [6, 26, 28, 40, 16, 9, 12] }])); U.toast(U.nf(list.length, 0) + ' sətir Excel faylına yazıldı'); return; }
      var tr = e.target.closest('tr[data-id]'); if (tr) location.hash = U.href(U.byId[tr.getAttribute('data-id')]);
    };
  };
})();
