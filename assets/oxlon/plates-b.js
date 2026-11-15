/* Oxlon: generators for the plates built from public data (policy rates, inflation and unemployment, the VIX). */
(function () {
  'use strict';
  var OX = window.OX, U = OX.util, C = OX.C, kit = OX.kit;

  /* ---------------------------------------------------------------- II. Central banks */
  var PB = function () { return window.OXLON_POLICY; };
  var pX = function (tm, M) { return -0.97 + 1.94 * tm / (M - 1); };
  var pY = function (r) { var s = r / 57; return -0.56 + 1.16 * (s < 0 ? -Math.sqrt(-s) : Math.sqrt(s)); };
  var pZ = function (e, E) { return 0.55 - 1.10 * e / (E - 1); };
  var BIG = { US: 1, XM: 1, JP: 1, GB: 1 };
  var SHOW = { CH: 1, JP: 1, XM: 1, GB: 1, US: 1, AU: 1, IN: 1, TR: 1, BR: 1 };
  var policy = {
    id: 'policy-rates', numeral: 'II', field: 'Central Banks', title: 'Policy Rates of 28 Central Banks',
    credit: 'Data · Bank for International Settlements, central bank policy rates',
    alt: 'Ribbons for 28 central bank policy rates since 1990. They fall together in 2008 and 2020 and rise together in 2022.',
    view: { yaw: -0.58, pitch: 0.36, zoom: 0.88 }, exposure: 1.0,
    params: [{ k: 'date', sym: '<i>t</i>', label: 'month', type: 'month', min: 0, max: 441, value: 441, regen: false,
      fmt: function (v) { return U.monthLabel(PB().start, v); } }],
    eq: '<div class="eqgrid">' +
      '<span class="l"><i>r</i><sub><i>i</i>,<i>t</i></sub></span><span class="r">=</span><span class="x">policy rate of bank <i>i</i> at the end of month <span class="p" data-k="date"><i>t</i></span></span>' +
      '<span class="l">height</span><span class="r">=</span><span class="x">sign(<i>r</i>)&thinsp;√(|<i>r</i>|&thinsp;/&thinsp;57)<span class="eqnote">57% is the highest rate shown</span></span>' +
      '</div>',
    note: 'Each ribbon is one central bank\'s policy rate since 1990, ordered from the lowest average rate since 2010 at the front to the highest at the back. Twenty-seven of the 28 cut between August 2008 and June 2009. Twenty-three cut again in the first half of 2020. Between December 2021 and June 2023, 26 raised rates. Height follows the square root of the rate, which keeps the many rates near zero visible.',
    generate: function (N) {
      var D = PB(), E = D.codes.length, M = D.r[0].length, rand = U.rng(31), g = U.gaussian(rand);
      var spans = D.r.map(function (row) {
        var v = []; for (var m = 0; m < M - 1; m++) if (row[m] !== null && row[m + 1] !== null) v.push(m);
        return v;
      });
      var tot = spans.reduce(function (s, v) { return s + v.length; }, 0);
      var pos = new Float32Array(N * 3), warm = new Float32Array(N), i = 0;
      for (var e = 0; e < E; e++) {
        var row = D.r[e], sp = spans[e], z = pZ(e, E), w = BIG[D.codes[e]] ? 1 : 0.32;
        var cnt = e === E - 1 ? N - i : Math.min(N - i, Math.round(N * sp.length / tot));
        if (!sp.length) continue;
        for (var k = 0; k < cnt; k++) {
          var m0 = sp[Math.floor(rand() * sp.length)], f = rand(), v = row[m0] + (row[m0 + 1] - row[m0]) * f;
          var curtain = rand() < 0.34, y = pY(v);
          if (curtain) y = pY(0) + (y - pY(0)) * rand();
          pos[3 * i] = pX(m0 + f, M); pos[3 * i + 1] = y; pos[3 * i + 2] = z + g() * 0.005;
          warm[i] = curtain ? w * 0.4 : w; i++;
        }
      }
      return { pos: pos, warm: warm, meta: {} };
    },
    overlay: function (P) {
      var D = PB(), E = D.codes.length, M = D.r[0].length, out = kit.floorRing(kit.empty(), -0.80), yb = -0.70, zf = pZ(0, E) + 0.08;
      kit.axis(out, [pX(0, M), yb, zf], [pX(M - 1, M), yb, zf],
        kit.yearTicks(1990, 2026, function (y) { return ((y - 1990) * 12) / (M - 1); }, 1, 10), [0, 0, 0.03], {});
      var xl = pX(0, M) - 0.05, zb = pZ(E - 1, E) - 0.05;
      kit.axis(out, [xl, pY(0), zb], [xl, pY(57), zb], [0, 1, 5, 10, 20, 40].map(function (v) {
        return { f: (pY(v) - pY(0)) / (pY(57) - pY(0)), label: v + '%' };
      }), [-0.03, 0, 0], { title: 'Policy Rate', titleAt: [xl, pY(57) + 0.08, zb] });
      out.lines.push({ pts: [[pX(0, M), pY(0), zf - 0.02], [pX(M - 1, M), pY(0), zf - 0.02]], col: C.steelFaint, w: 1, dash: [0.02, 0.015] });
      var c = Math.round(P.date), sec = [];
      D.codes.forEach(function (code, e) {
        var v = D.r[e][c];
        if (v === null) return;
        var p = [pX(c, M), pY(v), pZ(e, E)];
        sec.push(p);
        out.points.push({ p: p, s: BIG[code] ? 7 : 4, col: BIG[code] ? C.pale : C.gold });
        var last = D.r[e][M - 1];
        if (SHOW[code] && last !== null) out.labels.push({ p: [pX(M - 1, M) + 0.04, pY(last), pZ(e, E)], t: D.names[e], cls: 'mark small left' });
      });
      if (sec.length > 1) out.lines.push({ pts: sec, col: C.pale, w: 1.3 });
      out.labels.push({ p: [pX(c, M), pY(Math.max.apply(null, D.r.map(function (r) { return r[c] === null ? 0 : Math.min(r[c], 30); }))) + 0.1, pZ(E - 1, E)], t: U.monthLabel(D.start, c), cls: 'cursor' });
      return out;
    },
    readout: function (P) {
      var D = PB(), c = Math.round(P.date), get = function (code) { var v = D.r[D.codes.indexOf(code)][c]; return v === null ? 'n/a' : v.toFixed(2); };
      var vals = D.r.map(function (r) { return r[c]; }).filter(function (v) { return v !== null; }).sort(function (a, b) { return a - b; });
      var med = vals.length ? (vals.length % 2 ? vals[(vals.length - 1) / 2] : (vals[vals.length / 2 - 1] + vals[vals.length / 2]) / 2) : NaN;
      return '<b>' + U.monthLabel(D.start, c) + '</b> · US ' + get('US') + ' · euro area ' + get('XM') + ' · UK ' + get('GB') + ' · Japan ' + get('JP') +
        '<br>median ' + med.toFixed(2) + '% across the ' + vals.length + ' banks reporting';
    }
  };

  /* ---------------------------------------------------------------- III. Macroeconomics */
  var MD = function () { return window.OXLON_USMACRO; };
  var MACRO_LAST = (function () {
    var D = window.OXLON_USMACRO, l = D.u.length - 1;
    while (l > 0 && (D.u[l] === null || D.pi[l] === null)) l--;
    return l;
  })();
  function solve(A, b) { // Gaussian elimination, A is n x n, b is n x k
    var n = A.length, k = b[0].length, M = A.map(function (r, i) { return r.concat(b[i]); }), i, j, c;
    for (i = 0; i < n; i++) {
      var p = i; for (j = i + 1; j < n; j++) if (Math.abs(M[j][i]) > Math.abs(M[p][i])) p = j;
      var t = M[i]; M[i] = M[p]; M[p] = t;
      for (j = i + 1; j < n; j++) { var f = M[j][i] / M[i][i]; for (c = i; c < n + k; c++) M[j][c] -= f * M[i][c]; }
    }
    var X = []; for (i = 0; i < n; i++) X.push(new Array(k).fill(0));
    for (c = 0; c < k; c++) for (i = n - 1; i >= 0; i--) {
      var s = M[i][n + c]; for (j = i + 1; j < n; j++) s -= M[i][j] * X[j][c]; X[i][c] = s / M[i][i];
    }
    return X;
  }
  function macroFrame() {
    var D = MD(), n = D.u.length, y0 = +D.start.slice(0, 4), m0 = +D.start.slice(5, 7) - 1;
    var idx = function (y, m) { return (y - y0) * 12 + (m - 1 - m0); };
    var last = n - 1; while (last > 0 && (D.u[last] === null || D.pi[last] === null)) last--;
    var i0 = idx(1960, 1), H = 60, SPLIT = 0.40;
    // History and the five-year fan get separate stretches of the time axis, with a marked break at the latest month.
    return { D: D, n: n, idx: idx, last: last, i0: i0, H: H, SPLIT: SPLIT,
      X: function (m) { return m <= last ? -0.97 + (SPLIT + 0.97) * (m - i0) / (last - i0) : SPLIT + (0.97 - SPLIT) * (m - last) / H; },
      Y: function (p) { return -0.56 + 1.12 * (p + 3) / 18; },
      Z: function (u) { return 0.55 - 1.10 * (u - 2) / 13; } };
  }
  function fitVAR(F) {
    var D = F.D, ok = function (t) { var y = D.u[t], p = D.pi[t]; return y !== null && p !== null && !(t >= F.idx(2020, 3) && t <= F.idx(2020, 12)); };
    var XtX = [], XtY = [], i, j, rows = [];
    for (i = 0; i < 5; i++) { XtX.push([0, 0, 0, 0, 0]); XtY.push([0, 0]); }
    for (var t = F.idx(1985, 1); t <= F.last; t++) {
      if (!ok(t) || !ok(t - 1) || !ok(t - 2)) continue;
      var x = [1, D.u[t - 1], D.pi[t - 1], D.u[t - 2], D.pi[t - 2]], y = [D.u[t], D.pi[t]];
      rows.push([x, y]);
      for (i = 0; i < 5; i++) { XtY[i][0] += x[i] * y[0]; XtY[i][1] += x[i] * y[1]; for (j = 0; j < 5; j++) XtX[i][j] += x[i] * x[j]; }
    }
    var B = solve(XtX, XtY), S = [[0, 0], [0, 0]];
    rows.forEach(function (r) {
      var e = [0, 1].map(function (c) { var s = 0; for (var q = 0; q < 5; q++) s += r[0][q] * B[q][c]; return r[1][c] - s; });
      S[0][0] += e[0] * e[0]; S[0][1] += e[0] * e[1]; S[1][1] += e[1] * e[1];
    });
    var dof = rows.length - 5; S[0][0] /= dof; S[0][1] /= dof; S[1][1] /= dof; S[1][0] = S[0][1];
    var l11 = Math.sqrt(S[0][0]), l21 = S[1][0] / l11, l22 = Math.sqrt(Math.max(1e-12, S[1][1] - l21 * l21));
    return { B: B, L: [l11, l21, l22], T: rows.length };
  }
  var macro = {
    id: 'inflation-unemployment', numeral: 'III', field: 'Macroeconomics', title: 'Inflation, Unemployment and Their Futures',
    credit: 'Data · US Bureau of Labor Statistics · VAR estimated in your browser',
    alt: 'The path of US unemployment and inflation since 1960 as a thread through time. It ends in a fan of simulated futures.',
    view: { yaw: -0.62, pitch: 0.30, zoom: 1.0 }, exposure: 0.55,
    params: [{ k: 'date', sym: '<i>t</i>', label: 'month', type: 'month', min: 132, max: MACRO_LAST, value: MACRO_LAST, regen: false,
      fmt: function (v) { return U.monthLabel(MD().start, v); } }],
    actions: [{ k: 'reseed', label: 'New futures' }],
    action: function (k, P, ctx) { if (k === 'reseed') ctx.setParam('seed', P.seed + 1, { now: true }); },
    eq: '<div class="eqgrid">' +
      '<span class="l"><i>z</i><sub><i>t</i></sub></span><span class="r">=</span><span class="x"><i>c</i> + <i>A</i><sub>1</sub><i>z</i><sub><i>t</i>&minus;1</sub> + <i>A</i><sub>2</sub><i>z</i><sub><i>t</i>&minus;2</sub> + <i>e</i><sub><i>t</i></sub>,&ensp;<i>e</i><sub><i>t</i></sub> ∼ N(0, Σ)</span>' +
      '<span class="l"><i>z</i><sub><i>t</i></sub></span><span class="r">=</span><span class="x">(<i>u</i><sub><i>t</i></sub>, <i>π</i><sub><i>t</i></sub>)′<span class="eqnote">unemployment rate, 12-month CPI inflation</span></span>' +
      '</div>',
    note: 'The bright thread is US unemployment and inflation month by month since 1960, with time running from left to right. It loops through the stagflation of the 1970s, the disinflation of the early 1980s, the 2020 jump in unemployment and the inflation of 2022. After the break on the time axis, a VAR estimated on data since 1985 draws a fan of futures for the next five years.',
    generate: function (N, P) {
      var F = macroFrame(), D = F.D, H = F.H, K = 90, rand = U.rng(500 + P.seed * 13), g = U.gaussian(rand);
      var pos = new Float32Array(N * 3), warm = new Float32Array(N), i = 0, t, k, m;
      var nHist = Math.floor(N * 0.22), Mp = Math.floor((N - nHist) / K);
      nHist = N - Mp * K;
      var pts = [];
      for (t = F.i0; t <= F.last; t++) if (D.u[t] !== null && D.pi[t] !== null) pts.push([t, D.u[t], D.pi[t]]);
      var span = pts[pts.length - 1][0] - pts[0][0], j = 0;
      for (k = 0; k < nHist; k++) {
        var tm = pts[0][0] + span * (k + rand()) / nHist;
        while (j < pts.length - 2 && pts[j + 1][0] < tm) j++;
        var a = pts[j], b = pts[j + 1], f = (tm - a[0]) / Math.max(1, b[0] - a[0]);
        pos[3 * i] = F.X(tm); pos[3 * i + 1] = F.Y(a[2] + (b[2] - a[2]) * f) + g() * 0.0032; pos[3 * i + 2] = F.Z(a[1] + (b[1] - a[1]) * f) + g() * 0.0032;
        warm[i] = 0.62; i++;
      }
      var V = fitVAR(F), B = V.B, L = V.L, paths = new Float32Array(Mp * (H + 1) * 2);
      var u1 = D.u[F.last], p1 = D.pi[F.last], u2 = D.u[F.last - 1], p2 = D.pi[F.last - 1];
      for (m = 0; m < Mp; m++) {
        var cu = u1, cp = p1, pu = u2, pp = p2, o = m * (H + 1) * 2;
        paths[o] = cu; paths[o + 1] = cp;
        for (t = 1; t <= H; t++) {
          var e1 = g(), e2 = g(), eu = L[0] * e1, ep = L[1] * e1 + L[2] * e2;
          var nu = B[0][0] + B[1][0] * cu + B[2][0] * cp + B[3][0] * pu + B[4][0] * pp + eu;
          var np = B[0][1] + B[1][1] * cu + B[2][1] * cp + B[3][1] * pu + B[4][1] * pp + ep;
          pu = cu; pp = cp; cu = nu; cp = np;
          paths[o + 2 * t] = cu; paths[o + 2 * t + 1] = cp;
        }
      }
      for (k = 0; k < K; k++) for (m = 0; m < Mp; m++) {
        var h = (k + rand()) * H / K, q = Math.min(H - 1, Math.floor(h)), ff = h - q, oo = m * (H + 1) * 2;
        var uu = paths[oo + 2 * q] + (paths[oo + 2 * q + 2] - paths[oo + 2 * q]) * ff;
        var pv = paths[oo + 2 * q + 1] + (paths[oo + 2 * q + 3] - paths[oo + 2 * q + 1]) * ff;
        pos[3 * i] = F.X(F.last + h); pos[3 * i + 1] = F.Y(U.clamp(pv, -3, 15)); pos[3 * i + 2] = F.Z(U.clamp(uu, 1, 16));
        warm[i] = 1 - h / H; i++;
      }
      var endU = [], endP = [];
      for (m = 0; m < Mp; m++) { endU.push(paths[m * (H + 1) * 2 + 2 * H]); endP.push(paths[m * (H + 1) * 2 + 2 * H + 1]); }
      endU.sort(function (x, y) { return x - y; }); endP.sort(function (x, y) { return x - y; });
      var pc = function (arr, q) { return arr[Math.min(arr.length - 1, Math.max(0, Math.round(q * (arr.length - 1))))]; };
      return { pos: pos, warm: warm, meta: { M: Mp, T: V.T, last: F.last,
        u5: pc(endU, 0.05), u95: pc(endU, 0.95), p5: pc(endP, 0.05), p95: pc(endP, 0.95) } };
    },
    overlay: function (P, meta) {
      var F = macroFrame(), D = F.D, out = kit.floorRing(kit.empty(), -0.80), yb = -0.64, zf = F.Z(2) + 0.06;
      kit.axis(out, [F.X(F.i0), yb, zf], [F.X(F.last), yb, zf],
        kit.yearTicks(1960, 2026, function (y) { return (F.idx(y, 1) - F.i0) / (F.last - F.i0); }, 5, 10), [0, 0, 0.03], {});
      kit.axis(out, [F.X(F.last), yb, zf], [F.X(F.last + F.H), yb, zf],
        [1, 2, 3, 4, 5].map(function (k) { return { f: k / 5, label: '+' + k + ' yr', major: true }; }), [0, 0, 0.03],
        { title: 'Simulated', titleAt: [F.X(F.last + F.H / 2), yb - 0.09, zf + 0.12] });
      out.lines.push({ pts: [[F.SPLIT, yb, zf], [F.SPLIT, F.Y(15), zf]], col: C.steelFaint, w: 1, dash: [0.014, 0.012] });
      var xl = F.X(F.i0) - 0.05;
      kit.axis(out, [xl, F.Y(0), F.Z(15) - 0.03], [xl, F.Y(15), F.Z(15) - 0.03], [0, 5, 10, 15].map(function (v) { return { f: v / 15, label: v + '%' }; }),
        [-0.03, 0, 0], { title: 'Inflation', titleAt: [xl, F.Y(16.3), F.Z(15) - 0.03] });
      kit.axis(out, [xl, yb, F.Z(2)], [xl, yb, F.Z(15)], [2, 5, 10, 15].map(function (v) { return { f: (v - 2) / 13, label: v + '%' }; }),
        [-0.03, 0, 0], { title: 'Unemployment', titleAt: [xl - 0.12, yb - 0.07, F.Z(8.5)] });
      [[1974, 12, '1974'], [1980, 3, '1980'], [1982, 11, '1982'], [2009, 10, '2009'], [2020, 4, '2020'], [2022, 6, '2022']].forEach(function (e) {
        var t = F.idx(e[0], e[1]), u = D.u[t], p = D.pi[t];
        if (u === null || p === null) return;
        var q = [F.X(t), F.Y(p), F.Z(u)];
        out.points.push({ p: q, s: 5, col: C.gold });
        out.labels.push({ p: [q[0], q[1] + 0.06, q[2]], t: e[2], cls: 'mark small' });
      });
      var lq = [F.X(F.last), F.Y(D.pi[F.last]), F.Z(D.u[F.last])];
      out.points.push({ p: lq, s: 9, col: C.pale });
      out.labels.push({ p: [lq[0], lq[1] + 0.08, lq[2]], t: U.monthLabel(D.start, F.last), cls: 'mark' });
      var c = Math.round(P.date), cu = D.u[c], cp = D.pi[c];
      if (c <= F.last && cu !== null && cp !== null) {
        var cq = [F.X(c), F.Y(cp), F.Z(cu)];
        out.points.push({ p: cq, s: 11, col: C.pale });
        out.lines.push({ pts: [cq, [cq[0], yb, cq[2]]], col: C.steelFaint, w: 1, dash: [0.012, 0.012] });
        out.labels.push({ p: [cq[0], cq[1] + 0.09, cq[2]], t: U.monthLabel(D.start, c), cls: 'cursor' });
      }
      return out;
    },
    readout: function (P, meta) {
      var D = MD(), c = Math.round(P.date), u = D.u[c], p = D.pi[c];
      var head = '<b>' + U.monthLabel(D.start, c) + '</b> · ' + (u === null || p === null ? 'no BLS estimate for this month' :
        'unemployment ' + u.toFixed(1) + '% · inflation ' + p.toFixed(1) + '%');
      if (!meta || meta.u5 === undefined) return head;
      return head + '<br>' + U.fmtInt(meta.M) + ' futures · in five years, 90% of them have unemployment ' + meta.u5.toFixed(1) + ' to ' + meta.u95.toFixed(1) +
        '% and inflation ' + meta.p5.toFixed(1) + ' to ' + meta.p95.toFixed(1) + '%';
    }
  };

  /* ---------------------------------------------------------------- IV. Market risk */
  var VX = function () { return window.OXLON_VIX; };
  var vixDays = null;
  function days() {
    if (vixDays) return vixDays;
    var d = VX().dd, out = new Int32Array(d.length), s = 0;
    for (var i = 0; i < d.length; i++) { s += d[i]; out[i] = s; }
    vixDays = out; return out;
  }
  function dayLabel(n) {
    var dt = new Date(Date.UTC(1990, 0, 1) + n * 86400000);
    return dt.getUTCDate() + ' ' + U.MONTHS[dt.getUTCMonth()] + ' ' + dt.getUTCFullYear();
  }
  function helix(day, v, dMax, out) {
    var a = 2 * Math.PI * day / 365.25, r = 0.10 + 0.80 * Math.sqrt(U.clamp((v - 9) / 74, 0, 1));
    out[0] = r * Math.cos(a); out[1] = -0.62 + 1.24 * day / dMax; out[2] = r * Math.sin(a);
    return out;
  }
  var vix = {
    id: 'volatility', numeral: 'IV', field: 'Market Risk', title: 'The VIX, Every Trading Day since 1990',
    credit: 'Data · Cboe Global Markets, VIX daily close',
    alt: 'A helix with one turn per year since 1990. It bulges outwards on days when the VIX was high.',
    view: { yaw: 0.3, pitch: 0.46, zoom: 1.0 }, exposure: 0.95,
    params: [{ k: 'day', sym: '<i>t</i>', label: 'trading day', type: 'int', min: 0, max: 9315, step: 1, value: 9315, regen: false,
      fmt: function (v) { return dayLabel(days()[Math.round(v)]); } }],
    eq: '<div class="eqgrid">' +
      '<span class="l"><i>θ</i></span><span class="r">=</span><span class="x">2π&thinsp;<span class="frac"><span>day</span><span>365.25</span></span><span class="eqnote">one turn per year</span></span>' +
      '<span class="l">radius</span><span class="r">=</span><span class="x">0.1 + 0.8&thinsp;√((VIX &minus; 9)&thinsp;/&thinsp;74)</span>' +
      '</div>',
    note: 'Every trading day since January 1990 sits on a coil that turns once a year and rises with time. The coil swells outwards when the VIX is high. The index measures the volatility that S&amp;P 500 options imply for the next thirty days. Its two highest closes came in November 2008 and in March 2020.',
    generate: function (N) {
      var D = VX(), dd = days(), n = D.c.length, dMax = dd[n - 1], rand = U.rng(19), g = U.gaussian(rand);
      var pos = new Float32Array(N * 3), warm = new Float32Array(N), q = [0, 0, 0];
      for (var i = 0; i < N; i++) {
        var s = (i + rand()) / N * (n - 1), j = Math.min(n - 2, Math.floor(s)), f = s - j;
        var day = dd[j] + (dd[j + 1] - dd[j]) * f, v = D.c[j] + (D.c[j + 1] - D.c[j]) * f;
        helix(day, v, dMax, q);
        pos[3 * i] = q[0] + g() * 0.0016; pos[3 * i + 1] = q[1] + g() * 0.0016; pos[3 * i + 2] = q[2] + g() * 0.0016;
        warm[i] = U.smoothstep(18, 42, v);
      }
      return { pos: pos, warm: warm, meta: {} };
    },
    overlay: function (P) {
      var D = VX(), dd = days(), n = D.c.length, dMax = dd[n - 1], out = kit.floorRing(kit.empty(), -0.80), q = [0, 0, 0];
      [20, 40, 80].forEach(function (v) {
        var r = 0.10 + 0.80 * Math.sqrt(U.clamp((v - 9) / 74, 0, 1));
        out.lines.push({ pts: kit.ring([0, -0.80, 0], r, 'y', 160), col: C.steelFaint, w: 1 });
        out.labels.push({ p: [r + 0.02, -0.78, 0.04], t: 'VIX ' + v, cls: 'tick' });
      });
      var ticks = [];
      for (var y = 1990; y <= 2026; y++) {
        var dy = (Date.UTC(y, 0, 1) - Date.UTC(1990, 0, 1)) / 86400000;
        ticks.push({ f: dy / dMax, label: y % 5 === 0 ? String(y) : '', major: y % 5 === 0 });
      }
      kit.axis(out, [1.02, -0.62, 0], [1.02, 0.62, 0], ticks, [0.03, 0, 0], {});
      // the largest spikes, at least a year apart
      var taken = [], idx = [];
      for (var i = 0; i < n; i++) idx.push(i);
      idx.sort(function (a, b) { return D.c[b] - D.c[a]; });
      for (var k = 0; k < idx.length && taken.length < 6; k++) {
        var ii = idx[k], far = taken.every(function (t) { return Math.abs(dd[t] - dd[ii]) > 365; });
        if (far) taken.push(ii);
      }
      taken.forEach(function (t) {
        helix(dd[t], D.c[t], dMax, q);
        out.points.push({ p: [q[0], q[1], q[2]], s: 6, col: C.gold });
        var dt = new Date(Date.UTC(1990, 0, 1) + dd[t] * 86400000);
        out.labels.push({ p: [q[0] * 1.08, q[1] + 0.04, q[2] * 1.08], t: U.MONTHS[dt.getUTCMonth()] + ' ' + dt.getUTCFullYear() + ' · ' + D.c[t].toFixed(1), cls: 'mark small' });
      });
      var c = Math.round(P.day);
      helix(dd[c], D.c[c], dMax, q);
      out.points.push({ p: [q[0], q[1], q[2]], s: 11, col: C.pale });
      out.lines.push({ pts: [[0, q[1], 0], [q[0], q[1], q[2]]], col: C.steel, w: 1, dash: [0.012, 0.01] });
      out.labels.push({ p: [q[0], q[1] + 0.07, q[2]], t: dayLabel(dd[c]), cls: 'cursor' });
      return out;
    },
    readout: function (P) {
      var D = VX(), dd = days(), c = Math.round(P.day);
      return '<b>' + dayLabel(dd[c]) + '</b> · VIX close ' + D.c[c].toFixed(2) +
        '<br>' + U.fmtInt(D.c.length) + ' trading days from ' + dayLabel(dd[0]) + ' to ' + dayLabel(dd[D.c.length - 1]);
    }
  };

  /* ---------------------------------------------------------------- shared plates */
  var yields = OX.makeYields({
    id: 'yield-curve', numeral: 'I', field: 'Bond Markets', title: 'The US Yield Curve, 1990 to 2026',
    credit: 'Data · US Treasury par yield curve, monthly averages of daily rates',
    alt: 'A surface of 442 monthly US Treasury yield curves from 1990 to 2026.',
    note: 'Every month since January 1990 is one thread, which runs from the three-month bill to the ten-year note. Its short end sinks to zero after 2008 and again in 2020. It folds wherever short rates sit above long ones, as in 2000, 2006, 2019 and from late 2022 to late 2024. Pick a month to see its curve and the Nelson and Siegel fit beside it.'
  });
  var scaling = OX.makeScaling({
    id: 'ai-economy', numeral: 'V', field: 'AI and the New Economy', title: 'A Production Function for Language Models',
    credit: 'Hoffmann et al. (2022) · re-estimated by Besiroglu et al. (2024)',
    alt: 'The fitted loss surface of language models over parameters and training tokens, with isoquants and an expansion path.'
  });

  OX.PLATES_B = [yields, policy, macro, vix, scaling];
})();
