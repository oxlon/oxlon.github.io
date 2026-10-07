/* p_home.js — Başlanğıc: what the unit does, quick actions, KPI ranking infographic and one card per scenario with the
   headline effects (GDP, prices, unemployment, formal jobs, Gini, poverty, fiscal cost) short / medium / long term. */
(function () {
  'use strict';
  var U = window.U;
  /* headline rows of a card: [label, source, indicator/column, unit label] */
  U.CARD = [['Real ÜDM', 'p1', 'gdp_real'], ['Qiymət səviyyəsi (İQİ)', 'p1', 'cpi'], ['İşsizlik səviyyəsi', 'p1', 'unemp_rate'], ['Formal (muzdlu) iş yerləri', 'p1', 'employment_hired'],
    ['Gini (gəlir)', 'ms', 'gini', 'bənd'], ['Yoxsulluq səviyyəsi', 'ms', 'poverty_rate', 'f.b.'], ['Fiskal xərc (müddət üzrə cəm)', 'p1', 'fiscal_cost']];
  U.cardVal = function (sc, c, hz) {
    if (c[1] === 'p1') { var r = U.hl1(sc, c[2], hz); return r ? { v: r.effect, u: r.effect_unit, t: r.tier, e: r.source_engine } : null; }
    var m = U.msHz(sc, c[2]); return m && U.isNum(m[hz]) ? { v: m[hz], u: c[3], t: 'D', e: 'microsim' } : null;
  };
  U.egrid = function (sc) {
    return '<table class="egrid"><thead><tr><th>Göstərici (bazadan fərq)</th>' + U.HZ.map(function (h) { return '<th title="' + U.esc(h[2]) + '">' + U.esc(h[0]) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      U.CARD.map(function (c) {
        return '<tr><td>' + U.esc(c[0]) + (c[1] === 'ms' ? ' <span class="muted" title="mikrosimulyasiya — SİNTETİK məlumat">*</span>' : '') + '</td>' + U.HZ.map(function (h) {
          var x = U.cardVal(sc, c, h[0]); if (!x) return '<td class="muted">—</td>';
          var tn = U.tone(c[2], x.v); return '<td class="' + tn + '" title="' + U.esc((U.ENG[x.e] || x.e || '') + (x.t ? ' · sübut səviyyəsi ' + x.t : '')) + '">' + U.eff(x.v, x.u) + '</td>';
        }).join('') + '</tr>';
      }).join('') + '</tbody></table>';
  };
  /* one-sentence summary of a scenario (also used by the report builder) */
  U.story = function (sc) {
    var g = U.hl1(sc, 'gdp_real', 'qısa'), go = U.hl1(sc, 'gdp_real', 'orta'), p = U.hl1(sc, 'cpi', 'qısa'), u = U.hl1(sc, 'unemp_rate', 'qısa'), f = U.hl(sc, 'fiscal_cost').reduce(function (s, r) { return s + (U.isNum(r.effect) ? r.effect : 0); }, 0);
    var gi = U.msHz(sc, 'gini'), pv = U.msHz(sc, 'poverty_rate'), t = [];
    if (g) t.push('Real ÜDM qısa müddətdə bazadan ' + U.eff(g.effect, g.effect_unit) + (go ? ', orta müddətdə ' + U.eff(go.effect, go.effect_unit) : '') + ' fərqlənir');
    if (p) t.push('qiymət səviyyəsi ' + U.eff(p.effect, p.effect_unit));
    if (u) t.push('işsizlik ' + U.eff(u.effect, u.effect_unit));
    var s1 = t.length ? t.join(', ').replace(/\.$/, '') + '.' : 'Bu ssenari üçün makro nəticə yoxdur.';
    var s2 = (f ? ' Birbaşa fiskal xərc (bütün dövr) ' + U.nf(f, 0) + ' mln AZN.' : '') + (gi && U.isNum(gi['qısa']) ? ' Gini ' + U.sg(gi['qısa'], 2) + ' bənd, yoxsulluq ' + U.sg(pv && pv['qısa'], 2) + ' f.b. (qısa müddət; sintetik məlumat).' : '');
    return s1 + s2;
  };
  function card(s, rk) {
    var r = rk[s.id], tiers = U.uniq(U.hl(s.id).map(function (x) { return x.tier; }).join('').split('').filter(Boolean)).sort().join('');
    var ins = s.ins.map(function (i) { var m = U.instr(i.instrument) || {}; return U.fam(m.family) + ' <span>' + U.esc(m.name_az || i.instrument) + ': ' + U.sg(i.size, 2).replace(/^\+/, i.size > 0 ? '+' : '') + ' ' + U.esc(U.UNITN[i.unit] || i.unit || '') + '</span>'; }).join('<br>');
    var se = U.seCount ? U.seCount(s.id) : null;
    return '<article class="scard" data-fam="' + U.esc(s.ins.map(function (i) { return (U.instr(i.instrument) || {}).family; }).join(' ')) + '">' +
      '<div class="meta">' + (r ? '<span class="rankb" title="KPI üzrə çoxkriteriyalı reytinq (FR5)">' + r.rank + '-ci yer</span>' + (U.isNum(r.rank_conservative) ? '<span class="chip" title="' + U.esc(U.CONS_TXT) + '">ehtiyatlı: ' + r.rank_conservative + '</span>' : '') + (r.complete === false || r.complete === 'False' ? '<span class="chip warn" title="bəzi KPI-lar üçün giriş yoxdur">natamam</span>' : '') : '') + '<span>başlanğıc ' + U.esc(s.start || '') + '</span>' + (s.tags || []).map(function (t) { return '<span class="chip">' + U.esc(t) + '</span>'; }).join('') + '<span style="margin-left:auto">' + U.tier(tiers) + '</span></div>' +
      '<h3><a href="#/tesir?s=' + U.enc(s.id) + '">' + U.esc(s.name) + '</a></h3><div class="small">' + ins + '</div>' + U.egrid(s.id) +
      '<p class="small muted" style="margin:0">' + U.esc(U.story(s.id)) + '</p>' +
      (se ? '<div class="small">' + se + '</div>' : '') +
      '<div class="acts"><a class="btn sm pri" href="#/tesir?s=' + U.enc(s.id) + '">Ətraflı</a><a class="btn sm" href="#/sektor?s=' + U.enc(s.id) + '">Sektorlar</a><a class="btn sm" href="#/sosial?s=' + U.enc(s.id) + '">Sosial</a><a class="btn sm" href="#/risk?s=' + U.enc(s.id) + '">Risklər</a><a class="btn sm ghost" href="#/qurucu?from=' + U.enc(s.id) + '">Surət çıxar</a></div></article>';
  }
  U.pages[''] = function (v) {
    var rk = {}, R = U.T('P5_ranking'); R.forEach(function (r) { rk[r.scenario] = r; });
    var L = U.official().slice().sort(function (a, b) { return ((rk[a.id] || {}).rank || 99) - ((rk[b.id] || {}).rank || 99); });
    var fams = U.uniq(U.T('cfg_instruments').map(function (r) { return r.family; }));
    var st = U.T('P1_run_status'), errs = st.filter(function (r) { return r.status === 'xəta'; });
    v.innerHTML = U.head('MİİS §15.5.4 — iqtisadi siyasətlərin təsir analizi', 'Siyasət qərarı iqtisadiyyata necə təsir edir?',
      'Hər ssenari bir və ya bir neçə siyasət alətidir (vergi dərəcəsi, dövlət xərci, pensiya, minimum əmək haqqı, uçot dərəcəsi, tarif…). Panel onun təsirini <b>baza proqnozu ilə müqayisədə</b> göstərir: ssenari − baza. Qısa müddət — cari və növbəti il, orta — 3–4-cü illər, uzun — 5 il və daha çox.') +
      '<div class="flow" style="margin:14px 0"><span class="st">1. Alət və ölçü seçilir</span><span class="ar">→</span><span class="st">2. Baza proqnozu ilə müqayisə</span><span class="ar">→</span><span class="st">3. Beş metod: MikroUnit, CAEM, IO, mikrosimulyasiya, uzun müddət</span><span class="ar">→</span><span class="st">4. Makro, sektor, sosial təsirlər, risklər</span><span class="ar">→</span><span class="st">5. KPI ilə reytinq və hesabat</span></div>' +
      '<div class="toolbar"><a class="btn pri" href="#/qurucu">' + U.icon('tool', 15) + ' Yeni ssenari qur</a><a class="btn" href="#/kpi">' + U.icon('target', 15) + ' Ssenariləri KPI ilə müqayisə et</a><a class="btn" href="#/hesabat">' + U.icon('doc', 15) + ' Hesabat hazırla</a><a class="btn ghost" href="#/validasiya">' + U.icon('hist', 15) + ' Model keçmişdə necə işləyib?</a></div>' +
      (errs.length ? '<div class="note-w"><b>Diqqət:</b> son hesablamada ' + errs.length + ' mühərrik işi alınmayıb (məs. ' + U.esc(errs[0].scenario + ' · ' + (U.ENGS[errs[0].engine] || errs[0].engine) + ': ' + (errs[0].message_az || '')) + '). Bu nəticələr kartlarda «—» kimi görünür. <a href="#/metod/icra">Ətraflı</a></div>' : '') +
      U.sec('KPI reytinqi', 'Standart KPI seçimi və çəkilərlə çoxkriteriyalı bal (0–1) — öz seçiminiz üçün «KPI» bölməsi', '<div class="cols2"><div class="card pad"><div id="h-rank" class="ch"></div></div><div class="card pad"><div id="h-ce" class="ch"></div><p class="small muted">' + U.esc(U.CONS_TXT) + '</p><p class="small muted">Xərc-effektivlik: bal / 1 mlrd AZN birbaşa fiskal xərc (qısa + orta müddət). Xərcsiz ssenarilər göstərilmir.</p></div></div>') +
      U.sec('Ssenarilər', L.length + ' rəsmi ssenari · rəqəmlər bazadan fərqdir; yaşıl — əlverişli, qırmızı — əlverişsiz istiqamət; * — mikrosimulyasiya (sintetik məlumat)',
        '<div class="toolbar" style="margin-top:0">' + U.seg('h-fam', [['', 'Hamısı']].concat(fams.map(function (f) { return [f, f]; })), '') + '<input type="search" id="h-q" placeholder="ssenari axtar…" aria-label="Ssenari axtar"></div>' +
        '<div class="scards" id="h-cards" data-tour="cards">' + L.map(function (s) { return card(s, rk); }).join('') + '</div>') +
      U.sec('Nümunə ssenarilər', 'IO və mikrosimulyasiya mühərriklərinin ayrıca nümunələri (yalnız həmin mühərrikin nəticəsi)', '<div class="chips">' + U.scens().filter(function (s) { return s.src !== 'rəsmi'; }).map(function (s) { return '<a class="chip" href="#/' + (s.src === 'IO nümunəsi' ? 'sektor' : 'sosial') + '?s=' + U.enc(s.id) + '">' + U.esc(s.name) + '</a>'; }).join(' ') + '</div>');
    var top = R.slice().sort(function (a, b) { return b.score - a.score; });
    U.barH(U.$('#h-rank', v), top.map(function (r) { return r.scenario_name; }), null, 'çoxkriteriyalı bal (0–1)', { sets: [{ name: 'standart', v: top.map(function (r) { return r.score; }), c: '#0E6F7C' }].concat(top.some(function (r) { return U.isNum(r.score_conservative); }) ? [{ name: 'ehtiyatlı', v: top.map(function (r) { return r.score_conservative; }), c: '#E07B00' }] : []) });
    var ce = top.filter(function (r) { return U.isNum(r.score_per_bn_azn) && r.cost_mln_azn > 0; }).sort(function (a, b) { return b.score_per_bn_azn - a.score_per_bn_azn; });
    U.barH(U.$('#h-ce', v), ce.map(function (r) { return r.scenario_name; }), ce.map(function (r) { return r.score_per_bn_azn; }), 'bal / 1 mlrd AZN', { color: '#1F6FB2' });
    var flt = function () { var f = (U.$('#h-fam .on', v) || {}).getAttribute ? U.$('#h-fam .on', v).getAttribute('data-v') : '', q = U.fold(U.$('#h-q', v).value || '');
      U.$$('.scard', v).forEach(function (c) { c.hidden = (f && (' ' + c.getAttribute('data-fam') + ' ').indexOf(' ' + f + ' ') < 0) || (q && U.fold(c.textContent).indexOf(q) < 0); }); };
    U.$('#h-fam', v).onclick = function (e) { var b = e.target.closest('[data-v]'); if (!b) return; U.$$('#h-fam button', v).forEach(function (x) { x.classList.toggle('on', x === b); }); flt(); };
    U.$('#h-q', v).oninput = U.debounce(flt, 150);
  };
})();
