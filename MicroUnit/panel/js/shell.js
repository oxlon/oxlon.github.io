/* shell.js — tabs, hash router, scenario bar, search palette (Ctrl K), modal dialog, 1-minute tour. */
(function () {
  'use strict';
  var U = window.U, $ = U.$, META = U.META;
  U.pages = {};
  U.TABS = [['', 'Başlanğıc', 'home']].concat(META.frs.map(function (f) { return [f.slug, f.c + ' ' + f.t, '']; }))
    .concat([['ssenari', 'Ssenarilər', 'sliders'], ['hesabat', 'Hesabat', 'doc'], ['cedvel', 'Cədvəllər', 'table'], ['sintetik', 'Sintetik', 'flask'], ['beledci', 'Bələdçi', 'book']]);
  var ROUTE = '';
  function renderTabs() {
    var cur = ROUTE.split('/')[0] || '';
    $('#tabs').innerHTML = U.TABS.map(function (t) {
      var on = cur === t[0];
      return '<a class="tab' + (on ? ' on' : '') + '" href="#/' + t[0] + '" data-tour="tab-' + (t[0] || 'home') + '"' + (on ? ' aria-current="page"' : '') +
        ' title="' + U.esc(t[1]) + '">' + (t[2] ? U.icon(t[2]) : '') + '<span>' + (/^FR\d/.test(t[1]) ? U.esc(t[1].split(' ')[0]) + '<span class="tn"> ' + U.esc(t[1].split(' ').slice(1).join(' ')) + '</span>' : U.esc(t[1])) + '</span></a>';
    }).join('');
    var on = $('#tabs .tab.on'); if (on && on.scrollIntoView) on.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }
  function renderScenBar() {
    var raw = U.scenRaw();
    $('#scenbar').innerHTML = '<span><b>Ssenari</b> <span class="help" title="FR1-in üç makro ssenarisi bütün modullarda işlədilir. «Hamısı» qrafiklərdə üçünü birlikdə göstərir; cədvəllər bütün ssenariləri verir.">?</span></span>' +
      '<div class="seg" id="scen-seg" role="group" aria-label="Ssenari">' + ['B', 'A', 'R', 'all'].map(function (k) {
        return '<button type="button" data-k="' + k + '" class="' + (raw === k ? 'on' : '') + '">' + (k === 'all' ? 'Hamısı' : U.SCN[k]) + '</button>'; }).join('') + '</div>' +
      '<span class="legend">' + U.SC.map(function (k) { return '<span><i class="dotline" style="background:' + U.SCC[k] + '"></i>' + U.SCN[k] + '</span>'; }).join('') +
      '<span><i class="dotline" style="background:rgba(14,111,124,.3);height:8px"></i>5–95 % zolağı</span><span><i class="impdot"></i>' + U.IMPLAB + '</span></span>' +
      '<span class="muted small stamp">Mikro Model · proqnoz 2026–2030 · ' + META.stamp.date + '</span>';
    $('#scen-seg').onclick = function (e) { var b = e.target.closest('[data-k]'); if (!b) return; U.setScen(b.getAttribute('data-k')); };
  }
  U.onScen = function () { renderScenBar(); route(true); };
  function route(keep) {
    var hq = location.hash.replace(/^#\/?/, '').split('?');
    ROUTE = hq[0]; U.HQ = new URLSearchParams(hq[1] || '');
    renderTabs();
    var p = ROUTE.split('/').map(function (x) { try { return decodeURIComponent(x); } catch (e) { return x; } });
    var v = $('#view'), y = window.scrollY;
    var fn = U.pages[p[0]];
    if (!fn) { if (p[0]) U.toast('Belə bölmə yoxdur — başlanğıca qayıdıldı'); fn = U.pages['']; }
    v.onclick = null; v.oninput = null; v.onchange = null;
    try { fn(v, p); } catch (err) { v.innerHTML = '<div class="card pad"><b>Bölmə açılmadı.</b><p class="small muted">' + U.esc(err.message) + '</p></div>'; if (window.console) console.error(err); }
    if (keep) window.scrollTo(0, y); else window.scrollTo(0, 0);
  }
  U.route = route;
  U.go = function (h) { if (location.hash === h) route(true); else location.hash = h; };

  // ---- modal ---------------------------------------------------------------
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

  // ---- palette ------------------------------------------------------------
  var PAL = null, RES = [], SEL = 0;
  function build() {
    PAL = U.TABS.map(function (t) { return { k: 'Bölmə', t: t[1], go: '#/' + t[0] }; });
    U.S.forEach(function (s) { PAL.push({ k: s.f, t: s.e, sub: s.g + (s.u ? ' · ' + s.u : '') + ' · ' + s.i, go: U.href(s) }); });
    (window.MICRO.EQI ? window.MICRO.EQI.rows : []).forEach(function (e) { PAL.push({ k: 'Tənlik', t: e.t, sub: e.id + ' · ' + e.st, go: '#/' + e.f.toLowerCase() + '/tenlik/' + U.enc(e.id) }); });
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

  // ---- tour ---------------------------------------------------------------
  var TOUR = [
    ['#tabs', 'Bölmələr', 'Hər tələbin (FR) öz bölməsi, Ssenarilər (öz ssenarinizi qurmaq), Hesabat qurucusu, bütün proqnoz cədvəlləri, sintetik müəssisə məlumatı və bələdçi.'],
    ['#scenbar', 'Ssenari', 'Əsas, Mənfi və ya İslahat ssenarisini seçin — kartlar və qrafiklər dərhal yenilənir. Cədvəllər hər zaman üç ssenarinin hamısını göstərir.'],
    ['[data-tour="tab-fr1"]', 'Tələb bölməsi', 'Solda qruplar və komponentlər. Komponenti seçin: qrafik, 2026–2030 cədvəli və altında onu izah edən tənliklər, dayanıqlıq hökmü ilə.'],
    ['[data-tour="tab-ssenari"]', 'Ssenari qurucusu', 'Neftin qiyməti kimi fərziyyəni və ya əmsalı dəyişin, «Hesabla» düyməsini basın — FR1-in nəticəsi bütün modullara ötürülür.'],
    ['[data-tour="tab-hesabat"]', 'Hesabat', 'Göstəriciləri, ssenariləri və illəri seçin — Excel, Word, PDF və ya CSV hesabatı hazırdır.'],
    ['#open-pal', 'Sürətli axtarış', 'İstənilən göstəricini və ya tənliyi tapmaq üçün Ctrl+K (Mac: ⌘K).']];
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
    $('#pal-scrim').onclick = closePal; $('#scrim').onclick = U.closeModal;
    $('#modal').addEventListener('click', function (e) { if (e.target.closest('#modal-x')) U.closeModal(); });
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
    route(false);
    $('#boot').hidden = true;
    if (U.API) U.API.ping();
    if (!U.ls('mikroPanel.tour') && !/notour/.test(location.search)) setTimeout(U.startTour, 600);
  };
})();
