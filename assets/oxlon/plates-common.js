/* Oxlon plates: drawing kit and the two shared plates
   (US Treasury yield curve and language-model scaling law). */
(function () {
  'use strict';
  var OX = (window.OX = window.OX || {});
  var U = OX.util, C = OX.C;

  /* ------------------------------------------------------------------ kit */
  var kit = {};
  kit.empty = function () { return { lines: [], points: [], labels: [] }; };
  kit.merge = function (a, b) {
    a.lines = a.lines.concat(b.lines || []); a.points = a.points.concat(b.points || []); a.labels = a.labels.concat(b.labels || []);
    return a;
  };
  // Graduated ring on the floor of the stage (precomputed unit circle for speed).
  var RING_PTS = (function () {
    var R = 1.24, pts = [], ticks = [], i;
    for (i = 0; i <= 144; i++) {
      var a = i / 144 * 2 * Math.PI;
      pts.push([R * Math.cos(a), R * Math.sin(a)]);
    }
    for (i = 0; i < 72; i++) {
      var b = i / 72 * 2 * Math.PI, l = i % 6 === 0 ? 0.055 : 0.024;
      ticks.push([R * Math.cos(b), R * Math.sin(b), (R + l) * Math.cos(b), (R + l) * Math.sin(b)]);
    }
    return { pts: pts, ticks: ticks };
  })();
  kit.floorRing = function (o, y) {
    var pts = RING_PTS.pts.map(function (p) { return [p[0], y, p[1]]; });
    o.lines.push({ pts: pts, col: C.steelFaint, w: 1 });
    for (var i = 0; i < RING_PTS.ticks.length; i++) {
      var t = RING_PTS.ticks[i];
      o.lines.push({ pts: [[t[0], y, t[1]], [t[2], y, t[3]]], col: C.steelFaint, w: 1 });
    }
    return o;
  };
  // A straight axis from a to b with ticks; ticks are {f: 0..1, label, major}.
  kit.axis = function (o, a, b, ticks, tickVec, opt) {
    opt = opt || {};
    o.lines.push({ pts: [a, b], col: opt.col || C.steel, w: 1 });
    (ticks || []).forEach(function (t) {
      var p = [a[0] + (b[0] - a[0]) * t.f, a[1] + (b[1] - a[1]) * t.f, a[2] + (b[2] - a[2]) * t.f];
      var s = t.major === false ? 0.45 : 1;
      o.lines.push({ pts: [p, [p[0] + tickVec[0] * s, p[1] + tickVec[1] * s, p[2] + tickVec[2] * s]], col: opt.col || C.steel, w: 1 });
      if (t.label !== undefined && t.label !== null && t.label !== '') {
        var lp = [p[0] + tickVec[0] * (opt.lab || 2.8), p[1] + tickVec[1] * (opt.lab || 2.8), p[2] + tickVec[2] * (opt.lab || 2.8)];
        o.labels.push({ p: lp, html: t.label, cls: 'tick ' + (opt.cls || '') });
      }
    });
    if (opt.title) o.labels.push({ p: opt.titleAt, html: opt.title, cls: 'axis-title ' + (opt.titleCls || '') });
    return o;
  };
  kit.ring = function (c, r, axis, n) {
    var pts = [], steps = n || 80;
    for (var i = 0; i <= steps; i++) {
      var a = i / steps * 2 * Math.PI, u = r * Math.cos(a), v = r * Math.sin(a);
      if (axis === 'x') pts.push([c[0], c[1] + u, c[2] + v]);
      else if (axis === 'y') pts.push([c[0] + u, c[1], c[2] + v]);
      else pts.push([c[0] + u, c[1] + v, c[2]]);
    }
    return pts;
  };
  kit.alongPolylines = function (polys, n, rand, out, offset, jitter, warm, wout) {
    var segs = [], tot = 0;
    polys.forEach(function (pl) {
      for (var i = 0; i < pl.pts.length - 1; i++) {
        var a = pl.pts[i], b = pl.pts[i + 1];
        var L = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
        if (L <= 0) continue;
        tot += L; segs.push({ a: a, b: b, c: tot, len: L, w: pl.w });
      }
    });
    if (!segs.length) {
      for (var q = 0; q < n; q++) {
        out[3 * (offset + q)] = 0; out[3 * (offset + q) + 1] = -0.5; out[3 * (offset + q) + 2] = 0; wout[offset + q] = 0;
      }
      return;
    }
    var g = U.gaussian(rand), k = 0;
    for (var j = 0; j < n; j++) {
      var s = (j + rand()) / n * tot;
      while (k < segs.length - 1 && segs[k].c < s) k++;
      var sg = segs[k], L0 = sg.c - sg.len;
      var f = (s - L0) / Math.max(1e-9, sg.len), o = 3 * (offset + j);
      out[o] = sg.a[0] + (sg.b[0] - sg.a[0]) * f + g() * jitter;
      out[o + 1] = sg.a[1] + (sg.b[1] - sg.a[1]) * f + g() * jitter;
      out[o + 2] = sg.a[2] + (sg.b[2] - sg.a[2]) * f + g() * jitter;
      wout[offset + j] = sg.w !== undefined ? sg.w : warm;
    }
  };
  kit.yearTicks = function (startYear, endYear, toF, every, labelEvery) {
    var t = [];
    for (var y = startYear; y <= endYear; y++) {
      if (y % every) continue;
      t.push({ f: toF(y), label: y % labelEvery === 0 ? String(y) : '', major: y % labelEvery === 0 });
    }
    return t;
  };
  OX.kit = kit;

  /* ------------------------------------------------------------------ yield curve */
  function nsFit(mats, ys) {
    var lam = 0.0609, A = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], b = [0, 0, 0];
    mats.forEach(function (m, i) {
      var t = m * 12, e = Math.exp(-lam * t), a = (1 - e) / (lam * t), x = [1, a, a - e];
      for (var r = 0; r < 3; r++) { b[r] += x[r] * ys[i]; for (var c = 0; c < 3; c++) A[r][c] += x[r] * x[c]; }
    });
    return solve3(A, b);
  }
  function solve3(A, b) {
    var M = A.map(function (r, i) { return r.concat([b[i]]); }), n = 3, i, j, k;
    for (i = 0; i < n; i++) {
      var p = i;
      for (j = i + 1; j < n; j++) if (Math.abs(M[j][i]) > Math.abs(M[p][i])) p = j;
      var t = M[i]; M[i] = M[p]; M[p] = t;
      for (j = i + 1; j < n; j++) { var f = M[j][i] / M[i][i]; for (k = i; k <= n; k++) M[j][k] -= f * M[i][k]; }
    }
    var x = [0, 0, 0];
    for (i = n - 1; i >= 0; i--) { var s = M[i][n]; for (j = i + 1; j < n; j++) s -= M[i][j] * x[j]; x[i] = s / M[i][i]; }
    return x;
  }
  function nsCurve(beta, m) {
    var lam = 0.0609, t = m * 12, e = Math.exp(-lam * t), a = (1 - e) / (lam * t);
    return beta[0] + beta[1] * a + beta[2] * (a - e);
  }
  OX.makeYields = function (o) {
    var D = function () { return window.OXLON_YIELDS; };
    var X = function (tm, M) { return -0.97 + 1.94 * tm / (M - 1); };
    var Y = function (y) { return -0.56 + 1.12 * y / 9; };
    var Z = function (u) { return 0.52 - 1.04 * u; };
    var cachedUs = null, cachedTicks = null;
    function us() {
      if (cachedUs) return cachedUs;
      var mats = D().maturities, l0 = Math.log(mats[0]), l1 = Math.log(mats[mats.length - 1]);
      cachedUs = mats.map(function (m) { return (Math.log(m) - l0) / (l1 - l0); });
      return cachedUs;
    }
    return {
      id: o.id || 'yields', numeral: o.numeral, field: o.field, title: o.title, credit: o.credit, note: o.note, alt: o.alt,
      view: { yaw: -0.52, pitch: 0.40, zoom: 1.02 }, exposure: 1.05,
      params: [{ k: 'date', sym: '<i>t</i>', label: 'Month', type: 'month', min: 0, max: D().y.length - 1, value: D().y.length - 1, regen: false,
        fmt: function (v) { return U.monthLabel(D().start, v); } }],
      eq: o.eq || OX.YIELDS_EQ,
      generate: function (N) {
        var d = D(), M = d.y.length, J = d.maturities.length, u = us();
        var fns = d.y.map(function (row) { return U.pchip(u, row); });
        var rand = U.rng(99), pos = new Float32Array(N * 3), warm = new Float32Array(N), i = 0;
        var Kc = Math.floor(N * 0.86 / M), m, k;
        for (m = 0; m < M; m++) {
          var row = d.y[m], w = 0.12 + 0.88 * U.smoothstep(0.25, -0.6, row[J - 1] - row[0]);
          for (k = 0; k < Kc; k++) {
            var uu = (k + rand()) / Kc, tm = U.clamp(m + (rand() - 0.5) * 0.7, 0, M - 1);
            pos[3 * i] = X(tm, M); pos[3 * i + 1] = Y(fns[m](uu)); pos[3 * i + 2] = Z(uu); warm[i] = w; i++;
          }
        }
        var left = N - i, per = Math.floor(left / J);
        for (var j = 0; j < J; j++) {
          var cnt = j === J - 1 ? N - i : per;
          for (k = 0; k < cnt; k++) {
            var t2 = rand() * (M - 1), m0 = Math.floor(t2), f = t2 - m0, m1 = Math.min(M - 1, m0 + 1);
            pos[3 * i] = X(t2, M); pos[3 * i + 1] = Y(d.y[m0][j] + (d.y[m1][j] - d.y[m0][j]) * f); pos[3 * i + 2] = Z(u[j]);
            warm[i] = 0.5; i++;
          }
        }
        return { pos: pos, warm: warm, meta: { M: M } };
      },
      overlay: function (P) {
        var d = D(), M = d.y.length, out = kit.floorRing(kit.empty(), -0.80), u = us(), y0 = +d.start.slice(0, 4);
        var yb = -0.62, zf = Z(0) + 0.07, xl = X(0, M) - 0.05, xr = X(M - 1, M) + 0.05;
        if (!cachedTicks) cachedTicks = kit.yearTicks(1990, 2026, function (y) { return ((y - y0) * 12) / (M - 1); }, 1, 10);
        kit.axis(out, [X(0, M), yb, zf], [X(M - 1, M), yb, zf], cachedTicks,
          [0, 0, 0.03], { title: 'Month', titleAt: [X(M - 1, M) + 0.02, yb, zf + 0.14], cls: 'below' });
        kit.axis(out, [xr, yb, Z(0)], [xr, yb, Z(1)],
          [0, 2, 3, 5, 7].map(function (j) { return { f: u[j], label: d.labels[j] }; }), [0.03, 0, 0],
          { title: 'Maturity', titleAt: [xr + 0.16, yb, Z(0.5)] });
        kit.axis(out, [xl, Y(0), Z(1) - 0.04], [xl, Y(9), Z(1) - 0.04],
          [0, 2, 4, 6, 8].map(function (v) { return { f: v / 9, label: v + '%' }; }), [-0.03, 0, 0],
          { title: 'Yield', titleAt: [xl - 0.02, Y(9.8), Z(1) - 0.04] });
        var c = Math.round(P.date), row = d.y[c], fn = U.pchip(u, row), beta = nsFit(d.maturities, row), pts = [], fit = [];
        var l0 = Math.log(d.maturities[0]), l1 = Math.log(d.maturities[d.maturities.length - 1]);
        for (var s = 0; s <= 48; s++) {
          var uu = s / 48, mat = Math.exp(l0 + (l1 - l0) * uu);
          pts.push([X(c, M), Y(fn(uu)), Z(uu)]);
          fit.push([X(c, M), Y(nsCurve(beta, mat)), Z(uu)]);
        }
        out.lines.push({ pts: pts, col: C.pale, w: 2 });
        out.lines.push({ pts: fit, col: C.steel, w: 1.3, dash: [0.018, 0.014] });
        out.lines.push({ pts: [[X(c, M), yb, Z(0)], [X(c, M), Y(row[0]), Z(0)]], col: C.steelFaint, w: 1, dash: [0.012, 0.012] });
        row.forEach(function (v, j) { out.points.push({ p: [X(c, M), Y(v), Z(u[j])], s: 5.5, col: C.pale }); });
        out.labels.push({ p: [X(c, M), Y(Math.max.apply(null, row)) + 0.08, Z(0)], t: U.monthLabel(d.start, c), cls: 'cursor' });
        return out;
      },
      readout: function (P) {
        var d = D(), c = Math.round(P.date), r = d.y[c], b = nsFit(d.maturities, r), sp = r[7] - r[0];
        return '<b>' + U.monthLabel(d.start, c) + '</b> · 3M ' + r[0].toFixed(2) + '% · 2Y ' + r[3].toFixed(2) + '% · 10Y ' + r[7].toFixed(2) +
          '% · 10Y&minus;3M ' + (sp >= 0 ? '+' : '&minus;') + Math.abs(sp).toFixed(2) + ' pp' +
          '<span class="ro-sep"></span>Fitted <i>β</i><sub>0</sub> ' + b[0].toFixed(2) + ' · <i>β</i><sub>1</sub> ' + fmtSigned(b[1]) + ' · <i>β</i><sub>2</sub> ' + fmtSigned(b[2]);
      }
    };
  };
  function fmtSigned(x) { return (x < 0 ? '&minus;' : '') + Math.abs(x).toFixed(2); }
  OX.fmtSigned = fmtSigned;

  /* ------------------------------------------------------------------ scaling law as a production function */
  var FITS = [
    { name: 'Hoffmann et al. (2022)', E: 1.69, A: 406.4, B: 410.7, a: 0.34, b: 0.28 },
    { name: 'Besiroglu et al. (2024)', E: 1.8172, A: 482.01, B: 2085.43, a: 0.3478, b: 0.3658 }
  ];
  var MODELS = [
    { name: 'GPT-3', N: 175e9, D: 300e9 },
    { name: 'Gopher', N: 280e9, D: 300e9 },
    { name: 'Chinchilla', N: 70e9, D: 1.4e12 }
  ];
  function loss(f, lgN, lgD) { return f.E + f.A / Math.pow(10, f.a * lgN) + f.B / Math.pow(10, f.b * lgD); }
  function optimum(f, Cb) {
    var G = Math.pow(f.a * f.A / (f.b * f.B), 1 / (f.a + f.b)), K = Cb / 6;
    var n = G * Math.pow(K, f.b / (f.a + f.b));
    return { N: n, D: K / n };
  }
  OX.SCALING_NOTE = 'Hoffmann and co-authors fitted the loss of more than 400 language models to their size <i>N</i> and their training data <i>D</i>. Read it as an economist would: the contours are isoquants, compute <i>C</i> ≈ 6<i>ND</i> is the budget line, and the highlighted curve is the expansion path where each budget line touches an isoquant. With the original estimates Chinchilla sits off that path; the 2024 re-estimate places it almost on the path, while GPT-3 and Gopher stay far away.';
  OX.makeScaling = function (o) {
    var X = function (lgN) { return -0.95 + 1.9 * (lgN - 7) / 5; };
    var Z = function (lgD) { return 0.60 - 1.2 * (lgD - 9) / 5; };
    var LO = Math.log(0.15), HI = Math.log(3.1);
    var Y = function (L) { return -0.56 + 1.12 * (Math.log(Math.max(L - 1.6, 1e-3)) - LO) / (HI - LO); };
    var P3 = function (lgN, lgD, f) { return [X(lgN), Y(loss(f, lgN, lgD)), Z(lgD)]; };
    function isoquants(f) {
      var levels = [1.9, 2.0, 2.1, 2.25, 2.4, 2.6, 2.85, 3.15, 3.55, 4.1], polys = [];
      levels.forEach(function (Lc) {
        var cur = [];
        for (var s = 0; s <= 240; s++) {
          var lgN = 7 + 5 * s / 240, rem = Lc - f.E - f.A / Math.pow(10, f.a * lgN);
          var ok = rem > 0, lgD = ok ? Math.log10(Math.pow(f.B / rem, 1 / f.b)) : 99;
          if (ok && lgD >= 9 && lgD <= 14) cur.push([X(lgN), Y(Lc), Z(lgD)]);
          else if (cur.length > 1) { polys.push({ pts: cur }); cur = []; } else cur = [];
        }
        if (cur.length > 1) polys.push({ pts: cur });
      });
      return polys;
    }
    function isocost(f, Cb, n) {
      var lgK = Math.log10(Cb / 6), a = Math.max(7, lgK - 14), b = Math.min(12, lgK - 9), pts = [];
      if (b <= a) return pts;
      var steps = n || 72;
      for (var s = 0; s <= steps; s++) { var lgN = a + (b - a) * s / steps; pts.push(P3(lgN, lgK - lgN, f)); }
      return pts;
    }
    function path(f) {
      var pts = [];
      for (var s = 0; s <= 200; s++) {
        var lgC = 17.0 + 10 * s / 200, op = optimum(f, Math.pow(10, lgC)), lgN = Math.log10(op.N), lgD = Math.log10(op.D);
        if (lgN >= 7 && lgN <= 12 && lgD >= 9 && lgD <= 14) pts.push(P3(lgN, lgD, f));
      }
      return pts;
    }
    return {
      id: o.id || 'scaling', numeral: o.numeral, field: o.field, title: o.title, credit: o.credit,
      note: o.note || OX.SCALING_NOTE, alt: o.alt, eq: o.eq,
      view: { yaw: -0.30, pitch: 0.86, zoom: 1.0 }, exposure: 0.9,
      params: [
        { k: 'fit', label: 'Estimates', type: 'choice', choices: ['Hoffmann 2022', 'Besiroglu 2024'], value: 0 },
        { k: 'C', sym: '<i>C</i>', label: 'Compute, FLOP', type: 'log', min: 1e18, max: 1e26, value: 5.76e23, step: 0.05, regen: false,
          fmt: function (v) { return U.sci(v, 1); } }
      ],
      generate: function (N, P) {
        var f = FITS[P.fit], rand = U.rng(5 + P.fit);
        var pos = new Float32Array(N * 3), warm = new Float32Array(N), i = 0;
        var nS = Math.floor(N * 0.50), gw = Math.ceil(Math.sqrt(nS)), r, c;
        for (var q = 0; q < nS; q++) {
          r = Math.floor(q / gw); c = q % gw;
          var lgN = 7 + 5 * (c + rand()) / gw, lgD = 9 + 5 * Math.min(1, (r + rand()) / Math.ceil(nS / gw));
          var p = P3(lgN, lgD, f);
          pos[3 * i] = p[0]; pos[3 * i + 1] = p[1]; pos[3 * i + 2] = p[2]; warm[i] = 0.12 + 0.4 * (0.56 - p[1]) / 1.12; i++;
        }
        var nQ = Math.floor(N * 0.28), nI = Math.floor(N * 0.12), nP = N - nS - nQ - nI;
        kit.alongPolylines(isoquants(f), nQ, rand, pos, i, 0.0016, 0.55, warm); i += nQ;
        var costs = [];
        for (var e = 18; e <= 26; e++) costs.push({ pts: isocost(f, Math.pow(10, e), 80), w: 0.3 });
        kit.alongPolylines(costs, nI, rand, pos, i, 0.0016, 0.3, warm); i += nI;
        kit.alongPolylines([{ pts: path(f), w: 1 }], nP, rand, pos, i, 0.0035, 1, warm);
        return { pos: pos, warm: warm, meta: {} };
      },
      overlay: function (P) {
        var f = FITS[P.fit], out = kit.floorRing(kit.empty(), -0.80), yb = -0.62;
        var nl = ['10M', '100M', '1B', '10B', '100B', '1T'], dl = ['1B', '10B', '100B', '1T', '10T', '100T'];
        kit.axis(out, [X(7), yb, Z(9) + 0.06], [X(12), yb, Z(9) + 0.06], nl.map(function (t, j) { return { f: j / 5, label: t }; }),
          [0, 0, 0.03], { title: 'Parameters <i>N</i>', titleAt: [X(9.5), yb - 0.12, Z(9) + 0.27] });
        kit.axis(out, [X(7) - 0.06, yb, Z(9)], [X(7) - 0.06, yb, Z(14)], dl.map(function (t, j) { return { f: j / 5, label: t }; }),
          [-0.03, 0, 0], { title: 'Tokens <i>D</i>', titleAt: [X(7) - 0.24, yb - 0.06, Z(11.5)] });
        kit.axis(out, [X(7) - 0.06, Y(1.8), Z(14) - 0.03], [X(7) - 0.06, Y(4.5), Z(14) - 0.03],
          [1.8, 2, 2.5, 3, 4, 4.5].map(function (v) { return { f: (Y(v) - Y(1.8)) / (Y(4.5) - Y(1.8)), label: String(v) }; }),
          [-0.03, 0, 0], { title: 'Loss <i>L</i>, Log Scale', titleAt: [X(7) - 0.06, Y(4.5) + 0.09, Z(14) - 0.03] });
        var cost = isocost(f, P.C, 100);
        if (cost.length) out.lines.push({ pts: cost, col: C.gold, w: 2 });
        var op = optimum(f, P.C), lgN = Math.log10(op.N), lgD = Math.log10(op.D);
        if (lgN >= 7 && lgN <= 12 && lgD >= 9 && lgD <= 14) {
          var p = P3(lgN, lgD, f);
          out.points.push({ p: p, s: 10, col: C.pale });
          out.labels.push({ p: [p[0], p[1] + 0.07, p[2]], html: 'Optimum', cls: 'cursor' });
        }
        MODELS.forEach(function (m) {
          var q = P3(Math.log10(m.N), Math.log10(m.D), f);
          out.points.push({ p: q, s: 7.5, col: C.claret });
          out.lines.push({ pts: [q, [q[0], yb, q[2]]], col: C.steelFaint, w: 1, dash: [0.012, 0.012] });
          var dy = m.name === 'GPT-3' ? -0.055 : (m.name === 'Gopher' ? 0.065 : 0.05);
          var dx = m.name === 'GPT-3' ? -0.04 : 0.04;
          out.labels.push({ p: [q[0] + dx, q[1] + dy, q[2]], t: m.name, cls: 'mark' });
        });
        return out;
      },
      readout: function (P) {
        var f = FITS[P.fit], op = optimum(f, P.C), L = loss(f, Math.log10(op.N), Math.log10(op.D));
        return '<b>' + U.sci(P.C, 1) + ' FLOP</b> · ' + f.name + '<span class="ro-sep"></span>Optimum <i>N</i>* ' + U.big(op.N) +
          ' parameters · <i>D</i>* ' + U.big(op.D) + ' tokens · ' + (op.D / op.N).toFixed(0) + ' tok/param · <i>L</i> ' + L.toFixed(3);
      }
    };
  };
  OX.FITS = FITS;
})();
