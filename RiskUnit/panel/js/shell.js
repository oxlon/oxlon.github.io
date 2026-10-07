/* shell.js — tabs, hash router, status bar (as-of date, view toggle, server status), search palette (Ctrl K),
   modal dialog and the 1-minute tour. Adapted from the MicroUnit İş paneli. */
(function () {
  'use strict';
  var U = window.U, $ = U.$;
  U.pages = {};
  U.TABS = [['', 'Bu gün', 'home', 'Başlanğıc — bu gün'], ['reyestr', 'Reyestr', 'list', 'Risk reyestri'], ['monitor', 'Monitor', 'pulse', 'Monitor: axınlar, bazar, siqnallar, proqnoz təsiri'], ['paylanma', 'Paylanma', 'fan', 'Paylanmalar 2026–2030'],
    ['var', 'VaR/CaR', 'shield', 'VaR və CaR'], ['miqyas', 'Miqyas', 'scale', 'Miqyaslanma'], ['stress', 'Stress', 'bolt', 'Stress testləri və ssenari qurucusu'], ['tedbir', 'Tədbirlər', 'tool', 'Tədbirlər'],
    ['caem', 'CAEM', 'grid', 'CAEM'], ['sinaq', 'Sınaq', 'check', 'Geriyə sınaq (NFR1)'], ['hesabat', 'Hesabat', 'doc', 'Hesabat qurucusu'], ['metod', 'Metod', 'book', 'Metodologiya və mənbələr']];
  var ROUTE = '';
  var VIEW = (/[?&]view=(baseline|live)/.exec(location.search) || [])[1] || U.ls('riskPanel.view') || 'baseline';
  U.view = function () { return VIEW; };
  U.VIEWN = { baseline: 'Baza mərkəzli', live: 'Canlı şərtləndirilmiş' };
  U.setView = function (v) { VIEW = v; U.ls('riskPanel.view', v); renderBar(); route(true); };
  function renderTabs() {
    var cur = ROUTE.split('/')[0] || '';
    $('#tabs').innerHTML = U.TABS.map(function (t) {
      var on = cur === t[0];
      return '<a class="tab' + (on ? ' on' : '') + '" href="#/' + t[0] + '" data-tour="tab-' + (t[0] || 'home') + '"' + (on ? ' aria-current="page"' : '') + ' title="' + U.esc(t[3]) + '">' + U.icon(t[2]) + '<span>' + U.esc(t[1]) + '</span></a>';
    }).join('');
    var on = $('#tabs .tab.on'); if (on && on.scrollIntoView) on.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }
  function renderBar() {
    var st = U.META.stamp || {}, api = U.API && U.API.online;
    $('#scenbar').innerHTML = '<span><b>Vəziyyət</b> ' + U.esc(st.as_of || '') + '</span>' +
      '<span><b>Baxış</b>' + U.help('Baza mərkəzli: paylanmanın medianı rəsmi baza proqnozudur (skorlar və istilik xəritəsi bununla). Canlı: bugünkü bazar məlumatı (cari Brent) ilə şərtləndirilmiş paylanma — gündəlik monitorla (D6) uyğun.') + '</span>' +
      U.seg('view-seg', [['baseline', U.VIEWN.baseline], ['live', U.VIEWN.live]], VIEW) +
      '<span class="srv ' + (api ? 'on' : U.PY && U.PY.mode(api) === 'brauzer' ? 'py' : 'off') + '" id="srv" title="' + U.esc(U.PY ? U.PY.title(api) : (api ? 'Yerli server əlçatandır — canlı hesablamalar işləyir' : 'Server yoxdur — bütün nəticələr paketdən göstərilir; canlı hesablama üçün serveri başladın')) + '"><i></i>' + (U.PY ? U.PY.label(api) : (api ? 'Server: canlı' : 'Fayl rejimi')) + '</span>' +
      '<span class="muted small stamp">baza ' + U.esc(st.baseline_id || '') + ' · yığım ' + U.esc(st.date || '') + '</span>';
    $('#view-seg').onclick = function (e) { var b = e.target.closest('[data-v]'); if (b) U.setView(b.getAttribute('data-v')); };
    $('#srv').onclick = function () { if (U.API) U.API.openSettings(); };
  }
  U.renderBar = renderBar;
  function route(keep) {
    var hq = location.hash.replace(/^#\/?/, '').split('?');
    ROUTE = hq[0]; U.HQ = new URLSearchParams(hq[1] || ''); U.navTok++;
    renderTabs();
    var p = ROUTE.split('/').map(function (x) { try { return decodeURIComponent(x); } catch (e) { return x; } });
    var v = $('#view'), y = window.scrollY, fn = U.pages[p[0]];
    if (!fn) { if (p[0]) U.toast('Belə bölmə yoxdur — başlanğıca qayıdıldı'); fn = U.pages['']; }
    var nv = v.cloneNode(false); v.parentNode.replaceChild(nv, v); v = nv;   // drop the previous page's listeners
    U.dtBind(v);
    try { fn(v, p); } catch (err) { v.innerHTML = '<div class="card pad"><b>Bölmə açılmadı.</b><p class="small muted">' + U.esc(err.message) + '</p></div>'; if (window.console) console.error(err); }
    document.title = (U.TABS.filter(function (t) { return t[0] === p[0]; })[0] || U.TABS[0])[3] + ' — Risk paneli';
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
    U.T('FR2_risk_scores').forEach(function (r) { PAL.push({ k: 'Risk', t: r.risk_id + ' ' + r.ad, sub: (U.FAM[r.aile] || r.aile) + ' · skor ' + r.skor + ' · ' + r.prioritet, go: '#/reyestr/' + r.risk_id }); });
    U.T('M1_measures_v2').forEach(function (r) { PAL.push({ k: 'Tədbir', t: r.tedbir_id + ' ' + r.tedbir, sub: r.mesul + ' · ' + r.status, go: '#/tedbir/reyestr?t=' + r.tedbir_id }); });
    U.T('S0_factor_sigma').forEach(function (r) { PAL.push({ k: 'Amil', t: r.amil_ad, sub: 'miqyaslanma · 1σ = ' + U.nf(r.olcu_1sigma) + ' ' + r.vahid, go: '#/miqyas?f=' + r.amil }); });
    U.T('D5_daily_monitor').forEach(function (r) { PAL.push({ k: 'Göstərici', t: r.label_az, sub: 'monitor · ' + U.nf(r.latest) + ' ' + (r.unit || '') + ' · ' + r.signal, go: '#/monitor/siqnal' }); });
    U.T('D2_feed_status').forEach(function (r) { PAL.push({ k: 'Axın', t: r.source, sub: r.feed + ' · ' + r.tazelik + ' · ' + r.status, go: '#/monitor' }); });
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
    ['#tabs', 'Bölmələr', '«Bu gün» — rəhbərlik üçün gündəlik xülasə. Sonra risk reyestri, monitor, paylanmalar, VaR/CaR, miqyaslanma, stress testləri, tədbirlər, CAEM, geriyə sınaq, hesabat və metodologiya.'],
    ['#view-seg', 'İki baxış', 'Baza mərkəzli: paylanmanın ortası rəsmi proqnozdur. Canlı: bugünkü bazar məlumatı ilə şərtləndirilib. Seçim bütün paylanma qrafiklərinə tətbiq olunur.'],
    ['[data-tour="today"]', 'Bu günün xülasəsi', 'Ən yüksək risklər, yeni xəbərdarlıqlar, dünəndən nə dəyişdi və bugünkü məlumatın rəsmi proqnozlara təsiri.'],
    ['[data-tour="tab-reyestr"]', 'Riskin tam təhlili', 'Reyestrdə riskə klikləyin: tərif, göstərici, ehtimal üsulu, ötürmə kanalı, təsirlənən dəyişənlər, miqyaslanma əyrisi, tədbirlər və qalıq risk.'],
    ['[data-tour="tab-hesabat"]', 'Hesabat', '«Rəhbərlik üçün gündəlik xülasə» və ya «Analitik hesabat» şablonu — PDF, Excel, Word və ya CSV.'],
    ['#open-pal', 'Sürətli axtarış', 'Risk, tədbir, amil və ya göstəricini tapmaq üçün Ctrl+K (Mac: ⌘K).']];
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
  function end() { $('#tour').hidden = true; U.ls('riskPanel.tour', 'done'); }
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
    if (!U.ls('riskPanel.tour') && !/notour/.test(location.search)) setTimeout(U.startTour, 700);
  };
})();
