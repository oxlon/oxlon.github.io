/* site.js — the only runtime script on the site (no framework, no network).
     1. the mobile menu (the sidebar collapses below 900px),
     2. the in-page section highlight in the sidebar,
     3. the figure loader — draws the inline Plotly specs; a figure inside a closed <details>
        (equation cards, forecast groups) is drawn when the card is opened,
     4. the equation filter, "open all / close all" and the "Kopyala" button.
   Everything still reads without JavaScript: tables and <details> are plain HTML. */
(function () {
  'use strict';
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  /* ---------- 1. mobile menu ------------------------------------------- */
  var btn = document.getElementById('menu-button');
  var side = document.getElementById('sidebar');
  if (btn && side) {
    btn.addEventListener('click', function () {
      var open = side.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    side.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && window.matchMedia('(max-width: 900px)').matches) {
        side.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------- 2. section highlight ------------------------------------- */
  var links = $$('.nav-sections a');
  if (links.length && 'IntersectionObserver' in window) {
    var byId = {};
    links.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
    var heads = Object.keys(byId).map(function (id) { return document.getElementById(id); }).filter(Boolean);
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        links.forEach(function (a) { a.classList.remove('active'); });
        var a = byId[en.target.id];
        if (a) a.classList.add('active');
      });
    }, { rootMargin: '-10% 0px -75% 0px', threshold: 0 });
    heads.forEach(function (h) { obs.observe(h); });
  }

  /* ---------- 3. figures ------------------------------------------------ */
  var CONFIG = { displaylogo: false, responsive: true, locale: 'az',
                 modeBarButtonsToRemove: ['lasso2d', 'select2d'] };
  function draw(mount) {
    if (mount.getAttribute('data-drawn')) return;
    var id = mount.getAttribute('data-fig');
    var inline = document.getElementById('figdata-' + id);
    if (!inline) return;
    var spec;
    try { spec = JSON.parse(inline.textContent); }
    catch (e) { mount.textContent = 'Qrafikin məlumatı oxunmadı (' + id + ')'; return; }
    mount.setAttribute('data-drawn', '1');
    if (window.Plotly && spec && spec.data) {
      mount.textContent = '';
      mount.classList.remove('is-loading', 'is-pending');
      mount.classList.add('is-ready');
      window.Plotly.newPlot(mount, spec.data, spec.layout || {}, Object.assign({}, CONFIG, spec.config || {}));
      return;
    }
    mount.classList.remove('is-loading');
    mount.classList.add('is-pending');
    mount.textContent = 'Qrafik kitabxanası yüklənmədi — məlumat cədvəldədir';
  }
  function visible(el) {
    for (var p = el.parentElement; p; p = p.parentElement) {
      if (p.tagName === 'DETAILS' && !p.open) return false;
    }
    return true;
  }
  function drawVisible(root) {
    $$('.fig-mount', root).forEach(function (m) { if (visible(m)) draw(m); });
  }
  $$('.fig-mount').forEach(function (m) { if (!visible(m)) m.textContent = 'qrafik açılanda çəkiləcək'; });
  drawVisible(document);
  document.addEventListener('toggle', function (e) {
    var d = e.target;
    if (d.tagName === 'DETAILS' && d.open) {
      drawVisible(d);
      if (window.Plotly) $$('.fig-mount.is-ready', d).forEach(function (m) { window.Plotly.Plots.resize(m); });
    }
  }, true);
  /* open the card a link points to (e.g. …-tenlikler.html#eq-FR1-B1_oil_price) */
  function openHash() {
    var h = decodeURIComponent(location.hash.slice(1));
    var el = h && document.getElementById(h);
    if (el && el.tagName === 'DETAILS') { el.open = true; el.scrollIntoView(); }
  }
  window.addEventListener('hashchange', openHash);
  openHash();

  /* ---------- 4. equation filter, open/close all, copy ----------------- */
  var bar = document.querySelector('.eq-filter');
  if (bar) {
    bar.hidden = false;
    var cards = $$('details.eq');
    var groups = $$('section.eq-group');
    var sels = $$('select', bar);
    var count = bar.querySelector('.count');
    var apply = function () {
      var shown = 0;
      cards.forEach(function (c) {
        var ok = sels.every(function (s) { return !s.value || c.getAttribute('data-' + s.getAttribute('data-attr')) === s.value; });
        c.style.display = ok ? '' : 'none';
        if (ok) shown++;
      });
      groups.forEach(function (g) {
        g.style.display = $$('details.eq', g).some(function (c) { return c.style.display !== 'none'; }) ? '' : 'none';
      });
      if (count) count.textContent = shown + ' / ' + cards.length + ' tənlik göstərilir';
    };
    sels.forEach(function (s) { s.addEventListener('change', apply); });
    apply();
  }
  $$('.fc-tools').forEach(function (t) { t.hidden = false; });
  $$('button.eq-expand, button.fc-expand').forEach(function (b) {
    b.addEventListener('click', function () {
      var open = b.getAttribute('data-open') === '1';
      var sel = b.classList.contains('eq-expand') ? 'details.eq' : 'details.fc-group';
      $$(sel).forEach(function (d) { if (d.style.display !== 'none') d.open = open; });
    });
  });
  $$('button.copy-btn').forEach(function (b) {
    b.addEventListener('click', function () {
      var pre = document.getElementById(b.getAttribute('data-copy'));
      if (!pre) return;
      var txt = pre.textContent;
      var done = function () { b.textContent = 'Kopyalandı'; setTimeout(function () { b.textContent = 'Kopyala'; }, 1600); };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(txt).then(done, function () { fallback(txt); done(); });
      } else { fallback(txt); done(); }
    });
  });
  function fallback(txt) {
    var ta = document.createElement('textarea');
    ta.value = txt; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) { /* the text stays selectable in the page */ }
    document.body.removeChild(ta);
  }
})();
