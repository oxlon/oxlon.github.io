/* shell.js — tabs, hash router, status bar (current scenario, last run, server status), search palette (Ctrl K),
   modal dialog and the 1-minute tour. Copied from the Risk paneli (itself adapted from the MicroUnit İş paneli). */
(function () {
  'use strict';
  var U = window.U, $ = U.$;
  U.pages = {};
  U.TABS = [['', 'Başlanğıc', 'home', 'Başlanğıc — ssenarilərin əsas nəticələri'], ['qurucu', 'Ssenari qurucusu', 'tool', 'Ssenari qurucusu (NFR4)'], ['tesir', 'Makro və mikro', 'pulse', 'Makro və mikro təsirlər (FR1)'],
    ['sektor', 'Sektorlar', 'grid', 'Sektor təsirləri — girdi-çıxdı modeli (FR2)'], ['sosial', 'Sosial', 'users', 'Sosial təsirlər — mikrosimulyasiya (FR3)'], ['risk', 'Risklər', 'warn', 'Risklər və yan təsirlər (FR4)'],
    ['kpi', 'KPI', 'target', 'KPI və qiymətləndirmə (FR5)'], ['muqayise', 'Metodlar', 'cmp', 'Metodların müqayisəsi (NFR2)'], ['validasiya', 'Validasiya', 'hist', 'Tarixi validasiya (NFR1)'],
    ['hesabat', 'Hesabat', 'doc', 'Hesabat qurucusu'], ['metod', 'Metodologiya', 'book', 'Metodologiya və mənbələr']];
  var ROUTE = '';
  function renderTabs() {
    var cur = ROUTE.split('/')[0] || '';
    $('#tabs').innerHTML = U.TABS.map(function (t) {
      var on = cur === t[0];
      return '<a class="tab' + (on ? ' on' : '') + '" href="#/' + t[0] + '" data-tour="tab-' + (t[0] || 'home') + '"' + (on ? ' aria-current="page"' : '') + ' title="' + U.esc(t[3]) + '">' + U.icon(t[2]) + '<span>' + U.esc(t[1]) + '</span></a>';
    }).join('');
    var on = $('#tabs .tab.on'); if (on && on.scrollIntoView) on.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }
  var SCPAGES = { tesir: 1, sektor: 1, sosial: 1, risk: 1 };
  function renderBar() {
    var st = U.META.stamp || {}, api = U.API && U.API.online, cur = U.cur(), sc = U.scen(cur) || {}, pg = ROUTE.split('/')[0];
    $('#scenbar').innerHTML = '<span><b>Ssenari</b>' + U.help('Seçilmiş ssenari «Makro və mikro», «Sektorlar», «Sosial» və «Risklər» səhifələrində göstərilir. Hər nəticə eyni vintajlı baza proqnozu ilə müqayisədir (ssenari − baza).') + '</span>' +
      U.scenSel('bar-sc', cur) + (SCPAGES[pg] ? '' : '<span class="muted small">(təsir səhifələri üçün)</span>') +
      (sc.src && sc.src !== 'rəsmi' ? '<span class="chip warn">' + U.esc(sc.src) + '</span>' : '') +
      '<span class="srv ' + (api ? 'on' : U.PY && U.PY.mode(api) === 'brauzer' ? 'py' : 'off') + '" id="srv" title="' + U.esc(U.PY ? U.PY.title(api) : (api ? 'Yerli server əlçatandır — yeni ssenari hesablana bilər' : 'Server yoxdur — bütün nəticələr paketdən göstərilir; yeni hesablama üçün serveri başladın')) + '"><i></i>' + (U.PY ? U.PY.label(api) : (api ? 'Server: canlı' : 'Fayl rejimi')) + '</span>' +
      '<span class="muted small stamp">son hesablama ' + U.esc(st.date || '') + ' · MikroUnit vintajı ' + U.esc((st.vintage || {}).micro_vintage || '—') + '</span>';
    $('#bar-sc').onchange = function (e) { U.setCur(e.target.value); if (U.HQ && U.HQ.get('s')) { location.hash = '#/' + ROUTE; return; } renderBar(); route(true); };
    $('#srv').onclick = function () { if (U.API) U.API.openSettings(); };
  }
  U.renderBar = renderBar;
  function route(keep) {
    var hq = location.hash.replace(/^#\/?/, '').split('?');
    ROUTE = hq[0]; U.HQ = new URLSearchParams(hq[1] || ''); U.navTok++;
    renderTabs(); if ($('#bar-sc')) renderBar();
    var p = ROUTE.split('/').map(function (x) { try { return decodeURIComponent(x); } catch (e) { return x; } });
    var v = $('#view'), y = window.scrollY, fn = U.pages[p[0]];
    if (!fn) { if (p[0]) U.toast('Belə bölmə yoxdur — başlanğıca qayıdıldı'); fn = U.pages['']; }
    var nv = v.cloneNode(false); v.parentNode.replaceChild(nv, v); v = nv;   // drop the previous page's listeners
    U.dtBind(v);
    try { fn(v, p); } catch (err) { v.innerHTML = '<div class="card pad"><b>Bölmə açılmadı.</b><p class="small muted">' + U.esc(err.message) + '</p></div>'; if (window.console) console.error(err); }
    document.title = (U.TABS.filter(function (t) { return t[0] === p[0]; })[0] || U.TABS[0])[3] + ' — Siyasət paneli';
    if (keep) window.scrollTo(0, y); else window.scrollTo(0, 0);
  }
  U.route = route;
  U.go = function (h) { if (location.hash === h) route(true); else location.hash = h; };
  U.openModal = function (html, onClose) {
    var m = $('#modal'), b = $('#modal-body');
    b.innerHTML = html; m.hidden = false; $('#scrim').hidden = false; document.body.classList.add('modal-on');
    U._onClose = onClose; b.scrollTop = 0; var x = $('#modal-x'); if (x) x.focus();
    return b;
  };
  U.closeModal = function (silent) {
    if ($('#modal').hidden) return;
    $('#modal').hidden = true; $('#scrim').hidden = true; document.body.classList.remove('modal-on');
    var f = U._onClose; U._onClose = null; if (f && silent !== true) f();
  };
  // ---- palette --------------------------------------------------------------
  var PAL = null, RES = [], SEL = 0;
  U.palExtra = [];
  function build() {
    PAL = U.TABS.map(function (t) { return { k: 'Bölmə', t: t[3], go: '#/' + t[0] }; });
    U.scens().forEach(function (s) { PAL.push({ k: 'Ssenari', t: s.name, sub: s.id + ' · ' + s.src, go: '#/tesir?s=' + U.enc(s.id) }); });
    U.T('cfg_instruments').forEach(function (r) { PAL.push({ k: 'Alət', t: r.name_az, sub: r.family + ' · ' + (U.UNITN[r.unit] || r.unit) + ' · [' + r.min + '; ' + r.max + ']', go: '#/qurucu?i=' + U.enc(r.id) }); });
    U.T('P5_kpi_catalogue').forEach(function (r) { PAL.push({ k: 'KPI', t: r.name_az, sub: r.unit + ' · ' + (r.horizon || ''), go: '#/kpi' }); });
    var seen = {}; U.T('P1_headline').forEach(function (r) { if (!seen[r.indicator]) { seen[r.indicator] = 1; PAL.push({ k: 'Göstərici', t: r.label_az, sub: r.effect_unit, go: '#/tesir' }); } });
    U.T('cfg_io_sectors').forEach(function (r) { PAL.push({ k: 'Sektor', t: r.name_az, sub: 'IO sektoru ' + r.code + ' · NACE ' + r.nace_section, go: '#/sektor' }); });
    U.palExtra.forEach(function (e) { PAL.push(e); });
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
  // ---- tour -----------------------------------------------------------------
  var TOUR = [
    ['#tabs', 'Bölmələr', '«Başlanğıc» — bütün ssenarilərin əsas nəticələri. Sonra ssenari qurucusu, makro və mikro, sektor, sosial təsirlər, risklər, KPI reytinqi, metodların müqayisəsi, tarixi validasiya, hesabat və metodologiya.'],
    ['#bar-sc', 'Ssenari seçimi', 'Təsir səhifələrində göstərilən ssenari. Hər nəticə eyni baza proqnozu ilə müqayisədir: ssenari − baza.'],
    ['[data-tour="cards"]', 'Ssenari kartları', 'Hər kart: ÜDM, qiymətlər, işsizlik, formal iş yerləri, Gini, yoxsulluq və fiskal xərc — qısa, orta və uzun müddətdə. Karta klikləyin — ətraflı təhlil açılır.'],
    ['[data-tour="tab-qurucu"]', 'Yeni ssenari', 'Alətlər kataloqundan seçin, ölçü, illər, hədəf sektor və maliyyələşməni göstərin — proqramlaşdırma lazım deyil.'],
    ['[data-tour="tab-hesabat"]', 'Hesabat', 'Siyasət təsiri hesabatı — qrafiklər, cədvəllər və qısa izahlar; PDF, Excel, Word və ya CSV.'],
    ['#open-pal', 'Sürətli axtarış', 'Ssenari, alət, KPI, göstərici və ya sektoru tapmaq üçün Ctrl+K (Mac: ⌘K).']];
  var TI = 0;
  U.startTour = function () { TI = 0; if (ROUTE !== '') location.hash = '#/'; setTimeout(show, 120); };
  function show() {
    var st = TOUR[TI], el = $(st[0]), box = $('#tour');
    if (!el || !el.offsetParent) { if (TI < TOUR.length - 1) { TI++; show(); } else end(); return; }
    var r = el.getBoundingClientRect(), left = Math.min(Math.max(12, r.left), window.innerWidth - 372), top = Math.min(r.bottom + 14, window.innerHeight - 220);
    box.hidden = false;
    box.innerHTML = '<div class="tour-hole" style="left:' + (r.left - 6) + 'px;top:' + (r.top - 6) + 'px;width:' + (r.width + 12) + 'px;height:' + Math.min(r.height + 12, 260) + 'px"></div>' +
      '<div class="tour-card" role="dialog" style="left:' + left + 'px;top:' + top + 'px"><h4>' + U.esc(st[1]) + '</h4><p>' + U.esc(st[2]) + '</p><div class="row"><span class="muted">' + (TI + 1) + ' / ' + TOUR.length + '</span>' +
      '<button class="btn sm ghost" id="t-skip">Bağla</button>' + (TI ? '<button class="btn sm" id="t-back">Geri</button>' : '') + '<button class="btn sm pri" id="t-next">' + (TI === TOUR.length - 1 ? 'Başla' : 'Növbəti') + '</button></div></div>';
    $('#t-next').onclick = function () { if (TI < TOUR.length - 1) { TI++; show(); } else end(); };
    $('#t-skip').onclick = end; var b = $('#t-back'); if (b) b.onclick = function () { TI--; show(); };
  }
  function end() { $('#tour').hidden = true; U.ls('policyPanel.tour', 'done'); }
  U.boot = function () {
    renderBar();
    $('#open-pal').onclick = openPal; $('#tour-btn').onclick = U.startTour;
    $('#pal-scrim').onclick = closePal; $('#scrim').onclick = U.closeModal;
    $('#modal').addEventListener('click', function (e) { if (e.target.closest('#modal-x')) U.closeModal(); });
    U.dtBind($('#modal-body'));
    $('#pal-in').oninput = function (e) { draw(e.target.value); };
    $('#pal-list').onclick = function (e) { var it = e.target.closest('[data-i]'); if (it) pick(+it.getAttribute('data-i')); };
    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPal(); return; }
      if (e.key === 'Escape') { closePal(); U.closeModal(); end(); }
      if ($('#pal').hidden) return;
      var items = U.$$('#pal-list .pal-item[data-i]');
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); SEL = Math.max(0, Math.min(items.length - 1, SEL + (e.key === 'ArrowDown' ? 1 : -1))); items.forEach(function (x, i) { x.classList.toggle('on', i === SEL); }); if (items[SEL]) items[SEL].scrollIntoView({ block: 'nearest' }); }
      if (e.key === 'Enter') pick(SEL);
    });
    window.addEventListener('hashchange', function () { U.closeModal(true); route(false); });
    if (U.API) U.API.onChange(function () { renderBar(); });
    if (U.PY) U.PY.onChange(function () { renderBar(); });
    route(false);
    $('#boot').hidden = true;
    if (U.API) U.API.ping();
    if (!U.ls('policyPanel.tour') && !/notour/.test(location.search)) setTimeout(U.startTour, 700);
  };
})();
