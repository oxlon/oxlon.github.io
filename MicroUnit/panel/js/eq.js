/* eq.js — equation registry access: index (eqidx.js), full records loaded on demand (eq_frX.js), verdict chips,
   the compact performance strip shown under every component. */
(function () {
  'use strict';
  var U = window.U, M = window.MICRO;
  var EQI = (M.EQI && M.EQI.rows) || [];
  U.EQI = {};
  EQI.forEach(function (e) { U.EQI[e.id] = e; });
  U.eqRows = function (fr) { return EQI.filter(function (e) { return !fr || e.f === fr; }); };
  U.eqHdr = function (fr) { return ((M.EQI || {}).hdr || {})[fr] || {}; };
  U.VERD = { 'stabil': ['acc', 'stabil'], 'qismən stabil': ['warn', 'qismən stabil'], 'qeyri-stabil': ['bad', 'qeyri-stabil'] };
  U.vchip = function (v) {
    if (!v) return '<span class="chip" title="Dayanıqlıq testləri bu tənlik üçün tətbiq olunmur">hökm yoxdur</span>';
    var c = U.VERD[v] || ['', v];
    return '<span class="chip ' + c[0] + '" title="Dayanıqlıq hökmü: rekursiv, bir ili çıxarmaqla, Chow və CUSUM">' + U.esc(c[1]) + '</span>';
  };
  U.uchip = function (e) { return e.used ? '<span class="chip scen" title="Bu tənlik proqnozda istifadə olunur">proqnozda</span>' : '<span class="chip" title="Rədd edilmiş, variant və ya həssaslıq spesifikasiyası">variant</span>'; };
  /* full records of one module */
  U.eqLoad = function (fr) {
    var k = 'EQ_' + fr;
    if (M[k]) return Promise.resolve(M[k]);
    return U.loadScript('data/eq_' + fr.toLowerCase() + '.js').then(function () {
      (M[k] || []).forEach(function (e) { U.EQF = U.EQF || {}; U.EQF[e.id] = e; });
      return M[k] || [];
    });
  };
  U.eqFull = function (id) {
    var e = U.EQI[id]; if (!e) return Promise.reject(new Error('Tənlik tapılmadı: ' + id));
    return U.eqLoad(e.f).then(function () { return U.EQF[id]; });
  };
  /* equations of a component: catalog order, used ones first */
  U.eqOf = function (s) {
    var ids = (s.eq || []).filter(function (id) { return U.EQI[id]; });
    var l = ids.map(function (id) { return U.EQI[id]; });
    return l.filter(function (e) { return e.used; }).concat(l.filter(function (e) { return !e.used; }));
  };
  function num(v, d) { return U.isNum(v) ? U.nf(v, d) : '—'; }
  function u(v) { return !U.isNum(v) ? '—' : '<b class="' + (v < 1 ? 'up' : 'down') + '">' + U.nf(v, 2) + '</b>'; }
  U.strip = function (e) {
    return '<button type="button" class="eqstrip" data-eq="' + U.esc(e.id) + '" title="Tam reqressiya nəticəsini açmaq üçün klikləyin">' +
      '<span class="es-t"><b>' + U.esc(e.t) + '</b><small>' + U.esc(e.id) + ' · ' + U.esc(e.est) + '</small></span>' +
      '<span class="es-m"><i>R²</i>' + num(e.r2, 3) + '</span><span class="es-m"><i>düz. R²</i>' + num(e.r2a, 3) + '</span>' +
      '<span class="es-m"><i>n</i>' + (e.n == null ? '—' : e.n) + '</span><span class="es-m"><i>DW</i>' + num(e.dw, 2) + '</span>' +
      '<span class="es-m" title="Engle–Granger kointeqrasiya testinin p-dəyəri"><i>koint. p</i>' + U.pf(e.cp) + '</span>' +
      '<span class="es-m" title="Nümunədən kənar yoxlama: Theil U təsadüfi gəzişməyə qarşı (1-dən kiçik — model yaxşıdır)"><i>U (TG)</i>' + u(e.urw) + '</span>' +
      '<span class="es-m" title="Theil U sabit artıma qarşı"><i>U (SA)</i>' + u(e.uc) + '</span>' +
      '<span class="es-c">' + U.vchip(e.v) + U.uchip(e) + '</span></button>';
  };
  U.eqSection = function (s) {
    var l = U.eqOf(s);
    if (!l.length) return '<p class="small muted">Bu komponent birbaşa tənliklə deyil, eynilik, bölgü və ya kalibrlənmiş qayda ilə hesablanır (mənbə: ' + U.esc(s.src) + ').</p>';
    var used = l.filter(function (e) { return e.used; }), rest = l.filter(function (e) { return !e.used; });
    var h = '<div class="eqlist">' + (used.length ? used : l.slice(0, 1)).map(U.strip).join('') + '</div>';
    var more = used.length ? rest : rest.slice(1);
    if (more.length) h += '<details class="eqmore"><summary>Variantlar və rədd edilmiş spesifikasiyalar: ' + more.length + '</summary><div class="eqlist">' + more.map(U.strip).join('') + '</div></details>';
    return h;
  };
  /* delegate: any [data-eq] click opens the full regression output */
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-eq]');
    if (b && U.openEq) { ev.preventDefault(); U.openEq(b.getAttribute('data-eq')); }
  });
})();
