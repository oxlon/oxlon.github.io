/* shell.js — tabs, hash router, scenario bar, search palette (Ctrl K), drawer, 1-minute tour. */
(function () {
  'use strict';
  var U = window.U, $ = U.$, META = window.MICRO.META;
  U.pages = {};
  U.TABS = [['', 'Başlanğıc', 'home']].concat(META.frs.map(function (f) { return [f.slug, f.c + ' ' + f.t, '']; }))
    .concat([['ssenari', 'Ssenarilər', ''], ['cedvel', 'Proqnoz cədvəlləri', ''], ['sintetik', 'Sintetik', ''], ['beledci', 'Bələdçi', '']]);
  var ROUTE = '';
  function renderTabs() {
    var cur = ROUTE.split('/')[0] || '';
    $('#tabs').innerHTML = U.TABS.map(function (t) {
      var on = cur === t[0];
      return '<a class="tab' + (on ? ' on' : '') + '" href="#/' + t[0] + '" data-tour="tab-' + (t[0] || 'home') + '"' + (on ? ' aria-current="page"' : '') +
        ' title="' + U.esc(t[1]) + '">' + (t[2] ? U.icon(t[2]) : '') + '<span>' + U.esc(t[1]) + '</span></a>';
    }).join('');
    var on = $('#tabs .tab.on'); if (on && on.scrollIntoView) on.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }
  function renderScenBar() {
    var raw = U.scenRaw();
    $('#scenbar').innerHTML = '<span><b>Ssenari</b> <span class="help" title="FR1-in üç makro ssenarisi bütün modullarda işlədilir. «Hamısı» qrafiklərdə üçünü birlikdə göstərir; cədvəllər onda Əsas ssenarini götürür.">?</span></span>' +
      '<div class="seg" id="scen-seg" role="group" aria-label="Ssenari">' + ['B', 'A', 'R', 'all'].map(function (k) {
        return '<button data-k="' + k + '" class="' + (raw === k ? 'on' : '') + '">' + (k === 'all' ? 'Hamısı' : U.SCN[k]) + '</button>'; }).join('') + '</div>' +
      '<span class="legend">' + U.SC.map(function (k) { return '<span><i class="dotline" style="background:' + U.SCC[k] + '"></i>' + U.SCN[k] + '</span>'; }).join('') +
      '<span><i class="dotline" style="background:rgba(14,111,124,.3);height:8px"></i>5–95 % zolağı</span></span>' +
      '<span class="muted small" style="margin-left:auto">Mikro Model · proqnoz 2026–2030 · ' + META.stamp.date + '</span>';
    $('#scen-seg').onclick = function (e) { var b = e.target.closest('[data-k]'); if (!b) return; U.setScen(b.getAttribute('data-k')); };
  }
  U.onScen = function () { renderScenBar(); route(true); };
  function route(keep) {
    ROUTE = decodeURIComponent(location.hash.replace(/^#\/?/, ''));
    if (!keep) U.closeDrawer();
    renderTabs();
    var p = ROUTE.split('/'), v = $('#view'), y = window.scrollY;
    var fn = U.pages[p[0]] || U.pages[''];
    if (!U.pages[p[0]] && p[0]) { U.toast('Belə bölmə yoxdur — başlanğıca qayıdıldı'); }
    v.onclick = null; v.oninput = null; v.onchange = null;
    fn(v, p);
    if (keep) window.scrollTo(0, y); else window.scrollTo(0, 0);
    if (keep && !$('#drawer').hidden && U.DR) U.openDrawer(U.DR);
  }
  U.route = route;

  // ---- drawer -------------------------------------------------------------
  U.closeDrawer = function () { $('#drawer').hidden = true; $('#scrim').hidden = true; U.DR = null; };
  U.openDrawer = function (s) {
    U.DR = s;
    var I = META.info[s.m] || {}, o = s.o, d = $('#drawer');
    var hold = o ? '<table class="itbl" style="margin-top:6px"><tbody>' +
      '<tr><td>Təsadüfi gəzişməyə qarşı Theil U</td><td class="n"><b class="' + (o.rw < 1 ? 'up' : 'down') + '">' + U.nf(o.rw, 2) + '</b></td></tr>' +
      '<tr><td>' + (o.cgname ? 'Sabit etalona (' + U.esc(o.cgname) + ')' : 'Sabit artıma') + ' qarşı Theil U</td><td class="n"><b class="' + (U.isNum(o.cg) ? (o.cg < 1 ? 'up' : 'down') : '') + '">' + U.nf(o.cg, 2) + '</b></td></tr>' +
      '<tr><td>Model xətası (RMSE)</td><td class="n">' + U.nf(o.rmse, 2) + '</td></tr><tr><td>Yoxlama pəncərəsi</td><td class="n">' + U.esc(o.win) + '</td></tr></tbody></table>' +
      '<p class="small muted">U &lt; 1 — model etalondan yaxşıdır (yaşıl); U ≥ 1 — yaxşı deyil (qırmızı). Mənbə: <code>' + U.esc(o.src) + '</code></p>'
      : '<p class="muted small">Bu sıra üçün ayrıca hold-out nəticəsi ixrac olunmayıb; modulun ümumi yoxlaması «Klassik görünüş»dədir.</p>';
    d.innerHTML = '<div style="display:flex;gap:10px;align-items:start"><div style="flex:1"><div class="eyebrow">' + s.f + ' · ' + U.esc(s.g) + '</div><h3>' + U.esc(U.label(s)) + '</h3></div><button class="ibtn" id="dr-x" aria-label="Bağla">✕</button></div>' +
      '<p class="small" style="margin:8px 0">' + '<span class="chip">' + U.esc(s.u || 'vahid göstərilməyib') + '</span> ' + (s.q ? '<span class="chip acc">5–95 % zolağı var</span> ' : '') + (s.nt ? '<span class="chip">' + U.esc(s.nt) + '</span>' : '') + '</p>' +
      '<h4 style="margin-top:14px">Tərif</h4><p>' + U.esc(I.d || '') + '</p>' +
      '<h4>Model</h4><p>' + U.esc(I.m || '') + '</p><h4>Sürücülər</h4><p>' + U.esc(I.r || '') + '</p>' +
      '<h4>Nümunədən kənar yoxlama</h4>' + hold +
      '<h4 style="margin-top:12px">Bütün ssenarilər, 2026–2030</h4><div class="itbl-wrap">' + U.yearTable(s, true) + '</div>' +
      '<h4 style="margin-top:12px">Məhdudiyyətlər</h4><ul>' + (I.l || []).map(function (x) { return '<li>' + U.esc(x) + '</li>'; }).join('') + '</ul>' +
      '<h4>Mənbə faylı</h4><p><a href="../output/' + U.esc(String(s.src).split(' ')[0]) + '">' + U.esc(s.src) + '</a> · <a href="../site/fr/' + s.f.toLowerCase() + '.html">' + s.f + ' — klassik səhifə</a></p>';
    d.hidden = false; $('#scrim').hidden = false; $('#dr-x').onclick = U.closeDrawer; d.scrollTop = 0;
  };

  // ---- palette ------------------------------------------------------------
  var PAL = null, RES = [], SEL = 0;
  function build() {
    PAL = U.TABS.map(function (t) { return { k: 'Bölmə', t: t[1], go: '#/' + t[0] }; });
    U.S.forEach(function (s) { PAL.push({ k: s.f, t: U.label(s), sub: s.g + (s.u ? ' · ' + s.u : ''), go: '#/' + s.f.toLowerCase() + '/s/' + s.n }); });
    META.gloss.forEach(function (g) { PAL.push({ k: 'Termin', t: g[0], sub: g[1].slice(0, 90), go: '#/beledci' }); });
    PAL.forEach(function (e) { e.f = U.fold(e.t + ' ' + (e.sub || '') + ' ' + e.k); });
  }
  function draw(q) {
    var w = U.fold(q.trim()).split(/\s+/).filter(Boolean);
    RES = PAL.filter(function (e) { return w.every(function (x) { return e.f.indexOf(x) >= 0; }); }).slice(0, 60); SEL = 0;
    $('#pal-list').innerHTML = RES.length ? RES.map(function (e, i) { return '<div class="pal-item' + (i ? '' : ' on') + '" data-i="' + i + '"><span class="k">' + U.esc(e.k) + '</span><span>' + U.esc(e.t) + (e.sub ? '<small>' + U.esc(e.sub) + '</small>' : '') + '</span></div>'; }).join('') : '<div class="pal-item"><span class="muted">Nəticə tapılmadı</span></div>';
  }
  function openPal() { if (!PAL) build(); $('#pal').hidden = false; $('#pal-scrim').hidden = false; var i = $('#pal-in'); i.value = ''; draw(''); i.focus(); }
  function closePal() { $('#pal').hidden = true; $('#pal-scrim').hidden = true; }
  function pick(i) { var e = RES[i]; if (!e) return; closePal(); location.hash = e.go; }
  U.openPal = openPal;

  // ---- tour ---------------------------------------------------------------
  var TOUR = [
    ['#tabs', 'Bölmələr', 'Başlanğıc, hər tələb (FR) üçün ayrıca bölmə, Ssenarilər, Proqnoz cədvəlləri, Sintetik məlumat və Bələdçi.'],
    ['#scenbar', 'Ssenari', 'Əsas, Mənfi və ya İslahat ssenarisini seçin — bütün kartlar, qrafiklər və cədvəllər dərhal yenilənir. «Hamısı» üçünü birlikdə göstərir.'],
    ['[data-tour="tab-fr1"]', 'Tələb bölməsi', 'Solda bütün göstəricilər qruplar üzrə; birini seçin — qrafik və 2026–2030 illər üzrə açıq cədvəl görünür. «Hamısı» qrupun bütün üzvlərini bir cədvəldə verir.'],
    ['[data-tour="tab-cedvel"]', 'Proqnoz cədvəlləri', 'Bütün modulların bütün proqnoz sıraları bir cədvəldə: süzgəc, axtarış, CSV və Excel ixracı.'],
    ['#open-pal', 'Sürətli axtarış', 'İstənilən göstəricini tapmaq üçün Ctrl+K (Mac: ⌘K).'],
    ['#classic', 'Klassik görünüş', 'Metodologiya, məlumat mənbələri və yoxlamalar ətraflı sənəd şəklində.']];
  var TI = 0;
  U.startTour = function () { TI = 0; if (ROUTE !== '') location.hash = '#/'; setTimeout(show, 80); };
  function show() {
    var st = TOUR[TI], el = $(st[0]), box = $('#tour');
    if (!el || !el.offsetParent) { if (TI < TOUR.length - 1) { TI++; show(); } else end(); return; }
    var r = el.getBoundingClientRect(), left = Math.min(Math.max(12, r.left), window.innerWidth - 372);
    box.hidden = false;
    box.innerHTML = '<div class="tour-hole" style="left:' + (r.left - 6) + 'px;top:' + (r.top - 6) + 'px;width:' + (r.width + 12) + 'px;height:' + (r.height + 12) + 'px"></div>' +
      '<div class="tour-card" role="dialog" style="left:' + left + 'px;top:' + (r.bottom + 14) + 'px"><h4>' + U.esc(st[1]) + '</h4><p>' + U.esc(st[2]) + '</p><div class="row"><span class="muted">' + (TI + 1) + ' / ' + TOUR.length + '</span>' +
      '<button class="btn sm ghost" id="t-skip">Bağla</button>' + (TI ? '<button class="btn sm" id="t-back">Geri</button>' : '') + '<button class="btn sm pri" id="t-next">' + (TI === TOUR.length - 1 ? 'Başla' : 'Növbəti') + '</button></div></div>';
    $('#t-next').onclick = function () { if (TI < TOUR.length - 1) { TI++; show(); } else end(); };
    $('#t-skip').onclick = end; var b = $('#t-back'); if (b) b.onclick = function () { TI--; show(); };
  }
  function end() { $('#tour').hidden = true; U.ls('mikroPanel.tour', 'done'); }

  U.boot = function () {
    renderScenBar();
    $('#open-pal').onclick = openPal; $('#tour-btn').onclick = U.startTour;
    $('#pal-scrim').onclick = closePal; $('#scrim').onclick = U.closeDrawer;
    $('#pal-in').oninput = function (e) { draw(e.target.value); };
    $('#pal-list').onclick = function (e) { var it = e.target.closest('[data-i]'); if (it) pick(+it.getAttribute('data-i')); };
    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPal(); return; }
      if (e.key === 'Escape') { closePal(); U.closeDrawer(); end(); }
      if ($('#pal').hidden) return;
      var items = U.$$('#pal-list .pal-item[data-i]');
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); SEL = Math.max(0, Math.min(items.length - 1, SEL + (e.key === 'ArrowDown' ? 1 : -1))); items.forEach(function (x, i) { x.classList.toggle('on', i === SEL); }); if (items[SEL]) items[SEL].scrollIntoView({ block: 'nearest' }); }
      if (e.key === 'Enter') pick(SEL);
    });
    window.addEventListener('hashchange', function () { route(false); });
    route(false);
    $('#boot').hidden = true;
    if (!U.ls('mikroPanel.tour') && !/notour/.test(location.search)) setTimeout(U.startTour, 600);
  };
})();
