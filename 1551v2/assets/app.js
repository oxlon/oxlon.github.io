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
    nav_workbench:'Forecasts', nav_evidence:'Models and data', nav_why:'Why Oxlon?', nav_why_overview:'Why Oxlon?',
    nav_caem:'CAEM', nav_ministry:'Ministry macro', nav_oxlon:'Oxlon', nav_terminology:'Terminology', nav_caem_overview:'Forecast overview', nav_caem_real:'Real economy', nav_caem_prices:'Prices and exchange rates', nav_caem_fiscal:'Fiscal accounts and debt', nav_caem_monetary:'Monetary accounts', nav_caem_external:'External accounts', nav_caem_labour:'Employment and incomes', nav_caem_scenarios:'Saved scenarios', nav_caem_methods:'Methods and equations', nav_caem_data:'Original workbook data', nav_caem_checks:'Calculation checks', nav_caem_records:'All forecast records', nav_overview:'Overview', nav_forecasts:'Forecast explorer', nav_scenarios:'Saved scenarios',
    nav_models:'Models and methods', nav_equations:'Equations', nav_workbook:'Results workbook', nav_library:'Data library',
    nav_methods:'Methodology and sources', nav_requirements:'Functional requirements', nav_differences:'Method differences', nav_delivery:'Ministry delivery files',
    search_button:'Find a table or method', menu:'Menu', close:'Close', retry:'Retry',
    reset:'Reset filters', search:'Search', loading:'Loading saved content', rows:'rows',
    page:'Page', of:'of', page_size:'Rows per page', all:'All', unavailable:'Unavailable',
    exact:'Exact source values', wide:'Wide year grid', detail_title:'Record details',
    empty:'No rows match the current filters.', lang_button:'Azərbaycan dili',
    search_title:'Find a table or method', search_placeholder:'Search tables, documents, notebooks',
    strip_status:'Data definitions', strip_note:'Source vintages and definitions differ between engines; displayed differences are not a pure method comparison. This presentation does not renew the prior review or grant Ministry acceptance.'
  },
  az: {
    nav_workbench:'Proqnozlar', nav_evidence:'Modellər və məlumatlar', nav_why:'Niyə Oxlon?', nav_why_overview:'Niyə Oxlon?',
    nav_caem:'CAEM', nav_ministry:'Nazirliyin makro modeli', nav_oxlon:'Oxlon', nav_terminology:'Terminologiya', nav_caem_overview:'Proqnoz icmalı', nav_caem_real:'Real iqtisadiyyat', nav_caem_prices:'Qiymətlər və məzənnələr', nav_caem_fiscal:'Fiskal hesablar və borc', nav_caem_monetary:'Pul-kredit hesabları', nav_caem_external:'Xarici sektor hesabları', nav_caem_labour:'Məşğulluq və gəlirlər', nav_caem_scenarios:'Saxlanmış ssenarilər', nav_caem_methods:'Metodlar və tənliklər', nav_caem_data:'İlkin iş kitabı məlumatları', nav_caem_checks:'Hesablama yoxlamaları', nav_caem_records:'Bütün proqnoz qeydləri', nav_overview:'İcmal', nav_forecasts:'Proqnoz tədqiqatı', nav_scenarios:'Saxlanmış ssenarilər',
    nav_models:'Modellər', nav_equations:'Tənliklər', nav_workbook:'İş kitabı', nav_library:'Məlumat kitabxanası',
    nav_methods:'Metodologiya və mənbələr', nav_requirements:'Funksional tələblər', nav_differences:'Metod fərqləri', nav_delivery:'CSV təhvil faylları',
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

const FIELD_LABELS={fr:'Functional requirement',fr_id:'Functional requirement reference',fr_ids:'Functional requirement references',FR:'Functional requirement',model_id:'Model',scenario_id:'Scenario',vintage_id:'Source data vintage',series_id:'Source series identifier',concept_id:'Economic concept identifier',concept:'Economic indicator',frequency:'Frequency',year:'Year',value:'Value',status:'Calculation status',data_status:'Observation status',source_file:'Source file',source_sheet:'Source worksheet',source_cell:'Source cell',method:'Recorded calculation method',source_value_type:'Source value type',reporting_role:'Role of this output',parent_vintage_id:'Parent source vintage',input_vintage_id:'Input source vintage',primary_source_file:'Underlying source file',primary_source_sheet:'Underlying source worksheet',primary_source_cell:'Underlying source address',unit:'Unit',mapped_unit:'Mapped comparison unit',price_basis:'Price basis',coverage_scope:'Output coverage',source_series:'Mapped source series',all_period_rows:'Records across all periods',forecast_rows:'Forecast records',forecast_error_rows:'Forecast records with calculation errors',source_sheets:'Source worksheets',meaning:'Interpretation',error:'Recorded calculation error',detail:'Error details',source_formula:'Original source formula',source_atom_id:'Original source-output reference',unit_scale_unresolved:'Unit scale requires confirmation',caveat:'Interpretation limit',baseline_value:'Baseline value',difference:'Change from baseline',difference_unit:'Unit of the change',comparison_status:'Comparison status',gdp_diff:'GDP reconciliation difference',gdp_difference:'GDP reconciliation difference',deflator_diff:'GDP deflator reconciliation difference',deflator_difference:'GDP deflator reconciliation difference',tolerance:'Recorded numerical tolerance',check_result:'Consistency check result',records:'Output records',unavailable_values:'Unavailable values',run_errors:'Recorded calculation errors',observation_statuses:'Observation-status counts',source_files:'Source files',log_index_contribution:'Contribution to log-index change',contribution_pp:'Contribution (percentage points)',coefficient_source:'Source coefficient cell',driver_expression:'Source driver expression',difference_from_observed_pp:'Difference from observed (percentage points)',interpretation:'Interpretation',scope:'Statistical coverage',result_available:'Mapped source record available',observation_status:'Observation status',definition_group:'Economic definition group',sign_convention:'Source sign convention',time_aggregation:'Time aggregation',assumption_key:'Forecast assumption',source_sha256:'Original source checksum'};
function fieldLabel(key){return FIELD_LABELS[key]||String(key).replace(/_/g,' ')}
const STATUS_LABELS={original_formula_expected:'Retained workbook expected value',original_formula_forecast:'Calculated workbook forecast',original_forecast:'Retained model forecast',model_forecast:'Saved model forecast',observed_official:'Recorded official observation',observed_source:'Source historical observation',derived_model_history:'Derived historical value',derived_identity:'Accounting-derived value',source_historical:'Original source history',literal_source_historical:'Original historical input',legacy_historical_input:'Retained legacy historical input',run_calculated:'Calculated from supplied formulas',source_input:'Retained source input',run_error:'Calculation error',staff_estimate:'IMF staff estimate',staff_projection:'IMF staff projection',formula_calculated:'Calculated formula value'};
function friendlyValue(value,key){return ['status','data_status','observation_status','Baseline evaluation status'].includes(key)&&typeof value==='string'?(STATUS_LABELS[value]||value):value}
function requireLabel(id){return /^FR\d+$/.test(String(id))?'Functional requirement '+id.slice(2)+' ('+id+')':id}

class DataTable {
  constructor(opts) {
    this.opts = opts;
    this.state = opts.state || {q: '', sort: null, dir: 'asc', page: 1, size: opts.pageSize || 50};
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
    html += '<label>' + escapeHTML(t('page_size')) + ' <select data-role="size">' + (o.pageSizes || [50, 100, 250]).map(s => '<option' + (s === state.size ? ' selected' : '') + '>' + s + '</option>').join('') + '</select></label></div>';
    html += '<div class="table-scroll' + (o.tall === false ? '' : ' tall') + '"><table class="data">';
    if (o.caption) html += '<caption>' + escapeHTML(o.caption) + '</caption>';
    html += '<thead><tr>';
    for (const col of o.columns) {
      const active = state.sort === (col.key || col.label);
      const mark = active ? (state.dir === 'asc' ? '▲' : '▼') : '';
      const aria = active ? (state.dir === 'asc' ? 'ascending' : 'descending') : 'none';
      html += '<th' + ' class="' + [col.num?'num':'',col.sticky?'sticky-col':''].filter(Boolean).join(' ') + '"' + ' aria-sort="' + aria + '"><button type="button" class="th-btn" data-sort="' + escapeHTML(col.key || col.label) + '">' + escapeHTML(fieldLabel(col.label)) + '<span class="sort-mark">' + mark + '</span></button></th>';
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
    html += '<tr><th>' + escapeHTML(fieldLabel(k)) + '</th><td>' + shown + '</td></tr>';
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

const WHY_PAGES=[
 ['why-oxlon','Why Oxlon?','What the independent modelling framework adds to the Ministry’s toolkit.'],
 ['differences','Method differences','The roles, strengths and limits of Ministry macro, CAEM, Oxlon and IMF projections.'],
 ['oxlon-approach','Approach and equations','How assumptions, estimated equations, model selection and accounts become forecasts.'],
 ['oxlon-validation','Validation and benchmarks','Recorded forecast tests, their numerical results and the evidence still needed.'],
 ['indicator-comparison','Indicator comparisons','Definitions and source records for all 25 headline indicators.'],
 ['cpi-explained','CPI worked example','Why the saved 2025 inflation values differ, with original equation contributions.'],
 ['accounting-requirements','Accounts and requirements','Accounting identities, reconciliation and functional requirements 1–12.']
];

const SECTIONS = [
  {path:'overview', label:()=>t('nav_overview'), group:'nav_workbench'},
  {path:'forecasts', label:()=>t('nav_forecasts'), group:'nav_workbench'},
  {path:'ministry',label:()=>t('nav_ministry'),group:'nav_workbench'},
  {path:'oxlon',label:()=>t('nav_oxlon'),group:'nav_workbench'},
  {path:'scenarios', label:()=>t('nav_scenarios'), group:'nav_workbench'},
  {path:'models', label:()=>t('nav_models'), group:'nav_workbench'},
  {path:'equations', label:()=>t('nav_equations'), group:'nav_evidence'},
  {path:'workbook', label:()=>t('nav_workbook'), group:'nav_evidence'},
  {path:'library', label:()=>t('nav_library'), group:'nav_evidence'},
  {path:'methods', label:()=>t('nav_methods'), group:'nav_evidence'},
  {path:'delivery', label:()=>t('nav_delivery'), group:'nav_evidence'},
  {path:'requirements', label:()=>t('nav_requirements'), group:'nav_evidence'},
  {path:'terminology',label:()=>t('nav_terminology'),group:'nav_evidence'},
  ...WHY_PAGES.map(([path,title])=>({path,label:()=>path==='why-oxlon'?t('nav_why_overview'):path==='differences'?t('nav_differences'):title,group:'nav_why'})),
  {path:'caem',label:()=>t('nav_caem_overview'),group:'nav_caem'},  {path:'caem-real',label:()=>t('nav_caem_real'),group:'nav_caem'},  {path:'caem-prices',label:()=>t('nav_caem_prices'),group:'nav_caem'},  {path:'caem-fiscal',label:()=>t('nav_caem_fiscal'),group:'nav_caem'},  {path:'caem-monetary',label:()=>t('nav_caem_monetary'),group:'nav_caem'},  {path:'caem-external',label:()=>t('nav_caem_external'),group:'nav_caem'},  {path:'caem-labour',label:()=>t('nav_caem_labour'),group:'nav_caem'},  {path:'caem-scenarios',label:()=>t('nav_caem_scenarios'),group:'nav_caem'},  {path:'caem-methods',label:()=>t('nav_caem_methods'),group:'nav_caem'},  {path:'caem-data',label:()=>t('nav_caem_data'),group:'nav_caem'},  {path:'caem-checks',label:()=>t('nav_caem_checks'),group:'nav_caem'},  {path:'caem-records',label:()=>t('nav_caem_records'),group:'nav_caem'}
];
function renderNav(current) {
 const nav=$('#navigation'),activeGroup=SECTIONS.find(s=>s.path===current)?.group||'nav_workbench';let html='';
 for(const group of [...new Set(SECTIONS.map(s=>s.group))]){
  html+='<details class="nav-section"'+(group===activeGroup?' open':'')+'><summary class="nav-group">'+escapeHTML(t(group))+'</summary>';
  for(const section of SECTIONS.filter(s=>s.group===group))html+='<a href="#/'+section.path+'"'+(current===section.path?' class="active" aria-current="page"':'')+'><span class="nav-dot"></span>'+escapeHTML(section.label())+'</a>';
  html+='</details>';
 }
 nav.innerHTML=html;$('#sidebar-release').innerHTML='MİİS 15.5.1<br>17 September 2026';
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
  html+='<p class="definition-note">'+(lang==='az'?'Nazirlik makro və Nazirlik CAEM iki Nazirlik sistemidir. 2025-ci il üzrə CPI sətrləri gözlənilən qiymət, proqnoz, faktiki müşahidə və BVF qiymətləndirməsidir; məlumat dövrləri fərqlənir.':'Ministry macro and Ministry CAEM are both Ministry systems. Comparison rows retain expected, forecast, historical, derived and published-reference statuses with different information sets. Each indicator also requires its own definition and scope checks.')+' <a href="#/differences">'+(lang==='az'?'Metod və məlumat fərqləri':'Method and data differences')+'</a></p>';
  html+='<div class="comparison-wrap table-scroll"><table class="data comparison-matrix"><caption>'+(lang==='az'?'Baza ssenarisi · hər modelin mənbə məlumatları və ölçü vahidləri saxlanılır.':'Baseline comparison · each model retains its source data and units.')+'</caption><thead><tr><th class="sticky-col">'+(lang==='az'?'Göstərici / model':'Indicator / model')+'</th><th>'+(lang==='az'?'Vahid':'Unit')+'</th>'+years.map(y=>'<th class="num">'+y+'</th>').join('')+'<th>'+(lang==='az'?'Tərif və mənbə dövrü':'Definition and data vintage')+'</th></tr></thead><tbody>';
  let n=0;
  for (const c of filtered) {
    const maps=c.mappings.filter(m=>model==='*'||m.model_id===model);
    if(!maps.length)continue;
    html+='<tr class="indicator-row"><th colspan="'+(years.length+3)+'">'+escapeHTML(c.label)+' <a class="indicator-audit-link" href="#/indicator-comparison?indicator='+encodeURIComponent(c.concept_id)+'&year='+(start<=2025&&end>=2025?2025:start)+'">'+(lang==='az'?'Təriflər və metodlar':'Definitions and methods')+' →</a></th></tr>';
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
  html+='<div class="actions-row comparison-actions"><a class="btn" href="#/differences">'+(lang==='az'?'Bütün göstəricilər üzrə metod fərqləri':'Why the model results differ · all indicators')+'</a><a class="btn" href="#/delivery">'+(lang==='az'?'CSV təhvil faylları':'Ministry delivery CSV files')+'</a></div>';
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
function scenarioLabel(id,model) { const g=catalogue.result_groups.find(g=>g.model_id===model&&g.scenario_id===id);const n=catalogue.result_groups.filter(g=>g.model_id===model).findIndex(g=>g.scenario_id===id)+1;if(g?.label)return g.label.replace(/ · [a-f0-9]{10}$/, ' · saved case '+n);return id==='baseline'?'Baseline':id.startsWith('interactive_')?'Saved source-input scenario · case '+n:id.replace(/_/g,' '); }

async function viewForecasts(params, ticket, scope) {
  const scopedRoute=scope?.route||'forecasts';
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
  let html = head(scope?.title||'Forecast explorer',scope?'Saved source results, with recorded observation statuses, units, methods and calculation limits.':'Every saved record from the executed runs. Baseline ministry run is the default selection.');
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
  if(scope)$('#f-model').disabled=true;
  const currentFilters = () => ({model: model === '*' ? '' : model, scenario: scenario === '*' ? '' : scenario, fr: state.fr, unit: state.unit, start: state.start, end: state.end, q: state.q});
  function syncUrl() {
    const p = new URLSearchParams();
    if (model !== 'ministry_macro') p.set('model', model);
    if (scenario !== 'baseline') p.set('scenario', scenario);
    for (const k of ['fr','unit','q','start','end']) if (state[k]) p.set(k, state[k]);
    if (state.exact) p.set('exact', '1');
    p.set('wide', state.wide ? '1':'0');
    setParams(scopedRoute, p, false);
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
        rows: gridRows, columns, pageSize:50, exact: state.exact, searchable: false,
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
        rows: filtered, pageSize:50, exact: state.exact, searchable: false,
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
    setParams(scopedRoute, p, true);
  });
  $('#f-scenario').addEventListener('change', () => {
    const p = new URLSearchParams();
    if (model !== 'ministry_macro') p.set('model', model);
    const sc = $('#f-scenario').value;
    if (sc !== 'baseline') p.set('scenario', sc);
    for (const k of localKeys) if (state[k]) p.set(k, state[k]); p.set('wide',state.wide?'1':'0'); if(state.exact)p.set('exact','1');
    setParams(scopedRoute, p, true);
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
  $('#f-reset').addEventListener('click', () => setParams(scopedRoute, new URLSearchParams(), true));
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
      const table = new DataTable({rows, columns: dcols, pageSize:50, caption: 'Precomputed differences against the same-engine baseline. Source identities join exactly.',
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
 h+='<section class="panel"><h2>Why add Oxlon?</h2><p>Read how its recorded candidate selection, assumptions and validation complement the Ministry systems, with equations and numerical evidence.</p><a class="btn" href="#/why-oxlon">Why Oxlon? →</a></section>';
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
      rows: filteredRows, pageSize:50,
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
      rows: math, pageSize:50,
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
      rows, columns: cols, pageSize:50,
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
  const host=$('#wb-grid');host.innerHTML='';host.appendChild(new DataTable({rows:data,columns,pageSize:50,caption:entry.path+' · '+fmtInt(data.length)+' original source rows after the heading. Empty cells remain empty.',onActivate:r=>{const obj={'Workbook':'MIIS_1551_RESULTS.xlsx','Sheet':entry.sheet,'Original row':r.row};headers.forEach((v,i)=>{obj[String(v||entry.columns[i])+' ['+entry.columns[i]+']']=r.values[i]});openDetail(entry.sheet+' · row '+r.row,propsTable(obj));}}).root);
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
    rows, pageSize:50,
    columns: [
      {key:'title', label:'Dataset', sticky:true, wrap:true},
      {key:'description',label:'Contents and interpretation',wrap:true,get:r=>r.description||r.note||'Original source records; inspect the dataset for all source fields.'},
      {key:'kind', label:'Kind', render:r=>'<span class="badge">'+escapeHTML(r.kind)+'</span>'},
      {key:'scope', label:'Scope', wrap:true, render:r=>'<span class="' + (/Verification|historical|Original/i.test(r.scope) ? 'badge pending' : 'badge') + '">'+escapeHTML(r.scope)+'</span>'},
      {key:'model_id', label:'Engine', render:r=>r.model_id?modelTag(r.model_id):'<span class="unavail">-</span>'},
      {key:'row_count', label:'Rows', num:true},
      {key:'cols', label:'Columns', num:true, get:r=>r.columns.length},
      {key:'source',label:'Original file',get:r=>r.path,render:r=>'<details><summary>Source details</summary><code>'+escapeHTML(r.path)+'</code></details>'}
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
  let html = head(entry.title, entry.description||entry.note || null);
  html += '<div class="counters"><span class="counter"><span class="n">' + fmtInt(entry.row_count) + '</span><span class="l">' + escapeHTML(t('rows')) + '</span></span><span class="counter"><span class="n">' + entry.columns.length + '</span><span class="l">columns</span></span><span class="counter"><span class="n">' + escapeHTML(entry.kind) + '</span><span class="l">kind</span></span><span class="counter"><span class="n" style="font-size:13px">' + escapeHTML(entry.scope) + '</span><span class="l">scope</span></span></div>';
  html += '<details class="source-provenance"><summary>Original file and source details</summary><p>'+escapeHTML(entry.path)+'</p></details><div id="t-host"></div>';
  view().innerHTML = html;
  const cols = entry.columns.map((label, i) => ({
    key: 'c' + i, label:fieldLabel(label), originalLabel:label, wrap: String(label).length > 24 || i === entry.formula_column,
    get: r => r[i],
    render: i === entry.formula_column ? (r => '<code>' + escapeHTML(String(r[i] ?? '').slice(0, 160)) + '</code>') : (r => {
      const v = r[i];
      if (v === '') return '';
      if (isUnavailable(v)) return '<span class="unavail">' + escapeHTML(t('unavailable')) + '</span>';
      return escapeHTML(displayValue(friendlyValue(v,label)));
    })
  }));
  const q0 = params.get('q') || '';
  const table = new DataTable({
    rows, columns: cols, pageSize:50,
    state: {q: q0, sort: null, dir: 'asc', page: 1, size:50},
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
 $('#original-documents').appendChild(new DataTable({rows:originals,columns:docColumns,tall:false,pageSize:50,onActivate:r=>setParams('document',new URLSearchParams('id='+r.id),true)}).root);
 $('#notebook-index').appendChild(new DataTable({rows:catalogue.notebooks,columns:[{key:'title',label:'Notebook',sticky:true},{key:'path',label:'Source',wrap:true},{key:'cell_count',label:'Cells',num:true},{key:'note',label:'Scope',wrap:true}],tall:false,onActivate:r=>setParams('notebook',new URLSearchParams('id='+r.id),true)}).root);
 $('#doc-table').appendChild(new DataTable({rows:catalogue.documents.filter(d=>!originals.includes(d)),columns:docColumns,pageSize:50,onActivate:r=>setParams('document',new URLSearchParams('id='+r.id),true)}).root);
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
    const table = new DataTable({rows: arr, columns, pageSize:50, tall: false, caption: fmtInt(arr.length) + ' array items'});
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
 h+='<p class="definition-note">FR means <strong>functional requirement</strong>. FR1–FR12 are the twelve contractual requirement references in Ministry specification §15.5.1. <a href="#/terminology">Terminology and column meanings</a></p>';
 h+='<div class="fr-rail">'+reqs.map(r=>'<a href="#/requirements?fr='+r.id+'"'+(r.id===req.id?' class="active" aria-current="page"':'')+' title="'+escapeHTML(requireLabel(r.id))+'">'+r.id+'</a>').join('')+'</div>';
 h+='<section class="panel"><h2>'+requireLabel(req.id)+'</h2><p class="req-az" lang="az">'+escapeHTML(req.requested_text_az)+'</p><p class="req-en">'+escapeHTML(req.faithful_english)+'</p><table class="props"><tbody><tr><th>Requirement source</th><td>'+escapeHTML(req.source.file.split('/').pop())+' · '+escapeHTML(req.source.locator)+'</td></tr><tr><th>Source inputs still required</th><td>'+escapeHTML(req.outstanding_official_inputs)+'</td></tr></tbody></table></section>';
 h+='<section class="panel"><h2>'+requireLabel(req.id)+' · '+(lang==='az'?'Baza proqnoz cədvəli':'Baseline forecast table')+'</h2><p class="notice-line">'+(lang==='az'?'Sütun başlıqlarına klikləyərək sıralayın. Sətirə klikləyərək bütün illərin dəqiq qiymətlərini və mənbələrini görün.':'Sort using column headings. Select a row for exact values and sources across all years.')+'</p><div class="filterbar" id="reqfilters">'+selectField('Model','req-model',[{value:'*',label:t('all')},...release.models.map(m=>({value:m.id,label:modelMeta(m.id).short}))],params.get('model')||'*')+'<div class="field"><label for="req-q">'+t('search')+'</label><input id="req-q" type="search" placeholder="series, concept, source"></div></div><div id="requirement-results" class="loading">'+t('loading')+'</div></section>';
 const xs=catalogue.tables.find(x=>/FR_ATOMIC_CROSSWALK/.test(x.path));const fb=catalogue.tables.find(x=>/FEEDBACK_25_CROSSWALK/.test(x.path));
 h+='<section class="panel"><h2>Detailed requirement mapping</h2><div class="actions-row"><a class="btn" href="#/workbook?sheet='+req.id+'">'+req.id+' results workbook table</a><a class="btn" href="#/forecasts?model=*&scenario=baseline&fr='+req.id+'&wide=1&start=2024">All original '+req.id+' records</a>'+(xs?'<a class="btn" href="#/table?id='+xs.id+'&q='+req.id+' ">Atomic requirement definitions</a>':'')+(fb?'<a class="btn" href="#/table?id='+fb.id+'">Ministry feedback: 25 items</a>':'')+'</div></section>';
 h+='<section class="panel"><h2>All requirements</h2><div id="requirements-index"></div></section>';
 view().innerHTML=h;
 $('#requirements-index').appendChild(new DataTable({rows:reqs,columns:[{key:'id',label:'FR',sticky:true},{key:'faithful_english',label:'Required output',wrap:true},{key:'outstanding_official_inputs',label:'Required official inputs',wrap:true}],tall:false,pageSize:50,onActivate:r=>setParams('requirements',new URLSearchParams('fr='+r.id),true)}).root);
 const all=(await Promise.all(release.models.map(m=>loadGroupRows(m.id,'baseline')))).flat().filter(r=>(r.fr_ids||[]).includes(req.id)&&Number(r.year)>=2024&&Number(r.year)<=2030);
 if(!fresh(ticket))return;
 function show(){
  const model=$('#f-req-model').value,q=$('#req-q').value.toLocaleLowerCase();
  const rs=all.filter(r=>(model==='*'||r.model_id===model)&&(!q||[r.series_id,r.concept,r.source_file,r.source_sheet].join(' ').toLocaleLowerCase().includes(q)));
  const map=new Map();for(const r of rs){const k=JSON.stringify([r.model_id,r.series_id,r.unit,r.source_file,r.source_sheet,r.reporting_role]);if(!map.has(k))map.set(k,{meta:r,years:new Map()});const g=map.get(k);if(!g.years.has(Number(r.year)))g.years.set(Number(r.year),[]);g.years.get(Number(r.year)).push(r);}
  const grid=[...map.values()],years=[2024,2025,2026,2027,2028,2029,2030];
  const columns=[{key:'model',label:'Model',sticky:true,get:r=>r.meta.model_id,render:r=>modelTag(r.meta.model_id)},{key:'indicator',label:'Indicator',wrap:true,get:r=>r.meta.concept},{key:'series',label:'Series',get:r=>r.meta.series_id},{key:'unit',label:'Unit',get:r=>r.meta.unit},...years.map(y=>({key:'y'+y,label:String(y),num:true,get:r=>{const xs=r.years.get(y);return xs&&xs.length===1?xs[0].value:xs?xs.map(x=>x.value).join(' | '):null;},render:r=>{const xs=r.years.get(y);return xs?xs.map(x=>escapeHTML(displayValue(x.value))).join('<br>'):'<span class="unavail">—</span>';}})),{key:'source',label:'Source',wrap:true,get:r=>[r.meta.source_file,r.meta.source_sheet].join(' / ')}];
  const host=$('#requirement-results');host.className='';host.innerHTML='';host.appendChild(new DataTable({rows:grid,columns,searchable:false,pageSize:50,caption:fmtInt(rs.length)+' baseline source records; '+fmtInt(grid.length)+' indicator/source rows. Missing values are not replaced by zeros.',onActivate:r=>{let detail=recordDetail(r.meta);const vals=[...r.years.values()].flat();detail+='<table class="data"><thead><tr><th>Year</th><th>Exact value</th><th>Source cell</th><th>Data status</th></tr></thead><tbody>'+vals.map(x=>'<tr><td>'+x.year+'</td><td class="num">'+escapeHTML(displayValue(x.value,true))+'</td><td>'+escapeHTML(x.source_cell)+'</td><td>'+escapeHTML(x.data_status)+'</td></tr>').join('')+'</tbody></table>';openDetail(r.meta.concept,detail);}}).root);
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
  for (const section of SECTIONS)searchIndex.push({kind:'page',label:section.label(),sub:t(section.group),route:'#/'+section.path});
  for (const g of catalogue.result_groups) searchIndex.push({kind:'run', label:modelMeta(g.model_id).short + ' · ' + scenarioLabel(g.scenario_id,g.model_id), sub:g.row_count + ' records', route:'#/forecasts?model=' + encodeURIComponent(g.model_id) + '&scenario=' + encodeURIComponent(g.scenario_id)});
  for (let i = 1; i <= 12; i++) searchIndex.push({kind:'requirement', label:'Functional requirement '+i+' (FR'+i+')', sub:'Supplied requirement wording and saved output inventory', route:'#/requirements?fr=FR' + i});
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
 if (/derived|proxy/i.test(s)) return {kind:'derived',label:lang==='az'?'Hesablanmış / proksi':'Derived / proxy'};
 if (/observed|actual|historical|source_historical/i.test(s)) return {kind:'history',label:lang==='az'?'Tarixi / faktiki':'History / actual'};
 if (/forecast|projection/i.test(s)) return {kind:'forecast',label:lang==='az'?'Proqnoz':'Forecast'};
 if (/source_input/.test(s)) return {kind:'source',label:lang==='az'?'Mənbə girişi':'Source input'};
 return {kind:'forecast',label:r.data_status||r.status||'Saved value'};
}
const methodEvidenceP=()=>loadAsset(catalogue.method_evidence_key);
const deliveryP=()=>loadAsset(catalogue.delivery_key);
function evidenceColumns(keys) {return keys.map(k=>({key:k,label:fieldLabel(k),wrap:!['value','year','coefficient','driver','contribution_pp','log_index_contribution'].includes(k),num:['value','year','coefficient','driver','contribution_pp','log_index_contribution','difference_from_observed_pp'].includes(k),render:r=>escapeHTML(displayValue(friendlyValue(r[k],k),true))}));}
function renderAllIndicatorAudit(e,params) {
 const definitions=e.all_indicator_definitions,selected=params.get('indicator')||'gdp_real_growth_market',year=Number(params.get('year')||2025),d=definitions.find(x=>x.concept_id===selected)||definitions[0];
 const host=$('#all-indicator-audit');
 host.innerHTML='<h2>All 25 indicators · definitions, methods and source audit</h2><p>Read each economic target separately. The same units or similar names do not establish matching statistical boundaries, classification, source inputs or forecast origins. This audit retains every mapped saved value and its provenance for 2024–2031.</p><div id="indicator-definition-index"></div><div class="filterbar" id="indicator-controls">'+selectField('Detailed indicator','audit-indicator',definitions.map(x=>({value:x.concept_id,label:x.indicator})),d.concept_id)+selectField('Reference year','audit-year',[2024,2025,2026,2027,2028,2029,2030,2031],year)+'</div><h3>'+escapeHTML(d.indicator)+' · '+year+'</h3><p>'+escapeHTML(d.technical_interpretation)+'</p>'+(d.original_mapping_notes?'<p class="definition-note">'+escapeHTML(d.original_mapping_notes)+'</p>':'')+'<div id="indicator-source-results"></div><p>Select a source row to inspect its exact saved value, original formula, recorded method, source address, price basis, classification, sign convention and vintage. A missing mapped result remains unavailable; a source formula is not an authenticated updated Ministry forecast.</p><div id="indicator-definition-decisions"></div><a class="btn" href="#/overview?concept='+encodeURIComponent(d.concept_id)+'&start=2024&end=2031">Open this indicator’s complete comparison →</a> <a class="btn" href="#/delivery?file=all-comparisons">All indicator/year audit · HTML and CSV →</a>';
 const change=(indicator,refYear=year)=>{const p=new URLSearchParams(params);p.set('indicator',indicator);p.set('year',refYear);setParams('indicator-comparison',p,true)};
 $('#indicator-definition-index').appendChild(new DataTable({rows:definitions,columns:[{key:'indicator',label:'Indicator',wrap:true},{key:'technical_interpretation',label:'Definition and comparison limit',wrap:true}],caption:'Complete 25-indicator register · select any row for its numerical/source audit',tall:false,pageSize:50,onActivate:r=>change(r.concept_id)}).root);
 $('#f-audit-indicator').addEventListener('change',()=>change($('#f-audit-indicator').value,$('#f-audit-year').value));
 $('#f-audit-year').addEventListener('change',()=>change($('#f-audit-indicator').value,$('#f-audit-year').value));
 const rows=e.all_comparison_rows.filter(r=>r.concept_id===d.concept_id&&r.year===year);
 $('#indicator-source-results').appendChild(new DataTable({rows,columns:[{key:'model_id',label:'System',render:r=>modelTag(r.model_id)},{key:'value',label:'Value',num:true,render:r=>r.value==null?'Unavailable':escapeHTML(Number(r.value).toLocaleString('en-GB',{maximumFractionDigits:3}))},...evidenceColumns(['unit','observation_status','scope','source_sheet','source_cell'])],caption:'Separate source values · all precision and formulas available in row details',tall:false,onActivate:r=>{let html=propsTable(r);if(r.result_available&&['ministry_macro','ministry_caem'].includes(r.model_id))html+='<a class="btn" href="#/equations?tab=native&model='+encodeURIComponent(r.model_id)+'&sheet='+encodeURIComponent(r.source_sheet)+'">Original source formula network →</a>';openDetail(d.indicator+' · '+modelMeta(r.model_id).short+' · '+year,html)}}).root);
 $('#indicator-definition-decisions').appendChild(new DataTable({rows:d.comparability_decisions,columns:[{key:'models',label:'Provider pair',render:r=>r.models.map(x=>modelMeta(x).short).join(' / '),wrap:true},{key:'comparable_definition',label:'Definition mapped',render:r=>r.comparable_definition?'Mapped concept; read scope guards':'Different / unresolved'},{key:'comparable_vintage',label:'Common information set',render:r=>r.comparable_vintage?'Matched':'Different retained vintages'},...evidenceColumns(['reason'])],tall:false,caption:'Original definition decisions · added IMF references retain their separate published vintage'}).root);
}
function renderAccountCheck(e){
 const a=e.caem_nominal_account_check;
 $('#caem-account-check').innerHTML='<h2>CAEM current-price GDP · production and expenditure source totals</h2><p>The source production-book GDP for 2025 is <strong>'+escapeHTML(a.production.value.toLocaleString('en-GB',{maximumFractionDigits:3}))+' million AZN</strong> ('+escapeHTML(a.production.source_sheet)+'!'+a.production.source_cell+'). The expenditure-framework total is <strong>'+escapeHTML(a.expenditure.value.toLocaleString('en-GB',{maximumFractionDigits:3}))+' million AZN</strong> ('+escapeHTML(a.expenditure.source_sheet)+'!'+a.expenditure.source_cell+'). Their retained difference is <strong>'+escapeHTML(a.difference_mln_AZN.toLocaleString('en-GB',{maximumFractionDigits:3}))+' million AZN</strong>.</p><p>'+escapeHTML(a.note)+' The canonical headline continues to use the expenditure framework; the production total remains a distinct existing source result.</p>';
}
function renderRequirementScope(e){
 $('#fr-method-scope').appendChild(new DataTable({rows:e.fr_scope,columns:[{key:'fr',label:'Requirement',render:r=>'<a href="#/requirements?fr='+r.fr+'">'+r.fr+'</a>'},{key:'model_id',label:'System',render:r=>modelTag(r.model_id)},...evidenceColumns(['records','unavailable_values','run_errors','source_sheets','observation_statuses'])],caption:'All FR1–FR12 · saved baseline coverage and observation statuses',pageSize:50,tall:false,onActivate:r=>openDetail(r.fr+' · '+modelMeta(r.model_id).short,propsTable(r)+'<a class="btn" href="#/requirements?fr='+r.fr+'">Full requirement and recorded outputs →</a> <a class="btn" href="#/delivery?file='+r.fr+'">Requirement CSV and HTML preview →</a>')}).root);
}

function providerPanel(e){let h="";
 h+='<section class="panel" id="ownership"><h2>Which system belongs to whom?</h2><p>Both <strong>Ministry macro</strong> and <strong>Ministry CAEM</strong> are supplied Ministry of Economy systems. CAEM means <em>Comprehensive Adaptive Expectations Model</em>; it was developed with IMF technical assistance and customized for the Ministry. The IMF Article IV staff projections are a separate published reference.</p><p>The <a href="'+escapeHTML(e.sources.imf_ta)+'" target="_blank" rel="noopener noreferrer">IMF technical-assistance report</a> documents CAEM’s integration into the Ministry’s toolkit (pp. 7, 11, 15). Its provenance does not make the Ministry workbook identical to the IMF country team’s Article IV projections.</p><div id="provider-table"></div></section>';
return h;}

function accountingPanels(e){let h="";
 h+='<section class="panel" id="account-definitions"><h2>Accounting definitions used across the indicators</h2><p>These identities explain measurement and reconciliation. They do not replace the original model equations or estimate new coefficients.</p>';
 const identities=[['Market prices and basic prices',String.raw`Y_t^{\mathrm{market}}=\sum_j VA_{j,t}^{\mathrm{basic}}+T_t^{\mathrm{products}}-S_t^{\mathrm{products}}`,'Match branches, product-tax allocation and the oil/non-oil classification before comparing components.'],['Implicit GDP deflator growth',String.raw`1+g_t^{\mathrm{nom}}/100=(1+g_t^{\mathrm{real}}/100)(1+\pi_t^{\mathrm{GDP}}/100)`,'Nominal growth, volume growth and GDP-deflator growth require compatible annual GDP series. GDP inflation is different from CPI inflation.'],['Fixed capital and inventories',String.raw`I_t^{\mathrm{gross}}=GFCF_t+\Delta Inv_t`,'The original CAEM row 11 includes inventory change; source row 12 is fixed formation. Statistical investment directed to fixed capital has its own perimeter.'],['Fiscal balance',String.raw`B_t^{\mathrm{same\ perimeter}}=R_t-E_t`,'This simple difference uses the same institutional and accounting perimeter. General-government GFSM net lending/borrowing requires its actual source definitions of revenue, expense and net acquisition of nonfinancial assets.'],['Current-account amount',String.raw`CA_t=(X_t^{\mathrm{BoP}}-M_t^{\mathrm{BoP}})+PI_t^{\mathrm{net}}+SI_t^{\mathrm{net}}`,'Use the BoP goods/services balance and net primary/secondary income. National-account trade and customs goods remain separate targets.'],['Current-account/GDP currency alignment',String.raw`ca_t^{\%GDP}=100\frac{CA_t^{\mathrm{USD}}\,e_t^{\mathrm{AZN/USD}}}{Y_t^{\mathrm{AZN}}}`,'Both amounts must have compatible scales and vintages. This explains the conversion rule; it does not fill missing mappings or replace a non-oil ratio with a whole-economy ratio.']];
 for(const [title,tex,note] of identities)h+='<h3>'+title+'</h3><div class="math-block" data-display="1" data-math="'+escapeHTML(tex)+'"></div><p>'+note+'</p>';
 h+='</section><section class="panel" id="fr-scope"><h2>All 12 functional requirements</h2><p>The register below covers all contractual functional-requirement output groups (FR1–FR12), including monetary, wages, employment and detailed external flows that are outside the 25 headline comparison mappings. Open a requirement for its full supplied wording, saved result tables, statuses and original notebook/method sources. Counts describe mapped saved outputs and do not establish contractual acceptance.</p><div id="fr-method-scope"></div><div class="actions-row">'+Array.from({length:12},(_,i)=>'<a class="btn" href="#/notebook?id=notebook-FR'+String(i+1).padStart(2,'0')+'">FR'+(i+1)+' saved method</a>').join('')+'</div></section>';
return h;}

function cpiPanels(e){let h="";
 h+='<section class="panel" id="cpi-case"><h2>Why does annual-average CPI differ in 2025?</h2><p><code>cpi_infl</code> and <code>cpi_avg</code> are native series names for the same annual-average inflation concept in these mapped rows. The 2025 entries have different information sets and observation statuses.</p><div id="cpi-audit-table"></div><p>The <a href="'+escapeHTML(e.sources.official_cpi)+'" target="_blank" rel="noopener noreferrer">State Statistical Committee’s 14 January 2026 CPI release</a> reports annual-average inflation of <strong>5.6%</strong> and December-on-December inflation of <strong>5.2%</strong>. The Oxlon input cache records the 19 January macroeconomic release; it uses the same annual-average 5.6% value.</p><p>The old macro expected value is <strong>3.858 percentage points below</strong> the observed outcome; CAEM’s retained forecast is <strong>0.547 percentage points below</strong>. These are retrospective gaps in saved values. The files do not establish when each legacy forecast was formally issued, so they cannot establish a controlled out-of-sample comparison.</p><p>Oxlon’s 2025 value is a historical observation, and the IMF labels 2025 an estimate. Their agreement at 5.6% is <strong>not evidence of forecast superiority</strong>. Keep the legacy results as an auditable snapshot and distinguish them from updated actual data.</p><a class="btn" href="#/overview?concept=cpi_annual_average_inflation&start=2025&end=2031">Compare the complete CPI paths →</a></section>';
 h+='<section class="panel"><h2>Annual-average, December and index levels</h2><p>Using a consistent monthly CPI index, the annual-average inflation definition is:</p><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\bar I_t=\frac{1}{12}\sum_{m=1}^{12} I_{t,m},\qquad \pi_t^{\mathrm{avg}}=100\left(\frac{\bar I_t}{\bar I_{t-1}}-1\right)`)+'"></div><p>December-on-December inflation is a separate concept:</p><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\pi_t^{\mathrm{Dec}}=100\left(\frac{I_{t,12}}{I_{t-1,12}}-1\right)`)+'"></div><p>An index of 105.6 relative to the prior year’s 100 corresponds to a 5.6% increase. The two inflation formulas need not produce the same number. These formulas explain definitions; this page does not invent missing monthly observations.</p></section>';
 h+='<section class="panel" id="technical-methods"><h2>1. Ministry macro · linked accounts and CPI-index equation</h2><p>The bottom-up accounts use company/product volumes and domestic/export prices, branch value added and net taxes, with dependencies across the real, trade, fiscal and social workbooks. CPI is produced by its own supplied econometric equation in <code>MOE INF.xlsx</code>; it is not calculated by summing the company production plans.</p><p>The original <code>11_12!AJ6</code> formula is <code>AJ24/AI24*100-100</code>, with <code>AJ24=AJ25*AJ26</code>. The saved 2024 index is <code>1.8495871115884663</code>, the 2025 index is <code>1.8818119509529945</code>, and the add-factor <code>AJ26</code> equals 1.</p><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\pi_{2025}^{\mathrm{macro}}=100\left(\frac{1.8818119509529945}{1.8495871115884663}-1\right)=1.7422720542668912\%`)+'"></div><p>The index equation uses CPI persistence, current/lagged NEER, the WEO food-price index, M1, a lagged CPI-gap term and fixed source terms. In this retained 2025 formula the oil-price term and several dummy terms are explicitly multiplied by zero.</p><div id="macro-contribution-table"></div><p>The table reconstructs <code>log(AJ25/AI24)</code>; its terms must be exponentiated before interpreting inflation. The negative NEER terms lower this saved equation’s index growth. This is an explanation within the retained source equation, not a decomposition of the difference from actual inflation.</p><details class="fold"><summary>Original CPI formula and source index cells</summary><div class="fold-body" id="macro-source-cells"></div></details><a class="btn" href="#/equations?tab=native&model=ministry_macro&book=MOE+INF.xlsx&sheet=11_12">Inspect original workbook formulas →</a></section>';
 h+='<section class="panel"><h2>2. Ministry CAEM · adaptive expectations and structural transmission</h2><p>CAEM combines structural behavioural equations, accounting identities, trend/potential-output calculations and policy selectors. Consumption, private investment, exports, goods imports, inflation and interest rates interact with the real, fiscal, monetary and external accounts. The recovered calculation checks both GDP-growth and deflator residuals under the selected CP/YP closure.</p><p>For 2025, <code>6a. SEI!N19</code> links through <code>1c. Interest rates!O19</code> to <code>1b. Infl and Ex rates!O19</code>. The selected inflation regime is <code>Model determined</code>. Its original <code>O24</code> equation uses coefficients 0.1, 0.7, 0.2 and 0.4, then adds calibration and scenario terms.</p><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\pi_{2025}^{e}=0.2\times2.2+0.8\times4=3.64`)+'"></div><div class="math-block" data-display="1" data-math="'+escapeHTML(String.raw`\pi_{2025}^{\mathrm{CAEM}}=0.1(2.2)+0.7(3.64)+0.2(14.0958552363+0-3.9700271725)+0.4(0.6495550577)+0+0\simeq5.0529876359\%`)+'"></div><p>The <code>O8</code> input, 14.095855%, is labelled <em>Imported inflation (USD)</em>: the import deflator derived from partner-country export deflators weighted by imports. <code>O9</code> is the annual-average manat/US-dollar exchange-rate change (positive for depreciation), <code>O10</code> is the trend relative import-price change, and <code>O14</code> is the non-oil output gap as a percentage of non-oil potential output.</p><div id="caem-contribution-table"></div><p>The coefficient and driver cells below are saved source values. The full-precision term sum agrees with the exported 5.052987635856589% within <code>1e−10</code> percentage points; the final digits reflect floating-point calculation. The supplied workbook horizon ends in 2029.</p><details class="fold"><summary>Original CAEM CPI inputs, coefficients and formulas</summary><div class="fold-body" id="caem-source-cells"></div></details><a class="btn" href="#/equations?tab=caem">Original structural equations →</a></section>';
 h+='<section class="panel"><h2>3. Oxlon · recorded estimation, backtests and selected forecast paths</h2><p>Oxlon is an independent pipeline. In FR9 it anchors the history to observed annual-average CPI through 2025, examines econometric alternatives and uses recorded expanding-window forecast tests to choose an ensemble. The saved notebook includes AR(1), a fixed inflation-anchor candidate and a lagged-driver Phillips specification; conditional and diagnostic variants are retained separately.</p><p>The structural alternatives use HAC standard errors. Forecast paths depend on the recorded FR5 oil-price path and declared exchange-rate assumptions: future NEER log changes are set to zero, while the first lagged-driver forecast uses the observed 2025 change. These assumptions are distinct from the macro workbook’s retained NEER path and CAEM’s structural inputs.</p><p>Samples, saved coefficients, selection weights, outputs and limitations are available in the complete notebook. The 486-row specification catalogue includes alternatives and historical Ministry references; it is not a list of 486 operative forecast equations.</p><a class="btn" href="#/notebook?id=notebook-FR09">Read the complete saved FR9 calculation →</a> <a class="btn" href="#/equations?tab=published&model=oxlon.corrected.20260917">View published specifications →</a></section>';
return h;}

function imfPanel(e){let h="";
 h+='<section class="panel"><h2>IMF · published staff projections and CAEM method provenance</h2><p>IMF Article IV Table 1 provides a dated external reference. Its CPI sequence for 2025–2031 is <strong>5.6, 6.0, 5.1, 4.1, 4.0, 4.0, 4.0%</strong>. The reference is mapped into the overview for CPI, total GDP growth and non-oil GDP growth; the remaining indicators have no imported IMF mapping.</p><p>The <a href="'+escapeHTML(e.sources.imf_articleiv)+'#page=28" target="_blank" rel="noopener noreferrer">original Table 1</a> is on PDF page 28 (printed page 22), in report 26/112, completed 26 March and released 26 May 2026. The report’s press-release section contains some different projections; this website retains the identified Table 1 vintage. No separate executable IMF staff model or its coefficients were supplied.</p><p>To study the IMF-assisted CAEM method, use the Ministry CAEM equations and original workbook. To compare published IMF forecasts, use the separate Article IV reference. These are distinct uses of IMF material.</p><a class="btn" href="#/forecasts?model=imf_articleiv_benchmark&scenario=Table1&start=2025&wide=1">IMF reference table →</a></section>';
return h;}

function fairComparisonPanel(e){let h="";
 h+='<section class="panel" id="fair-comparison"><h2>How to make a consistent model comparison</h2><ol><li>Agree the target definitions: annual-average CPI versus December CPI; market-price GDP versus basic-price value added; national-account versus BoP trade; state-budget versus consolidated fiscal accounts.</li><li>Freeze a dated historical information set with matching nominal, real and price series, prior-year bases and declared observation statuses.</li><li>Obtain approved upstream company/product/branch/tax and institutional forecasts, with units, owner, release date and exact original input mappings. Updating only a calculated headline cannot update the complete bottom-up system.</li><li>Run each implemented model on the compatible inputs, retain its endogenous mechanisms and selectors, and save manifests, source input changes, equations, convergence and account checks.</li><li>Compare forecast accuracy only using the same target, forecast origin, information available at that origin, horizon and evaluation sample. Record missing values and source-definition limits before ranking models.</li></ol><p>The present site retains the source vintages and calculated snapshots. A latest-official common-input rerun still needs the missing owner-supplied inputs and agreed mappings. The CSV delivery page makes the current outputs and input collection forms available without relabelling them as authenticated Ministry forecasts.</p><a class="btn" href="#/delivery">Ministry delivery files →</a></section>';
return h;}


function whyNav(active){return '<nav class="topic-nav" aria-label="Why Oxlon pages">'+WHY_PAGES.map(([path,title])=>'<a href="#/'+path+'"'+(path===active?' aria-current="page"':'')+'>'+escapeHTML(title)+'</a>').join('')+'</nav>'}
function whyHead(route,title,lede){return head(title,lede)+whyNav(route)}
function whyCards(exclude){return '<div class="topic-cards">'+WHY_PAGES.filter(x=>x[0]!==exclude).map(([p,title,desc])=>'<a href="#/'+p+'"><strong>'+escapeHTML(title)+'</strong><span>'+escapeHTML(desc)+'</span><span class="topic-arrow" aria-hidden="true">→</span></a>').join('')+'</div>'}
function textTable(id,rows,columns,caption,options={}){$('#'+id).appendChild(new DataTable({rows,columns,caption,tall:false,pageSize:50,...options}).root)}
function whyMath(tex){return '<div class="math-block" data-display="1" data-math="'+escapeHTML(tex)+'"></div>'}
function whySource(route,label){return '<a class="btn" href="#/'+route+'">'+escapeHTML(label)+'</a>'}
async function viewWhyOxlon(params,ticket){
 view().innerHTML=whyHead('why-oxlon','Why Oxlon?','An independent, testable forecast perspective alongside the Ministry’s own models.')+
 '<section class="panel why-intro"><h2>Make the forecast choice explainable</h2><p>Oxlon adds a documented process for testing alternative equations, selecting forecast paths, recording assumptions and tracing results back to data. Its value is a second, inspectable view of the economy: analysts can see which relationships support a forecast, where a simple benchmark works better and why the numbers change.</p><p>The Ministry macro system contributes detailed company, product and branch information. CAEM contributes integrated structural relationships and policy transmission. Oxlon combines sector modelling, statistical forecast selection and accounting aggregation; it complements these systems while allowing their outputs to be challenged against explicit evidence.</p></section>'+
 '<section class="panel"><h2>What makes Oxlon different?</h2><div id="oxlon-advantages"></div></section>'+
 '<section class="panel"><h2>What “better” means in this delivery</h2><p><strong>A more testable decision process:</strong> alternatives, assumptions, selection rules and source records are available for review. The saved CPI ensemble has a 19.4% lower root mean squared error than a last-observation benchmark over 14 annual forecasts. This result uses the same sample for selection and evaluation; it is evidence about the saved selection process.</p><p><strong>Forecast superiority over the Ministry models has not yet been established.</strong> Their retained outputs use different histories, forecast origins and assumptions. A fair ranking requires matched information sets and a separate evaluation sample. Updated historical observations, accounting identities and a larger specification catalogue are not forecast-accuracy gains.</p>'+whySource('oxlon-validation','Read the numerical evidence')+'</section>'+
 '<section class="panel"><h2>Read the explanation in focused pages</h2>'+whyCards('why-oxlon')+'</section>';
 const rows=[
 ['Test alternatives against a simple benchmark','Recorded expanding-window tests compare candidate forecasts with the last observed value; eligible candidates receive inverse-error weights.','Makes the choice of forecast method inspectable, including cases where complexity does not help.','oxlon-validation','Forecast tests'],
 ['Preserve the economic structure','Sector growth and deflators feed production accounts; external-account components feed balance identities. A separate demand calculation remains visible.','Connects individual forecasts to accounts while exposing differences between production and demand results.','oxlon-approach','Model architecture'],
 ['Record estimation choices','Samples, coefficients, diagnostics and alternative specifications are retained in notebooks and equation tables.','Lets analysts examine the mechanism and reproduce the recorded calculation. This transparency is not unique to Oxlon: supplied Ministry equations are also retained.','equations?tab=published&model=oxlon.corrected.20260917','Oxlon specifications'],
 ['Make assumptions explicit','Oil paths, currency-regime assumptions and approved input fields are identified; forecast-input validation checks years, units and required metadata.','Distinguishes an estimated response from a policy assumption or an external project plan. Metadata validation does not authenticate the data owner.','table?id=csv-5126f112242954a0','Assumption register'],
 ['Show risk and limitations','Recorded uncertainty bands, conditional scenarios, source gaps and residual account differences are visible.','Supports sensitivity analysis; nominal bands still depend on distributional and regime assumptions.','oxlon-approach','Uncertainty and assumptions'],
 ['Keep the review connected to delivery','Functional requirements, data definitions, exact result rows and delivery files are linked.','Allows a result to be checked against its stated purpose and source. This is a shared portal capability available for all three systems.','accounting-requirements','Requirements and accounts']
 ].map(([feature,implementation,benefit,path,link])=>({feature,implementation,benefit,path,link}));
 textTable('oxlon-advantages',rows,[{key:'feature',label:'Capability',wrap:true},{key:'implementation',label:'What the saved implementation does',wrap:true},{key:'benefit',label:'Why it helps the Ministry',wrap:true},{key:'source',label:'Evidence',render:r=>'<a href="#/'+r.path+'">'+r.link+'</a>'}],'Evidence-based capabilities · open each source for the implementation and its limits');
}
async function viewDifferences(params,ticket){
 if(params.has('indicator'))return viewIndicatorComparisons(params,ticket);
 loadingView();const e=await methodEvidenceP();if(!fresh(ticket))return;
 view().innerHTML=whyHead('differences','Method differences','A concise comparison of model purpose, economic mechanism and input requirements.')+providerPanel(e)+
 '<section class="panel"><h2>Choose the tool for the question</h2><div id="model-use-cases"></div><p>Oxlon and the Ministry macro model both use econometric relationships and bottom-up elements. CAEM also contains estimated or calibrated behavioural equations. The distinction lies in their source inputs, equation systems, estimation and selection rules, accounting closures and intended use.</p>'+whySource('models','Complete model architecture register')+'</section>'+imfPanel(e)+'<section class="panel"><h2>Continue to the evidence</h2>'+whyCards('differences')+'</section>';
 textTable('provider-table',e.models,evidenceColumns(['provider','method','input_boundary','forecast_years','role']),'Original model roles and retained forecast boundaries');
 textTable('model-use-cases',[
 {question:'What follows from company production plans and detailed branch inputs?',tool:'Ministry macro',strength:'Product quantities, domestic/export prices, branch value added and tax links.',need:'Approved upstream inputs and working source dependencies.'},
 {question:'How do structural relationships and policy assumptions interact across macroeconomic accounts?',tool:'Ministry CAEM',strength:'Behavioural equations, accounting links, adaptive expectations and declared reconciliation choices.',need:'The original selected regime, calibration, exogenous assumptions and closure checks.'},
 {question:'Which empirical specification forecasts a defined series more usefully than a simple benchmark?',tool:'Oxlon',strength:'Candidate comparisons, saved forecast errors, selection rules and explicit assumptions alongside sector accounts.',need:'Adequate history, origin-available drivers, transparent selection and independent evaluation.'},
 {question:'How does the outlook compare with the IMF country team’s published assessment?',tool:'IMF Article IV reference',strength:'A separately dated external published forecast.',need:'Matching definitions and report vintage; no executable IMF staff model is supplied.'}
 ],[{key:'question',label:'Analytical question',wrap:true},{key:'tool',label:'Relevant system',wrap:true},{key:'strength',label:'Contribution',wrap:true},{key:'need',label:'What it depends on',wrap:true}]);
}
async function viewIndicatorComparisons(params,ticket){
 loadingView();const e=await methodEvidenceP();if(!fresh(ticket))return;
 view().innerHTML=whyHead('indicator-comparison','Indicator comparisons','Compare like with like: definitions, units, source dates and observation statuses.')+'<section class="panel" id="all-indicator-audit"></section><section class="panel"><h2>Related explanations</h2>'+whySource('cpi-explained','CPI worked example')+whySource('accounting-requirements','Accounting definitions and all 12 requirements')+whySource('oxlon-validation','Conditions for a fair accuracy comparison')+'</section>';
 renderAllIndicatorAudit(e,params);
}
async function viewAccountingRequirements(params,ticket){
 loadingView();const e=await methodEvidenceP();if(!fresh(ticket))return;
 view().innerHTML=whyHead('accounting-requirements','Accounts and requirements','Economic identities and the scope of all 12 functional requirements.')+accountingPanels(e)+'<section class="panel" id="caem-account-check"></section>';
 renderRequirementScope(e);renderAccountCheck(e);mathAfterRender(view());
}
async function viewCpiExplained(params,ticket){
 loadingView();const e=await methodEvidenceP();if(!fresh(ticket))return;
 view().innerHTML=whyHead('cpi-explained','CPI worked example','One concept, different dates and mechanisms. Read the comparison first; expand the source calculations below.')+cpiPanels(e);
 textTable('cpi-audit-table',e.cpi_2025,[{key:'model_id',label:'System',render:r=>modelTag(r.model_id)},...evidenceColumns(['series_id']),{key:'value',label:'CPI (%)',num:true,render:r=>escapeHTML(Number(r.value).toFixed(3))},...evidenceColumns(['interpretation']),{key:'difference_from_observed_pp',label:'Gap from observed (pp)',num:true,render:r=>escapeHTML(Number(r.difference_from_observed_pp).toFixed(3))}],'Annual-average CPI in 2025 · select a row for its exact source values',{onActivate:r=>openDetail(modelMeta(r.model_id).short+' · CPI 2025',propsTable(r))});
 textTable('macro-contribution-table',e.macro_terms,evidenceColumns(['term','coefficient','driver','log_index_contribution','coefficient_source','driver_expression']),'Original macro CPI equation · log-index contributions, not percentage points');
 textTable('caem-contribution-table',e.caem_terms,evidenceColumns(['term','coefficient','driver','contribution_pp','source']),'Original CAEM 2025 CPI equation · contributions in percentage points');
 textTable('macro-source-cells',e.macro_cells,evidenceColumns(['sheet','cell','executed_value','formula']));
 textTable('caem-source-cells',e.caem_cells,evidenceColumns(['sheet','cell','value','formula']));
 for(const section of [...view().querySelectorAll(':scope > section')]){const heading=section.querySelector('h2');if(!heading||!/^\d\./.test(heading.textContent))continue;const fold=document.createElement('details');fold.className='panel calculation-fold';const summary=document.createElement('summary');summary.textContent=heading.textContent.replace(/^\d\. /,'');fold.appendChild(summary);heading.remove();const body=document.createElement('div');body.className='fold-body';while(section.firstChild)body.appendChild(section.firstChild);fold.appendChild(body);section.replaceWith(fold);}
 mathAfterRender(view());
}
async function viewOxlonApproach(params,ticket){
 const blocks=[
 {title:'1. Sector forecasts build production accounts',text:'Oxlon’s saved headline non-oil GDP comes from the sector block, with value added and product-tax allocation aggregated on consistent price bases. The demand core provides a separate reading. Their forecast difference is published; the sector forecasts are not scaled to conceal it.',tex:String.raw`Y_t^{\mathrm{production}}=\sum_s VA_{s,t}^{\mathrm{basic}}+T_t^{\mathrm{products}}-S_t^{\mathrm{products}}`,symbols:'VA is sector value added; T and S are product taxes and subsidies. Use compatible current-price or volume measures.',route:'notebook?id=notebook-FR02',source:'Sector modelling and aggregation · FR2'},
 {title:'2. Choose a suitable dynamic relationship',text:'Candidate sector equations include a driver relationship, a lagged dependent variable and, where the sample and cointegration checks allow it, an error-correction form. These are alternative families, not three equations applied to every series. The source notebooks record the selected form.',tex:String.raw`g_{s,t}=a_s+b_s x_{s,t}+\varepsilon_{s,t}\qquad\text{or}\qquad g_{s,t}=a_s+\rho_s g_{s,t-1}+b_s x_{s,t}+\varepsilon_{s,t}`,symbols:'g is the sector’s real growth rate; x is its selected economic driver; ρ measures persistence. Actual samples, transformations and dummy variables are specification-specific.',route:'notebook?id=notebook-FR02',source:'Candidate forms and selection · FR2'},
 {title:'3. Test a long-run relationship before using error correction',text:'The sector workflow admits the error-correction candidate when its recorded sample and Engle–Granger cointegration conditions pass. A long-run relationship is an empirical hypothesis, not an automatic consequence of two series trending together.',tex:String.raw`ec_{t-1}=\ln L^g_{t-1}-\hat a-\hat b\ln L^x_{t-1},\qquad \Delta\ln L^g_t=c+\lambda ec_{t-1}+\gamma\Delta\ln L^x_t+u_t`,symbols:'L denotes a level index reconstructed from growth; ec is the deviation from the estimated long-run relationship; λ is the adjustment coefficient. This is the recorded family’s explanatory notation, not newly estimated coefficients.',route:'notebook?id=notebook-FR02',source:'Error-correction eligibility and implementation'},
 {title:'4. Use information available for the stated forecast',text:'The operational CPI candidate uses lagged inflation, Brent-price changes and NEER changes. A contemporaneous-driver specification is retained as a conditional diagnostic. The saved future NEER-change assumption is zero; the first forecast uses the observed 2025 driver in the lagged equation.',tex:String.raw`\pi_t=a+\rho\pi_{t-1}+b\,(100\Delta\ln P^B_{t-1})+c\,(100\Delta\ln NEER_{t-1})+dD_t+u_t`,symbols:'π is annual-average CPI inflation; Pᴮ is Brent; NEER is the nominal effective exchange-rate index; D marks the historical devaluation episode. In the notebook, log differences are multiplied by 100; coefficients must use that same scale.',route:'notebook?id=notebook-FR09',source:'Operational CPI equation · FR9'},
 {title:'5. Combine candidates that improve on the benchmark',text:'For the shared backtest rule, keep eligible candidates with a lower recorded root mean squared error than the last-observation benchmark. Weight them by inverse squared error. If none qualifies, use the benchmark. Block-specific eligibility rules and conditional variants must still be checked.',tex:String.raw`\mathcal K=\{m:RMSE_m<RMSE_{RW}\},\qquad w_m=\frac{RMSE_m^{-2}}{\sum_{j\in\mathcal K}RMSE_j^{-2}},\qquad \hat y_{T+h}=\sum_{m\in\mathcal K}w_m\hat y^{(m)}_{T+h}`,symbols:'RW repeats the last observation; m identifies a candidate; weights sum to one. Selection on the evaluation window makes the resulting skill a selection-sample result.',route:'oxlon-validation',source:'Saved selection results and exact forecast errors'},
 {title:'6. Publish uncertainty with its assumptions',text:'The saved CPI intervals combine horizon-dependent residual variance and a parameter-covariance term, using normal quantiles. This is an approximation: the covariance comes from the lagged Phillips specification, while the centre is an ensemble. It is not a complete joint model of ensemble, driver and regime uncertainty.',tex:String.raw`s_h^2=\sigma_1^2\sum_{j=0}^{h-1}\rho^{2j}+x_h^{\prime}\widehat V x_h,\qquad [L_h,U_h]=\hat\pi_{T+h}\pm z\,s_h`,symbols:'σ₁ is the recorded ensemble one-step RMSE; ρ is the fitted AR(1) coefficient; V is the Phillips parameter covariance; z≈1.2816 for the displayed 80% band. Other blocks use their own documented interval rules.',route:'notebook?id=notebook-FR09',source:'CPI uncertainty calculation · FR9'}
 ];
 view().innerHTML=whyHead('oxlon-approach','Oxlon approach and equations','From source data to candidate models, forecast selection and accounting results.')+
 '<section class="panel"><h2>The workflow</h2><ol class="workflow-steps"><li>Define the economic target and retain source history, units and observation status.</li><li>Declare exogenous assumptions and specify candidate relationships.</li><li>Estimate on the stated sample; retain coefficients and diagnostics.</li><li>Evaluate the recorded forecast errors and apply the block’s selection rule.</li><li>Aggregate components, publish uncertainty and inspect accounting differences.</li></ol><p>The equations below explain the existing implementation. Exact estimated coefficients, sample sizes and source calculations remain in the linked notebooks.</p></section>'+
 blocks.map((b,i)=>'<details class="panel calculation-fold"'+(i===0?' open':'')+'><summary>'+b.title+'</summary><div class="fold-body"><p>'+b.text+'</p>'+whyMath(b.tex)+'<p class="definition-note">'+b.symbols+'</p>'+whySource(b.route,b.source)+'</div></details>').join('')+
 '<section class="panel"><h2>Estimation background</h2><p>Selected regressions report ordinary least squares with heteroskedasticity and autocorrelation consistent (HAC) standard errors. HAC changes uncertainty estimates for coefficients; it does not fix omitted variables, identify causal effects or guarantee smaller forecast errors. Cointegration tests assess evidence for a long-run relation under their assumptions.</p><p>Technical references: <a href="https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html" target="_blank" rel="noopener noreferrer">statsmodels robust covariance documentation</a> and <a href="https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html" target="_blank" rel="noopener noreferrer">Engle–Granger test documentation</a>. The saved source, rather than the current library documentation, determines this delivery’s implementation.</p>'+whySource('document?id=doc-3661c9eb5f5ccbe9','Read the saved estimation and selection implementation')+'</section>'+
 '<section class="panel"><h2>Where assumptions still matter</h2><p>Oil production and project investment paths can remain external inputs. Currency forecasts depend on the stated exchange-rate regime. Some financial-account paths use historical profiles, and reserve flows can be balancing items. Oxlon’s production and demand readings are not fully reconciled. Those choices belong in the interpretation of every forecast.</p>'+whySource('notebook?id=notebook-FR01','GDP production and demand differences')+whySource('notebook?id=notebook-FR10','Currency-regime assumptions')+whySource('notebook?id=notebook-FR12','External-account closure and limits')+'</section>';
 mathAfterRender(view());
}
async function viewOxlonValidation(params,ticket){
 loadingView();const [e,v]=await Promise.all([methodEvidenceP(),loadAsset(catalogue.why_oxlon_key)]);if(!fresh(ticket))return;
 const series=params.get('series')==='current_account'?'current_account':'cpi_infl';
 view().innerHTML=whyHead('oxlon-validation','Validation and benchmarks','What the saved tests demonstrate, and what is needed to compare Oxlon fairly with the Ministry systems.')+
 '<section class="panel"><h2>Read the evidence at the right level</h2><p>The examples below reconstruct recorded one-year-ahead forecast errors from the saved validation table. CPI covers 2012–2025 (14 target years); the current account covers 2019–2025 (7 target years). Both are assessed against a last-observation benchmark on matching rows. They are selected examples, not a ranking of every Oxlon output.</p><p><strong>These are historical selection and diagnostic results.</strong> Candidate weights were informed by the same recorded errors used to assess the combination. The saved histories do not establish the exact data releases available at every historical forecast date. A separate evaluation sample is needed to assess performance after model selection.</p><div id="oxlon-validation-summary"></div></section>'+
 '<section class="panel"><h2>How forecast error is measured</h2>'+whyMath(String.raw`e_{m,v,h}=\hat y^{(m)}_{v+h\mid v}-y_{v+h},\quad RMSE_m=\sqrt{\frac{1}{N}\sum_{(v,h)\in\mathcal C}e_{m,v,h}^{2}},\quad Skill_m=100\left(1-\frac{RMSE_m}{RMSE_{RW}}\right)`)+
 '<p>v is the forecast origin, h the horizon and C the common evaluation rows. Lower RMSE is better; positive skill means a smaller error than the benchmark. CPI errors are in percentage points; current-account errors are in million US dollars. Their raw RMSE levels cannot be ranked against each other.</p></section>'+
 '<section class="panel"><h2>Inspect the saved forecast errors</h2><div class="filterbar">'+selectField('Economic series','validation-series',[{value:'cpi_infl',label:'Annual-average CPI inflation'},{value:'current_account',label:'Current-account balance'}],series)+'</div><div id="oxlon-validation-records"></div><p>Original field names and values are retained in each row’s details. “Forecast origin” is the final training year; target year = origin + horizon. The reconstructed CPI ensemble summary is derived from the recorded candidate rows; it is not an additional original CSV row.</p>'+whySource('table?id=csv-dc1ec6b0891ca256','Read the complete saved validation table')+'</section>'+
 '<section class="panel"><h2>What the numbers do and do not establish</h2><ul><li>The selected CPI ensemble’s RMSE is 4.241 percentage points versus 5.261 for the benchmark: a 19.4% reduction on the selection sample. Its contemporaneous-driver Phillips diagnostic performs worse than the benchmark and has no ensemble weight.</li><li>The saved current-account component combination has an RMSE of 4,757.852 million USD versus 9,035.142: a 47.3% reduction over seven target years. The short sample and component selection limit generalisation.</li><li>The validation file also includes conditional calculations, other sample windows and dynamics indicators. A dynamics ratio is not an accuracy score; similarly, conditional knowledge of a future driver is not an unconditional forecast.</li><li>The code truncates training by year, but this alone cannot exclude revisions to historical data or information used in selecting a specification. Independent evaluation must freeze both vintage and selection.</li><li>No matched-origin evaluation of the complete Ministry macro and CAEM forecasts against Oxlon is supplied. Their old expected values and forecasts cannot be ranked against Oxlon’s later observed data.</li></ul>'+whySource('notebook?id=notebook-FR09','CPI candidate definitions, weights and limits')+whySource('notebook?id=notebook-FR12','Current-account combination and limits')+'</section>'+fairComparisonPanel(e);
 textTable('oxlon-validation-summary',v.examples,[{key:'indicator',label:'Economic target',wrap:true},{key:'method',label:'Method or benchmark',wrap:true},{key:'target_years',label:'Target years'},{key:'sample_size',label:'Years',num:true},{key:'rmse',label:'RMSE',num:true},{key:'unit',label:'Error unit',wrap:true},{key:'improvement_pct',label:'Error reduction vs benchmark (%)',num:true},{key:'selection_weight',label:'CPI ensemble weight',num:true,render:r=>r.selection_weight==null?'—':escapeHTML((100*r.selection_weight).toFixed(1)+'%')},{key:'interpretation',label:'How to interpret',wrap:true}],'Saved one-step assessments and reconstructed CPI ensemble · same-sample selection, not independent Ministry-model comparisons');
 const records=v.records.filter(r=>r.series_code===series);
 $('#oxlon-validation-records').appendChild(new DataTable({rows:records,columns:[{key:'method',label:'Method',wrap:true},{key:'vintage_year',label:'Forecast origin',num:true},{key:'target_year',label:'Target year',num:true},{key:'horizon_h',label:'Horizon (years)',num:true},...['actual','forecast','error'].map(key=>({key,label:key==='actual'?'Observed value':key==='forecast'?'Saved forecast':'Forecast minus observed',num:true,render:r=>escapeHTML(displayValue(Number(r[key])))}))],tall:false,pageSize:50,onActivate:r=>openDetail(r.method+' · '+r.target_year,propsTable(r))}).root);
 $('#f-validation-series').addEventListener('change',()=>setParams('oxlon-validation',new URLSearchParams({series:$('#f-validation-series').value}),true));mathAfterRender(view());
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

const CAEM_INDICATOR_LABELS={output_gap:'Non-oil output gap / non-oil potential output',investment_growth:'Real fixed-capital formation growth',gdp_nom:'Nominal GDP at market prices · expenditure framework',gdp_nom_production_source:'Nominal GDP at market prices · production account',nonoil_gdp_nom:'Non-oil GDP at market prices · source partition',nonoil_gdp_growth:'Real non-oil GDP growth'};
const CAEM_SECTORS={
 real:{en:'Real economy',az:'Real iqtisadiyyat',sheets:['1a. Real GDP - Production','1d. Real GDP - Expenditure','5a.  GDP Nominal + (S+I)','Oil_and_gas_sector'],series:['gdp_growth','output_gap','domestic_demand_growth','consumption_growth','private_consumption_growth','public_consumption_growth','investment_growth','exports_growth','imports_growth'],note:'Production and expenditure accounts, oil/non-oil GDP and demand growth. The retained production and expenditure nominal GDP totals are separate source results.'},
 prices:{en:'Prices and exchange rates',az:'Qiymətlər və məzənnələr',sheets:['1b. Infl and Ex rates','1c. Interest rates'],series:['cpi_avg','gdp_deflator','policy_rate','reer','reer_growth'],note:'Annual-average CPI, the implicit GDP deflator, bilateral dollar exchange rate and effective exchange-rate indices are different measures. Missing policy-rate outputs remain unavailable.'},
 fiscal:{en:'Fiscal accounts and debt',az:'Fiskal hesablar və borc',sheets:['3a. Fiscal ','Fiscal sector','3b. OUT for debt dynamics'],series:['fiscal_revenue_ratio','fiscal_expenditure_ratio','overall_fiscal_balance','government_domestic_debt','government_external_debt','government_total_debt'],note:'The saved summary outputs are general-government/consolidated fiscal ratios and government debt as percentages of GDP. They must remain separate from state-budget amounts and perimeters.'},
 monetary:{en:'Monetary accounts',az:'Pul-kredit hesabları',sheets:['4.  Monetary-Financial','1c. Interest rates'],series:['monetary_nfa','monetary_nda','private_credit_ratio','broad_money_ratio','reserves_broad_money','policy_rate'],note:'Monetary net foreign/domestic assets, private-sector credit, broad money, reserves and interest-rate outputs retain their original units. A ratio to GDP is distinct from a currency amount.'},
 external:{en:'External accounts',az:'Xarici sektor hesabları',sheets:['2a.  External USD','2b. External LCU'],series:['current_account','net_fdi','portfolio_other_investment','reserves_ratio','net_iip','external_debt','saving_investment'],note:'Balance-of-payments amounts in USD and summary ratios to GDP are presented separately. Financial flows retain the source asset/liability sign convention; reserve changes remain a distinct category.'},
 labour:{en:'Employment and incomes',az:'Məşğulluq və gəlirlər',sheets:['1e. Social sector'],series:[],note:'The original CAEM social-sector workbook formulas are available below. No separate normalized employment or wage output series is exported in this saved CAEM baseline; cached source values are not presented as new forecasts.'}
};
function caemSourceLinks(sheets){const entries=catalogue.tables.filter(x=>x.kind==='native'&&x.model_id==='ministry_caem'&&sheets.includes(x.sheet));return '<div class="actions-row">'+entries.map(x=>'<a class="btn" href="#/table?id='+x.id+'">'+escapeHTML(x.sheet.trim())+' · original formulas</a>').join('')+'</div>'}
function caemBoundary(){return '<p class="definition-note">'+(lang==='az'?'Nazirliyin CAEM modeli · son faktiki il 2024 · saxlanmış proqnozlar 2025–2029.':'Ministry CAEM · last historical boundary: 2024 · saved forecasts: 2025–2029.')+' The original workbook, selected source assumptions and saved calculation results are retained. Latest-official common-input recalculation requires approved owner-supplied inputs.</p>'}
function caemResultGrid(rows){const groups=new Map();for(const r of rows){const key=JSON.stringify([r.series_id,r.unit,r.source_sheet]);if(!groups.has(key))groups.set(key,{meta:r,years:new Map()});groups.get(key).years.set(Number(r.year),r)}return [...groups.values()]}
function mountCaemForecasts(rows,host,caption){const years=[2024,2025,2026,2027,2028,2029];const grid=caemResultGrid(rows);host.appendChild(new DataTable({rows:grid,columns:[{key:'indicator',label:'Indicator',sticky:true,wrap:true,get:r=>CAEM_INDICATOR_LABELS[r.meta.series_id]||r.meta.concept},{key:'unit',label:'Unit',get:r=>r.meta.unit,render:r=>escapeHTML(r.meta.unit+(r.meta.unit_scale_unresolved?' · scale requires confirmation':''))},...years.map(y=>({key:'y'+y,label:String(y),num:true,get:r=>r.years.get(y)?.value,render:r=>{const v=r.years.get(y);return v?escapeHTML(displayValue(v.value)):'<span class="unavail">—</span>'}})),{key:'source',label:'Source worksheet',wrap:true,get:r=>r.meta.source_sheet}],caption:caption+' · 2024 source history; 2025–2029 saved forecasts. Select a row for statuses and exact source records.',tall:false,onActivate:r=>{let h=recordDetail(r.meta);h+='<table class="data"><thead><tr><th>Year</th><th>Exact saved value</th><th>Observation status</th><th>Source cell</th></tr></thead><tbody>'+[...r.years.values()].map(v=>'<tr><td>'+v.year+'</td><td class="num">'+escapeHTML(displayValue(v.value,true))+'</td><td>'+escapeHTML(friendlyValue(v.data_status||v.status,'data_status'))+'</td><td>'+escapeHTML(v.source_cell)+'</td></tr>').join('')+'</tbody></table>';openDetail(r.meta.concept,h)}}).root)}
async function viewCaem(params,ticket){loadingView();const rows=await loadGroupRows('ministry_caem','baseline');if(!fresh(ticket))return;const canonical=rows.filter(r=>!r.series_id.startsWith('source:')&&r.series_id!=='gdp_nom_production_source');let h=head('CAEM · '+(lang==='az'?'Proqnoz icmalı':'Forecast overview'),'Comprehensive Adaptive Expectations Model · supplied Ministry of Economy system, developed with IMF technical assistance.');h+=caemBoundary();h+='<section class="panel"><h2>Key economic indicators</h2><div id="caem-summary-results"></div><a class="btn" href="#/caem-records">All saved CAEM output records →</a> <a class="btn" href="#/delivery?file=ministry_caem">CAEM baseline · HTML and CSV →</a></section><section class="panel"><h2>Sector accounts</h2><div class="caem-sectors">'+Object.entries(CAEM_SECTORS).map(([k,s])=>'<a class="sector-card" href="#/caem-'+k+'"><strong>'+escapeHTML(lang==='az'?s.az:s.en)+'</strong><span>'+escapeHTML(s.note)+'</span></a>').join('')+'</div></section><section class="panel"><h2>Methods, scenarios and checks</h2><div class="actions-row"><a class="btn" href="#/caem-scenarios">Saved scenarios</a><a class="btn" href="#/caem-methods">Structural methods and equations</a><a class="btn" href="#/caem-data">Original workbook data</a><a class="btn" href="#/caem-checks">Calculation consistency checks</a><a class="btn" href="#/differences">Differences across Ministry macro, CAEM, Oxlon and IMF</a></div></section>';view().innerHTML=h;mountCaemForecasts(canonical,$('#caem-summary-results'),'Saved CAEM summary')}
async function viewCaemSector(params,ticket){const key=parseHash().path.replace('caem-',''),s=CAEM_SECTORS[key];loadingView();const all=await loadGroupRows('ministry_caem','baseline');if(!fresh(ticket))return;const rows=all.filter(r=>s.sheets.includes(r.source_sheet)||s.series.includes(r.series_id));let h=head('CAEM · '+(lang==='az'?s.az:s.en),s.note);h+=caemBoundary();h+='<section class="panel"><h2>Saved model outputs</h2><div id="caem-sector-results"></div></section><section class="panel"><h2>Original sector worksheets and formulas</h2><p>Read the source formulas, saved evaluation status and separately retained cached values. Cached values and unexecuted cells are distinguished from evaluated baseline calculations.</p>'+caemSourceLinks(s.sheets)+'</section><section class="panel"><h2>Related material</h2><a class="btn" href="#/caem-methods">CAEM methods</a> <a class="btn" href="#/differences">Indicator definitions and comparison limits</a> <a class="btn" href="#/terminology">Terminology and column meanings</a></section>';view().innerHTML=h;if(rows.length)mountCaemForecasts(rows,$('#caem-sector-results'),s.en);else $('#caem-sector-results').innerHTML='<p>No separate normalized output series is available for this sector in the saved baseline. The original source worksheets remain available below.</p>'}
async function viewCaemScenarios(params,ticket){loadingView();const ids=['oil_plus10','partner_minus1','wages_plus10'],groups=catalogue.result_groups.filter(g=>g.model_id==='ministry_caem'&&ids.includes(g.scenario_id));const selected=groups.find(g=>g.scenario_id===params.get('case'));let h=head('CAEM · Saved scenarios','Recorded conditional calculations using the supplied Ministry CAEM model and its source controls.');h+=caemBoundary();h+='<section class="panel"><h2>Available conditional scenarios</h2><div id="caem-scenario-register"></div><p>Each scenario compares with the same saved CAEM baseline. Percentage price-level shocks and percentage-point growth shocks are different controls. These records are saved calculations with declared inputs and closure settings.</p></section><div id="caem-scenario-detail"></div>';view().innerHTML=h;$('#caem-scenario-register').appendChild(new DataTable({rows:groups,columns:[{key:'label',label:'Scenario and source control',wrap:true},{key:'row_count',label:'Saved output records',num:true},{key:'open',label:'Open',render:r=>'<a href="#/caem-scenarios?case='+r.scenario_id+'">Compare with baseline</a>'}],tall:false}).root);if(selected){const rows=await loadParts(selected.difference_parts||[]);if(!fresh(ticket))return;const host=$('#caem-scenario-detail');host.innerHTML='<section class="panel"><h2>'+escapeHTML(selected.label)+'</h2><div id="caem-scenario-values"></div></section>';if(selected.scenario_detail)host.firstChild.insertAdjacentHTML('afterbegin','<details><summary>Original scenario settings and source changes</summary>'+propsTable(selected.scenario_detail)+'</details>');$('#caem-scenario-values').appendChild(new DataTable({rows,columns:[{key:'concept',label:'Indicator',wrap:true},...evidenceColumns(['year','unit','baseline_value','value','difference','difference_unit','comparison_status'])],caption:'Exact saved scenario and same-engine baseline comparison',tall:false,onActivate:r=>openDetail(r.concept+' · '+r.year,recordDetail(r,RECORD_FIELDS.concat(['baseline_value','difference','difference_unit','comparison_status'])))}).root)}}
async function viewCaemData(params,ticket){let h=head('CAEM · Original workbook data','Source inputs, original formulas, summary worksheets and retained calculation records.');h+=caemBoundary();h+='<section class="panel"><h2>Original formula worksheets</h2><div id="caem-original-worksheets"></div></section><section class="panel"><h2>Complete original source cells · all worksheets</h2><p>These source inventories retain original literal cells and cached formula references. They are distinguished from executed model outputs.</p><div id="caem-source-cell-sheets"></div></section><section class="panel"><h2>Read data and source definitions</h2><div class="actions-row"><a class="btn" href="#/caem-records">All saved CAEM output records</a><a class="btn" href="#/delivery?file=caem-input">Blank input collection form</a><a class="btn" href="#/delivery?file=ministry_caem">Baseline CSV and HTML</a><a class="btn" href="#/caem-methods">Source methods and equations</a></div></section>';view().innerHTML=h;const rows=catalogue.tables.filter(x=>x.kind==='native'&&x.model_id==='ministry_caem');$('#caem-original-worksheets').appendChild(new DataTable({rows,columns:[{key:'sheet',label:'Original worksheet',wrap:true},{key:'row_count',label:'Source formula records',num:true},{key:'note',label:'Meaning of displayed values',wrap:true},{key:'open',label:'Open',render:r=>'<a href="#/table?id='+r.id+'">Read worksheet</a>'}],tall:false}).root);const sources=catalogue.tables.filter(x=>x.kind==='source-cells'&&x.model_id==='ministry_caem');$('#caem-source-cell-sheets').appendChild(new DataTable({rows:sources,columns:[{key:'sheet',label:'Original worksheet',wrap:true},{key:'row_count',label:'Original source cells',num:true},{key:'open',label:'Open',render:r=>'<a href="#/table?id='+r.id+'">Read all original cells</a>'}],tall:false}).root)}
async function viewCaemChecks(params,ticket){loadingView();const e=await methodEvidenceP(),table=catalogue.tables.find(x=>x.path==='results/caem/baseline/residuals.csv');const source=await loadTableRows(table);if(!fresh(ticket))return;const rows=source.map(r=>({year:r[0],gdp_difference:r[1],deflator_difference:r[2],tolerance:.001,check_result:Math.abs(Number(r[1]))<=.001&&Math.abs(Number(r[2]))<=.001?'Within recorded tolerance':'Requires review'}));const a=e.caem_nominal_account_check;view().innerHTML=head('CAEM · Calculation consistency checks','GDP-growth and deflator reconciliation, current-price account differences and source-data limits.')+caemBoundary()+'<section class="panel"><h2>Saved GDP-growth and deflator residuals</h2><p>A residual is the remaining difference in an accounting/reconciliation equation. The recorded tolerance is 0.001; these checks assess the saved solver equations and do not prove forecast accuracy or formal Ministry acceptance.</p><div id="caem-residual-checks"></div></section><section class="panel"><h2>Current-price GDP accounts require separate reconciliation</h2><p>For 2025, production-source GDP is '+escapeHTML(displayValue(a.production.value))+' million AZN; expenditure-framework GDP is '+escapeHTML(displayValue(a.expenditure.value))+' million AZN. Their retained difference is <strong>'+escapeHTML(displayValue(a.difference_mln_AZN))+' million AZN</strong>.</p><p>Passing the GDP-growth and deflator residual checks does not eliminate this nominal-account difference.</p><a class="btn" href="#/indicator-comparison?indicator=gdp_nominal_market&year=2025">Inspect definitions and exact sources →</a></section><section class="panel"><h2>Source limits</h2><p>CAEM’s last actual boundary is 2024 and its original forecast horizon ends in 2029. Source unit flags, unavailable values and regime selections remain part of the saved records. Approved dated owner inputs are required for a latest-official common-input comparison.</p><a class="btn" href="#/delivery?file=fr-coverage">Functional requirement output inventory</a> <a class="btn" href="#/terminology">What these terms mean</a></section>';$('#caem-residual-checks').appendChild(new DataTable({rows,columns:evidenceColumns(['year','gdp_difference','deflator_difference','tolerance','check_result']),tall:false}).root)}
async function viewCaemMethods(params,ticket){const p=new URLSearchParams(params);p.set('tab','caem');await viewEquations(p,ticket);if(!fresh(ticket))return;$('#view .tabs')?.remove();$('.view-head h1').textContent='CAEM · Methods and equations';$('.view-head .lede').textContent='Original structural equations and methodological expressions from the supplied Ministry CAEM documentation.';const doc=catalogue.documents.find(d=>d.path==='sources/caem/CAEM_documentation.docx');$('.view-head').insertAdjacentHTML('afterend','<div class="actions-row">'+(doc?'<a class="btn" href="#/document?id='+doc.id+'">Read the original CAEM technical document</a>':'')+'<a class="btn" href="#/caem-data">Original workbook formulas</a><a class="btn" href="#/terminology">Terminology</a></div>')}
function scopedForecasts(params,ticket,model,route,title){const p=new URLSearchParams(params);p.set('model',model);return viewForecasts(p,ticket,{route,title})}
async function viewTerminology(params,ticket){const entries=[['FR · Functional requirement','A required system function or output in the Ministry specification. FR1–FR12 are retained contractual references, not variable names or grades. “Requirement output inventory” counts the saved records mapped to them.'],['CAEM','Comprehensive Adaptive Expectations Model. The supplied Ministry model was developed with IMF technical assistance; Article IV staff projections are a separate published reference.'],['Ministry macro','The linked bottom-up Ministry workbook system, including source behavioural equations, branch accounts, product/company inputs, prices and taxes.'],['Oxlon','The independent modelling pipeline with recorded input histories, estimation specifications, forecast methods and backtests.'],['Baseline','A model’s recorded reference case before a specified scenario change. Different models can retain different baseline assumptions and source vintages.'],['Observed / historical','A saved source observation or historical input. Its source release and precision must be inspected before treating it as an authenticated official observation.'],['Expected / forecast','An expected value retained in a source workbook, or a saved model projection. Its issue date, information set and horizon matter for evaluation.'],['Derived / proxy','A value calculated from other records or used as a stand-in. It is distinguished from a separately observed statistical release.'],['Data vintage / snapshot','The dated information set or saved copy used in a calculation. A saved-copy timestamp is not an official statistical release date.'],['Source cells with formula errors','Spreadsheet cells with recorded errors such as #REF! (an invalid reference) or #DIV/0! (division by zero). This is different from a statistical forecast error.'],['Forecast error / backtest','A difference between a prediction and the corresponding observation, evaluated at a stated forecast origin and horizon. Comparing differently dated actual/expected/forecast records does not by itself establish a forecast-accuracy ranking.'],['Residual / consistency check','The remaining difference in an equation or accounting reconciliation. A numerical tolerance check assesses that saved calculation, not source-data completeness or contractual acceptance.'],['CP / YP','Original CAEM reconciliation selector labels. In the recorded solver, CP adjusts the named demand–supply wedge (WedgeSD), while YP adjusts named GDP growth; both reconcile the GDP deflator. The precise source controls remain available in the model documents.'],['% versus percentage points','A move from 4% to 5% is an increase of 1 percentage point. Increasing a price or amount by 10% is a proportional level change.'],['GDP / value added / deflator','Market-price GDP includes taxes less subsidies on products. Basic-price value added has a different perimeter. The implicit GDP deflator compares compatible nominal and volume GDP and differs from CPI.'],['CPI · Consumer Price Index','Annual-average inflation compares average index levels across years. December-on-December compares the two December index levels. These are separate series.'],['BoP · Balance of payments','Resident/nonresident goods, services, income and financial flows. BoP, national-account trade and customs merchandise statistics have distinct measurement rules.'],['GFCF · Gross fixed capital formation','Fixed-capital formation excludes inventory change. Statistical investment directed to fixed capital can have a different measurement perimeter.'],['NEER / REER','Nominal / real effective exchange-rate indices. They are weighted measures and are distinct from bilateral AZN/USD or AZN/EUR exchange rates.'],['HS chapter 27','The customs commodity chapter for mineral fuels, oils and related products. The source HS coverage must be retained when comparing product trade.'],['Scenario','A recorded conditional change to specified source inputs or policy controls. Saved sensitivity tests and declared scenarios are identified separately from baseline results.'],['Current-price / constant-price / % GDP','Current-price amounts, volume measures and ratios to GDP are different units. Match period, currency, scale and statistical perimeter before comparing them.']].map(([term,meaning])=>({term,meaning}));view().innerHTML=head('Terminology and column meanings','Plain explanations of requirement references, model names, data statuses and technical checks.')+'<section class="panel"><h2>Terms used in this website</h2><div id="terms-table"></div></section><section class="panel"><h2>Column headings</h2><div id="column-meanings"></div><p>Column headings use readable descriptions. Original field keys, source filenames and values remain available in source details and CSV exports.</p></section>';$('#terms-table').appendChild(new DataTable({rows:entries,columns:[{key:'term',label:'Term',sticky:true,wrap:true},{key:'meaning',label:'Meaning and interpretation',wrap:true}],tall:false}).root);$('#column-meanings').appendChild(new DataTable({rows:Object.entries(FIELD_LABELS).map(([key,label])=>({key,label})),columns:[{key:'label',label:'Displayed heading',wrap:true},{key:'key',label:'Original source field',wrap:true}],tall:false}).root)}

const VIEWS = {
  overview: viewOverview, forecasts: viewForecasts, ministry:(p,t)=>scopedForecasts(p,t,'ministry_macro','ministry','Ministry macro · Forecasts'),oxlon:(p,t)=>scopedForecasts(p,t,'oxlon.corrected.20260917','oxlon','Oxlon · Forecasts'),terminology:viewTerminology,caem:viewCaem,'caem-real':viewCaemSector,'caem-prices':viewCaemSector,'caem-fiscal':viewCaemSector,'caem-monetary':viewCaemSector,'caem-external':viewCaemSector,'caem-labour':viewCaemSector,'caem-scenarios':viewCaemScenarios,'caem-data':viewCaemData,'caem-checks':viewCaemChecks,'caem-methods':viewCaemMethods,'caem-records':(p,t)=>scopedForecasts(p,t,'ministry_caem','caem-records','CAEM · All forecast records'), scenarios: viewScenarios, models: viewModels,
  equations: viewEquations, workbook: viewWorkbook, library: viewLibrary, table: viewTable,
  methods: viewMethods, differences:viewDifferences, 'why-oxlon':viewWhyOxlon, 'oxlon-approach':viewOxlonApproach, 'oxlon-validation':viewOxlonValidation, 'indicator-comparison':viewIndicatorComparisons, 'cpi-explained':viewCpiExplained, 'accounting-requirements':viewAccountingRequirements, delivery:viewDelivery, document: viewDocument, notebook: viewNotebook, requirements: viewRequirements
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
