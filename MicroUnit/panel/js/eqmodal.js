/* eqmodal.js — the FULL regression output of one equation in a dialog: coefficients, fit, diagnostics, difference
   form, restrictions, robustness, hold-out, notes and the plain-text summary (copy button). Charts: eqcharts.js. */
(function () {
  'use strict';
  var U = window.U;
  function kv(rows) {
    return '<table class="itbl kv"><tbody>' + rows.filter(Boolean).map(function (r) { return '<tr><td class="lab">' + r[0] + '</td><td class="n">' + r[1] + '</td></tr>'; }).join('') + '</tbody></table>';
  }
  function val(v, d, p) {
    if (v && typeof v === 'object' && v.x) return '<span class="muted" title="' + U.esc(v.x) + '">tətbiq olunmur ⓘ</span>';
    return p ? U.pf(v) : (U.isNum(v) ? U.nf(v, d == null ? 3 : d) : '—');
  }
  function pcol(p) { return U.isNum(p) ? (p < 0.05 ? ' class="n up"' : ' class="n"') : ' class="n"'; }
  function coefTable(e) {
    var h = '<table class="itbl"><thead><tr><th class="l">İzahedici dəyişən</th><th>Əmsal</th><th>Standart xəta</th><th>t-statistikası</th><th>p-dəyəri</th><th>95 % etibarlılıq intervalı</th><th>Proqnozda</th><th class="l">Qeyd</th></tr></thead><tbody>';
    e.co.forEach(function (c) {
      var notes = [];
      if (c.fx) notes.push('<span class="chip warn">sabitlənib (məhdudiyyət)</span>');
      if (c.r === 'dols_aug') notes.push('<span class="chip">DOLS köməkçi hədd</span>');
      if (c.ed) notes.push('<span class="chip coef">ssenaridə dəyişdirilə bilər</span>');
      h += '<tr' + (c.r === 'dols_aug' ? ' class="sub"' : '') + '><td class="lab">' + U.esc(c.l || c.n) + '<span class="u">' + U.esc(c.n) + '</span></td><td class="n"><b>' + U.sig(c.c) + '</b></td><td class="n">' + U.sig(c.se) + '</td>' +
        '<td class="n">' + val(c.t, 2) + '</td><td' + pcol(c.p) + '>' + U.pf(c.p) + '</td><td class="n">' + (U.isNum(c.lo) ? '[' + U.sig(c.lo) + '; ' + U.sig(c.hi) + ']' : '—') + '</td>' +
        '<td class="n">' + (c.u == null ? '—' : U.sig(c.u)) + '</td><td class="lab small">' + notes.join(' ') + '</td></tr>';
    });
    return h + '</tbody></table>';
  }
  function fitBlock(e) {
    var f = e.fit || {};
    return kv([['Determinasiya əmsalı (R²)', val(f.r2, 4)], ['Düzəldilmiş R²', val(f.r2a, 4)], f.r2l != null ? ['R² (səviyyə qalığı üzrə)', val(f.r2l, 4)] : null,
      ['Reqressiyanın standart xətası', val(f.ser, 4)], ['Log-həqiqətəbənzərlik', val(f.ll, 2)], ['AIC / BIC', val(f.aic, 2) + ' / ' + val(f.bic, 2)],
      ['F-statistikası' + (f.Ft ? ' <span class="u">' + U.esc(f.Ft) + '</span>' : ''), val(f.F, 2) + ' (p ' + val(f.Fp, 3, 1) + ')'],
      ['Müşahidələr (n) / parametrlər (k)', ((e.smp || {}).n || '—') + ' / ' + ((e.smp || {}).k || '—')], ['Nümunə', ((e.smp || {}).start || '') + '–' + ((e.smp || {}).end || '')]]);
  }
  function diagBlock(e) {
    var g = e.dg || {};
    return kv([['Durbin–Watson', val(g.dw, 3)], g.dwl != null ? ['Durbin–Watson (səviyyə qalığı)', val(g.dwl, 3)] : null,
      ['Avtokorrelyasiya (Breusch–Godfrey), p', val(g.bg, 3, 1)], ['Normallıq (Jarque–Bera), p', val(g.jb, 3, 1)],
      ['Heteroskedastiklik (White), p', val(g.wh, 3, 1)], ['Heteroskedastiklik (Breusch–Pagan), p', val(g.bp, 3, 1)],
      ['Funksional forma (RESET), p', val(g.reset, 3, 1)], ['VIF (maks.)', val(g.vif, 2)], ['Şərt ədədi', val(g.cond, 1)],
      ['Kointeqrasiya (Engle–Granger), p', val(g.egp, 3, 1) + (g.egt ? ' <span class="u">' + (g.egt === 'ct' ? 'sabit + trend' : 'sabit') + '</span>' : '')],
      ['EG statistikası', val(g.egs, 3)], ['Kointeqrasiya müəyyən edilib', g.ce === true ? '<b class="up">bəli</b>' : g.ce === false ? '<b class="down">xeyr</b>' : '—']]);
  }
  function dfBlock(e) {
    var d = e.df; if (!d || !d.c) return '';
    var ks = Object.keys(d.c);
    return '<h4>Fərq forması və uyğunluq</h4><p class="small muted">Eyni tənlik birinci fərqlərdə: səviyyə əmsalı fərq formasının 95 % intervalına düşürsə, iki forma uyğundur. ' +
      'Hökm: ' + (d.ok === true ? '<b class="up">uyğundur</b>' : d.ok === false ? '<b class="down">uyğun deyil</b>' : '—') + '</p>' +
      '<table class="itbl"><thead><tr><th class="l">Dəyişən</th><th>Səviyyə əmsalı</th><th>Fərq forması</th><th>95 % interval</th><th>Uyğun</th></tr></thead><tbody>' +
      ks.map(function (k) { var ci = (d.ci || {})[k] || [], lv = (d.lv || {})[k], out = (d.out || []).indexOf(k) >= 0;
        return '<tr><td class="lab">' + U.esc(k) + '</td><td class="n">' + U.sig(lv) + '</td><td class="n">' + U.sig(d.c[k]) + '</td><td class="n">[' + U.sig(ci[0]) + '; ' + U.sig(ci[1]) + ']</td><td>' + (out ? '<span class="chip bad">intervaldan kənar</span>' : '<span class="chip acc">daxilində</span>') + '</td></tr>'; }).join('') + '</tbody></table>';
  }
  function rsBlock(e) {
    if (!e.rs || !e.rs.length) return '';
    return '<h4>Məhdudiyyətlər və onların testi</h4><table class="itbl"><thead><tr><th class="l">Məhdudiyyət</th><th class="l">Test</th><th>Statistika</th><th>p-dəyəri</th><th>Tətbiq edilib</th></tr></thead><tbody>' +
      e.rs.map(function (r) { return '<tr><td class="lab" style="white-space:normal">' + U.esc(r.t) + '</td><td class="small">' + U.esc(r.test || '—') + '</td><td class="n">' + val(r.stat, 3) + '</td><td class="n">' + U.pf(r.p) + '</td><td>' + (r.imp ? '<span class="chip warn">bəli</span>' : '<span class="chip">xeyr</span>') + '</td></tr>'; }).join('') + '</tbody></table>';
  }
  function robBlock(e) {
    var r = e.rb || {}, h = '<h4>Dayanıqlıq</h4><p>' + U.vchip(r.v) + ' <span class="small">' + U.esc(r.nt || '') + '</span></p>';
    if (r.chow && r.chow.length) h += '<table class="itbl"><thead><tr><th class="l">Struktur qırılma (Chow)</th><th>İl</th><th>F</th><th>p-dəyəri</th></tr></thead><tbody>' +
      r.chow.map(function (c) { return '<tr><td class="lab">' + U.esc(c.l || '') + '</td><td class="n">' + (c.y || '—') + '</td><td class="n">' + val(c.f, 2) + '</td><td class="n">' + (U.isNum(c.p) ? U.pf(c.p) : '<span class="muted" title="' + U.esc(c.x || '') + '">mümkün deyil ⓘ</span>') + '</td></tr>'; }).join('') + '</tbody></table>';
    h += '<p class="small">CUSUM testi, p-dəyəri: <b>' + U.pf(r.cusum) + '</b></p>';
    if (r.loo) {
      var full = {}; e.co.forEach(function (c) { full[c.n] = c.c; });
      h += '<table class="itbl"><thead><tr><th class="l">Bir ili çıxarmaqla: əmsalın aralığı</th><th>Tam nümunə</th><th>Minimum</th><th>Maksimum</th><th>İşarə</th></tr></thead><tbody>' +
        Object.keys(r.loo).map(function (k) { var a = r.loo[k] || []; var same = U.isNum(a[0]) && a[0] * a[1] > 0;
          return '<tr><td class="lab">' + U.esc(k) + '</td><td class="n">' + U.sig(full[k]) + '</td><td class="n">' + U.sig(a[0]) + '</td><td class="n">' + U.sig(a[1]) + '</td><td>' + (same ? '<span class="chip acc">saxlanılır</span>' : '<span class="chip bad">dəyişir</span>') + '</td></tr>'; }).join('') + '</tbody></table>';
    }
    if (r.rec && r.rec.y) h += '<div class="toolbar" style="margin:10px 0 0"><label class="small muted">Rekursiv qiymətləndirmə (genişlənən pəncərə):</label><select id="eq-rc" class="btn sm">' +
      Object.keys(r.rec.c || {}).map(function (k) { return U.opt(k, k); }).join('') + '</select></div><div id="eq-rec"></div>';
    return h;
  }
  function hoBlock(e) {
    var o = e.ho; if (!o) return '<h4>Nümunədən kənar yoxlama</h4><p class="small muted">Bu tənlik üçün ayrıca nümunədən kənar yoxlama aparılmayıb.</p>';
    return '<h4>Nümunədən kənar yoxlama</h4>' + kv([['Kəsim ili / yoxlama illəri', (o.cut || '—') + ' / ' + (o.y ? o.y[0] + '–' + o.y[o.y.length - 1] : '—')],
      ['RMSE' + (o.un ? ' <span class="u">' + U.esc(o.un) + '</span>' : ''), val(o.rmse, 3)], ['Theil U — təsadüfi gəzişməyə qarşı', val(o.urw, 3)],
      ['Theil U — sabit artıma qarşı', val(o.uc, 3)], ['Diebold–Mariano p (təsadüfi gəzişmə / sabit artım)', U.pf(o.dm) + ' / ' + U.pf(o.dmc)]]) +
      (o.md ? '<p class="small muted">' + U.esc(o.md) + (o.bm ? ' · etalonlar: ' + U.esc(o.bm) : '') + '</p>' : '');
  }
  function body(e) {
    var sm = e.smp || {};
    return '<div class="eyebrow">' + e.f + ' · ' + U.esc(e.st || '') + '</div><h2 class="mh">' + U.esc(e.t) + '</h2>' +
      '<p class="small">' + U.vchip(e.rb && e.rb.v) + ' ' + U.uchip(e) + (e.syn ? ' <span class="chip bad">SİNTETİK MƏLUMAT</span>' : '') + ' <code>' + U.esc(e.id) + '</code></p>' +
      kv([['Asılı dəyişən', U.esc(e.dep.l || '') + ' <span class="u">' + U.esc(e.dep.c || '') + '</span>'], ['Qiymətləndirmə üsulu', U.esc(e.est)], ['Kovariasiya', U.esc(e.cov || '—')],
        ['Nümunə', (sm.start || '') + '–' + (sm.end || '') + ', n = ' + (sm.n || '—')],
        ['Komponentlər', (e.comp || []).map(function (c) { var s = U.byId[c]; return s ? '<a href="' + U.href(s) + '">' + U.esc(s.e) + '</a>' : U.esc(c); }).join(', ') || '—']]) +
      '<h4>Reqressiya nəticəsi</h4><div class="itbl-wrap">' + coefTable(e) + '</div>' +
      '<div class="grid g2w" style="margin-top:12px"><div><h4>Uyğunluq statistikası</h4>' + fitBlock(e) + '</div><div><h4>Diaqnostika</h4>' + diagBlock(e) + '</div></div>' +
      dfBlock(e) + rsBlock(e) + robBlock(e) +
      '<h4>Faktiki və qiymətləndirilmiş dəyərlər</h4><div id="eq-fit"></div><div id="eq-res"></div>' + hoBlock(e) +
      (e.nt ? '<h4>Qeydlər</h4><p class="small">' + U.esc(e.nt) + '</p>' : '') +
      '<h4>Mətn şəklində reqressiya nəticəsi <button type="button" class="btn sm" id="eq-copy">Kopyala</button></h4><pre class="eqtxt" id="eq-txt">' + U.esc(e.sum || '') + '</pre>';
  }
  U.openEq = function (id, onClose) {
    var b = U.openModal('<div class="muted">Tənlik yüklənir…</div>', onClose);
    U.eqFull(id).then(function (e) {
      if (!e) { b.innerHTML = '<p>Tənlik tapılmadı: ' + U.esc(id) + '</p>'; return; }
      b.innerHTML = body(e);
      if (U.eqCharts) U.eqCharts(e);
      U.$('#eq-copy').onclick = function () {
        var t = U.$('#eq-txt').textContent;
        (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(function () { U.toast('Mətn kopyalandı'); }, function () {
          var r = document.createRange(); r.selectNodeContents(U.$('#eq-txt')); var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r); U.toast('Mətn seçildi — Ctrl+C ilə kopyalayın'); });
      };
    }, function (err) { b.innerHTML = '<p>' + U.esc(err.message) + '</p>'; });
  };
})();
