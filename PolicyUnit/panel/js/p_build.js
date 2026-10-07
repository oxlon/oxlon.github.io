/* p_build.js — Ssenari qurucusu, part 1 (NFR4): the draft scenario (config/scenarios JSON format), instrument rows with
   catalogue bounds, target and financing choices, client-side validation with Azerbaijani messages and the offline
   approximate preview (linear scaling of the bundled single-instrument scenarios — clearly labelled). */
(function () {
  'use strict';
  var U = window.U;
  var LAST = 2035, KEY = 'policyPanel.draft';
  U.FR12 = [['CEM', 'Sement'], ['MOB', 'Mobil rabitə'], ['BNK', 'Bank sektoru'], ['ICT', 'İnformasiya və rabitə'], ['AGR', 'Kənd təsərrüfatı'], ['IND', 'Sənaye'], ['CON', 'Tikinti'], ['TRD', 'Ticarət'], ['TRA', 'Nəqliyyat'], ['ACC', 'Yerləşdirmə və iaşə'], ['REA', 'Daşınmaz əmlak'], ['EDU', 'Təhsil'], ['HEA', 'Səhiyyə'], ['OTH', 'Digər sahələr']];
  U.FR1G = [['man', 'Emal sənayesi'], ['agr', 'Kənd təsərrüfatı'], ['con', 'Tikinti'], ['trd', 'Ticarət'], ['tra', 'Nəqliyyat'], ['ict', 'İnformasiya və rabitə'], ['tou', 'Turizm (yerləşdirmə və iaşə)'], ['elc', 'Elektrik enerjisi'], ['wat', 'Su təchizatı'], ['min', 'Mədənçıxarma'], ['oth', 'Digər xidmətlər']];
  U.CONS = [['food', 'Ərzaq'], ['alc', 'Spirtli içkilər'], ['tobacco', 'Tütün'], ['clothing', 'Geyim və ayaqqabı'], ['housing', 'Mənzil və kommunal'], ['furnish', 'Ev əşyaları'], ['health', 'Səhiyyə'], ['transport', 'Nəqliyyat'], ['comm', 'Rabitə'], ['recreation', 'İstirahət'], ['education', 'Təhsil'], ['restaurants', 'İaşə'], ['misc', 'Digər']];
  U.FR4S = [['agr', 'Kənd təsərrüfatı'], ['mining', 'Mədənçıxarma'], ['manuf', 'Emal sənayesi'], ['elec', 'Elektrik enerjisi'], ['water', 'Su təchizatı'], ['constr', 'Tikinti'], ['trade', 'Ticarət'], ['transp', 'Nəqliyyat'], ['hotel', 'Yerləşdirmə və iaşə'], ['ict', 'İnformasiya və rabitə'], ['fin', 'Maliyyə'], ['realest', 'Daşınmaz əmlak'], ['prof', 'Peşə fəaliyyəti'], ['admsup', 'İnzibati xidmətlər'], ['pubadm', 'Dövlət idarəetməsi'], ['educ', 'Təhsil'], ['health', 'Səhiyyə'], ['art', 'İncəsənət'], ['othsvc', 'Digər xidmətlər']];
  /* target choices of an instrument: [list, label, required] */
  U.targets = function (m) {
    if (!m) return null;
    var io = U.T('cfg_io_sectors').map(function (r) { return [r.code, r.name_az]; });
    if (m.id === 'market_entry') return [U.FR12, 'FR12 bazarı', true];
    if (m.id === 'consumer_price') return [U.CONS, 'İstehlak kateqoriyası', true];
    if (m.id === 'sector_jobs') return [U.FR4S, 'FR4 bölməsi', true];
    if (m.id === 'export_subsidy') return [U.FR1G.concat(io), 'Hədəf sektor', false];
    if (/target|hədəf sektor/i.test(m.description_az || '') && /io/.test(m.engines)) return [io, 'IO sektoru', false];
    return null;
  };
  U.needsFin = function (m) { return m && m.cost_rule && m.cost_rule !== 'none'; };
  function blank() { return { id: '', name_az: '', description_az: '', start_year: 2027, instruments: [], tags: [] }; }
  var B = U.BLD = { s: blank(), res: null, val: null, busy: false };
  try { var st = JSON.parse(U.ls(KEY) || 'null'); if (st && st.instruments) B.s = st; } catch (e) { /* ignore */ }
  /* scenario code (file name / identifier): generated from instruments + sizes + start year, unique; editable only on request */
  U.sizeTok = function (x) { if (!U.isNum(x)) return 'x'; var a = Math.round(Math.abs(x) * 100) / 100; return (x < 0 ? 'm' : '') + String(a).replace('.', 'p'); };
  B.srvIds = {};
  U.takenIds = function () { var o = {}; U.scens().forEach(function (x) { o[x.id] = 1; }); try { JSON.parse(U.ls('policyPanel.saved') || '[]').forEach(function (x) { o[x.id] = 1; }); } catch (e) { /* ignore */ } Object.keys(B.srvIds).forEach(function (k) { o[k] = 1; }); if (B.s && B.s._saved) delete o[B.s._saved]; return o; };
  U.autoId = function (s) {
    var L = s.instruments, base = L.length ? L.slice(0, 2).map(function (it) { return it.instrument + '_' + U.sizeTok(it.size); }).join('_') + (L.length > 2 ? '_va_' + (L.length - 2) : '') : 'yeni_ssenari';
    base = (base + '_' + s.start_year).replace(/[^a-z0-9_]/g, '_').slice(0, 64);
    var t = U.takenIds(), id = base, k = 2; while (t[id]) id = base + '_' + k++; return id;
  };
  U.autoName = function (s) {
    return s.instruments.length ? s.instruments.map(function (it) { var m = U.instr(it.instrument) || {}; return (m.name_az || it.instrument) + ' ' + U.sg(it.size, 2) + ' ' + ({ pct: '%', pp: 'f.b.', mln_azn: 'mln AZN/il', abs: '' }[it.unit] || ''); }).join(' + ') + ' (' + s.start_year + '-dən)' : '';
  };
  U.bSync = function () { var s = B.s; if (!s.idManual) s.id = U.autoId(s); if (!s.nameManual) s.name_az = U.autoName(s); };
  U.bSave = function () { U.bSync(); U.ls(KEY, JSON.stringify(B.s)); };
  U.bReset = function () { B.s = blank(); B.res = null; B.val = null; U.bSave(); };
  U.bLoad = function (sc, copy) {
    var o = JSON.parse(JSON.stringify(sc));
    B.s = { id: o.id, idManual: !copy, nameManual: true, _saved: copy ? null : o.id, name_az: (o.name_az || o.name || '') + (copy ? ' (surət)' : ''), description_az: o.description_az || o.desc || '', start_year: o.start_year || o.start || 2027, instruments: o.instruments || o.ins || [], tags: o.tags || [] };
    B.res = null; B.val = null; U.bSave();
  };
  U.bAdd = function (id) {
    var m = U.instr(id); if (!m) return;
    var y0 = +B.s.start_year || 2027, t = U.targets(m);
    B.s.instruments.push({ instrument: id, years: [y0, y0 + 1, y0 + 2, y0 + 3].filter(function (y) { return y <= LAST; }), size: m.default_size, unit: m.unit, target: t && t[2] ? t[0][0][0] : null, financing: U.needsFin(m) ? 'deficit' : null });
    B.res = null; B.val = null; U.bSave();
  };
  U.slug = function (s) { return U.fold(s || '').replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 40); };
  /* client-side validation (same rules as policyunit.scenario; the server repeats them) */
  U.bCheck = function (s) {
    var e = [], w = [];
    if (s.idManual && !/^[a-z0-9_]+$/.test(s.id || '')) e.push('Ssenarinin kodu (id) yalnız kiçik latın hərfləri, rəqəm və «_» ola bilər (məs. ' + (U.slug(s.name_az) || 'vat_minus2') + ').');
    if (!String(s.name_az || '').trim()) e.push('Ssenarinin adı boşdur.');
    if (!(s.start_year >= 2026 && s.start_year <= 2030)) e.push('Başlanğıc il 2026–2030 aralığında olmalıdır.');
    if (!s.instruments.length) e.push('Ən azı bir siyasət aləti əlavə edin.');
    s.instruments.forEach(function (it, i) {
      var m = U.instr(it.instrument), n = 'alət #' + (i + 1) + ' (' + (m ? m.name_az : it.instrument) + ')';
      if (!m) { e.push(n + ': kataloqda belə alət yoxdur.'); return; }
      if (!U.isNum(it.size)) e.push(n + ': ölçü rəqəm olmalıdır.');
      else if (it.size < m.min || it.size > m.max) e.push(n + ': ölçü ' + U.nf(it.size) + ' icazə verilən [' + U.nf(m.min) + '; ' + U.nf(m.max) + '] intervalından kənardır.');
      else if (it.size === 0) w.push(n + ': ölçü sıfırdır — təsir olmayacaq.');
      var ys = it.years === 'all' ? null : it.years || [];
      if (ys && !ys.length) e.push(n + ': ən azı bir il seçin.');
      if (ys && ys.some(function (y) { return y < s.start_year || y > LAST; })) e.push(n + ': illər ' + s.start_year + '–' + LAST + ' aralığında olmalıdır.');
      var t = U.targets(m); if (t && t[2] && !it.target) e.push(n + ': ' + t[1].toLowerCase() + ' seçilməlidir.');
      if (U.needsFin(m) && !it.financing) w.push(n + ': maliyyələşmə göstərilməyib — standart olaraq borc (kəsir) hesab olunur.');
      if (ys && ys.some(function (y) { return y > 2030; }) && /micro/.test(m.engines)) w.push(n + ': 2030-dan sonrakı illər yalnız uzun müddət ekstrapolyasiyasında nəzərə alınır (MikroUnit 2030-da bitir).');
    });
    if (s.idManual && s.id !== s._saved && U.scens().some(function (x) { return x.id === s.id && x.src === 'rəsmi'; })) w.push('Bu kodla rəsmi ssenari artıq var — saxlanarkən yeni kod verin və ya «Surət» istifadə edin.');
    return { errors: e, warnings: w, valid: !e.length };
  };
  U.bEngines = function (s) { var o = {}; s.instruments.forEach(function (it) { var m = U.instr(it.instrument); if (m) U.ids(m.engines).forEach(function (x) { o[x] = 1; }); }); return Object.keys(o); };
  /* offline approximate preview: for each instrument a bundled official scenario with only that instrument → scale linearly */
  U.bApprox = function (s) {
    var parts = [], miss = [];
    s.instruments.forEach(function (it) {
      var ref = U.official().filter(function (x) { return x.ins.length === 1 && x.ins[0].instrument === it.instrument && U.isNum(x.ins[0].size) && x.ins[0].size !== 0; })[0];
      if (ref) parts.push({ ref: ref, k: it.size / ref.ins[0].size, it: it }); else miss.push(it.instrument);
    });
    var rows = {};
    parts.forEach(function (p) {
      U.hl(p.ref.id).forEach(function (r) {
        var key = r.indicator + '|' + r.horizon, o = rows[key] = rows[key] || { indicator: r.indicator, label_az: r.label_az, horizon: r.horizon, effect: 0, effect_unit: r.effect_unit, refs: [] };
        if (U.isNum(r.effect)) o.effect += r.effect * p.k; o.refs.push(p.ref.id);
      });
    });
    return { parts: parts, miss: miss, rows: Object.keys(rows).sort().map(function (k) { return rows[k]; }) };
  };
})();
