/* p_scal.js — Miqyaslanma explorer: pick a risk factor (S0) and a shock size (slider over the S1 σ-grid + today's live
   deviation) → impact on every headline variable 2026–2030 (chart + full table), the response curve, elasticities (S2)
   and non-linearity (S3); «Canlı hesabla» runs /scalability/run for any size. Impact map, parameters, cross-model:
   p_scal2.js. */
(function () {
  'use strict';
  var U = window.U;
  var SC = U.SC = { f: null, k: 1, t: 'ru:nonoil_g', y: 2027 };
  U.factorSel = function (id, cur) { return U.sel(id, U.T('S0_factor_sigma').map(function (f) { return [f.amil, f.amil_ad + ' (' + f.risk_idler + ')']; }), cur); };
  function fac() { return U.T('S0_factor_sigma').filter(function (f) { return f.amil === SC.f; })[0] || U.T('S0_factor_sigma')[0]; }
  function grid(f) {
    var s1 = U.T('S1_scalability_grid').filter(function (r) { return r.amil === f.amil; });
    var ks = U.uniq(s1.filter(function (r) { return r.variant !== 'canlı'; }).map(function (r) { return r.k_sigma; })).sort(function (a, b) { return a - b; });
    var live = s1.filter(function (r) { return r.variant === 'canlı'; }), lk = live.length ? live[0].k_sigma : null;
    return { s1: s1, ks: ks, live: live, lk: lk };
  }
  function at(G, k, isLive) { return G.s1.filter(function (r) { return isLive ? r.variant === 'canlı' : r.variant !== 'canlı' && r.k_sigma === k; }); }
  function body(el) {
    var f = fac(), G = grid(f), isLive = SC.k === 'live', k = isLive ? G.lk : +SC.k, rows = at(G, k, isLive), r0 = rows[0] || {};
    if (!isLive && G.ks.indexOf(k) < 0) { k = 1; SC.k = 1; rows = at(G, 1, false); r0 = rows[0] || {}; }
    var ki = G.ks.indexOf(k), wide = {};
    rows.forEach(function (r) { var w = wide[r.hedef_id] = wide[r.hedef_id] || { hedef_id: r.hedef_id, hedef_ad: r.hedef_ad, vahid: r.vahid }; w['d' + r.il] = r.delta; w['p' + r.il] = r.delta_pct; w['b' + r.il] = r.baza; if (r.qeyd) w.qeyd = r.qeyd; });
    var W = Object.keys(wide).map(function (k2) { return wide[k2]; }), head = W.filter(function (w) { return U.HEADT.indexOf(w.hedef_id) >= 0; });
    el.innerHTML = '<div class="card pad"><div class="ctl"><label>Şokun ölçüsü' + U.help('S1 şəbəkəsi: ±0,5; ±1; ±2; ±3 σ və bugünkü canlı sapma. İstənilən ölçü üçün «Canlı hesabla».') + '</label>' +
      '<input type="range" id="sc-k" min="0" max="' + (G.ks.length - 1) + '" step="1" value="' + (isLive ? G.ks.indexOf(1) : ki) + '"' + (isLive ? ' disabled' : '') + '>' +
      '<b class="tnum" style="font-size:18px">' + (isLive ? 'bu gün: ' : '') + U.sg(k, 2) + 'σ = ' + U.sg(r0.olcu, 2) + ' ' + U.esc(r0.olcu_vahidi || f.vahid) + '</b>' +
      (G.lk != null ? '<button class="btn sm' + (isLive ? ' pri' : '') + '" id="sc-live">Bugünkü canlı sapma (' + U.sg(G.lk, 2) + 'σ)</button>' : '<span class="small muted">bu amil üçün canlı sapma yoxdur</span>') + '</div>' +
      '<p class="small muted" style="margin:4px 0 0">' + U.esc(f.amil_ad) + ': 1σ = ' + U.nf(f.olcu_1sigma) + ' ' + U.esc(f.vahid) + ' · ' + U.esc(f.sigma_esasi) + ' · ötürmə: ' + U.esc(f.oturme_kanali) + ' · pis istiqamət: ' + U.esc(f.pis_istiqamet) + (f.canli_tesvir ? ' · bu gün: ' + U.esc(f.canli_tesvir) : '') + '</p></div>' +
      '<div class="cols2"><div class="card pad"><h3>Baş göstəricilərə təsir, 2026–2030 (bazadan fərq)</h3><div id="sc-p" class="ch"></div></div><div class="card pad"><h3>Cavab əyrisi: ' + SC.y + '</h3><div id="sc-c" class="ch"></div></div></div>' +
      U.dt('sc-t', W, [{ k: 'hedef_ad', l: 'Göstərici' }, { k: 'vahid', l: 'Vahid' }].concat(U.YEARS.map(function (y) { return { k: 'd' + y, l: 'Fərq ' + y, n: 1 }; }), U.YEARS.slice(1, 2).map(function (y) { return { k: 'b' + y, l: 'Baza ' + y, n: 1 }; }), U.YEARS.map(function (y) { return { k: 'p' + y, l: '% ' + y, n: 1, d: 2 }; }), [{ k: 'qeyd', l: 'Qeyd' }]),
        { title: 'Bütün göstəricilər (S1): ' + U.esc(f.amil_ad) + ', ' + U.sg(k, 2) + 'σ', file: 'S1_' + f.amil + '_' + k, onRow: function (r) { SC.t = r.hedef_id; body(el); } }) +
      '<div class="card pad" id="sc-live-box"><h3>Canlı hesabla — istənilən ölçü</h3><div class="ctl"><label>Ölçü<input class="num" id="sc-sz" value="' + U.esc(String(U.nf(k, 2))) + '"></label>' + U.seg('sc-un', [['k', 'σ vahidində'], ['size', 'təbii vahiddə (' + f.vahid + ')']], 'k') +
      '<button class="btn pri" id="sc-run">' + U.icon('play', 14) + ' Canlı hesabla</button></div><div id="sc-res"></div></div><div id="sc-more"></div>';
    var hs = head.slice(0, 6);
    U.lines(U.$('#sc-p', el), hs.map(function (w, i) { return { x: U.YEARS, y: U.YEARS.map(function (y) { return w['d' + y]; }), name: w.hedef_ad + ' (' + w.vahid + ')', mode: 'lines+markers', c: U.PAL[i] }; }), 'bazadan fərq', { years: true, zero: true });
    U.curve(U.$('#sc-c', el), f.amil, U.uniq([SC.t].concat(U.HEADT.slice(0, 3))), SC.y);
    U.SC2.more(U.$('#sc-more', el), f, k);
    U.$('#sc-k', el).oninput = function (e) { SC.k = G.ks[+e.target.value]; body(el); };
    var lb = U.$('#sc-live', el); if (lb) lb.onclick = function () { SC.k = isLive ? 1 : 'live'; body(el); };
    var un = 'k'; U.$('#sc-un', el).onclick = function (e) { var b = e.target.closest('[data-v]'); if (!b) return; un = b.getAttribute('data-v'); U.$$('#sc-un button', el).forEach(function (x) { x.classList.toggle('on', x === b); }); };
    U.$('#sc-run', el).onclick = function () { U.SC2.run(U.$('#sc-res', el), f, U.parseNum(U.$('#sc-sz', el).value), un); };
  }
  U.pages.miqyas = function (v, p) {
    var sub = p[1] || '', q = U.HQ.get('f');
    if (q) SC.f = q;
    if (!SC.f) SC.f = 'brent';
    v.innerHTML = U.head('Risk miqyaslanmasının dinamik modeli', 'Miqyaslanma', 'Risk amili X qədər dəyişsə, hansı dəyişənlər, hansı ölçüdə və hansı parametrlər vasitəsilə təsirlənir? Şok MikroUnit zəncirinə (FR1 → FR3 → FR4 → FR5 → FR10 → FR12) struktur yolla verilir; nəticə bazadan fərqdir — yeni mərkəzi proqnoz deyil.') +
      U.subtabs('miqyas', [['', 'Amil və ölçü'], ['xerite', 'Təsir xəritəsi (S4)'], ['parametr', 'Parametrlər (S5)'], ['model', 'Modellər arası (S6, C5)']], sub) +
      '<div class="toolbar"><label class="small"><b>Amil</b></label>' + U.factorSel('sc-f', SC.f) + '</div><div id="sc-body"></div>';
    var b = U.$('#sc-body', v), go = function () { if (sub === 'xerite') U.SC2.map(b); else if (sub === 'parametr') U.SC2.params(b); else if (sub === 'model') U.SC2.models(b); else body(b); };
    U.need(sub === 'xerite' ? ['s4'] : sub === 'model' ? ['scal'] : sub === 'parametr' ? ['scal'] : ['s1', 's2', 'scal'], b, go);
    U.$('#sc-f', v).onchange = function (e) { SC.f = e.target.value; SC.k = 1; go(); };
  };
})();
