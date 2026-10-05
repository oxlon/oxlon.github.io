/* bigtable.js — Proqnoz cədvəlləri: every forecast series of every requirement in one filterable table,
   with CSV and Excel export of exactly the rows that pass the filters. */
(function () {
  'use strict';
  var U = window.U;
  var F = { fr: '', g: '', sc: '', q: '', show: 'b', page: 0 }, PER = 150;
  var ROWS = null;
  function all() {
    if (ROWS) return ROWS;
    ROWS = [];
    U.S.forEach(function (s) { U.scens(s).forEach(function (k) { ROWS.push({ s: s, k: k, t: U.fold([s.f, s.g, s.e, s.v, s.u].join(' ')) }); }); });
    return ROWS;
  }
  function filtered() {
    var w = U.fold(F.q.trim()).split(/\s+/).filter(Boolean);
    var sc = F.sc || (U.scenRaw() === 'all' ? '' : U.scen());
    return all().filter(function (r) {
      return (!F.fr || r.s.f === F.fr) && (!F.g || r.s.g === F.g) && (!sc || r.k === sc) && w.every(function (x) { return r.t.indexOf(x) >= 0; });
    });
  }
  function opt(v, lab, on) { return '<option value="' + U.esc(v) + '"' + (v === on ? ' selected' : '') + '>' + U.esc(lab) + '</option>'; }
  function exportRows(list) {
    return [U.HEAD].concat(list.map(function (r) { var s = r.s; return [s.f, s.g, s.e, s.v, s.u, U.SCN[r.k], s.b].concat(s.s[r.k], s.gr[r.k]); }));
  }
  U.pages.cedvel = function (v) {
    var frs = window.MICRO.META.frs, groups = F.fr ? U.groups(F.fr) : [];
    if (F.g && groups.indexOf(F.g) < 0) F.g = '';
    var list = filtered(), pages = Math.max(1, Math.ceil(list.length / PER));
    if (F.page >= pages) F.page = 0;
    var vis = list.slice(F.page * PER, (F.page + 1) * PER), gl = F.show === 'g';
    var h = '<div class="eyebrow">Açıq proqnoz</div><h1 class="h1" style="margin-top:4px">Proqnoz cədvəlləri, 2026–2030</h1>' +
      '<p class="lead">Bütün modulların ixrac etdiyi hər proqnoz sırası — hər ssenari üçün ayrıca sətir, beş il, səviyyə və illik artım. Süzgəcdən keçən sətirlər CSV və Excel faylına yüklənir.</p>' +
      '<div class="toolbar"><input type="search" id="bt-q" placeholder="Axtar: göstərici, qrup, vahid…" value="' + U.esc(F.q) + '">' +
      '<select id="bt-fr" class="btn sm">' + opt('', 'Bütün tələblər') + frs.map(function (f) { return opt(f.c, f.c + ' · ' + f.t, F.fr); }).join('') + '</select>' +
      '<select id="bt-g" class="btn sm"' + (F.fr ? '' : ' disabled') + '>' + opt('', 'Bütün qruplar') + groups.map(function (g) { return opt(g, g, F.g); }).join('') + '</select>' +
      '<select id="bt-sc" class="btn sm">' + opt('', 'Ssenari: yuxarıdakı seçim') + U.SC.map(function (k) { return opt(k, U.SCN[k], F.sc); }).join('') + opt('*', 'Bütün ssenarilər', F.sc) + '</select>' +
      '<div class="seg" id="bt-show"><button data-v="l" class="' + (F.show === 'l' ? 'on' : '') + '">Səviyyə</button><button data-v="g" class="' + (gl ? 'on' : '') + '">İllik artım</button><button data-v="b" class="' + (F.show === 'b' ? 'on' : '') + '">İkisi</button></div>' +
      '<span style="margin-left:auto;display:flex;gap:8px"><button class="btn sm" id="bt-csv">CSV</button><button class="btn sm pri" id="bt-xlsx">Excel (.xlsx)</button></span></div>' +
      '<div class="small muted" style="margin-bottom:8px"><b class="tnum">' + U.nf(list.length, 0) + '</b> sətir (' + U.nf(all().length, 0) + ' cəmi) · səhifə ' + (F.page + 1) + ' / ' + pages + '</div>' +
      '<div class="card itbl-wrap"><table class="itbl"><thead><tr><th class="l">FR</th><th class="l">Göstərici</th><th class="l">Vahid</th><th class="l">Ssenari</th><th>2025</th>';
    var cols = F.show === 'b' ? ['l', 'g'] : [F.show];
    cols.forEach(function (c) { U.YEARS.forEach(function (y) { h += '<th class="fc">' + y + (c === 'g' ? '<span class="st">artım</span>' : '') + '</th>'; }); });
    h += '</tr></thead><tbody>';
    vis.forEach(function (r) {
      var s = r.s;
      h += '<tr data-n="' + s.n + '"><td>' + s.f + '</td><td class="lab">' + U.esc(s.e) + (s.v ? ' <span class="u">' + U.esc(s.v) + '</span>' : '') + '<div class="small muted">' + U.esc(s.g) + '</div></td>' +
        '<td class="small">' + U.esc(s.u) + '</td><td><span style="color:' + U.SCC[r.k] + ';font-weight:700">' + U.SCN[r.k] + '</span></td><td class="n">' + U.nf(s.b, s.d) + '</td>';
      cols.forEach(function (c) {
        h += c === 'g' ? s.gr[r.k].map(function (x) { return '<td class="n fc dcell" style="' + U.heat(x, s.k === 'rate' ? 1.5 : 8) + '">' + U.sg(x, U.gdec(s)) + '</td>'; }).join('')
          : s.s[r.k].map(function (x) { return '<td class="n fc">' + U.nf(x, s.d) + '</td>'; }).join('');
      });
      h += '</tr>';
    });
    h += '</tbody></table></div><div class="toolbar"><button class="btn sm" id="bt-prev"' + (F.page ? '' : ' disabled') + '>← Əvvəlki</button>' +
      '<button class="btn sm" id="bt-next"' + (F.page < pages - 1 ? '' : ' disabled') + '>Növbəti →</button><span class="small muted">Sətrə klikləyin — göstəricinin qrafiki açılır. Artım: səviyyə göstəricilərində %, faiz göstəricilərində faiz bəndi.</span></div>';
    v.innerHTML = h;
    var q = U.$('#bt-q');
    q.oninput = function () { F.q = q.value; F.page = 0; var p = q.selectionStart; U.route(true); var t = U.$('#bt-q'); t.focus(); t.setSelectionRange(p, p); };
    U.$('#bt-fr').onchange = function (e) { F.fr = e.target.value; F.g = ''; F.page = 0; U.route(true); };
    U.$('#bt-g').onchange = function (e) { F.g = e.target.value; F.page = 0; U.route(true); };
    U.$('#bt-sc').onchange = function (e) { F.sc = e.target.value === '*' ? '*' : e.target.value; F.page = 0; U.route(true); };
    v.onclick = function (e) {
      var b = e.target.closest('#bt-show [data-v]'); if (b) { F.show = b.getAttribute('data-v'); U.route(true); return; }
      if (e.target.id === 'bt-prev') { F.page--; U.route(true); return; }
      if (e.target.id === 'bt-next') { F.page++; U.route(true); return; }
      if (e.target.id === 'bt-csv') { U.download('mikro_proqnoz_2026_2030.csv', new Blob([U.csvOf(exportRows(filtered()))], { type: 'text/csv' })); U.toast(U.nf(list.length, 0) + ' sətir CSV faylına yazıldı'); return; }
      if (e.target.id === 'bt-xlsx') { U.download('mikro_proqnoz_2026_2030.xlsx', U.xlsx('Proqnoz 2026-2030', exportRows(filtered()), [6, 28, 40, 16, 16, 9, 12, 12, 12, 12, 12, 12, 10, 10, 10, 10, 10])); U.toast(U.nf(list.length, 0) + ' sətir Excel faylına yazıldı'); return; }
      var tr = e.target.closest('tr[data-n]'); if (tr) location.hash = '#/' + U.S[+tr.getAttribute('data-n')].f.toLowerCase() + '/s/' + tr.getAttribute('data-n');
    };
  };
  // '*' means all scenarios
  var _f = filtered;
  filtered = function () { if (F.sc === '*') { var keep = F.sc; F.sc = ''; var raw = U.scenRaw; U.scenRaw = function () { return 'all'; }; var r = _f(); U.scenRaw = raw; F.sc = keep; return r; } return _f(); };
})();
