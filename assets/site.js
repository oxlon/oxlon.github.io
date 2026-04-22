/* Shared site chrome renderer — injects top bar and footer into every page */
(function(){
  const CURRENT = (document.body && document.body.dataset.page) || '';

  const NAV = [
    { href:'econai.html',     label:'Platform',  key:'platform' },
    { href:'advisory.html',   label:'Advisory',  key:'advisory' },
    { href:'research.html',   label:'Research',  key:'research' },
    { href:'about.html',      label:'About',     key:'about'    },
    { href:'contact.html',    label:'Contact',   key:'contact'  }
  ];

  const FOOT_COLS = [
    { h:'Platform', items:[
      {href:'econai.html',              t:'EconAI'},
      {href:'learning.html',            t:'Oxlon Atlas'},
      {href:'econai.html#security',     t:'Security &amp; deployment'},
      {href:'case-azerbaijan.html',     t:'Case: Azerbaijan'}
    ]},
    { h:'Advisory', items:[
      {href:'advisory.html',            t:'Overview'},
      {href:'economics-of-ai.html',     t:'Economics of AI'},
      {href:'advisory.html#model-review',t:'Model review'},
      {href:'advisory.html#custom',     t:'Custom research'}
    ]},
    { h:'Research', items:[
      {href:'research.html',            t:'All papers'},
      {href:'research.html#papers',     t:'Working papers'},
      {href:'research.html#newsletter', t:'The Oxlon Memo'},
      {href:'research.html#insights',   t:'Insights'}
    ]},
    { h:'Firm', items:[
      {href:'about.html',               t:'About'},
      {href:'about.html#founders',      t:'Team'},
      {href:'about.html#hiring',        t:'Careers'},
      {href:'contact.html',             t:'Contact'},
      {href:'legal.html',               t:'Legal'}
    ]}
  ];

  function bar(){
    const darkClass = document.body.classList.contains('dark-chrome') ? ' dark' : '';
    const links = NAV.map(n => {
      const here = (CURRENT === n.key) ? ' aria-current="page"' : '';
      return `<a href="${n.href}"${here}>${n.label}</a>`;
    }).join('');
    return `
      <header class="bar${darkClass}" id="site-bar">
        <a class="brand" href="index.html"><span class="mark"></span><span class="wm">Ox<em>lon</em></span></a>
        <nav class="nav" aria-label="Primary">${links}</nav>
        <a class="btn-cta" href="contact.html">Request a scoping call</a>
        <button class="mobile-toggle" aria-label="Menu" id="site-bar-toggle">Menu</button>
      </header>`;
  }

  function foot(){
    const cols = FOOT_COLS.map(c => `
      <div class="foot-col">
        <h4>${c.h}</h4>
        <ul>${c.items.map(i => `<li><a href="${i.href}">${i.t}</a></li>`).join('')}</ul>
      </div>`).join('');
    const yr = new Date().getFullYear();
    return `
      <footer class="site-foot">
        <div class="wrap">
          <div class="foot-top">
            <div class="foot-col">
              <div class="foot-brand">Ox<em>lon</em>.</div>
              <div class="foot-tag">Intelligence, distilled for decision-making.</div>
              <div style="margin-top:28px;font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:rgba(246,241,230,.55);line-height:2">
                Oxford &middot; London &middot; Baku<br>
                <a href="mailto:info@oxlon.uk" style="color:rgba(246,241,230,.78);text-decoration:none;border-bottom:1px solid rgba(246,241,230,.2);padding-bottom:2px">info@oxlon.uk</a>
              </div>
            </div>
            ${cols}
          </div>
          <div class="foot-bottom">
            <div>&copy; ${yr} Oxlon Ltd &middot; Oxford &middot; London</div>
            <div>
              <a href="https://www.linkedin.com/company/oxlon/" target="_blank" rel="noopener">LinkedIn</a>
              &nbsp;&middot;&nbsp;
              <a href="legal.html">Legal</a>
              &nbsp;&middot;&nbsp;
              <a href="legal.html#privacy">Privacy</a>
              &nbsp;&middot;&nbsp;
              <a href="legal.html#cookies">Cookies</a>
            </div>
          </div>
        </div>
      </footer>`;
  }

  function mount(){
    const head = document.getElementById('site-bar-mount');
    const footMount = document.getElementById('site-foot-mount');
    if(head) head.outerHTML = bar();
    if(footMount) footMount.outerHTML = foot();

    const toggle = document.getElementById('site-bar-toggle');
    const barEl = document.getElementById('site-bar');
    if(toggle && barEl){
      toggle.addEventListener('click', () => {
        const open = barEl.classList.toggle('open');
        toggle.textContent = open ? 'Close' : 'Menu';
      });
    }

    // Fade-up observer
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.15 });
    document.querySelectorAll('.fade-up').forEach(el => io.observe(el));
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
