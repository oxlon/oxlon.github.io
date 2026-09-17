(function () {
'use strict';

const catalogue = window.MIIS_V4_CATALOG;
window.MIIS_V4_DATA = window.MIIS_V4_DATA || {};
const inFlight = new Map();
async function loadAsset(key) {
  if (Object.hasOwn(window.MIIS_V4_DATA || {}, key)) return window.MIIS_V4_DATA[key];
  if (!Object.hasOwn(catalogue.assets, key)) throw new Error('Unknown content asset');
  if (!inFlight.has(key)) inFlight.set(key, new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = catalogue.assets[key].path + '?v=' + catalogue.assets[key].sha256.slice(0,12);
    script.onload = () => { script.remove(); resolve(window.MIIS_V4_DATA[key]); };
    script.onerror = () => { script.remove(); inFlight.delete(key); reject(new Error('This saved content could not be loaded. Retry this view.')); };
    document.head.append(script);
  }));
  return inFlight.get(key);
}
async function loadParts(parts) { const all = []; for (const key of parts) all.push(...await loadAsset(key)); return all; }
async function loadPool(keys, onProgress) {
  const out = new Array(keys.length);
  let next = 0, done = 0;
  async function worker() {
    while (next < keys.length) {
      const i = next++;
      out[i] = await loadAsset(keys[i]);
      done++;
      if (onProgress) onProgress(done, keys.length);
    }
  }
  await Promise.all([worker(), worker(), worker(), worker()]);
  return out;
}

const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
function filterRecords(rows, filters) {
  const query = (filters.q || '').toLocaleLowerCase();
  return rows.filter(row => (!filters.model || row.model_id === filters.model)
    && (!filters.scenario || row.scenario_id === filters.scenario)
    && (!filters.fr || (row.fr_ids || []).includes(filters.fr))
    && (!filters.start || Number(row.year) >= Number(filters.start))
    && (!filters.end || Number(row.year) <= Number(filters.end))
    && (!filters.unit || row.unit === filters.unit)
    && (!query || [row.series_id,row.concept,row.source_file,row.source_sheet,row.status,row.data_status].join(' ').toLocaleLowerCase().includes(query)));
}
function displayValue(value, exact=false) {
  if (value === null || value === undefined || value === '') return 'Unavailable';
  if (typeof value === 'object') return JSON.stringify(value);
  if (exact || typeof value !== 'number') return String(value);
  return new Intl.NumberFormat('en-GB', {maximumFractionDigits:3}).format(value);
}
function literalTex(text) {
 const substitutions={'\\':'\\textbackslash{}','{':'\\{','}':'\\}','_':'\\_','%':'\\%','&':'\\&','#':'\\#','$':'\\$','^':'\\textasciicircum{}','~':'\\textasciitilde{}'};
 const lines=String(text).match(/.{1,90}/gs)||[''];
 return '\\begin{gathered}'+lines.map(line=>'\\texttt{'+[...line].map(c=>substitutions[c]||c).join('')+'}').join(' \\\\ ')+'\\end{gathered}';
}

const I18N = {
  en: {
    nav_workbench:'Forecasts', nav_evidence:'Models and data',
    nav_overview:'Overview', nav_forecasts:'Forecast explorer', nav_scenarios:'Saved scenarios',
    nav_models:'Models and methods', nav_equations:'Equations', nav_workbook:'Results workbook', nav_library:'Data library',
    nav_methods:'Methodology and sources', nav_requirements:'FR1–FR12', nav_differences:'Method differences', nav_delivery:'Ministry delivery files',
    search_button:'Find a table or method', menu:'Menu', close:'Close', retry:'Retry',
    reset:'Reset filters', search:'Search', loading:'Loading saved content', rows:'rows',
    page:'Page', of:'of', page_size:'Rows per page', all:'All', unavailable:'Unavailable',
    exact:'Exact source values', wide:'Wide year grid', detail_title:'Record details',
    empty:'No rows match the current filters.', lang_button:'Azərbaycan dili',
    search_title:'Find a table or method', search_placeholder:'Search tables, documents, notebooks',
    strip_status:'Data definitions', strip_note:'Source vintages and definitions differ between engines; displayed differences are not a pure method comparison. This presentation does not renew the prior review or grant Ministry acceptance.'
  },
  az: {
    nav_workbench:'İş masası', nav_evidence:'Sübutlar və mənbələr',
    nav_overview:'İcmal', nav_forecasts:'Proqnoz tədqiqatı', nav_scenarios:'Saxlanmış ssenarilər',
    nav_models:'Modellər', nav_equations:'Tənliklər', nav_workbook:'İş kitabı', nav_library:'Məlumat kitabxanası',
    nav_methods:'Metodologiya və mənbələr', nav_requirements:'Tələblər FR1-12', nav_differences:'Metod fərqləri', nav_delivery:'CSV təhvil faylları',
    search_button:'Cədvəl və ya metod axtar', menu:'Menyu', close:'Bağla', retry:'Yenidən cəhd et',
    reset:'Filtrləri sıfırla', search:'Axtarış', loading:'Saxlanmış məzmun yüklənir', rows:'sətir',
    page:'Səhifə', of:'/', page_size:'Səhifədə sətir', all:'Hamısı', unavailable:'Mövcud deyil',
    exact:'Dəqiq mənbə qiymətləri', wide:'Geniş il cədvəli', detail_title:'Qeydin təfərrüatları',
    empty:'Cari filtrlərə uyğun sətir yoxdur.', lang_button:'English',
    search_title:'Cədvəl və ya metod axtar', search_placeholder:'Cədvəl, sənəd və dəftərçələr üzrə axtarış',
    strip_status:'Təqdim edilmiş müstəqil yoxlama', strip_note:'Mühərriklər arasında mənbə vintajları və təriflər fərqlidir; göstərilən fərqlər təmiz metod müqayisəsi deyil. Bu təqdimat əvvəlki yoxlamanı yeniləmir və Nazirlik qəbulu vermir.'
  }
};
let lang = 'en';
try { lang = localStorage.getItem('miis_1551_v3_lang') === 'az' ? 'az' : 'en'; } catch (e) {}
const t = key => (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;

const MODEL_META = {
  'ministry_macro': {short:'Ministry macro', cls:'ministry', colour:'var(--ministry)'},
  'ministry_caem': {short:'Ministry CAEM', cls:'caem', colour:'var(--caem)'},
  'oxlon.corrected.20260917': {short:'Oxlon', cls:'oxlon', colour:'var(--oxlon)'},
  'imf_articleiv_benchmark': {short:'IMF reference', cls:'benchmark', colour:'var(--benchmark)'}
};
const modelMeta = id => MODEL_META[id] || {short:id, cls:'benchmark', colour:'var(--benchmark)'};
const modelTag = id => '<span class="model-tag ' + modelMeta(id).cls + '">' + escapeHTML(modelMeta(id).short) + '</span>';
const isTestScenario = s => /^test_only/i.test(s || '');
const fmtInt = n => new Intl.NumberFormat('en-GB').format(n);
const $ = sel => document.querySelector(sel);
const view = () => $('#view');

window.MIIS_V4_MATH_ERRORS = [];
function presentationMath(tex) {
  // FR12 cell 39 omits the final closing brace of its text label.
  // Repair only this exact recorded typo; source cells remain unchanged.
  return String(tex).replace(/\\text\{`rw\\_rmse\\_h` = 1\{,\}0\.$/, '\\text{`rw\\_rmse\\_h` = 1{,}0.}');
}
function renderMath(tex, display) {
  try {
    return katex.renderToString(presentationMath(tex), {displayMode: !!display, throwOnError: true, strict: false});
  } catch (err) {
    window.MIIS_V4_MATH_ERRORS.push({tex: String(tex), error: String(err && err.message || err)});
    return '<code class="math-fallback">' + escapeHTML(tex) + '</code>';
  }
}
function mathAfterRender(container) {
  container.querySelectorAll('[data-math]').forEach(node => {
    node.innerHTML = renderMath(node.getAttribute('data-math'), node.getAttribute('data-display') === '1');
  });
}

const md = window.markdownit ? window.markdownit({html: false, linkify: false}) : null;
function extractMath(src) {
  const store = [];
  const keep = (tex, display) => { store.push({tex, display}); return '\uE000' + (store.length - 1) + '\uE000'; };
  let out = String(src);
  out = out.replace(/\$\$([\s\S]+?)\$\$/g, (m, g) => keep(g, true));
  out = out.replace(/\\\[([\s\S]+?)\\\]/g, (m, g) => keep(g, true));
  out = out.replace(/\\\(([\s\S]+?)\\\)/g, (m, g) => keep(g, false));
  out = out.replace(/\$([^\$\n]+?)\$/g, (m, g) => /[A-Za-z\\^_{}]/.test(g) && !/^\s*[\d.,\s]+\s*$/.test(g) ? keep(g, false) : m);
  return {text: out, store};
}
function renderMarkdown(src, basePath) {
  if (!md) return '<pre class="code-view">' + escapeHTML(src) + '</pre>';
  const ex = extractMath(src);
  let html = md.render(ex.text);
  html = html.replace(/\uE000(\d+)\uE000/g, (m, i) => {
    const item = ex.store[Number(i)];
    return item ? renderMath(item.tex, item.display) : m;
  });
  const doc = new DOMParser().parseFromString(html, 'text/html');
  doc.querySelectorAll('a[href]').forEach(a => {
    const resolved = resolveArtifactRef(a.getAttribute('href'), basePath);
    if (resolved && resolved.route) {
      a.setAttribute('href', resolved.route);
    } else if (resolved && resolved.external) {
      a.setAttribute('rel', 'noopener noreferrer');
      a.setAttribute('target', '_blank');
    } else {
      const code = doc.createElement('code');
      code.textContent = a.getAttribute('href');
      a.replaceWith(code);
    }
  });
  doc.querySelectorAll('table').forEach(tb => { tb.classList.add('reader-table'); });
  return doc.body.innerHTML;
}

const SAFE_TAGS = new Set(['TABLE','THEAD','TBODY','TFOOT','TR','TH','TD','CAPTION','COLGROUP','COL','DIV','SPAN','P','BR','HR','H1','H2','H3','H4','H5','H6','UL','OL','LI','PRE','CODE','EM','STRONG','B','I','U','SMALL','SUB','SUP','DL','DT','DD','BLOCKQUOTE','FIGURE','FIGCAPTION','ABBR','MARK','S','KBD','SAMP','VAR','SECTION','ARTICLE','HEADER','FOOTER','DETAILS','SUMMARY']);
const DROP_TAGS = new Set(['SCRIPT','STYLE','IFRAME','OBJECT','EMBED','LINK','META','FORM','INPUT','BUTTON','SELECT','TEXTAREA','OPTION','AUDIO','VIDEO','SOURCE','TRACK','SVG','MATH','CANVAS','NOSCRIPT','TEMPLATE','BASE','AREA','MAP','PICTURE','DIALOG']);
const SAFE_ATTRS = new Set(['colspan','rowspan','class','align','valign','scope','title','headers','abbr','char','charoff']);
function sanitizeRecordedHTML(html) {
  const parsed = new DOMParser().parseFromString(String(html), 'text/html');
  const clean = (node) => {
    const children = [...node.childNodes];
    for (const child of children) {
      if (child.nodeType === 8) { child.remove(); continue; }
      if (child.nodeType !== 1) continue;
      const tag = child.tagName;
      if (DROP_TAGS.has(tag)) { child.remove(); continue; }
      if (tag === 'A') {
        const span = parsed.createElement('span');
        while (child.firstChild) span.appendChild(child.firstChild);
        child.replaceWith(span);
        clean(span);
        continue;
      }
      if (tag === 'IMG') {
        const src = child.getAttribute('src') || '';
        if (!/^data:image\/(png|jpeg|gif);base64,/i.test(src)) { child.remove(); continue; }
        for (const attr of [...child.attributes]) if (attr.name !== 'src' && attr.name !== 'alt' && attr.name !== 'title') child.removeAttribute(attr.name);
        continue;
      }
      if (!SAFE_TAGS.has(tag)) {
        while (child.firstChild) child.parentNode.insertBefore(child.firstChild, child);
        child.remove();
        continue;
      }
      for (const attr of [...child.attributes]) {
        const name = attr.name.toLowerCase();
        if (!SAFE_ATTRS.has(name)) child.removeAttribute(attr.name);
      }
      clean(child);
    }
  };
  clean(parsed.body);
  return parsed.body.innerHTML;
}

function dirname(path) { const i = path.lastIndexOf('/'); return i < 0 ? '' : path.slice(0, i); }
function resolveArtifactRef(href, basePath) {
  if (!href) return null;
  const raw = String(href).trim();
  if (/^(https?:|mailto:)/i.test(raw)) return {external: raw};
  if (raw.startsWith('#')) return {route: raw};
  let clean = raw.split('#')[0].split('?')[0];
  try { clean = decodeURIComponent(clean); } catch (e) {}
  if (!clean) return {route: raw};
  if (/^([A-Za-z]:)?\//.test(clean) || /^~/.test(clean)) return {text: clean};
  const joined = (basePath ? dirname(basePath) + '/' : '') + clean;
  const norm = [];
  for (const seg of joined.split('/')) {
    if (!seg || seg === '.') continue;
    if (seg === '..') { norm.pop(); continue; }
    norm.push(seg);
  }
  const resolved = norm.join('/');
  const hit = catalogue.path_lookup[resolved] || catalogue.path_lookup[clean];
  if (hit) return {route: routeForLookup(hit)};
  return {text: clean};
}
function routeForLookup(l) {
  if (!l) return '#/overview';
  if (l.view === 'table') return '#/table?id=' + encodeURIComponent(l.id);
  if (l.view === 'document') return '#/document?id=' + encodeURIComponent(l.id);
  if (l.view === 'notebook') return '#/notebook?id=' + encodeURIComponent(l.id);
  if (l.view === 'workbook') {
    const entry = catalogue.workbook.find(w => w.id === l.id) || catalogue.tables.find(x => x.id === l.id);
    return '#/workbook?sheet=' + encodeURIComponent(entry ? (entry.sheet || entry.title) : l.id);
  }
  if (l.view === 'equations') {
    if (l.id === 'native-caem') return '#/equations?tab=native&model=ministry_caem';
    if (l.id === 'native-macro') return '#/equations?tab=native&model=ministry_macro';
    return '#/equations';
  }
  if (l.view === 'forecasts') return '#/forecasts';
  return '#/overview';
}
function artifactLink(path, label) {
  const hit = catalogue.path_lookup[path];
  if (hit) return '<a href="' + routeForLookup(hit) + '">' + escapeHTML(label || path) + '</a>';
  return '<code>' + escapeHTML(path) + '</code>';
}

function isUnavailable(v) { return v === null || v === undefined || v === ''; }
function numericValue(v) {
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v === 'string' && v.trim() !== '') {
    const n = Number(v.replace(/,/g, ''));
    return Number.isFinite(n) ? n : null;
  }
  return null;
}
function compareValues(a, b, dir) {
  const au = isUnavailable(a), bu = isUnavailable(b);
  if (au && bu) return 0;
  if (au) return 1;
  if (bu) return -1;
  const an = numericValue(a), bn = numericValue(b);
  let c;
  if (an !== null && bn !== null) c = an - bn;
  else c = String(a).toLocaleLowerCase().localeCompare(String(b).toLocaleLowerCase());
  return dir === 'desc' ? -c : c;
}

class DataTable {
  constructor(opts) {
    this.opts = opts;
    this.state = opts.state || {q: '', sort: null, dir: 'asc', page: 1, size: opts.pageSize || 25};
    this.filtered = null;
    this.root = document.createElement('div');
    this.root.className = 'dt';
    this.render();
  }
  value(row, col) { return col.get ? col.get(row) : row[col.key]; }
  apply() {
    const q = (this.state.q || '').toLocaleLowerCase();
    let rows = this.opts.rows;
    if (q) rows = rows.filter(r => this.opts.columns.some(c => String(this.value(r, c) ?? '').toLocaleLowerCase().includes(q)));
    if (this.state.sort) {
      const col = this.opts.columns.find(c => (c.key || c.label) === this.state.sort);
      if (col) rows = [...rows].sort((a, b) => compareValues(this.value(a, col), this.value(b, col), this.state.dir));
    }
    this.filtered = rows;
  }
  pages() { return Math.max(1, Math.ceil(this.filtered.length / this.state.size)); }
  render() {
    this.apply();
    const o = this.opts;
    const state = this.state;
    const pages = this.pages();
    if (state.page > pages) state.page = pages;
    const start = (state.page - 1) * state.size;
    const slice = this.filtered.slice(start, start + state.size);
    let html = '<div class="table-tools">';
    if (o.searchable !== false) html += '<input type="search" data-role="q" aria-label="' + escapeHTML(t('search')) + '" placeholder="' + escapeHTML(t('search')) + '" value="' + escapeHTML(state.q) + '">';
    html += '<span data-role="count">' + fmtInt(this.filtered.length) + ' ' + escapeHTML(t('rows')) + (this.filtered.length !== o.rows.length ? ' · ' + fmtInt(o.rows.length) + ' ' + escapeHTML(t('all')).toLowerCase() : '') + '</span><span class="spacer"></span>';
    if (o.extraTools) html += o.extraTools;
    html += '<label>' + escapeHTML(t('page_size')) + ' <select data-role="size">' + (o.pageSizes || [25, 50, 100, 250]).map(s => '<option' + (s === state.size ? ' selected' : '') + '>' + s + '</option>').join('') + '</select></label></div>';
    html += '<div class="table-scroll' + (o.tall === false ? '' : ' tall') + '"><table class="data">';
    if (o.caption) html += '<caption>' + escapeHTML(o.caption) + '</caption>';
    html += '<thead><tr>';
    for (const col of o.columns) {
      const active = state.sort === (col.key || col.label);
      const mark = active ? (state.dir === 'asc' ? '▲' : '▼') : '';
      const aria = active ? (state.dir === 'asc' ? 'ascending' : 'descending') : 'none';
      html += '<th' + ' class="' + [col.num?'num':'',col.sticky?'sticky-col':''].filter(Boolean).join(' ') + '"' + ' aria-sort="' + aria + '"><button type="button" class="th-btn" data-sort="' + escapeHTML(col.key || col.label) + '">' + escapeHTML(col.label) + '<span class="sort-mark">' + mark + '</span></button></th>';
    }
    html += '</tr></thead><tbody>';
    if (!slice.length) {
      html += '<tr><td colspan="' + o.columns.length + '"><div class="empty-state">' + escapeHTML(o.emptyText || t('empty')) + '</div></td></tr>';
    }
    for (const row of slice) {
      const cls = (o.rowClass ? o.rowClass(row) : '') + (o.onActivate ? ' clickable' : '');
      html += '<tr' + (cls ? ' class="' + cls.trim() + '"' : '') + (o.onActivate ? ' tabindex="0" role="button"' : '') + '>';
      for (const col of o.columns) {
        const v = this.value(row, col);
        let cell;
        if (col.render) cell = col.render(row, v);
        else if (isUnavailable(v)) cell = '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>';
        else cell = escapeHTML(displayValue(v, o.exact));
        html += '<td' + ' class="' + [col.num?'num':'',col.wrap?'wrap':'',col.sticky?'sticky-col':''].filter(Boolean).join(' ') + '"' + '>' + cell + '</td>';
      }
      html += '</tr>';
    }
    html += '</tbody></table></div>';
    html += '<div class="pager"><button type="button" class="btn small" data-page="first" aria-label="First page">«</button><button type="button" class="btn small" data-page="prev" aria-label="Previous page">‹</button><span>' + escapeHTML(t('page')) + ' ' + fmtInt(state.page) + ' ' + escapeHTML(t('of')) + ' ' + fmtInt(pages) + '</span><button type="button" class="btn small" data-page="next" aria-label="Next page">›</button><button type="button" class="btn small" data-page="last" aria-label="Last page">»</button><span class="spacer"></span><span>' + fmtInt(this.filtered.length ? start + 1 : 0) + '-' + fmtInt(Math.min(start + state.size, this.filtered.length)) + ' / ' + fmtInt(this.filtered.length) + '</span></div>';
    this.root.innerHTML = html;
    this.wire(slice);
  }
  wire(slice) {
    const root = this.root;
    const o = this.opts;
    const search = root.querySelector('[data-role="q"]');
    if (search) {
      let timer = null;
      search.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          this.state.q = search.value;
          this.state.page = 1;
          this.render();
          if (o.onState) o.onState(this.state);
          const again = root.querySelector('[data-role="q"]');
          if (again) { again.focus(); again.setSelectionRange(again.value.length, again.value.length); }
        }, 220);
      });
    }
    const size = root.querySelector('[data-role="size"]');
    if (size) size.addEventListener('change', () => { this.state.size = Number(size.value); this.state.page = 1; this.render(); if (o.onState) o.onState(this.state); });
    root.querySelectorAll('[data-sort]').forEach(btn => btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-sort');
      if (this.state.sort === key) this.state.dir = this.state.dir === 'asc' ? 'desc' : 'asc';
      else { this.state.sort = key; this.state.dir = 'asc'; }
      this.render();
      if (o.onState) o.onState(this.state);
    }));
    root.querySelectorAll('[data-page]').forEach(btn => btn.addEventListener('click', () => {
      const p = btn.getAttribute('data-page');
      const pages = this.pages();
      if (p === 'first') this.state.page = 1;
      else if (p === 'prev') this.state.page = Math.max(1, this.state.page - 1);
      else if (p === 'next') this.state.page = Math.min(pages, this.state.page + 1);
      else this.state.page = pages;
      this.render();
      if (o.onState) o.onState(this.state);
    }));
    if (o.onActivate) {
      root.querySelectorAll('tbody tr').forEach((tr, i) => {
        const row = slice[i];
        if (!row) return;
        const go = () => o.onActivate(row);
        tr.addEventListener('click', go);
        tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
      });
    }
    if (o.onRendered) o.onRendered(this.root);
  }
}

const detailDialog = $('#detail-dialog');
let lastFocus = null;
function openDetail(titleText, html) {
  lastFocus = document.activeElement;
  $('#detail-title').textContent = titleText;
  const body = $('#detail-body');
  body.innerHTML = html;
  mathAfterRender(body);
  if (!detailDialog.open) detailDialog.showModal();
}
function closeDetail() { if (detailDialog.open) detailDialog.close(); }
detailDialog.addEventListener('close', () => { if (lastFocus && lastFocus.focus) lastFocus.focus(); });
$('#detail-close').addEventListener('click', closeDetail);

function propsTable(obj, order) {
  const keys = order || Object.keys(obj);
  let html = '<table class="props"><tbody>';
  for (const k of keys) {
    if (!Object.hasOwn(obj, k)) continue;
    const v = obj[k];
    let shown;
    if (v === null || v === undefined || v === '') shown = '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>';
    else if (Array.isArray(v)) shown = escapeHTML(v.join(', ')) || '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>';
    else if (typeof v === 'object') shown = '<code>' + escapeHTML(JSON.stringify(v)) + '</code>';
    else shown = escapeHTML(String(v));
    html += '<tr><th>' + escapeHTML(k) + '</th><td>' + shown + '</td></tr>';
  }
  return html + '</tbody></table>';
}
const RECORD_FIELDS = ['model_id','scenario_id','vintage_id','series_id','concept','unit','frequency','year','value','status','data_status','source_file','source_sheet','source_cell','method','source_value_type','reporting_role','parent_vintage_id','input_vintage_id','fr_ids','primary_source_file','primary_source_sheet','primary_source_cell','transformation'];
function recordDetail(row, extra) {
  const shown = Object.assign({}, row);
  if (Object.hasOwn(shown, 'value')) shown.value = (shown.value === null || shown.value === undefined) ? shown.value : String(shown.value);
  return propsTable(shown, extra || Object.keys(shown));
}

let renderEpoch = 0;
const routeState = {suppress: false, ignoredHashes: new Set()};
function parseHash() {
  const raw = location.hash.replace(/^#/, '') || '/overview';
  const [pathPart, queryPart] = raw.split('?');
  const path = pathPart.replace(/^\//, '') || 'overview';
  return {path, params: new URLSearchParams(queryPart || '')};
}
function buildHash(path, params) {
  const q = params && params.toString();
  return '#/' + path + (q ? '?' + q : '');
}
function setParams(path, params, push) {
  const h = buildHash(path, params);
  if (push) { location.hash = h; }
  else {
    routeState.suppress = true;
    const url = location.pathname + location.search + h;
    try { history.replaceState(null, '', h); } catch (err) { if (err.name !== 'SecurityError') throw err; if (location.hash !== h) { routeState.ignoredHashes.add(h); location.hash = h; } }
    routeState.suppress = false;
  }
}
function loadingView(label) {
  view().innerHTML = '<div class="loading"><div>' + escapeHTML(label || t('loading')) + '</div><div class="bar"><i></i></div><div data-role="prog"></div></div>';
}
function progressView(done, total) {
  const n = view().querySelector('[data-role="prog"]');
  if (n) n.textContent = done + ' / ' + total;
}
function errorView(message, retry) {
  view().innerHTML = '<div class="error-box">' + escapeHTML(message) + '<button type="button" class="btn" id="retry-btn">' + escapeHTML(t('retry')) + '</button></div>';
  $('#retry-btn').addEventListener('click', retry);
}
const fresh = ticket => ticket === renderEpoch;

const releaseP = () => loadAsset(catalogue.release_key);
const overviewP = () => loadAsset(catalogue.overview_key);
const comparisonP = () => loadAsset(catalogue.comparison_key);
const sourceMathP = () => loadAsset(catalogue.source_math_key);
const groupCache = new Map();
function groupEntry(model, scenario) { return catalogue.result_groups.find(g => g.model_id === model && g.scenario_id === scenario); }
async function loadGroupRows(model, scenario, onP) {
  const key = model + '|' + scenario;
  if (!groupCache.has(key)) {
    const g = groupEntry(model, scenario);
    if (!g) throw new Error('Unknown result group');
    groupCache.set(key, (async () => {
      const rows = [];
      let done = 0;
      for (const p of g.parts) { rows.push(...await loadAsset(p)); if (onP) onP(++done, g.parts.length); }
      return rows;
    })());
  }
  return groupCache.get(key);
}
const tableCache = new Map();
async function loadTableRows(entry, onP) {
  if (!tableCache.has(entry.id)) {
    tableCache.set(entry.id, (async () => {
      const rows = [];
      let done = 0;
      for (const p of entry.parts) { rows.push(...await loadAsset(p)); if (onP) onP(++done, entry.parts.length); }
      return rows;
    })());
  }
  return tableCache.get(entry.id);
}
const docCache = new Map();
async function loadDocumentText(entry, onP) {
  if (!docCache.has(entry.id)) {
    docCache.set(entry.id, (async () => {
      let text = '';
      let done = 0;
      for (const p of entry.parts) { text += await loadAsset(p); if (onP) onP(++done, entry.parts.length); }
      return text;
    })());
  }
  return docCache.get(entry.id);
}
const notebookCache = new Map();
async function loadNotebookCells(entry, onP) {
  if (!notebookCache.has(entry.id)) {
    notebookCache.set(entry.id, (async () => {
      const cells = [];
      let done = 0;
      for (const p of entry.parts) { cells.push(...await loadAsset(p)); if (onP) onP(++done, entry.parts.length); }
      return cells;
    })());
  }
  return notebookCache.get(entry.id);
}

const SECTIONS = [
  {path:'overview', label:()=>t('nav_overview'), group:'nav_workbench'},
  {path:'forecasts', label:()=>t('nav_forecasts'), group:'nav_workbench'},
  {path:'scenarios', label:()=>t('nav_scenarios'), group:'nav_workbench'},
  {path:'models', label:()=>t('nav_models'), group:'nav_workbench'},
  {path:'equations', label:()=>t('nav_equations'), group:'nav_evidence'},
  {path:'workbook', label:()=>t('nav_workbook'), group:'nav_evidence'},
  {path:'library', label:()=>t('nav_library'), group:'nav_evidence'},
  {path:'methods', label:()=>t('nav_methods'), group:'nav_evidence'},
  {path:'differences', label:()=>t('nav_differences'), group:'nav_evidence'},
  {path:'delivery', label:()=>t('nav_delivery'), group:'nav_evidence'},
  {path:'requirements', label:()=>t('nav_requirements'), group:'nav_evidence'}
];
function renderNav(current) {
  const nav = $('#navigation');
  let html = '';
  let lastGroup = null;
  for (const s of SECTIONS) {
    if (s.group !== lastGroup) { html += '<div class="nav-group">' + escapeHTML(t(s.group)) + '</div>'; lastGroup = s.group; }
    html += '<a href="#/' + s.path + '"' + (current === s.path ? ' class="active" aria-current="page"' : '') + '><span class="nav-dot"></span>' + escapeHTML(s.label()) + '</a>';
  }
  nav.innerHTML = html;
  $('#sidebar-release').innerHTML = 'MİİS 15.5.1<br>17 September 2026';
}
function breadcrumb(items) {
  $('#breadcrumb').innerHTML = items.map((it, i) => {
    const sep = i ? '<span class="sep">/</span>' : '';
    return sep + (it.href && i < items.length - 1 ? '<a href="' + it.href + '">' + escapeHTML(it.label) + '</a>' : '<span class="' + (i === items.length - 1 ? 'current' : '') + '">' + escapeHTML(it.label) + '</span>');
  }).join('');
}
function head(title, lede, pathNote) {
  return '<div class="view-head"><h1>' + escapeHTML(title) + '</h1>' + (lede ? '<p class="lede">' + escapeHTML(lede) + '</p>' : '') + (pathNote ? '<div class="path-note">' + escapeHTML(pathNote) + '</div>' : '') + '</div>';
}
function statusStrip() { return '<div class="definition-note">Model data vintages and definitions are retained. Missing source values remain visible; saved calculations are shown at their original forecast boundaries.</div>'; }

function selectField(label, name, options, current, allLabel) {
  let html = '<div class="field"><label for="f-' + name + '">' + escapeHTML(label) + '</label><select id="f-' + name + '" name="' + name + '">';
  if (allLabel !== undefined) html += '<option value="">' + escapeHTML(allLabel) + '</option>';
  for (const op of options) {
    const val = typeof op === 'object' ? op.value : op;
    const lab = typeof op === 'object' ? op.label : op;
    html += '<option value="' + escapeHTML(val) + '"' + (String(val) === String(current) ? ' selected' : '') + '>' + escapeHTML(lab) + '</option>';
  }
  return html + '</select></div>';
}
function wireFilterbar(root, onChange) {
  root.querySelectorAll('select,input').forEach(el => {
    el.addEventListener('change', () => onChange());
    if (el.type === 'search' || el.type === 'number' || el.type === 'text') {
      let timer = null;
      el.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(onChange, 300); });
    }
  });
}

async function viewOverview(params, ticket) {
  loadingView();
  const [comparison,release] = await Promise.all([comparisonP(),releaseP()]);
  if (!fresh(ticket)) return;
  const q = params.get('q') || '';
  const metric = params.get('concept') || '*';
  const model = params.get('model') || '*';
  const start = Number(params.get('start') || 2024), end = Number(params.get('end') || 2030);
  const years = Array.from({length:Math.max(0,Math.min(8,end-start+1))},(_,i)=>start+i);
  const order=['gdp_real_growth_market','cpi_annual_average_inflation','gdp_nominal_market'];comparison.sort((a,b)=>(order.includes(a.concept_id)?order.indexOf(a.concept_id):99)-(order.includes(b.concept_id)?order.indexOf(b.concept_id):99));const filtered=comparison.filter(c=>(metric==='*'||c.concept_id===metric)&&(!q||[c.label,c.concept_id,...c.mappings.map(m=>m.series_id)].join(' ').toLocaleLowerCase().includes(q.toLocaleLowerCase())));
  let html=head(lang==='az'?'Makroiqtisadi proqnozlar':'Macroeconomic forecasts',lang==='az'?'MİİS 15.5.1 · Nazirliyin makro modeli, Nazirlik CAEM, Oxlon və BVF istinadı':'MİİS 15.5.1 · Ministry macro, Ministry CAEM, Oxlon and IMF reference');
  html+='<div class="summary-line">'+(lang==='az'?'Məlumat tarixi: 17 sentyabr 2026':'Prepared: 17 September 2026')+' <span>•</span> '+fmtInt(catalogue.counts.forecast_records)+' '+(lang==='az'?'nəticə qeydi':'result records')+' <span>•</span> FR1–FR12</div>';
  html+='<div class="filterbar" id="comparison-filters">'+selectField(lang==='az'?'Göstərici':'Indicator','concept',[{value:'*',label:lang==='az'?'Bütün 25 göstərici':'All 25 indicators'},...comparison.map(c=>({value:c.concept_id,label:c.label}))],metric)+selectField(lang==='az'?'Model':'Model','model',[{value:'*',label:t('all')},...FORECAST_MODELS().map(m=>({value:m,label:modelMeta(m).short}))],model);
  html+=selectField(lang==='az'?'İldən':'From','start',[2024,2025,2026,2027,2028,2029,2030],start)+selectField(lang==='az'?'İlədək':'To','end',[2024,2025,2026,2027,2028,2029,2030,2031],end);
  html+='<div class="field"><label for="comparison-q">'+t('search')+'</label><input type="search" id="comparison-q" value="'+escapeHTML(q)+'" placeholder="GDP, CPI, exports…"></div><button class="btn" id="comparison-reset">'+t('reset')+'</button></div>';
  html+='<p class="definition-note">'+(lang==='az'?'Nazirlik makro və Nazirlik CAEM iki Nazirlik sistemidir. 2025-ci il üzrə CPI sətrləri gözlənilən qiymət, proqnoz, faktiki müşahidə və BVF qiymətləndirməsidir; məlumat dövrləri fərqlənir.':'Ministry macro and Ministry CAEM are both Ministry systems. Their 2025 CPI entries represent a retained expected value, a forecast, an observed value and an IMF estimate, with different information sets.')+' <a href="#/differences">'+(lang==='az'?'Metod və məlumat fərqləri':'Method and data differences')+'</a></p>';
  html+='<div class="comparison-wrap table-scroll"><table class="data comparison-matrix"><caption>'+(lang==='az'?'Baza ssenarisi · hər modelin mənbə məlumatları və ölçü vahidləri saxlanılır.':'Baseline comparison · each model retains its source data and units.')+'</caption><thead><tr><th class="sticky-col">'+(lang==='az'?'Göstərici / model':'Indicator / model')+'</th><th>'+(lang==='az'?'Vahid':'Unit')+'</th>'+years.map(y=>'<th class="num">'+y+'</th>').join('')+'<th>'+(lang==='az'?'Tərif və mənbə dövrü':'Definition and data vintage')+'</th></tr></thead><tbody>';
  let n=0;
  for (const c of filtered) {
    const maps=c.mappings.filter(m=>model==='*'||m.model_id===model);
    if(!maps.length)continue;
    html+='<tr class="indicator-row"><th colspan="'+(years.length+3)+'">'+escapeHTML(c.label)+'</th></tr>';
    for(const m of maps){
      html+='<tr><th scope="row" class="sticky-col">'+modelTag(m.model_id)+'<small>'+escapeHTML(m.series_id)+'</small></th><td>'+escapeHTML(m.unit)+'</td>';
      for(const y of years){const p=m.path.find(x=>Number(x.year)===y),r=p&&p.record;
        const state=r?comparisonStatus(r):null;const type=state?state.kind:'';
        html+='<td class="num '+type+'">'+(r?'<button class="value-button" data-record="'+n+'" data-concept="'+escapeHTML(c.concept_id)+'" data-series="'+escapeHTML(m.series_id)+'" data-model="'+escapeHTML(m.model_id)+'" data-year="'+y+'" aria-label="'+escapeHTML(c.label+' '+modelMeta(m.model_id).short+' '+y)+'">'+escapeHTML(displayValue(r.value))+'</button><small class="cell-status">'+escapeHTML(state.label)+'</small>':'<span class="unavail" title="No supplied observation">—</span>')+'</td>';
      }
      html+='<td class="wrap definition-cell">'+escapeHTML([m.scope,m.price_basis,m.vintage_group,m.note].filter(Boolean).join(' · '))+'</td></tr>';n++;
    }
  }
  if(!n)html+='<tr><td colspan="'+(years.length+3)+'">'+t('empty')+'</td></tr>';
  html+='</tbody></table></div><div class="table-legend"><span><i class="legend-history"></i>'+(lang==='az'?'Tarixi müşahidə':'Historical observation')+'</span><span><i class="legend-expected"></i>'+(lang==='az'?'Gözlənilən':'Expected')+'</span><span><i class="legend-forecast"></i>'+(lang==='az'?'Proqnoz':'Forecast')+'</span><span>— '+(lang==='az'?'Mənbədə yoxdur':'Not supplied')+'</span></div>';
  html+='<div class="actions-row comparison-actions"><a class="btn" href="#/differences">'+(lang==='az'?'Metod və CPI fərqləri':'Why the models and CPI values differ')+'</a><a class="btn" href="#/delivery">'+(lang==='az'?'CSV təhvil faylları':'Ministry delivery CSV files')+'</a></div>';
  html+='<p class="definition-note">'+(lang==='az'?'Modellərin məlumat dövrləri və iqtisadi tərifləri fərqlənir. Fərqlər yalnız metodun təsiri kimi şərh edilməməlidir. Mənbə, tərif və dəqiq qiymət üçün cədvəldəki rəqəmə klikləyin.':'Model data vintages and economic definitions differ. Differences cannot be attributed to method alone. Select any figure to inspect its definition, exact value and source.')+'</p>';
  html+='<section class="panel"><h2>'+(lang==='az'?'Məlumat dövrləri':'Data and forecast boundaries')+'</h2><table class="data"><thead><tr><th>Model</th><th>'+(lang==='az'?'Baza məlumatları':'Input data')+'</th><th>'+(lang==='az'?'Proqnoz dövrü':'Forecast period')+'</th><th>'+(lang==='az'?'Nəticələr':'Results')+'</th></tr></thead><tbody>';
  const defs=[['ministry_macro','Supplied linked Ministry workbooks; 2025 expected','2026–2030'],['ministry_caem','Original CAEM.xlsb; 2024 last actual','2025–2029'],['oxlon.corrected.20260917','Updated project histories through 2025','2026–2030'],['imf_articleiv_benchmark','IMF Article IV 2026 Table 1; dated external benchmark','2025–2031']];
  for(const [m,d,h] of defs)html+='<tr><th scope="row">'+modelTag(m)+'</th><td class="wrap">'+escapeHTML(d)+'</td><td>'+h+'</td><td><a href="#/forecasts?model='+encodeURIComponent(m)+'&scenario='+(m==='imf_articleiv_benchmark'?'Table1':'baseline')+'&wide=1&start=2024">'+(lang==='az'?'Cədvəli aç':'Open table')+' →</a></td></tr>';
  html+='</tbody></table></section>';
  view().innerHTML=html;
  const update=()=>{const p=new URLSearchParams();for(const k of ['concept','model','start','end'])p.set(k,$('#f-'+k).value);p.set('q',$('#comparison-q').value);if(Number(p.get('start'))>Number(p.get('end')))p.set('end',p.get('start'));setParams('overview',p,true);};
  view().querySelectorAll('#comparison-filters select').forEach(el=>el.addEventListener('change',update));
  let timer;$('#comparison-q').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(update,350);});
  $('#comparison-reset').addEventListener('click',()=>setParams('overview',new URLSearchParams(),true));
  view().querySelectorAll('[data-record]').forEach(b=>b.addEventListener('click',()=>{const c=comparison.find(c=>c.concept_id===b.dataset.concept);const m=c.mappings.find(m=>m.model_id===b.dataset.model&&m.series_id===b.dataset.series);const r=m.path.find(p=>Number(p.year)===Number(b.dataset.year)).record;openDetail(c.label+' · '+b.dataset.year,propsTable({definition:c.label,scope:m.scope,price_basis:m.price_basis,definition_group:m.definition_group,vintage:m.vintage_group})+recordDetail(r));}));
}

const FORECAST_MODELS = () => [...new Set(catalogue.result_groups.map(g => g.model_id))];
function groupKeyOf(r) { return r.model_id + '|' + r.scenario_id; }
function scenarioLabel(id,model) { const g=catalogue.result_groups.find(g=>g.model_id===model&&g.scenario_id===id); return g&&g.label || (id==='baseline'?'Baseline':id.replace(/_/g,' ')); }

async function viewForecasts(params, ticket) {
  const model = params.get('model') || 'ministry_macro';
  const scenario = params.get('scenario') || 'baseline';
  const state = {
    fr: params.get('fr') || '', unit: params.get('unit') || '',
    q: params.get('q') || '', start: params.get('start') || '2024',
    end: params.get('end') || '',
    exact: params.get('exact') === '1', wide: params.get('wide') !== '0'
  };
  loadingView();
  const groups = catalogue.result_groups.filter(g => (model === '*' || g.model_id === model) && (scenario === '*' || g.scenario_id === scenario));
  if (!groups.length) { errorView('No saved run matches this selection.', () => route()); return; }
  const rows = [];
  let done = 0;
  const totalParts = groups.reduce((a, g) => a + g.parts.length, 0);
  for (const g of groups) {
    for (const key of g.parts) {
      rows.push(...await loadAsset(key));
      progressView(++done, totalParts);
      if (!fresh(ticket)) return;
    }
  }
  const release = await releaseP();
  if (!fresh(ticket)) return;
  const units = [...new Set(rows.map(r => r.unit).filter(Boolean))].sort();
  const scenarios = [...new Set(catalogue.result_groups.filter(g => model === '*' || g.model_id === model).map(g => g.scenario_id))];
  let html = head('Forecast explorer', 'Every saved record from the executed runs. Baseline ministry run is the default selection.');
  html += statusStrip(release);
  html += '<div class="filterbar" id="ff">';
  html += selectField('Model', 'model', [{value:'*',label:t('all') + ' (' + fmtInt(catalogue.counts.forecast_records) + ')'}].concat(FORECAST_MODELS().map(m => ({value:m,label:modelMeta(m).short + ' · ' + m}))), model);
  html += selectField('Scenario', 'scenario', [{value:'*',label:t('all')}].concat(scenarios.map(sc => ({value:sc,label:(isTestScenario(sc)?'Sensitivity test · ':'') + scenarioLabel(sc,model)}))), scenario);
  const frs = (release.requirements || []).map(r => r.id);
  html += selectField('Requirement', 'fr', frs, state.fr, t('all'));
  html += '<div class="field"><label for="f-start">Year from</label><input id="f-start" name="start" type="number" min="1985" max="2031" value="' + escapeHTML(state.start) + '" placeholder="1985"></div>';
  html += '<div class="field"><label for="f-end">Year to</label><input id="f-end" name="end" type="number" min="1985" max="2031" value="' + escapeHTML(state.end) + '" placeholder="2031"></div>';
  html += selectField('Unit', 'unit', units, state.unit, t('all'));
  html += '<div class="field"><label for="f-q">' + escapeHTML(t('search')) + '</label><input id="f-q" name="q" type="search" value="' + escapeHTML(state.q) + '" placeholder="series, concept, source, status"></div>';
  html += '<div class="check"><input type="checkbox" id="f-exact"' + (state.exact ? ' checked' : '') + '><label for="f-exact">' + escapeHTML(t('exact')) + '</label></div>';
  html += '<div class="check"><input type="checkbox" id="f-wide"' + (state.wide ? ' checked' : '') + '><label for="f-wide">' + escapeHTML(t('wide')) + '</label></div>';
  html += '<button type="button" class="btn" id="f-reset">' + escapeHTML(t('reset')) + '</button></div>';
  html += '<div id="fcount" class="table-tools"></div><div id="ftable"></div>';
  view().innerHTML = html;
  const currentFilters = () => ({model: model === '*' ? '' : model, scenario: scenario === '*' ? '' : scenario, fr: state.fr, unit: state.unit, start: state.start, end: state.end, q: state.q});
  function syncUrl() {
    const p = new URLSearchParams();
    if (model !== 'ministry_macro') p.set('model', model);
    if (scenario !== 'baseline') p.set('scenario', scenario);
    for (const k of ['fr','unit','q','start','end']) if (state[k]) p.set(k, state[k]);
    if (state.exact) p.set('exact', '1');
    p.set('wide', state.wide ? '1':'0');
    setParams('forecasts', p, false);
  }
  let liveTable = null;
  function renderResult() {
    const filtered = filterRecords(rows, currentFilters());
    $('#fcount').innerHTML = '<strong>' + fmtInt(filtered.length) + '</strong> ' + escapeHTML(t('rows')) + ' shown · ' + fmtInt(rows.length) + ' loaded from ' + groups.length + ' saved run' + (groups.length > 1 ? 's' : '');
    const host = $('#ftable');
    const sig = state.wide ? [...new Set(filtered.map(r => Number(r.year)))].sort((a, b) => a - b).join(',') : '';
    if (liveTable && liveTable.wide === state.wide && liveTable.sig === sig) {
      liveTable.table.opts.rows = liveTable.rows(filtered);
      liveTable.table.opts.exact = state.exact;
      liveTable.table.render();
      return;
    }
    liveTable = null;
    host.innerHTML = '';
    if (state.wide) {
      const keyFn = r => [r.model_id, r.scenario_id, r.series_id, r.unit, r.source_file, r.source_sheet].join('¦');
      const gridify = rowsIn => {
        const map = new Map();
        for (const r of rowsIn) {
          const k = keyFn(r);
          if (!map.has(k)) map.set(k, {meta: r, years: new Map()});
          const g = map.get(k);
          if (!g.years.has(r.year)) g.years.set(r.year, []);
          g.years.get(r.year).push(r);
        }
        return [...map.values()];
      };
      const years = [...new Set(filtered.map(r => Number(r.year)))].sort((a, b) => a - b);
      const gridRows = gridify(filtered);
      const columns = [
        {key:'model', label:'Engine', sticky:true, get:r=>r.meta.model_id, render:r=>modelTag(r.meta.model_id)},
        {key:'scenario', label:'Scenario', get:r=>r.meta.scenario_id, render:r=>'<span class="' + (isTestScenario(r.meta.scenario_id) ? 'scenario-test' : '') + '">' + escapeHTML(r.meta.scenario_id) + '</span>'},
        {key:'series', label:'Series', get:r=>r.meta.series_id},
        {key:'concept', label:'Concept', wrap:true, get:r=>r.meta.concept},
        {key:'unit', label:'Unit', get:r=>r.meta.unit},
        {key:'src', label:'Source', wrap:true, get:r=>r.meta.source_file + ' ' + r.meta.source_sheet, render:r=>'<span class="muted">' + escapeHTML(r.meta.source_file + ' / ' + r.meta.source_sheet) + '</span>'}
      ];
      for (const y of years) columns.push({key:'y' + y, label:String(y), num:true, get:r=>{
        const recs = r.years.get(y);
        if (!recs || !recs.length) return null;
        return recs.length === 1 ? recs[0].value : recs.map(x => x.value).join(' | ');
      }, render:r=>{
        const recs = r.years.get(y);
        if (!recs || !recs.length) return '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>';
        return recs.map(x => escapeHTML(displayValue(x.value, state.exact))).join('<br>');
      }});
      const table = new DataTable({
        rows: gridRows, columns, pageSize: 25, exact: state.exact, searchable: false,
        caption: 'Grouped by engine, run, series, unit and source identity. Multiple original records in one cell are shown stacked.',
        onActivate: r => {
          const list = [...r.years.entries()].sort((a, b) => a[0] - b[0]);
          let d = '<h3 style="margin:0 0 8px">' + escapeHTML(r.meta.series_id) + '</h3>' + recordDetail(r.meta, ['model_id','scenario_id','vintage_id','series_id','concept','unit','frequency','source_file','source_sheet','method','data_status','fr_ids']);
          d += '<div class="table-scroll tall" style="margin-top:10px"><table class="data"><thead><tr><th><button type="button" class="th-btn">Year</button></th><th class="num"><button type="button" class="th-btn">Value</button></th><th><button type="button" class="th-btn">Cell</button></th><th><button type="button" class="th-btn">Status</button></th></tr></thead><tbody>';
          for (const [y, recs] of list) for (const rec of recs) d += '<tr><td>' + y + '</td><td class="num">' + escapeHTML(displayValue(rec.value, true)) + '</td><td>' + escapeHTML(rec.source_cell || '') + '</td><td>' + escapeHTML(rec.status || '') + '</td></tr>';
          openDetail(r.meta.series_id + ' · all years', d + '</tbody></table></div>');
        }
      });
      liveTable = {wide: true, rows: gridify, table, sig};
      host.appendChild(table.root);
    } else {
      const table = new DataTable({
        rows: filtered, pageSize: 25, exact: state.exact, searchable: false,
        columns: [
          {key:'model_id', label:'Engine', sticky:true, render:r=>modelTag(r.model_id)},
          {key:'scenario_id', label:'Scenario', render:r=>'<span class="' + (isTestScenario(r.scenario_id) ? 'scenario-test' : '') + '">' + escapeHTML(r.scenario_id) + '</span>'},
          {key:'series_id', label:'Series'},
          {key:'concept', label:'Concept', wrap:true},
          {key:'year', label:'Year', num:true},
          {key:'value', label:'Value', num:true, render:r=>isUnavailable(r.value)?'<span class="unavail">'+escapeHTML(t('unavailable'))+'</span>':escapeHTML(displayValue(r.value, state.exact))},
          {key:'unit', label:'Unit'},
          {key:'status', label:'Status', wrap:true},
          {key:'data_status', label:'Data status', wrap:true},
          {key:'source', label:'Source', wrap:true, get:r=>(r.source_file||'')+' '+(r.source_sheet||'')+' '+(r.source_cell||''), render:r=>'<span class="muted">'+escapeHTML([r.source_file,r.source_sheet,r.source_cell].filter(Boolean).join(' / '))+'</span>'},
          {key:'fr', label:'FR', get:r=>(r.fr_ids||[]).join(' ')}
        ],
        caption: 'Long-format saved records. Click a row for the complete original record.',
        onActivate: row => openDetail(row.series_id + ' · ' + row.year, recordDetail(row))
      });
      liveTable = {wide: false, rows: rs => rs, table, sig};
      host.appendChild(table.root);
    }
  }
  const localKeys = ['fr','unit','q','start','end'];
  const localApply = () => {
    state.fr = $('#f-fr').value; state.unit = $('#f-unit').value; state.q = $('#f-q').value;
    state.start = $('#f-start').value; state.end = $('#f-end').value;
    syncUrl(); renderResult();
  };
  $('#f-model').addEventListener('change', () => {
    const p = new URLSearchParams();
    const m = $('#f-model').value;
    if (m !== 'ministry_macro') p.set('model', m);
    const first = catalogue.result_groups.find(g => m === '*' || g.model_id === m);
    const sc = $('#f-scenario').value;
    const stillValid = catalogue.result_groups.some(g => (m === '*' || g.model_id === m) && g.scenario_id === sc);
    if (stillValid && sc !== 'baseline') p.set('scenario', sc);
    else if (!catalogue.result_groups.some(g=>g.model_id===m&&g.scenario_id==='baseline') && first) p.set('scenario', first.scenario_id);
    for (const k of localKeys) if (state[k]) p.set(k, state[k]); p.set('wide',state.wide?'1':'0'); if(state.exact)p.set('exact','1');
    setParams('forecasts', p, true);
  });
  $('#f-scenario').addEventListener('change', () => {
    const p = new URLSearchParams();
    if (model !== 'ministry_macro') p.set('model', model);
    const sc = $('#f-scenario').value;
    if (sc !== 'baseline') p.set('scenario', sc);
    for (const k of localKeys) if (state[k]) p.set(k, state[k]); p.set('wide',state.wide?'1':'0'); if(state.exact)p.set('exact','1');
    setParams('forecasts', p, true);
  });
  let localTimer = null;
  const scheduleLocal = () => { clearTimeout(localTimer); localTimer = setTimeout(localApply, 300); };
  for (const k of localKeys) {
    const el = $('#f-' + k);
    if (!el) continue;
    if (el.tagName === 'SELECT') el.addEventListener('change', localApply);
    else { el.addEventListener('input', scheduleLocal); el.addEventListener('change', scheduleLocal); }
  }
  $('#f-exact').addEventListener('change', () => { state.exact = $('#f-exact').checked; syncUrl(); renderResult(); });
  $('#f-wide').addEventListener('change', () => { state.wide = $('#f-wide').checked; syncUrl(); renderResult(); });
  $('#f-reset').addEventListener('click', () => setParams('forecasts', new URLSearchParams(), true));
  renderResult();
}

async function viewScenarios(params, ticket) {
  loadingView();
  const release = await releaseP();
  if (!fresh(ticket)) return;
  const diffGroups = catalogue.result_groups.filter(g => g.difference_parts && g.difference_parts.length);
  const selected = params.get('group') || '';
  let html = head('Saved scenarios', 'Compare saved sensitivity calculations with the same model baseline. Each case retains its original source inputs, units and closure.');
  html += statusStrip(release);
  html += '<div class="panel"><h2>Saved runs with baseline differences</h2><div class="table-scroll"><table class="data"><thead><tr><th><button type="button" class="th-btn">Engine</button></th><th><button type="button" class="th-btn">Scenario</button></th><th class="num"><button type="button" class="th-btn">Rows</button></th><th><button type="button" class="th-btn"></button></th></tr></thead><tbody>';
  for (const g of diffGroups) {
    const active = selected === g.model_id + '|' + g.scenario_id;
    html += '<tr' + (active ? ' class="selected-row"' : '') + '><td>' + modelTag(g.model_id) + '</td><td><span class="' + (isTestScenario(g.scenario_id) ? 'scenario-test' : '') + '">' + escapeHTML(scenarioLabel(g.scenario_id,g.model_id)) + (isTestScenario(g.scenario_id) ? ' <span class="badge test">TEST ONLY</span>' : '') + '</span></td><td class="num">' + fmtInt(g.row_count) + '</td><td><a class="btn small" href="#/scenarios?group=' + encodeURIComponent(g.model_id + '|' + g.scenario_id) + '">Open</a></td></tr>';
  }
  html += '</tbody></table></div></div>';
  html += '<div class="panel"><h2>All saved runs</h2><div class="table-scroll"><table class="data"><thead><tr><th><button type="button" class="th-btn">Engine</button></th><th><button type="button" class="th-btn">Scenario</button></th><th class="num"><button type="button" class="th-btn">Records</button></th><th><button type="button" class="th-btn">Years</button></th><th><button type="button" class="th-btn"></button></th></tr></thead><tbody>';
  for (const g of catalogue.result_groups) {
    html += '<tr><td>' + modelTag(g.model_id) + '</td><td><span class="' + (isTestScenario(g.scenario_id) ? 'scenario-test' : '') + '">' + escapeHTML(scenarioLabel(g.scenario_id,g.model_id)) + '</span>' + (g.difference_parts ? ' <span class="badge pass">delta</span>' : '') + '</td><td class="num">' + fmtInt(g.row_count) + '</td><td class="muted">' + escapeHTML(g.years[0] + '-' + g.years[g.years.length - 1]) + '</td><td><a class="btn small" href="#/forecasts?model=' + encodeURIComponent(g.model_id) + '&scenario=' + encodeURIComponent(g.scenario_id) + '">Browse</a></td></tr>';
  }
  html += '</tbody></table></div><p class="notice-line">Oxlon baseline and imported comparison paths are available through the forecast explorer; they are not a Ministry engine run and carry no scenario delta.</p></div>';
  html += '<div id="scenario-detail"></div>';
  view().innerHTML = html;
  if (selected) {
    const [m, s] = selected.split('|');
    const g = groupEntry(m, s);
    if (g && g.difference_parts) {
      const host = $('#scenario-detail');
      host.innerHTML = '<div class="panel"><h2>' + escapeHTML(s) + '</h2><div class="loading">' + escapeHTML(t('loading')) + '<div class="bar"><i></i></div></div></div>';
      const rows = [];
      for (const key of g.difference_parts) rows.push(...await loadAsset(key));
      if (!fresh(ticket)) return;
      const dcols = [
        {key:'series_id', label:'Series', sticky:true},
        {key:'concept', label:'Concept', wrap:true},
        {key:'year', label:'Year', num:true},
        {key:'baseline_value', label:'Baseline', num:true, render:r=>isUnavailable(r.baseline_value)?'<span class="unavail">'+escapeHTML(t('unavailable'))+'</span>':escapeHTML(displayValue(r.baseline_value))},
        {key:'value', label:'Scenario', num:true, render:r=>isUnavailable(r.value)?'<span class="unavail">'+escapeHTML(t('unavailable'))+'</span>':escapeHTML(displayValue(r.value))},
        {key:'difference', label:'Difference', num:true, render:r=>{ if(isUnavailable(r.difference)) return '<span class="unavail">'+escapeHTML(t('unavailable'))+'</span>'; const n=numericValue(r.difference); const cls=n>0?'diff-pos':(n<0?'diff-neg':''); return '<span class="'+cls+'">'+escapeHTML(displayValue(r.difference))+'</span>'; }},
        {key:'difference_unit', label:'Unit'},
        {key:'comparison_status', label:'Comparison', wrap:true},
        {key:'source', label:'Source', wrap:true, get:r=>(r.source_file||'')+' '+(r.source_sheet||'')+' '+(r.source_cell||''), render:r=>'<span class="muted">'+escapeHTML([r.source_file,r.source_sheet,r.source_cell].filter(Boolean).join(' / '))+'</span>'}
      ];
      host.innerHTML = '<div class="panel"><h2>' + escapeHTML(scenarioLabel(s,m)) + ' <span class="badge">Saved calculation</span>' + (isTestScenario(s) ? ' <span class="badge test">TEST ONLY</span>' : '') + '</h2><div id="sd-table"></div></div>';
      if(g.scenario_detail) host.insertAdjacentHTML('afterbegin','<section class="panel"><h2>Scenario definition and source inputs</h2>'+propsTable(g.scenario_detail)+'</section>');
      const table = new DataTable({rows, columns: dcols, pageSize: 25, caption: 'Precomputed differences against the same-engine baseline. Source identities join exactly.',
        onActivate: row => openDetail(row.series_id + ' · ' + row.year, recordDetail(row, RECORD_FIELDS.concat(['baseline_value','difference','difference_unit','comparison_status'])))});
      host.querySelector('#sd-table').appendChild(table.root);
    }
  }
}

async function viewModels(params,ticket){
 loadingView();const release=await releaseP();if(!fresh(ticket))return;
 let h=head(lang==='az'?'Modellər və metodlar':'Models and methods',lang==='az'?'Nazirliyin orijinal sistemləri və Oxlon modeli ayrıca təqdim olunur.':'The supplied Ministry systems and the independent Oxlon model are presented separately.');
 const rows=[
 ['Purpose','Bottom-up macroeconomic forecast from company, product and branch plans','Integrated structural macroeconomic framework with accounting reconciliation','Independent FR1–FR12 econometric forecasting pipeline','Published staff benchmark'],
 ['Authoritative source','Original linked workbooks in Modellər / Makroekonometrik model','Original Modellər / CAEM.xlsb; the older CAEM.xlsx is a separate project file','Updated project datasets, recorded notebooks and published specifications','Article IV report 26/112, Table 1'],
 ['Mechanism','Physical quantities × domestic/export prices → branch accounts → value added, net taxes and GDP; linked trade, investment, fiscal and social blocks','Structural accounts; consumption, private investment, exports, goods imports, inflation and interest-rate behaviours; potential output and policy selectors','Equation selection, assumptions, component aggregation and explicit reconciliation; goods drivers precede selected service forecasts','Dated published figures; no separate executable IMF model'],
 ['Source coverage','11 linked workbooks · 109 sheets · 125,253 original formulas','54 source sheets · 51,294 formula anchors','486 catalogue specifications, including alternatives and 92 Ministry references; 747 dictionary entries','21 benchmark observations'],
 ['Data boundary','2025 expected; native forecasts 2026–2030','2024 last actual; native forecasts 2025–2029','Histories through 2025; estimates 2026–2030. Observed, derived and proxy series remain labelled','2025 staff estimate; projections 2026–2031'],
 ['Accounting and estimation','Source formulas are calculated from literal inputs. Missing dependencies and source errors remain visible','CP: demand wedge adjusts to production growth. YP: production growth adjusts to demand. Both reconcile the GDP deflator; tolerance 0.001 on each residual','Sample dates, adjusted R², equation standard error and recorded backtests are shown where available. Alternative specifications are distinguished from operative selections','Values retain the report date and definitions'],
 ['Versioned corrections','Year headers excluded from economic outputs; original formula graph retained','Solver checks both residuals, at most 20 reconciliation iterations per year, rechecks earlier years and makes a final all-year check. Manual calibration targets private investment and goods imports at their native perimeters','Separate statutory and production non-oil GDP definitions; corrected source deflators; governed input overlay and documented source/proxy statuses','No invented recalculation or updating'],
 ['Interpretation','Original Department assumptions, rather than an authenticated latest Ministry forecast vintage','Native selectors and accounting distinctions are preserved. Alternative floating/manual regimes are not fully verified','Independent model results; separate assumptions and input vintages','External comparison, rather than a fourth forecasting engine']
 ];
 h+='<div class="table-scroll"><table class="data model-matrix"><caption>Model architecture and economic interpretation</caption><thead><tr><th class="sticky-col">Attribute</th><th>Ministry macroeconometric model</th><th>Ministry CAEM</th><th>Oxlon</th><th>IMF Article IV</th></tr></thead><tbody>'+rows.map(r=>'<tr><th scope="row" class="sticky-col">'+escapeHTML(r[0])+'</th>'+r.slice(1).map(c=>'<td class="wrap">'+escapeHTML(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
 h+='<section class="panel"><h2>Source models and implementation</h2><div class="actions-row"><a class="btn" href="#/equations?tab=legacy">Ministry econometric equations</a><a class="btn" href="#/equations?tab=native&model=ministry_macro">Linked workbook formulas</a><a class="btn" href="#/equations?tab=caem">CAEM structural equations</a><a class="btn" href="#/equations?tab=native&model=ministry_caem">CAEM workbook formulas</a><a class="btn" href="#/equations?tab=published&model=oxlon.corrected.20260917">Oxlon specifications</a></div></section>';
 h+='<section class="panel"><h2>Saved scenario calculations</h2><table class="data"><thead><tr><th>Model</th><th>Control</th><th>Source input</th><th>Meaning</th><th>Closure</th></tr></thead><tbody>';
 const controls=[['Ministry macro','ACG volume','Original product-volume plans','+10% physical ACG volume; linked workbook transmission','Original graph'],['CAEM','Partner growth','Scenario D44:F44','Percentage-point change; 2025–2027','YP'],['CAEM','Oil price','Scenario D56:F56','Percent change in the oil-price level; 2025–2027','YP'],['CAEM','GDP supply','Scenario L15:N15','Percentage-point production-growth change; 2025–2027','CP'],['CAEM','Government compensation','Fiscal O320:Q320','Percent change in the literal employee-compensation amount; 2025–2027','YP'],['CAEM','Policy rate','Scenario D31:F31','Percentage-point interest-rate change; 2025–2027','YP']];
 h+=controls.map(r=>'<tr>'+r.map(c=>'<td class="wrap">'+escapeHTML(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table><p class="notice-line">The original import-price control has no active transmission in the supplied selected graph; it is retained as a diagnostic case. The generic scenario-sheet fiscal control is inactive in the selected fiscal accounts. Saved tests and scenarios are identified by their source case; they are not official forecast assumptions.</p><a class="btn" href="#/scenarios">Compare saved scenario results →</a></section>';
 h+='<section class="panel"><h2>Definitions that affect comparison</h2><table class="data"><thead><tr><th>Concept</th><th>Required distinction</th></tr></thead><tbody>';
 const defs=[['GDP','Market-price GDP, basic-price value added and constructed gross-output proxies have different perimeters.'],['Non-oil GDP','Statutory market-price non-oil GDP differs from the production partition that includes reclassified non-oil mining.'],['CAEM nominal GDP','Core GDP: expenditure framework, sheet 5a row 24. Production-book GDP: sheet 1a row 85. The source nominal-account difference remains; GDP-growth and deflator closure alone does not eliminate it.'],['Trade and external accounts','National-account AZN trade, balance-of-payments USD flows, gross institutional flows and net balances require distinct definitions.'],['Investment and fiscal accounts','Investment including inventories differs from fixed-capital investment; state-budget and consolidated fiscal accounts require separate mappings.'],['Prices and exchange rates','Annual-average and end-period CPI/FX are separate concepts. Deflator indexes and percentage changes are also distinct.'],['Oil and gas quantities','Questionable native physical-unit scales remain unresolved rather than being silently multiplied or divided.'],['Common-input comparison','An authenticated Ministry vintage and approved company, product, branch, tax and institutional input bridges are required before a common-input model comparison.']];
 h+=defs.map(r=>'<tr><th scope="row">'+escapeHTML(r[0])+'</th><td class="wrap">'+escapeHTML(r[1])+'</td></tr>').join('')+'</tbody></table></section>';
 view().innerHTML=h;
}


function equationEntryByPath(path) { return catalogue.equation_catalogues.find(e => e.path === path); }
async function viewEquations(params, ticket) {
  const tab = params.get('tab') || 'published';
  loadingView();
  const release = await releaseP();
  if (!fresh(ticket)) return;
  let html = head('Equations', 'Econometric specifications, original CAEM structural equations and the complete source workbook formula networks.');
  html += statusStrip(release);
  const tabs = [['published','Econometric specifications'],['caem','CAEM methodology'],['native','Original workbook formulas'],['legacy','Ministry EViews equations (92)']];
  html += '<div class="tabs" role="tablist">' + tabs.map(([id, lab]) => '<button type="button" role="tab" class="' + (tab === id ? 'active' : '') + '" data-tab="' + id + '" aria-selected="' + (tab === id) + '">' + lab + '</button>').join('') + '</div>';
  html += '<div id="eq-body"></div>';
  view().innerHTML = html;
  view().querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', () => {
    const p = parseHash().params; p.set('tab', b.getAttribute('data-tab'));
    for (const k of ['model','book','sheet','fr','q']) p.delete(k);
    setParams('equations', p, true);
  }));
  const body = $('#eq-body');
  if (tab === 'published' || tab === 'legacy') {
    const entry = tab === 'published' ? equationEntryByPath('models/oxlon/outputs/equations_catalog.csv') : catalogue.equation_catalogues.find(e => e !== equationEntryByPath('models/oxlon/outputs/equations_catalog.csv'));
    const rows = await loadAsset(entry.key);
    if (!fresh(ticket)) return;
    const modelFilter = params.get('model') || '';
    const frFilter = params.get('fr') || '';
    const frs = [...new Set(rows.map(r => r.fr).filter(Boolean))].sort();
    const models = [...new Set(rows.map(r => r.model_id).filter(Boolean))].sort();
    let bar = '<div class="panel"><p class="notice-line">' + escapeHTML(entry.note || '') + ' ' + (tab === 'published' ? 'Published regressor specifications retain their source syntax. Parameter values are shown only where supplied; alternative specifications are included.' : 'Historical EViews equations complement the operative linked workbook formulas.') + '</p>';
    bar += '<div class="filterbar" id="eqf">';
    bar += selectField('Model', 'model', models.map(m => ({value:m, label:modelMeta(m).short + ' · ' + m})), modelFilter, t('all'));
    if (frs.length) bar += selectField('Requirement', 'fr', frs, frFilter, t('all'));
    bar += '<button type="button" class="btn" id="eq-reset">' + escapeHTML(t('reset')) + '</button>';
    bar += '</div><div id="eq-table"></div></div>';
    body.innerHTML = bar;
    const readBar = () => {
      const p = parseHash().params;
      const mv = body.querySelector('#f-model'); const fv = body.querySelector('#f-fr');
      if (mv) { if (mv.value) p.set('model', mv.value); else p.delete('model'); }
      if (fv) { if (fv.value) p.set('fr', fv.value); else p.delete('fr'); }
      setParams('equations', p, false);
      table.opts.rows = rows.filter(r => (!mv || !mv.value || r.model_id === mv.value) && (!fv || !fv.value || r.fr === fv.value));
      table.state.page = 1;
      table.render();
    };
    const filteredRows = rows.filter(r => (!modelFilter || r.model_id === modelFilter) && (!frFilter || r.fr === frFilter));
    const table = new DataTable({
      rows: filteredRows, pageSize: 25,
      columns: [
        {key:'eq_name', label:'Name', sticky:true, wrap:true},
        {key:'fr', label:'FR'},
        {key:'model_id', label:'Engine', render:r=>modelTag(r.model_id)},
        {key:'tex', label:'Specification', wrap:true, get:r=>r.tex||r.expression||r.lhs||'', render:r=>'<span data-math="'+escapeHTML(r.tex||r.expression||'')+'"></span><div class="equation-original">'+escapeHTML(r.expression||'')+'</div>'},
        {key:'sample', label:'Sample', get:r=>[r.sample_start,r.sample_end].filter(Boolean).join('-')},
        {key:'adj_r2', label:'Adj. R²', num:true},
        {key:'se_regression', label:'S.E.', num:true},
        {key:'description', label:'Description', wrap:true, render:r=>'<span class="muted">'+escapeHTML(String(r.description||'').slice(0,160))+'</span>'}
      ],
      caption: entry.count + ' catalogue rows. Alternative specifications and reference rows are included.',
      onActivate: row => {
        let d = '<div class="math-block" data-math="' + escapeHTML(row.tex || '') + '" data-display="1"></div>';
        d += propsTable(row);
        if (row.expression) d += '<h3 style="font-size:13px;margin:12px 0 4px">Source expression</h3><div class="formula-src">' + escapeHTML(row.expression) + '</div>';
        openDetail(row.eq_name || 'Catalogue row', d);
      },
      onRendered: root => mathAfterRender(root)
    });
    body.querySelector('#eq-table').appendChild(table.root);
    $('#eq-reset').addEventListener('click', () => {
      body.querySelector('#f-model').value = '';
      const fv = body.querySelector('#f-fr'); if (fv) fv.value = '';
      readBar();
    });
    wireFilterbar($('#eqf'), readBar);
    return;
  }
  if (tab === 'caem') {
    const math = await sourceMathP();
    if (!fresh(ticket)) return;
    const featured = [
      [37, 'Consumption'], [49, 'Private investment'], [61, 'Exports'],
      [67, 'Goods imports'], [1, 'Inflation'], [26, 'Policy rate']
    ];
    let h = '<div class="panel"><h2>Core methodology expressions</h2><p class="notice-line">Original CAEM methodology expressions with their supplied parameters, lags and accents. These are methodology source, not newly estimated coefficients.</p>';
    for (const [idx, label] of featured) {
      const item = math.find(m => m.source_index === idx);
      if (!item) continue;
      h += '<div style="margin:10px 0"><div style="font-size:12px;color:var(--ink-faint);font-weight:600">' + escapeHTML(label) + ' · source ' + idx + '</div><div class="math-block" data-math="' + escapeHTML(item.tex) + '" data-display="1"></div></div>';
    }
    h += '</div><div class="panel"><h2>All indexed source expressions (' + math.length + ')</h2><div id="caem-table"></div></div>';
    body.innerHTML = h;
    mathAfterRender(body.querySelector('.panel'));
    const table = new DataTable({
      rows: math, pageSize: 25,
      columns: [
        {key:'source_index', label:'Index', num:true, sticky:true},
        {key:'tex', label:'Expression', wrap:true, get:r=>r.source_text||r.tex, render:r=>'<span data-math="'+escapeHTML(r.tex)+'"></span>'},
        {key:'source_text', label:'Source text', wrap:true, render:r=>'<span class="muted">'+escapeHTML(String(r.source_text||'').slice(0,180))+'</span>'}
      ],
      caption: 'Every Office Math expression extracted from the original CAEM Word document, including variable definitions.',
      onActivate: row => openDetail('CAEM source expression ' + row.source_index, '<div class="math-block" data-math="' + escapeHTML(row.tex) + '" data-display="1"></div>' + propsTable(row)),
      onRendered: root => mathAfterRender(root)
    });
    body.querySelector('#caem-table').appendChild(table.root);
    mathAfterRender(body);
    return;
  }
  if (tab === 'native') {
    const natives = catalogue.tables.filter(x => x.kind === 'native' || x.kind === 'native-arrays' || x.kind === 'native-names');
    const modelParam = params.get('model') || 'ministry_macro';
    const books = [...new Set(natives.filter(n => n.model_id === modelParam).map(n => n.book || n.title))];
    const bookParam = params.get('book') || books[0];
    const sheets = natives.filter(n => n.model_id === modelParam && (n.book || n.title) === bookParam);
    const sheetParam = params.get('sheet') || (sheets[0] && sheets[0].id);
    const entry = natives.find(n => n.id === sheetParam) || sheets[0];
    let bar = '<div class="panel"><div class="filterbar" id="nf">';
    bar += selectField('Model', 'model', [{value:'ministry_macro',label:'Ministry macro'},{value:'ministry_caem',label:'Ministry CAEM'}], modelParam);
    bar += selectField('Book', 'book', books, bookParam);
    bar += selectField('Sheet', 'sheet', sheets.map(s => ({value:s.id, label:(s.sheet||s.title) + ' (' + fmtInt(s.row_count) + ')'})), entry && entry.id);
    bar += '</div><p class="notice-line">' + escapeHTML((entry && entry.note) || '') + '</p><div id="native-table"></div></div>';
    body.innerHTML = bar;
    $('#f-model').addEventListener('change', () => { const p = parseHash().params; p.set('model', $('#f-model').value); p.delete('book'); p.delete('sheet'); setParams('equations', p, true); });
    $('#f-book').addEventListener('change', () => { const p = parseHash().params; p.set('book', $('#f-book').value); p.delete('sheet'); setParams('equations', p, true); });
    $('#f-sheet').addEventListener('change', () => { const p = parseHash().params; p.set('sheet', $('#f-sheet').value); setParams('equations', p, true); });
    if (!entry) { body.querySelector('#native-table').innerHTML = '<div class="empty-state">No formula export for this selection.</div>'; return; }
    const host = body.querySelector('#native-table');
    host.innerHTML = '<div class="loading">' + escapeHTML(t('loading')) + '<div class="bar"><i></i></div></div>';
    const rows = await loadTableRows(entry);
    if (!fresh(ticket)) return;
    host.innerHTML = '';
    const cols = entry.columns.map((label, i) => ({
      key: 'c' + i, label, wrap: i === entry.formula_column || label.toLowerCase().includes('formula'),
      get: r => r[i],
      render: i === entry.formula_column ? (r => '<code>' + escapeHTML(String(r[i] ?? '')) + '</code>') : undefined
    }));
    const table = new DataTable({
      rows, columns: cols, pageSize: 25,
      caption: entry.title + ' · ' + fmtInt(entry.row_count) + ' rows. Cache values are references, not substituted results.',
      onActivate: row => {
        let d = '<table class="props"><tbody>';
        entry.columns.forEach((label, i) => { d += '<tr><th>' + escapeHTML(label) + '</th><td>' + (isUnavailable(row[i]) ? '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>' : '<code>' + escapeHTML(typeof row[i] === 'object' ? JSON.stringify(row[i]) : String(row[i])) + '</code>') + '</td></tr>'; });
        d += '</tbody></table>';
        const fc = entry.formula_column;
        if (fc !== undefined && fc !== null && row[fc]) {
          d += '<h3 style="font-size:13px;margin:12px 0 4px">Source formula (verbatim)</h3><div class="math-block" data-math="' + escapeHTML(literalTex(row[fc])) + '" data-display="1"></div><div class="formula-src">' + escapeHTML(String(row[fc])) + '</div>';
        }
        openDetail(entry.title + ' · ' + (row[0] || ''), d);
      }
    });
    host.appendChild(table.root);
    return;
  }
}

async function viewWorkbook(params,ticket){
 const sheets=catalogue.workbook;const want=params.get('sheet')||'FR1';const entry=sheets.find(w=>w.sheet===want)||sheets[0];
 loadingView();const rows=await loadTableRows(entry);if(!fresh(ticket))return;
 const title=entry.sheet==='Verification'?'Source checks':entry.sheet==='Read me'?'Data definitions':entry.sheet;
 const ordered=[...sheets].sort((a,b)=>{const f=x=>/^FR\d+$/.test(x.sheet)?Number(x.sheet.slice(2)):20+sheets.indexOf(x);return f(a)-f(b)});
 let h=head(lang==='az'?'Nəticə cədvəlləri':'Results workbook tables','Published result tables, shown with their economic column headings. Select any row for all original fields and exact values.');
 h+='<div class="tabs" role="tablist">'+ordered.map(w=>'<button type="button" role="tab" data-sheet="'+escapeHTML(w.sheet)+'" aria-selected="'+(w.sheet===entry.sheet)+'" class="'+(w.sheet===entry.sheet?'active':'')+'">'+escapeHTML(w.sheet==='Verification'?'Source checks':w.sheet==='Read me'?'Data definitions':w.sheet)+'</button>').join('')+'</div>';
 h+='<section class="panel"><h2>'+escapeHTML(title)+'</h2><p class="notice-line">'+escapeHTML(entry.sheet==='Verification'?'Source accounting checks and remaining input requirements.':rows[1]?.[0]||'')+'</p>';
 if(/^FR\d+$/.test(entry.sheet))h+='<div class="check"><input id="wb-all-columns" type="checkbox"><label for="wb-all-columns">Show all source and method columns</label></div>';
 h+='<div id="wb-grid"></div></section>';view().innerHTML=h;
 view().querySelectorAll('[data-sheet]').forEach(b=>b.addEventListener('click',()=>setParams('workbook',new URLSearchParams('sheet='+b.dataset.sheet),true)));
 const headers=rows[3]||entry.columns;const data=rows.slice(4).map((r,i)=>({values:r,row:i+5}));
 function mount(){
  const full=$('#wb-all-columns')?.checked;const indices=headers.map((_,i)=>i).filter(i=>headers[i]!==null&&headers[i]!==undefined&&headers[i]!==''&&(!/^FR\d+$/.test(entry.sheet)||full||[0,3,4,5,6,7,8,9,10,11].includes(i)));
  const columns=indices.map(i=>({key:'c'+i,label:String(headers[i]),get:r=>r.values[i],num:typeof headers[i]==='number'||['Year','Value','GDP residual','Deflator residual','Tolerance','Bytes'].includes(headers[i]),wrap:['Concept','Method','Source file','Source sheet','Rule','Result','Provenance / role','Source boundary / vintage'].includes(headers[i]),sticky:i===indices[0],render:r=>{const v=r.values[i];return v===null||v===undefined||v===''?'<span class="unavail">—</span>':escapeHTML(displayValue(v));}}));
  const host=$('#wb-grid');host.innerHTML='';host.appendChild(new DataTable({rows:data,columns,pageSize:25,caption:entry.path+' · '+fmtInt(data.length)+' original source rows after the heading. Empty cells remain empty.',onActivate:r=>{const obj={'Workbook':'MIIS_1551_RESULTS.xlsx','Sheet':entry.sheet,'Original row':r.row};headers.forEach((v,i)=>{obj[String(v||entry.columns[i])+' ['+entry.columns[i]+']']=r.values[i]});openDetail(entry.sheet+' · row '+r.row,propsTable(obj));}}).root);
 }
 $('#wb-all-columns')?.addEventListener('change',mount);mount();
}

async function viewLibrary(params, ticket) {
  const kind = params.get('kind') || '';
  const scope = params.get('scope') || '';
  const model = params.get('model') || '';
  let html = head('Data library', 'Complete input and result tables, source dictionaries, workbook sheets and original formula networks. Select a dataset to read all its records here.');
  const kinds = [...new Set(catalogue.tables.map(x => x.kind))];
  const scopes = [...new Set(catalogue.tables.map(x => x.scope))];
  const models = [...new Set(catalogue.tables.map(x => x.model_id).filter(Boolean))];
  html += '<div class="filterbar" id="lf">';
  html += selectField('Kind', 'kind', kinds, kind, t('all'));
  html += selectField('Scope', 'scope', scopes, scope, t('all'));
  html += selectField('Model', 'model', models, model, t('all'));
  html += '<button type="button" class="btn" id="l-reset">' + escapeHTML(t('reset')) + '</button>';
  html += '</div><div id="lib-table"></div>';
  view().innerHTML = html;
  const rows = catalogue.tables.filter(x => (!kind || x.kind === kind) && (!scope || x.scope === scope) && (!model || x.model_id === model));
  const table = new DataTable({
    rows, pageSize: 25,
    columns: [
      {key:'title', label:'Dataset', sticky:true, wrap:true},
      {key:'path', label:'Source path', wrap:true, render:r=>'<code>'+escapeHTML(r.path)+'</code>'},
      {key:'kind', label:'Kind', render:r=>'<span class="badge">'+escapeHTML(r.kind)+'</span>'},
      {key:'scope', label:'Scope', wrap:true, render:r=>'<span class="' + (/Verification|historical|Original/i.test(r.scope) ? 'badge pending' : 'badge') + '">'+escapeHTML(r.scope)+'</span>'},
      {key:'model_id', label:'Engine', render:r=>r.model_id?modelTag(r.model_id):'<span class="unavail">-</span>'},
      {key:'row_count', label:'Rows', num:true},
      {key:'cols', label:'Columns', num:true, get:r=>r.columns.length},
      {key:'parts', label:'Parts', num:true, get:r=>r.parts.length}
    ],
    caption: 'Verification, historical and archived sources are labelled and never mixed into current forecasts.',
    onActivate: row => {
      if (row.kind === 'workbook') setParams('workbook', new URLSearchParams('sheet=' + row.sheet), true);
      else setParams('table', new URLSearchParams('id=' + row.id), true);
    }
  });
  $('#lib-table').appendChild(table.root);
  $('#l-reset').addEventListener('click', () => setParams('library', new URLSearchParams(), true));
  wireFilterbar($('#lf'), () => {
    const p = parseHash().params;
    for (const k of ['kind','scope','model']) { const el = $('#f-' + k); if (el && el.value) p.set(k, el.value); else p.delete(k); }
    setParams('library', p, true);
  });
}

async function viewTable(params, ticket) {
  const id = params.get('id') || '';
  const entry = catalogue.tables.find(x => x.id === id);
  if (!entry) { errorView('Unknown dataset.', () => route()); return; }
  if (entry.kind === 'workbook') { setParams('workbook', new URLSearchParams('sheet=' + (entry.sheet || entry.title)), false); return route(); }
  loadingView();
  const rows = await loadTableRows(entry, (d, n) => progressView(d, n));
  if (!fresh(ticket)) return;
  let html = head(entry.title, entry.note || null, entry.path);
  html += '<div class="counters"><span class="counter"><span class="n">' + fmtInt(entry.row_count) + '</span><span class="l">' + escapeHTML(t('rows')) + '</span></span><span class="counter"><span class="n">' + entry.columns.length + '</span><span class="l">columns</span></span><span class="counter"><span class="n">' + escapeHTML(entry.kind) + '</span><span class="l">kind</span></span><span class="counter"><span class="n" style="font-size:13px">' + escapeHTML(entry.scope) + '</span><span class="l">scope</span></span></div>';
  html += '<div id="t-host"></div>';
  view().innerHTML = html;
  const cols = entry.columns.map((label, i) => ({
    key: 'c' + i, label, wrap: String(label).length > 24 || i === entry.formula_column,
    get: r => r[i],
    render: i === entry.formula_column ? (r => '<code>' + escapeHTML(String(r[i] ?? '').slice(0, 160)) + '</code>') : (r => {
      const v = r[i];
      if (v === '') return '';
      if (isUnavailable(v)) return '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>';
      return escapeHTML(displayValue(v));
    })
  }));
  const q0 = params.get('q') || '';
  const table = new DataTable({
    rows, columns: cols, pageSize: 25,
    state: {q: q0, sort: null, dir: 'asc', page: 1, size: 25},
    caption: entry.row_count + ' source rows. Empty source strings stay empty; missing values are marked unavailable.',
    onActivate: row => {
      const obj = {};
      entry.columns.forEach((label, i) => { obj[label + '  [' + String.fromCharCode(65 + (i < 26 ? i : i % 26)) + (i >= 26 ? Math.floor(i / 26) : '') + ']'] = (typeof row[i] === 'object' && row[i] !== null) ? JSON.stringify(row[i]) : row[i]; });
      obj['source path'] = entry.path;
      if (entry.kind === 'native' && entry.formula_column !== undefined && row[entry.formula_column]) {
        openDetail(entry.title + ' · row', '<div class="formula-src">' + escapeHTML(row[entry.formula_column]) + '</div>' + propsTable(obj));
      } else openDetail(entry.title + ' · row', propsTable(obj));
    }
  });
  $('#t-host').appendChild(table.root);
}

async function viewMethods(params,ticket){
 const originals=catalogue.documents.filter(d=>d.path.startsWith('sources/')&&['docx','pdf-text','markdown'].includes(d.format));
 let h=head(lang==='az'?'Metodologiya və mənbələr':'Methodology and sources',lang==='az'?'Texniki sənədlər, metodlar və iqtisadi təriflər bu səhifədə oxuna bilər.':'Source technical documents, methods and economic definitions can be read within this website.');
 h+='<section class="panel"><h2>Original source documents</h2><div id="original-documents"></div></section>';
 h+='<section class="panel"><h2>Econometric methods and diagnostics</h2><table class="data"><thead><tr><th>Method</th><th>Application</th><th>What is available</th></tr></thead><tbody>';
 const methods=[['Bottom-up accounting','Ministry macro model: company/product quantities and prices feed branch value added, taxes and aggregate accounts','Full original workbook formulas, literal input series, source addresses and saved calculations'],['Structural behavioural equations','CAEM: six behaviour equations with source parameters, lags and add-factors','Original methodological expressions, source workbook formulas and recorded calibration calculations'],['HP and HP with priors','CAEM trend/potential-output functions','Original method definitions and formula calls; source selector settings are retained'],['CP / YP reconciliation','CAEM demand/supply and deflator consistency','Both residuals for every forecast year; tolerance 0.001'],['Specification comparison','Oxlon equation catalogue includes alternatives and historical Ministry references','Dependent variable, regressor specification, source, sample dates, adjusted R² and regression standard error where supplied'],['Recorded forecasting pipeline','Oxlon FR notebooks; saved source, figures and result tables','Complete recorded notebook cells and outputs, with code available in expandable sections'],['Forecast backtesting','Oxlon historical forecast evaluation','6,739 source backtest records; horizons, models and evaluation measures retain their original fields'],['Input governance','Compatible official source observations, assumptions and per-series vintage labels','Input tables, source snapshots, assumption registry, unit/source dictionaries and empty official-overlay tables'],['Accounting definitions','Statutory/production GDP, prices, trade and fiscal perimeters','Common concept mappings and 150 source snapshots, including explicit definition/vintage compatibility']];
 h+=methods.map(r=>'<tr>'+r.map(c=>'<td class="wrap">'+escapeHTML(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table></section>';
 h+='<section class="panel"><h2>Recorded model notebooks</h2><div id="notebook-index"></div></section><section class="panel"><h2>Model documentation and calculation sources</h2><div id="doc-table"></div></section>';
 view().innerHTML=h;
 const docColumns=[{key:'title',label:'Document',sticky:true,wrap:true},{key:'path',label:'Source',wrap:true},{key:'format',label:'Format'},{key:'scope',label:'Scope',wrap:true}];
 $('#original-documents').appendChild(new DataTable({rows:originals,columns:docColumns,tall:false,pageSize:25,onActivate:r=>setParams('document',new URLSearchParams('id='+r.id),true)}).root);
 $('#notebook-index').appendChild(new DataTable({rows:catalogue.notebooks,columns:[{key:'title',label:'Notebook',sticky:true},{key:'path',label:'Source',wrap:true},{key:'cell_count',label:'Cells',num:true},{key:'note',label:'Scope',wrap:true}],tall:false,onActivate:r=>setParams('notebook',new URLSearchParams('id='+r.id),true)}).root);
 $('#doc-table').appendChild(new DataTable({rows:catalogue.documents.filter(d=>!originals.includes(d)),columns:docColumns,pageSize:25,onActivate:r=>setParams('document',new URLSearchParams('id='+r.id),true)}).root);
}


let jsonPaged = [];
function renderJSONValue(v, depth) {
  if (v === null || v === undefined) return '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>';
  if (typeof v !== 'object') return escapeHTML(String(v));
  if (Array.isArray(v)) {
    if (!v.length) return '<span class="unavail">empty</span>';
    if (v.length > 25) {
      const idx = jsonPaged.length;
      jsonPaged.push(v);
      return '<div class="json-paged" data-arr="' + idx + '"></div>';
    }
    if (v.every(x => typeof x !== 'object' || x === null)) return v.map(x => escapeHTML(String(x))).join(', ');
    const allObj = v.every(x => x && typeof x === 'object' && !Array.isArray(x));
    if (allObj) {
      const keys = [...new Set(v.flatMap(x => Object.keys(x)))];
      let h = '<div class="table-scroll"><table class="data"><thead><tr>' + keys.map(k => '<th><button type="button" class="th-btn">' + escapeHTML(k) + '</button></th>').join('') + '</tr></thead><tbody>';
      for (const item of v) h += '<tr>' + keys.map(k => '<td class="wrap">' + renderJSONValue(item[k], depth + 1) + '</td>').join('') + '</tr>';
      return h + '</tbody></table></div>';
    }
    return '<ol style="margin:4px 0 4px 20px">' + v.map(x => '<li>' + renderJSONValue(x, depth + 1) + '</li>').join('') + '</ol>';
  }
  let h = '<table class="props"><tbody>';
  for (const [k, val] of Object.entries(v)) h += '<tr><th>' + escapeHTML(k) + '</th><td>' + renderJSONValue(val, depth + 1) + '</td></tr>';
  return h + '</tbody></table>';
}
function mountPagedJSON(root) {
  root.querySelectorAll('.json-paged').forEach(slot => {
    const arr = jsonPaged[Number(slot.getAttribute('data-arr'))];
    if (!arr) return;
    const allObj = arr.every(x => x && typeof x === 'object' && !Array.isArray(x));
    let columns;
    if (allObj) {
      const keys = [...new Set(arr.flatMap(x => Object.keys(x)))];
      columns = keys.map(k => ({key: k, label: k, wrap: true, get: r => r[k], render: r => {
        const v = r[k];
        if (v === null || v === undefined) return '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>';
        return typeof v === 'object' ? '<code>' + escapeHTML(JSON.stringify(v)) + '</code>' : escapeHTML(String(v));
      }}));
    } else {
      columns = [{key: 'value', label: 'value', wrap: true, get: r => r, render: r => typeof r === 'object' ? '<code>' + escapeHTML(JSON.stringify(r)) + '</code>' : escapeHTML(String(r))}];
    }
    const table = new DataTable({rows: arr, columns, pageSize: 25, tall: false, caption: fmtInt(arr.length) + ' array items'});
    slot.appendChild(table.root);
  });
}
function renderDocx(doc) {
  let html = '';
  for (const b of doc.blocks || []) {
    if (b.type === 'paragraph') {
      const style = b.style ? ' sty-' + String(b.style).replace(/[^A-Za-z0-9_-]/g, '') : '';
      let inner = '';
      for (const r of b.runs || []) {
        if (r.type === 'math') inner += '<span class="math-inline" data-math="' + escapeHTML(r.tex) + '" title="source ' + escapeHTML(String(r.source_index)) + '"></span>';
        else inner += escapeHTML(r.text || '');
      }
      html += '<div class="docx-para' + style + '">' + (inner || '&nbsp;') + '</div>';
    } else if (b.type === 'table') {
      html += '<div class="table-scroll"><table class="data">';
      for (const row of b.rows || []) {
        html += '<tr>';
        for (const cell of row) {
          let inner = '';
          for (const r of cell.runs || []) {
            if (r.type === 'math') inner += '<span class="math-inline" data-math="' + escapeHTML(r.tex) + '"></span>';
            else inner += escapeHTML(r.text || '');
          }
          html += '<td class="wrap">' + inner + '</td>';
        }
        html += '</tr>';
      }
      html += '</table></div>';
    }
  }
  if (doc.images && doc.images.length) {
    html += '<details class="fold"><summary>Source image appendix (' + doc.images.length + ')</summary><div class="fold-body">';
    for (const img of doc.images) {
      if (/^data:image\/(png|jpeg|gif);base64,/i.test(img.src || '')) html += '<div style="margin:10px 0"><div style="font-size:11px;color:var(--ink-faint)">' + escapeHTML(img.name || 'image') + '</div><img class="doc-img" alt="' + escapeHTML(img.name || 'source image') + '" src="' + img.src + '"></div>';
    }
    html += '</div></details>';
  }
  return html;
}
async function viewDocument(params, ticket) {
  const id = params.get('id') || '';
  const entry = catalogue.documents.find(x => x.id === id);
  if (!entry) { errorView('Unknown document.', () => route()); return; }
  loadingView();
  const text = await loadDocumentText(entry, (d, n) => progressView(d, n));
  if (!fresh(ticket)) return;
  let html = head(entry.title, entry.note || null, entry.path);
  html += '<div class="counters"><span class="counter"><span class="n">' + escapeHTML(entry.format) + '</span><span class="l">format</span></span><span class="counter"><span class="n" style="font-size:12.5px">' + escapeHTML(entry.scope) + '</span><span class="l">scope</span></span></div>';
  if (entry.note) html += '<p class="notice-line">' + escapeHTML(entry.note) + '</p>';
  html += '<div class="panel reader" id="doc-body"></div>';
  view().innerHTML = html;
  const body = $('#doc-body');
  try {
    if (entry.format === 'markdown') {
      body.innerHTML = renderMarkdown(text, entry.path);
    } else if (entry.format === 'code') {
      body.innerHTML = '<pre class="code-view">' + escapeHTML(text) + '</pre>';
    } else if (entry.format === 'json') {
      jsonPaged = [];
      body.innerHTML = renderJSONValue(JSON.parse(text), 0);
      mountPagedJSON(body);
    } else if (entry.format === 'pdf-text') {
      const pages = JSON.parse(text);
      body.innerHTML = pages.map((p, i) => '<div class="pdf-page"><div class="pg-label">Page ' + (i + 1) + ' of ' + pages.length + '</div><pre>' + escapeHTML(p) + '</pre></div>').join('');
    } else if (entry.format === 'docx') {
      body.innerHTML = renderDocx(JSON.parse(text));
      mathAfterRender(body);
    } else {
      body.innerHTML = '<pre class="code-view">' + escapeHTML(text) + '</pre>';
    }
  } catch (err) {
    body.innerHTML = '<div class="error-box">This saved document could not be rendered: ' + escapeHTML(String(err && err.message || err)) + '</div><pre class="code-view">' + escapeHTML(text.slice(0, 20000)) + '</pre>';
  }
}

function renderNotebookOutput(out) {
  const label = t => '<div class="out-label">' + t + '</div>';
  if (out.output_type === 'stream') {
    const txt = Array.isArray(out.text) ? out.text.join('') : String(out.text || '');
    return '<div class="cell-out">' + label(out.name === 'stderr' ? 'stderr' : 'stdout') + '<pre class="' + (out.name === 'stderr' ? 'nb-stream-err' : '') + '">' + escapeHTML(txt) + '</pre></div>';
  }
  const data = out.data || {};
  let html = '';
  if (data['image/png'] || data['image/jpeg'] || data['image/gif']) {
    const [mime, payload] = data['image/png'] ? ['image/png', data['image/png']] : data['image/jpeg'] ? ['image/jpeg', data['image/jpeg']] : ['image/gif', data['image/gif']];
    const b64 = String(Array.isArray(payload) ? payload.join('') : payload).replace(/\s+/g, '');
    html += '<div class="cell-out">' + label('recorded image') + '<img class="nb-img" alt="recorded output image" src="data:' + mime + ';base64,' + b64 + '"></div>';
  }
  if (data['text/html']) {
    const raw = Array.isArray(data['text/html']) ? data['text/html'].join('') : String(data['text/html']);
    html += '<div class="cell-out">' + label('recorded html') + '<div class="scroll-x">' + sanitizeRecordedHTML(raw) + '</div></div>';
  }
  if (data['text/latex']) {
    const raw = Array.isArray(data['text/latex']) ? data['text/latex'].join('') : String(data['text/latex']);
    const tex = raw.replace(/^\$+|\$+$/g, '');
    html += '<div class="cell-out">' + label('recorded latex') + '<span data-math="' + escapeHTML(tex) + '"></span></div>';
  }
  if (data['text/markdown']) {
    const raw = Array.isArray(data['text/markdown']) ? data['text/markdown'].join('') : String(data['text/markdown']);
    html += '<div class="cell-out">' + label('recorded markdown') + renderMarkdown(raw, '') + '</div>';
  }
  if (data['text/plain'] && !data['text/html']) {
    const raw = Array.isArray(data['text/plain']) ? data['text/plain'].join('') : String(data['text/plain']);
    html += '<div class="cell-out">' + label('recorded text') + '<pre>' + escapeHTML(raw) + '</pre></div>';
  }
  if (!html) {
    html = '<div class="cell-out">' + label('recorded output') + '<pre>' + escapeHTML(JSON.stringify(out, null, 1).slice(0, 8000)) + '</pre></div>';
  }
  return html;
}
async function viewNotebook(params, ticket) {
  const id = params.get('id') || '';
  const entry = catalogue.notebooks.find(x => x.id === id);
  if (!entry) { errorView('Unknown notebook.', () => route()); return; }
  loadingView();
  const cells = await loadNotebookCells(entry, (d, n) => progressView(d, n));
  if (!fresh(ticket)) return;
  const perPage = 20;
  const page = Math.max(1, Number(params.get('page') || 1));
  const pages = Math.max(1, Math.ceil(cells.length / perPage));
  const cur = Math.min(page, pages);
  const slice = cells.slice((cur - 1) * perPage, cur * perPage);
  let html = head('Notebook · ' + entry.title, entry.note || 'Recorded source and saved outputs. This site does not execute cells.', entry.path);
  if (/FR13/.test(entry.title)) html += '<p class="notice-line"><span class="badge pending">Legacy comparison notebook; not the native Ministry engine.</span></p>';
  const pager = '<div class="pager"><button type="button" class="btn small" data-page="prev">‹</button><span>' + escapeHTML(t('page')) + ' ' + cur + ' ' + escapeHTML(t('of')) + ' ' + pages + ' · ' + cells.length + ' cells</span><button type="button" class="btn small" data-page="next">›</button></div>';
  html += pager + '<div id="nb-cells"></div>' + pager;
  view().innerHTML = html;
  let ch = '';
  slice.forEach((cell, i) => {
    const idx = (cur - 1) * perPage + i + 1;
    if (cell.cell_type === 'markdown') {
      ch += '<div class="cell cell-md"><div class="reader">' + renderMarkdown(Array.isArray(cell.source) ? cell.source.join('') : String(cell.source || ''), entry.path) + '</div></div>';
    } else {
      const src = Array.isArray(cell.source) ? cell.source.join('') : String(cell.source || '');
      ch += '<div class="cell cell-code"><details><summary>Code · cell ' + idx + (cell.execution_count ? ' · execution ' + cell.execution_count : '') + '</summary><pre class="code-view">' + escapeHTML(src) + '</pre></details>';
      for (const out of cell.outputs || []) ch += renderNotebookOutput(out);
      ch += '</div>';
    }
  });
  $('#nb-cells').innerHTML = ch;
  mathAfterRender($('#nb-cells'));
  view().querySelectorAll('[data-page]').forEach(b => b.addEventListener('click', () => {
    const p = parseHash().params;
    p.set('page', String(b.getAttribute('data-page') === 'prev' ? Math.max(1, cur - 1) : Math.min(pages, cur + 1)));
    setParams('notebook', p, true);
  }));
}

async function viewRequirements(params,ticket){
 loadingView();const release=await releaseP();if(!fresh(ticket))return;
 const reqs=release.requirements,req=reqs.find(r=>r.id===params.get('fr'))||reqs[0];
 let h=head(lang==='az'?'Funksional tələblər FR1–FR12':'Functional requirements FR1–FR12',lang==='az'?'Nazirliyin dəqiq tələbi, model üzrə nəticələr və tələb olunan mənbə məlumatları.':'The exact Ministry requirement, model results and required source inputs.');
 h+='<div class="fr-rail">'+reqs.map(r=>'<a href="#/requirements?fr='+r.id+'"'+(r.id===req.id?' class="active" aria-current="page"':'')+'>'+r.id+'</a>').join('')+'</div>';
 h+='<section class="panel"><h2>'+req.id+'</h2><p class="req-az" lang="az">'+escapeHTML(req.requested_text_az)+'</p><p class="req-en">'+escapeHTML(req.faithful_english)+'</p><table class="props"><tbody><tr><th>Requirement source</th><td>'+escapeHTML(req.source.file.split('/').pop())+' · '+escapeHTML(req.source.locator)+'</td></tr><tr><th>Source inputs still required</th><td>'+escapeHTML(req.outstanding_official_inputs)+'</td></tr></tbody></table></section>';
 h+='<section class="panel"><h2>'+req.id+' · '+(lang==='az'?'Baza proqnoz cədvəli':'Baseline forecast table')+'</h2><p class="notice-line">'+(lang==='az'?'Sütun başlıqlarına klikləyərək sıralayın. Sətirə klikləyərək bütün illərin dəqiq qiymətlərini və mənbələrini görün.':'Sort using column headings. Select a row for exact values and sources across all years.')+'</p><div class="filterbar" id="reqfilters">'+selectField('Model','req-model',[{value:'*',label:t('all')},...release.models.map(m=>({value:m.id,label:modelMeta(m.id).short}))],params.get('model')||'*')+'<div class="field"><label for="req-q">'+t('search')+'</label><input id="req-q" type="search" placeholder="series, concept, source"></div></div><div id="requirement-results" class="loading">'+t('loading')+'</div></section>';
 const xs=catalogue.tables.find(x=>/FR_ATOMIC_CROSSWALK/.test(x.path));const fb=catalogue.tables.find(x=>/FEEDBACK_25_CROSSWALK/.test(x.path));
 h+='<section class="panel"><h2>Detailed requirement mapping</h2><div class="actions-row"><a class="btn" href="#/workbook?sheet='+req.id+'">'+req.id+' results workbook table</a><a class="btn" href="#/forecasts?model=*&scenario=baseline&fr='+req.id+'&wide=1&start=2024">All original '+req.id+' records</a>'+(xs?'<a class="btn" href="#/table?id='+xs.id+'&q='+req.id+' ">Atomic requirement definitions</a>':'')+(fb?'<a class="btn" href="#/table?id='+fb.id+'">Ministry feedback: 25 items</a>':'')+'</div></section>';
 h+='<section class="panel"><h2>All requirements</h2><div id="requirements-index"></div></section>';
 view().innerHTML=h;
 $('#requirements-index').appendChild(new DataTable({rows:reqs,columns:[{key:'id',label:'FR',sticky:true},{key:'faithful_english',label:'Required output',wrap:true},{key:'outstanding_official_inputs',label:'Required official inputs',wrap:true}],tall:false,pageSize:25,onActivate:r=>setParams('requirements',new URLSearchParams('fr='+r.id),true)}).root);
 const all=(await Promise.all(release.models.map(m=>loadGroupRows(m.id,'baseline')))).flat().filter(r=>(r.fr_ids||[]).includes(req.id)&&Number(r.year)>=2024&&Number(r.year)<=2030);
 if(!fresh(ticket))return;
 function show(){
  const model=$('#f-req-model').value,q=$('#req-q').value.toLocaleLowerCase();
  const rs=all.filter(r=>(model==='*'||r.model_id===model)&&(!q||[r.series_id,r.concept,r.source_file,r.source_sheet].join(' ').toLocaleLowerCase().includes(q)));
  const map=new Map();for(const r of rs){const k=JSON.stringify([r.model_id,r.series_id,r.unit,r.source_file,r.source_sheet,r.reporting_role]);if(!map.has(k))map.set(k,{meta:r,years:new Map()});const g=map.get(k);if(!g.years.has(Number(r.year)))g.years.set(Number(r.year),[]);g.years.get(Number(r.year)).push(r);}
  const grid=[...map.values()],years=[2024,2025,2026,2027,2028,2029,2030];
  const columns=[{key:'model',label:'Model',sticky:true,get:r=>r.meta.model_id,render:r=>modelTag(r.meta.model_id)},{key:'indicator',label:'Indicator',wrap:true,get:r=>r.meta.concept},{key:'series',label:'Series',get:r=>r.meta.series_id},{key:'unit',label:'Unit',get:r=>r.meta.unit},...years.map(y=>({key:'y'+y,label:String(y),num:true,get:r=>{const xs=r.years.get(y);return xs&&xs.length===1?xs[0].value:xs?xs.map(x=>x.value).join(' | '):null;},render:r=>{const xs=r.years.get(y);return xs?xs.map(x=>escapeHTML(displayValue(x.value))).join('<br>'):'<span class="unavail">—</span>';}})),{key:'source',label:'Source',wrap:true,get:r=>[r.meta.source_file,r.meta.source_sheet].join(' / ')}];
  const host=$('#requirement-results');host.className='';host.innerHTML='';host.appendChild(new DataTable({rows:grid,columns,searchable:false,pageSize:25,caption:fmtInt(rs.length)+' baseline source records; '+fmtInt(grid.length)+' indicator/source rows. Missing values are not replaced by zeros.',onActivate:r=>{let detail=recordDetail(r.meta);const vals=[...r.years.values()].flat();detail+='<table class="data"><thead><tr><th>Year</th><th>Exact value</th><th>Source cell</th><th>Data status</th></tr></thead><tbody>'+vals.map(x=>'<tr><td>'+x.year+'</td><td class="num">'+escapeHTML(displayValue(x.value,true))+'</td><td>'+escapeHTML(x.source_cell)+'</td><td>'+escapeHTML(x.data_status)+'</td></tr>').join('')+'</tbody></table>';openDetail(r.meta.concept,detail);}}).root);
 }
 $('#f-req-model').addEventListener('change',show);let tm;$('#req-q').addEventListener('input',()=>{clearTimeout(tm);tm=setTimeout(show,250);});show();
}


const searchDialog = $('#search-dialog');
const searchIndex = [];
function buildSearchIndex() {
  if (searchIndex.length) return;
  for (const x of catalogue.tables) searchIndex.push({kind:'table', label:x.title, sub:x.path, route:'#/table?id=' + encodeURIComponent(x.id)});
  for (const x of catalogue.documents) searchIndex.push({kind:'document', label:x.title, sub:x.path + ' · ' + x.format, route:'#/document?id=' + encodeURIComponent(x.id)});
  for (const x of catalogue.notebooks) searchIndex.push({kind:'notebook', label:x.title, sub:x.path, route:'#/notebook?id=' + encodeURIComponent(x.id)});
  for (const x of catalogue.workbook) searchIndex.push({kind:'sheet', label:'Workbook · ' + x.sheet, sub:x.path, route:'#/workbook?sheet=' + encodeURIComponent(x.sheet)});
  for (const x of catalogue.equation_catalogues) searchIndex.push({kind:'equations', label:x.title, sub:x.path + ' · ' + x.count + ' rows', route:'#/equations'});
  searchIndex.push({kind:'view', label:'CAEM methodology expressions', sub:'283 original methodology expressions', route:'#/equations?tab=caem'});
  for (const g of catalogue.result_groups) searchIndex.push({kind:'run', label:g.model_id + ' · ' + g.scenario_id, sub:g.row_count + ' records', route:'#/forecasts?model=' + encodeURIComponent(g.model_id) + '&scenario=' + encodeURIComponent(g.scenario_id)});
  for (let i = 1; i <= 12; i++) searchIndex.push({kind:'requirement', label:'FR' + i, sub:'Supplied requirement wording and coverage', route:'#/requirements?fr=FR' + i});
}
function runGlobalSearch(q) {
  buildSearchIndex();
  const query = q.toLocaleLowerCase();
  const hits = searchIndex.filter(e => (e.label + ' ' + e.sub).toLocaleLowerCase().includes(query)).slice(0, 60);
  const box = $('#global-results');
  box.innerHTML = hits.length
    ? hits.map(h => '<a class="res" href="' + h.route + '"><span class="kind">' + escapeHTML(h.kind) + '</span>' + escapeHTML(h.label) + '<span class="sub">' + escapeHTML(h.sub) + '</span></a>').join('')
    : '<div class="empty-state">' + escapeHTML(t('empty')) + '</div>';
}
function openSearch() {
  buildSearchIndex();
  lastFocus = document.activeElement;
  $('#global-search').value = '';
  runGlobalSearch('');
  if (!searchDialog.open) searchDialog.showModal();
  $('#global-search').focus();
}
$('#quick-search').addEventListener('click', openSearch);
$('#search-close').addEventListener('click', () => searchDialog.close());
$('#global-search').addEventListener('input', e => runGlobalSearch(e.target.value));
searchDialog.addEventListener('close', () => { if (lastFocus && lastFocus.focus) lastFocus.focus(); });
searchDialog.addEventListener('click', e => { if (e.target.closest('a.res')) searchDialog.close(); });
document.addEventListener('keydown', e => {
  if (e.key === '/' && !e.target.closest('input,textarea,select,[contenteditable]')) { e.preventDefault(); openSearch(); }
});

function comparisonStatus(r) {
 if (r.model_id==='imf_articleiv_benchmark') return {kind:'reference',label:lang==='az'?(Number(r.year)===2025?'BVF qiymətləndirməsi':'BVF proqnozu'):(Number(r.year)===2025?'IMF estimate':'IMF projection')};
 const s=(r.data_status||'')+' '+(r.status||'');
 if (/expected/i.test(s)) return {kind:'expected',label:lang==='az'?'Gözlənilən':'Expected'};
 if (/observed|actual|historical|source_historical/i.test(s)) return {kind:'history',label:lang==='az'?'Tarixi / faktiki':'History / actual'};
 if (/derived|proxy/i.test(s)) return {kind:'derived',label:lang==='az'?'Hesablanmış / proksi':'Derived / proxy'};
 if (/forecast|projection/i.test(s)) return {kind:'forecast',label:lang==='az'?'Proqnoz':'Forecast'};
 if (/source_input/.test(s)) return {kind:'source',label:lang==='az'?'Mənbə girişi':'Source input'};
 return {kind:'forecast',label:r.data_status||r.status||'Saved value'};
}
const methodEvidenceP=()=>loadAsset(catalogue.method_evidence_key);
const deliveryP=()=>loadAsset(catalogue.delivery_key);
function evidenceColumns(keys) {return keys.map(k=>({key:k,label:k.replace(/_/g,' '),wrap:!['value','year','coefficient','driver','contribution_pp','log_index_contribution'].includes(k),num:['value','year','coefficient','driver','contribution_pp','log_index_contribution','difference_from_observed_pp'].includes(k),render:r=>escapeHTML(displayValue(r[k],true))}));}
async function viewDifferences(params,ticket) {
 loadingView();const e=await methodEvidenceP();if(!fresh(ticket))return;
 let h=head(lang==='az'?'Metod və məlumat fərqləri':'Method differences',lang==='az'?'İki Nazirlik modeli, müstəqil Oxlon modeli və BVF-nin dərc edilmiş istinadı.':'Two Ministry models, the independent Oxlon model, and the published IMF reference.');
 h+='<nav class="section-jumps" aria-label="Method sections"><a href="#ownership">Providers and roles</a><a href="#cpi-case">2025 CPI explained</a><a href="#technical-methods">Technical calculations</a><a href="#fair-comparison">A consistent comparison</a></nav>';
 h+='<section class="panel" id="ownership"><h2>Which system belongs to whom?</h2><p>Both <strong>Ministry macro</strong> and <strong>Ministry CAEM</strong> are supplied Ministry of Economy systems. CAEM means <em>Comprehensive Adaptive Expectations Model</em>; it was developed with IMF technical assistance and customized for the Ministry. The IMF Article IV staff projections are a separate published reference.</p><p>The <a href="'+escapeHTML(e.sources.imf_ta)+'" target="_blank" rel="noopener noreferrer">IMF technical-assistance report</a> documents CAEM’s integration into the Ministry’s toolkit (pp. 7, 11, 15). Its provenance does not make the Ministry workbook identical to the IMF country team’s Article IV projections.</p><div id="provider-table"></div></section>';
 h+='<section class="panel" id="cpi-case"><h2>Why does annual-average CPI differ in 2025?</h2><p><code>cpi_infl</code> and <code>cpi_avg</code> are native series names for the same annual-average inflation concept in these mapped rows. The 2025 entries have different information sets and observation statuses.</p><div id="cpi-audit-table"></div><p>The <a href="'+escapeHTML(e.sources.official_cpi)+'" target="_blank" rel="noopener noreferrer">State Statistical Committee’s 14 January 2026 CPI release</a> reports annual-average inflation of <strong>5.6%</strong> and December-on-December inflation of <strong>5.2%</strong>. The Oxlon input cache records the 19 January macroeconomic release; it uses the same annual-average 5.6% value.</p><p>The old macro expected value is <strong>3.858 percentage points below</strong> the observed outcome; CAEM’s retained forecast is <strong>0.547 percentage points below</strong>. These are retrospective gaps in saved values. The files do not establish when each legacy forecast was formally issued, so they cannot establish a controlled out-of-sample comparison.</p><p>Oxlon’s 2025 value is a historical observation, and the IMF labels 2025 an estimate. Their agreement at 5.6% is <strong>not evidence of forecast superiority</strong>. Keep the legacy results as an auditable snapshot and distinguish them from updated actual data.</p><a class="btn" href="#/overview?concept=cpi_annual_average_inflation&start=2025&end=2031">Compare the complete CPI paths →</a></section>';
 h+='<section class="panel"><h2>Annual-average, December and index levels</h2><p>Using a consistent monthly CPI index, the annual-average inflation definition is:</p><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\bar I_t=\frac{1}{12}\sum_{m=1}^{12} I_{t,m},\qquad \pi_t^{\mathrm{avg}}=100\left(\frac{\bar I_t}{\bar I_{t-1}}-1\right)`)+'"></div><p>December-on-December inflation is a separate concept:</p><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\pi_t^{\mathrm{Dec}}=100\left(\frac{I_{t,12}}{I_{t-1,12}}-1\right)`)+'"></div><p>An index of 105.6 relative to the prior year’s 100 corresponds to a 5.6% increase. The two inflation formulas need not produce the same number. These formulas explain definitions; this page does not invent missing monthly observations.</p></section>';
 h+='<section class="panel" id="technical-methods"><h2>1. Ministry macro · linked accounts and CPI-index equation</h2><p>The bottom-up accounts use company/product volumes and domestic/export prices, branch value added and net taxes, with dependencies across the real, trade, fiscal and social workbooks. CPI is produced by its own supplied econometric equation in <code>MOE INF.xlsx</code>; it is not calculated by summing the company production plans.</p><p>The original <code>11_12!AJ6</code> formula is <code>AJ24/AI24*100-100</code>, with <code>AJ24=AJ25*AJ26</code>. The saved 2024 index is <code>1.8495871115884663</code>, the 2025 index is <code>1.8818119509529945</code>, and the add-factor <code>AJ26</code> equals 1.</p><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\pi_{2025}^{\mathrm{macro}}=100\left(\frac{1.8818119509529945}{1.8495871115884663}-1\right)=1.7422720542668912\%`)+'"></div><p>The index equation uses CPI persistence, current/lagged NEER, the WEO food-price index, M1, a lagged CPI-gap term and fixed source terms. In this retained 2025 formula the oil-price term and several dummy terms are explicitly multiplied by zero.</p><div id="macro-contribution-table"></div><p>The table reconstructs <code>log(AJ25/AI24)</code>; its terms must be exponentiated before interpreting inflation. The negative NEER terms lower this saved equation’s index growth. This is an explanation within the retained source equation, not a decomposition of the difference from actual inflation.</p><details class="fold"><summary>Original CPI formula and source index cells</summary><div class="fold-body" id="macro-source-cells"></div></details><a class="btn" href="#/equations?tab=native&model=ministry_macro&book=MOE+INF.xlsx&sheet=11_12">Inspect original workbook formulas →</a></section>';
 h+='<section class="panel"><h2>2. Ministry CAEM · adaptive expectations and structural transmission</h2><p>CAEM combines structural behavioural equations, accounting identities, trend/potential-output calculations and policy selectors. Consumption, private investment, exports, goods imports, inflation and interest rates interact with the real, fiscal, monetary and external accounts. The recovered calculation checks both GDP-growth and deflator residuals under the selected CP/YP closure.</p><p>For 2025, <code>6a. SEI!N19</code> links through <code>1c. Interest rates!O19</code> to <code>1b. Infl and Ex rates!O19</code>. The selected inflation regime is <code>Model determined</code>. Its original <code>O24</code> equation uses coefficients 0.1, 0.7, 0.2 and 0.4, then adds calibration and scenario terms.</p><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\pi_{2025}^{e}=0.2\times2.2+0.8\times4=3.64`)+'"></div><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\pi_{2025}^{\mathrm{CAEM}}=0.1(2.2)+0.7(3.64)+0.2(14.0958552363+0-3.9700271725)+0.4(0.6495550577)+0+0\simeq5.0529876359\%`)+'"></div><p>The <code>O8</code> input, 14.095855%, is labelled <em>Imported inflation (USD)</em>: the import deflator derived from partner-country export deflators weighted by imports. <code>O9</code> is the annual-average manat/US-dollar exchange-rate change (positive for depreciation), <code>O10</code> is the trend relative import-price change, and <code>O14</code> is the non-oil output gap as a percentage of non-oil potential output.</p><div id="caem-contribution-table"></div><p>The coefficient and driver cells below are saved source values. The full-precision term sum agrees with the exported 5.052987635856589% within <code>1e−10</code> percentage points; the final digits reflect floating-point calculation. The supplied workbook horizon ends in 2029.</p><details class="fold"><summary>Original CAEM CPI inputs, coefficients and formulas</summary><div class="fold-body" id="caem-source-cells"></div></details><a class="btn" href="#/equations?tab=caem">Original structural equations →</a></section>';
 h+='<section class="panel"><h2>3. Oxlon · recorded estimation, backtests and selected forecast paths</h2><p>Oxlon is an independent pipeline. In FR9 it anchors the history to observed annual-average CPI through 2025, examines econometric alternatives and uses recorded expanding-window forecast tests to choose an ensemble. The saved notebook includes AR(1), an anchored adaptive path and a lagged-driver Phillips specification; conditional and diagnostic variants are retained separately.</p><p>The structural alternatives use HAC standard errors. Forecast paths depend on the recorded FR5 oil-price path and declared exchange-rate assumptions: future NEER log changes are set to zero, while the first lagged-driver forecast uses the observed 2025 change. These assumptions are distinct from the macro workbook’s retained NEER path and CAEM’s structural inputs.</p><p>Samples, saved coefficients, selection weights, outputs and limitations are available in the complete notebook. The 486-row specification catalogue includes alternatives and historical Ministry references; it is not a list of 486 operative forecast equations.</p><a class="btn" href="#/notebook?id=notebook-FR09">Read the complete saved FR9 calculation →</a> <a class="btn" href="#/equations?tab=published&model=oxlon.corrected.20260917">View published specifications →</a></section>';
 h+='<section class="panel"><h2>4. IMF · published staff projections and CAEM method provenance</h2><p>IMF Article IV Table 1 provides a dated external reference. Its CPI sequence for 2025–2031 is <strong>5.6, 6.0, 5.1, 4.1, 4.0, 4.0, 4.0%</strong>. The reference is mapped into the overview for CPI, total GDP growth and non-oil GDP growth; the remaining indicators have no imported IMF mapping.</p><p>The <a href="'+escapeHTML(e.sources.imf_articleiv)+'#page=28" target="_blank" rel="noopener noreferrer">original Table 1</a> is on PDF page 28 (printed page 22), in report 26/112, completed 26 March and released 26 May 2026. The report’s press-release section contains some different projections; this website retains the identified Table 1 vintage. No separate executable IMF staff model or its coefficients were supplied.</p><p>To study the IMF-assisted CAEM method, use the Ministry CAEM equations and original workbook. To compare published IMF forecasts, use the separate Article IV reference. These are distinct uses of IMF material.</p><a class="btn" href="#/forecasts?model=imf_articleiv_benchmark&scenario=Table1&start=2025&wide=1">IMF reference table →</a></section>';
 h+='<section class="panel" id="fair-comparison"><h2>How to make a consistent model comparison</h2><ol><li>Agree the target definitions: annual-average CPI versus December CPI; market-price GDP versus basic-price value added; national-account versus BoP trade; state-budget versus consolidated fiscal accounts.</li><li>Freeze a dated historical information set with matching nominal, real and price series, prior-year bases and declared observation statuses.</li><li>Obtain approved upstream company/product/branch/tax and institutional forecasts, with units, owner, release date and exact original input mappings. Updating only a calculated headline cannot update the complete bottom-up system.</li><li>Run each implemented model on the compatible inputs, retain its endogenous mechanisms and selectors, and save manifests, source input changes, equations, convergence and account checks.</li><li>Compare forecast accuracy only using the same target, forecast origin, information available at that origin, horizon and evaluation sample. Record missing values and source-definition limits before ranking models.</li></ol><p>The present site retains the source vintages and calculated snapshots. A latest-official common-input rerun still needs the missing owner-supplied inputs and agreed mappings. The CSV delivery page makes the current outputs and input collection forms available without relabelling them as authenticated Ministry forecasts.</p><a class="btn" href="#/delivery">Ministry delivery files →</a></section>';
 view().innerHTML=h;
 $('#provider-table').appendChild(new DataTable({rows:e.models,columns:evidenceColumns(['provider','model_id','method','input_boundary','forecast_years','role','comparability_limit']),tall:false}).root);
 $('#cpi-audit-table').appendChild(new DataTable({rows:e.cpi_2025,columns:[{key:'model_id',label:'System',render:r=>modelTag(r.model_id)},...evidenceColumns(['series_id']),{key:'value',label:'CPI (%)',num:true,render:r=>escapeHTML(Number(r.value).toFixed(3))},...evidenceColumns(['interpretation']),{key:'difference_from_observed_pp',label:'Gap from observed (pp)',num:true,render:r=>escapeHTML(Number(r.difference_from_observed_pp).toFixed(3))}],caption:'Annual-average CPI in 2025 · select a row for exact values and source provenance',tall:false,onActivate:r=>openDetail(modelMeta(r.model_id).short+' · CPI 2025',propsTable(r))}).root);
 $('#macro-contribution-table').appendChild(new DataTable({rows:e.macro_terms,columns:evidenceColumns(['term','coefficient','driver','log_index_contribution','coefficient_source','driver_expression']),caption:'Original macro CPI equation · log-index contributions, not percentage points',tall:false}).root);
 $('#caem-contribution-table').appendChild(new DataTable({rows:e.caem_terms,columns:evidenceColumns(['term','coefficient','driver','contribution_pp','source']),caption:'Original CAEM 2025 CPI equation · contributions in percentage points',tall:false}).root);
 $('#macro-source-cells').appendChild(new DataTable({rows:e.macro_cells,columns:evidenceColumns(['sheet','cell','executed_value','formula']),tall:false}).root);
 $('#caem-source-cells').appendChild(new DataTable({rows:e.caem_cells,columns:evidenceColumns(['sheet','cell','value','formula']),tall:false}).root);
 mathAfterRender(view());
 view().querySelectorAll('.section-jumps a').forEach(a=>a.addEventListener('click',ev=>{ev.preventDefault();document.getElementById(a.getAttribute('href').slice(1)).scrollIntoView({behavior:'smooth',block:'start'});}));
}
async function deliveryRows(meta,file) {
 if(file.recordset)return meta.recordsets[file.recordset];
 let rows=[];for(const key of file.groups){const g=catalogue.result_groups.find(g=>g.model_id+'|'+g.scenario_id===key);rows.push(...await loadParts(g.parts));}
 if(file.fr)rows=rows.filter(r=>(r.fr_ids||[]).includes(file.fr));
 return rows;
}
async function viewDelivery(params,ticket) {
 loadingView();const meta=await deliveryP();if(!fresh(ticket))return;
 const id=params.get('file'),file=meta.files.find(f=>f.id===id);
 let h=head(lang==='az'?'Nazirliyə təhvil CSV faylları':'Ministry delivery files',lang==='az'?'Saxlanmış hesablamalar, FR1–FR12 nəticələri, mənbələr və boş giriş formaları.':'Saved model results, FR1–FR12 outputs, provenance and blank input collection forms.');
 h+='<p class="definition-note">'+meta.files.length+' CSV files · '+fmtInt(meta.baseline_records)+' baseline records across the three engines. These exports preserve source data vintages, full precision, source locations and unavailable/error flags. They are a delivery snapshot of saved calculations; a new latest-official common-input model run and Ministry acceptance are not claimed.</p>';
 if(file){
  loadingView();const rows=await deliveryRows(meta,file);if(!fresh(ticket))return;
  h+='<section class="panel"><a href="#/delivery">← All delivery files</a><h2>'+escapeHTML(file.label)+'</h2><p>'+escapeHTML(file.description)+'</p><div class="actions-row"><a class="btn primary" href="'+escapeHTML(file.href)+'" download="'+escapeHTML(file.filename)+'">Download CSV</a></div><p class="csv-provenance">'+escapeHTML(file.filename)+' · '+fmtInt(file.rows)+' records · '+file.columns.length+' columns · '+escapeHTML(file.source)+'</p><details><summary>File integrity</summary><p class="csv-provenance">SHA-256: '+escapeHTML(file.sha256)+'</p></details><label class="full-column-control"><input type="checkbox" id="delivery-all-columns"'+(params.get('columns')==='all'?' checked':'')+'> Show every source column</label><div id="delivery-preview"></div></section>';
  view().innerHTML=h;
  const preferred=['model_id','scenario_id','fr_ids','series_id','concept','year','value','unit','status','data_status','source_file','source_sheet','source_cell','vintage_id'];let keys=params.get('columns')==='all'?file.columns:preferred.filter(k=>file.columns.includes(k));if(!keys.length)keys=file.columns;
  $('#delivery-preview').appendChild(new DataTable({rows,columns:evidenceColumns(keys),caption:'Exact CSV record preview · blank fields are unavailable/not supplied; lists and objects use JSON',tall:false}).root);
  $('#delivery-all-columns').addEventListener('change',()=>{const p=new URLSearchParams(params);if($('#delivery-all-columns').checked)p.set('columns','all');else p.delete('columns');setParams('delivery',p,true)});
 }else{
  h+='<div class="filterbar"><div class="field"><label for="delivery-filter">Find a delivery file</label><input type="search" id="delivery-filter" placeholder="FR9, baseline, CPI, template…" value="'+escapeHTML(params.get('q')||'')+'"></div></div><div id="delivery-index">';
  const query=(params.get('q')||'').toLocaleLowerCase();
  for(const category of [...new Set(meta.files.map(f=>f.category))]){
   const files=meta.files.filter(f=>f.category===category&&(!query||[f.label,f.filename,f.description,f.category].join(' ').toLocaleLowerCase().includes(query)));if(!files.length)continue;
   h+='<section class="panel"><h2>'+escapeHTML(category)+'</h2><div class="table-scroll"><table class="data delivery-table"><thead><tr><th>CSV file and contents</th><th class="num">Records</th><th>Open / download</th></tr></thead><tbody>';
   for(const f of files)h+='<tr data-delivery-id="'+escapeHTML(f.id)+'"><td class="wrap"><strong>'+escapeHTML(f.label)+'</strong><p>'+escapeHTML(f.description)+'</p><small class="csv-provenance">'+escapeHTML(f.filename)+'</small></td><td class="num">'+fmtInt(f.rows)+'</td><td><a href="#/delivery?file='+encodeURIComponent(f.id)+'">Preview in HTML</a><br><a href="'+escapeHTML(f.href)+'" download="'+escapeHTML(f.filename)+'">Download CSV</a></td></tr>';
   h+='</tbody></table></div></section>';
  }
  h+='</div><section class="panel"><h2>What these files do and do not contain</h2><p>The baseline and FR exports include historical records, literal source inputs, calculated outputs and explicitly unavailable/error records. FR files overlap where a source row serves multiple requirements. Their row counts are an output inventory, not a statement that every contractual sub-requirement is accepted.</p><p>The four named scenarios are saved conditional model runs. Experimental <code>test_only</code> cases, unnamed interactive runs, obsolete template-sample results and diagnostic copies are excluded from this delivery index.</p><p>CSV files use UTF-8 with a byte-order mark for Azerbaijani text and Excel compatibility. Values retain saved numerical precision; nested lists/objects are JSON inside CSV cells. Blank fields do not mean zero. Read the model/vintage registry and data dictionary alongside the results.</p><p>The blank input forms are requests for genuine dated owner-supplied inputs. They do not contain invented official forecasts and do not extend CAEM’s original five-year horizon. Ministry macro and CAEM collection forms require conversion to their existing governed JSON contracts; the Oxlon CSV requires its documented validation before execution.</p><a class="btn" href="#/differences">Read the technical method comparison →</a></section>';
  view().innerHTML=h;let timer;$('#delivery-filter').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>setParams('delivery',new URLSearchParams({q:$('#delivery-filter').value}),true),350);});
 }
}

const VIEWS = {
  overview: viewOverview, forecasts: viewForecasts, scenarios: viewScenarios, models: viewModels,
  equations: viewEquations, workbook: viewWorkbook, library: viewLibrary, table: viewTable,
  methods: viewMethods, differences:viewDifferences, delivery:viewDelivery, document: viewDocument, notebook: viewNotebook, requirements: viewRequirements
};
const CRUMB_PARENT = {table:'library', document:'methods', notebook:'methods'};
async function route() {
  const ticket = ++renderEpoch;
  const {path, params} = parseHash();
  const fn = VIEWS[path] || viewOverview;
  const active = VIEWS[path] ? path : 'overview';
  const DETAIL_LABEL = {table:'Dataset', document:'Document', notebook:'Notebook'};
  renderNav(CRUMB_PARENT[active] || active);
  const section = SECTIONS.find(s => s.path === active);
  const crumbs = [{label:'MİİS 15.5.1', href:'#/overview'}];
  if (CRUMB_PARENT[path]) {
    const parent = SECTIONS.find(s => s.path === CRUMB_PARENT[path]);
    crumbs.push({label:parent.label(), href:'#/' + parent.path});
    crumbs.push({label:DETAIL_LABEL[path]});
  } else crumbs.push({label:section.label()});
  breadcrumb(crumbs);
  document.title = 'MİİS 15.5.1 v3 | ' + (section ? section.label() : DETAIL_LABEL[path] || path);
  $('#sidebar').classList.remove('open');
  $('.scrim') && $('.scrim').classList.remove('show');
  $('#menu-toggle').setAttribute('aria-expanded', 'false');
  try {
    view().dataset.route='';
    await fn(params, ticket);
    if(fresh(ticket))view().dataset.route=buildHash(path,params);
  } catch (err) {
    if (!fresh(ticket)) return;
    errorView(String(err && err.message || err), () => route());
  }
}
window.addEventListener('hashchange', event => { const h = event.newURL ? new URL(event.newURL).hash : location.hash; if (routeState.ignoredHashes.has(h)) { routeState.ignoredHashes.delete(h); return; } if (!routeState.suppress) route(); });

const scrim = document.createElement('div');
scrim.className = 'scrim';
document.body.appendChild(scrim);
scrim.addEventListener('click', () => { $('#sidebar').classList.remove('open'); scrim.classList.remove('show'); $('#menu-toggle').setAttribute('aria-expanded', 'false'); });
$('#menu-toggle').addEventListener('click', () => {
  const open = $('#sidebar').classList.toggle('open');
  scrim.classList.toggle('show', open);
  $('#menu-toggle').setAttribute('aria-expanded', String(open));
});
function applyLang() {
  document.documentElement.lang = lang;
  $('#language-toggle').textContent = t('lang_button');
  $('#quick-search').innerHTML = '<span>' + escapeHTML(t('search_button')) + '</span> <kbd>/</kbd>';
  $('#menu-toggle').textContent = t('menu');
  $('#search-title').textContent = t('search_title');
  $('#global-search').setAttribute('aria-label', t('search_placeholder'));
  $('#global-search').setAttribute('placeholder', t('search_placeholder'));
  $('#search-close').textContent = t('close');
  $('#detail-close').textContent = t('close');
  $('#sidebar').setAttribute('aria-label', lang === 'az' ? 'İş masası naviqasiyası' : 'Workbench navigation');
}
$('#language-toggle').addEventListener('click', () => {
  lang = lang === 'en' ? 'az' : 'en';
  try { localStorage.setItem('miis_1551_v3_lang', lang); } catch (e) {}
  applyLang();
  route();
});
$('#footer').innerHTML = 'MİİS 15.5.1 · 17 September 2026 · Original model data and saved calculation results';
applyLang();
route();
})();
