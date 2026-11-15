/* Oxlon, version A: seven plates, one for each field of work. */
(function () {
  'use strict';
  var OX = window.OX, U = OX.util, C = OX.C, kit = OX.kit;

  /* ---------------------------------------------------------------- I. Forecasting */
  var forecast = {
    id: 'forecasting', numeral: 'I', field: 'Forecasting', title: 'A Fan of Futures',
    credit: 'Vector autoregression · simulated in your browser',
    alt: 'Simulated paths for inflation and the output gap fan out over ten years from one starting point.',
    view: { yaw: -0.62, pitch: 0.30, zoom: 1.0 }, exposure: 1.0,
    params: [
      { k: 'rho', sym: '<i>ρ</i>', label: 'persistence', min: 0.5, max: 0.99, step: 0.01, value: 0.93, dec: 2 },
      { k: 'theta', sym: '<i>θ</i>', label: 'rotation per quarter', min: 0, max: 0.6, step: 0.01, value: 0.22, dec: 2 },
      { k: 'sigma', sym: '<i>σ</i>', label: 'shock size', min: 0.05, max: 0.8, step: 0.01, value: 0.35, dec: 2 }
    ],
    actions: [{ k: 'reseed', label: 'New shocks' }],
    action: function (k, P, ctx) { if (k === 'reseed') ctx.setParam('seed', P.seed + 1, { now: true }); },
    eq: '<div class="eqgrid">' +
      '<span class="l"><i>z</i><sub><i>t</i>+1</sub></span><span class="r">=</span><span class="x"><i>A</i> <i>z</i><sub><i>t</i></sub> + <span class="p" data-k="sigma"><i>σ</i></span> <i>ε</i><sub><i>t</i>+1</sub>,&ensp;<i>ε</i> ∼ N(0, <i>I</i>)</span>' +
      '<span class="l"><i>A</i></span><span class="r">=</span><span class="x"><span class="p" data-k="rho"><i>ρ</i></span>&thinsp;<span class="mat"><span>cos <span class="p" data-k="theta"><i>θ</i></span></span><span>&minus;sin <span class="p" data-k="theta"><i>θ</i></span></span><span>sin <span class="p" data-k="theta"><i>θ</i></span></span><span>cos <span class="p" data-k="theta"><i>θ</i></span></span></span></span>' +
      '<span class="l"><i>z</i><sub><i>t</i></sub></span><span class="r">=</span><span class="x">(<i>π</i><sub><i>t</i></sub>, <i>y</i><sub><i>t</i></sub>)′<span class="eqnote">inflation gap, output gap</span></span>' +
      '</div>',
    note: 'Each thread is one possible future for inflation and the output gap over ten years, drawn from the same model and the same starting point. Persistence <i>ρ</i> sets how slowly the economy returns to target, while the rotation <i>θ</i> makes the two circle each other on the way. Rings enclose nine futures in ten. That spread, more than the central line, is the forecast.',
    generate: function (N, P) {
      var H = 40, K = 100, rand = U.rng(1000 + P.seed * 7919), g = U.gaussian(rand);
      var M = Math.floor(N * 0.965 / K), nMean = N - M * K;
      var rho = P.rho, th = P.theta, sg = P.sigma, c = Math.cos(th), s = Math.sin(th);
      var a11 = rho * c, a12 = -rho * s, a21 = rho * s, a22 = rho * c, z0 = [2.2, -1.6];
      var sd = sg / Math.sqrt(Math.max(1e-6, 1 - rho * rho));
      var S = Math.min(0.17, 0.58 / Math.max(2.7, 2.6 * sd));
      var paths = new Float32Array(M * (H + 1) * 2), m, q;
      for (m = 0; m < M; m++) {
        var x = z0[0], y = z0[1], o = m * (H + 1) * 2;
        paths[o] = x; paths[o + 1] = y;
        for (q = 1; q <= H; q++) {
          var nx = a11 * x + a12 * y + sg * g(), ny = a21 * x + a22 * y + sg * g();
          x = nx; y = ny; paths[o + 2 * q] = x; paths[o + 2 * q + 1] = y;
        }
      }
      var pos = new Float32Array(N * 3), warm = new Float32Array(N), i = 0;
      var X = function (t) { return -0.95 + 1.9 * t / H; };
      for (var k = 0; k < K; k++) {
        for (m = 0; m < M; m++) {
          var t = (k + rand()) * H / K, qq = Math.min(H - 1, Math.floor(t)), f = t - qq, b = m * (H + 1) * 2;
          var q0 = Math.max(0, qq - 1), q2 = qq + 1, q3 = Math.min(H, qq + 2), f2 = f * f, f3 = f2 * f;
          for (var d = 0; d < 2; d++) {
            var p0 = paths[b + 2 * q0 + d], p1 = paths[b + 2 * qq + d], p2 = paths[b + 2 * q2 + d], p3 = paths[b + 2 * q3 + d];
            var v = 0.5 * (2 * p1 + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f2 + (-p0 + 3 * p1 - 3 * p2 + p3) * f3);
            pos[3 * i + 1 + d] = v * S;
          }
          pos[3 * i] = X(t); warm[i] = 1 - t / H; i++;
        }
      }
      for (var j = 0; j < nMean; j++) {
        var tt = (j + rand()) * H / nMean, r = Math.pow(rho, tt), ct = Math.cos(th * tt), st = Math.sin(th * tt);
        pos[3 * i] = X(tt);
        pos[3 * i + 1] = r * (ct * z0[0] - st * z0[1]) * S + g() * 0.002;
        pos[3 * i + 2] = r * (st * z0[0] + ct * z0[1]) * S + g() * 0.002;
        warm[i] = 1; i++;
      }
      return { pos: pos, warm: warm, meta: { S: S, M: M, H: H, z0: z0 } };
    },
    overlay: function (P, meta) {
      if (!meta || !meta.S) return null;
      var out = kit.floorRing(kit.empty(), -0.80), S = meta.S, H = 40, z0 = meta.z0;
      var X = function (t) { return -0.95 + 1.9 * t / H; }, yb = -0.64, zf = 0.62;
      kit.axis(out, [X(0), yb, zf], [X(40), yb, zf],
        [0, 8, 16, 24, 32, 40].map(function (q, j) { return { f: q / 40, label: j ? j * 2 + ' yr' : 'now' }; }),
        [0, 0, 0.03], { title: 'horizon', titleAt: [X(20), yb - 0.1, zf + 0.12] });
      var stepv = [0.5, 1, 2, 5][[0.5, 1, 2, 5].map(function (v) { return v * S >= 0.12; }).indexOf(true)] || 5, ticks = [];
      for (var v = -Math.floor(0.55 / S / stepv) * stepv; v <= 0.55 / S + 1e-9; v += stepv) ticks.push(v);
      var xa = X(0) - 0.07;
      kit.axis(out, [xa, ticks[0] * S, 0], [xa, ticks[ticks.length - 1] * S, 0],
        ticks.map(function (v) { return { f: (v - ticks[0]) / (ticks[ticks.length - 1] - ticks[0]), label: (v > 0 ? '+' : v < 0 ? '&minus;' : '') + Math.abs(v) }; }),
        [-0.03, 0, 0], { title: 'inflation gap, pp', titleAt: [xa - 0.02, ticks[ticks.length - 1] * S + 0.09, 0] });
      kit.axis(out, [xa, yb, ticks[0] * S], [xa, yb, ticks[ticks.length - 1] * S],
        ticks.map(function (v) { return { f: (v - ticks[0]) / (ticks[ticks.length - 1] - ticks[0]), label: (v > 0 ? '+' : v < 0 ? '&minus;' : '') + Math.abs(v), major: true }; }),
        [-0.03, 0, 0], { title: 'output gap, pp', titleAt: [xa - 0.1, yb - 0.08, ticks[0] * S - 0.1] });
      out.lines.push({ pts: [[X(0), 0, 0], [X(40), 0, 0]], col: C.steel, w: 1, dash: [0.02, 0.016] });
      out.labels.push({ p: [X(40) + 0.06, 0, 0], t: 'target', cls: 'mark' });
      var rho = P.rho, th = P.theta;
      [8, 20, 40].forEach(function (h) {
        var r = Math.pow(rho, h), ct = Math.cos(th * h), st = Math.sin(th * h);
        var cy = r * (ct * z0[0] - st * z0[1]) * S, cz = r * (st * z0[0] + ct * z0[1]) * S;
        var rad = 1.645 * P.sigma * Math.sqrt((1 - Math.pow(rho, 2 * h)) / (1 - rho * rho)) * S;
        out.lines.push({ pts: kit.ring([X(h), cy, cz], rad, 'x', 120), col: C.pale, w: 1.2 });
        if (h === 40) out.labels.push({ p: [X(h), cy + rad + 0.06, cz], t: '90%', cls: 'mark' });
      });
      return out;
    },
    readout: function (P, meta) {
      if (!meta || !meta.M) return '';
      var r90 = 1.645 * P.sigma * Math.sqrt((1 - Math.pow(P.rho, 80)) / (1 - P.rho * P.rho));
      return '<b>' + U.fmtInt(meta.M || 0) + ' futures</b> over 40 quarters<br>half life ' + (Math.log(0.5) / Math.log(P.rho)).toFixed(1) +
        ' quarters<br>90% ring at ten years, radius ' + r90.toFixed(2) + ' pp';
    }
  };

  /* ---------------------------------------------------------------- II. Machine learning */
  var T0 = 1.5 * Math.PI, T1 = 4.5 * Math.PI, TN = 2048;
  function arcLen(t) { return 0.5 * (t * Math.sqrt(1 + t * t) + Math.asinh(t)); }
  function rollTable(lam) {
    var xs = new Float64Array(TN), ys = new Float64Array(TN), dt = (T1 - T0) / (TN - 1), j;
    var phi0 = T0 + Math.atan(T0), px = T0 * Math.cos(T0), py = T0 * Math.sin(T0);
    xs[0] = px; ys[0] = py;
    for (j = 1; j < TN; j++) {
      var tm = T0 + (j - 0.5) * dt, phi = phi0 + (1 - lam) * (tm + Math.atan(tm) - phi0), ds = Math.sqrt(1 + tm * tm) * dt;
      px += Math.cos(phi) * ds; py += Math.sin(phi) * ds; xs[j] = px; ys[j] = py;
    }
    var c = Math.cos(-phi0), s = Math.sin(-phi0), x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (j = 0; j < TN; j++) {
      var X = xs[j] * c - ys[j] * s, Y = xs[j] * s + ys[j] * c;
      xs[j] = X; ys[j] = Y;
      if (X < x0) x0 = X; if (X > x1) x1 = X; if (Y < y0) y0 = Y; if (Y > y1) y1 = Y;
    }
    var hx = (x1 - x0) / 2, hy = (y1 - y0) / 2;
    return { xs: xs, ys: ys, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, k: Math.min(0.95 / Math.max(hx, 1e-6), 0.6 / Math.max(hy, 1e-6), 0.6 / 10.5) };
  }
  function rollAt(T, t) {
    var f = (t - T0) / (T1 - T0) * (TN - 1), j = Math.min(TN - 2, Math.max(0, Math.floor(f))), r = f - j;
    return [T.xs[j] + (T.xs[j + 1] - T.xs[j]) * r, T.ys[j] + (T.ys[j + 1] - T.ys[j]) * r];
  }
  var TA = 2.5 * Math.PI, TB = 4.5 * Math.PI - 1e-6;
  function rollBuild(N, P) {
    var T = rollTable(P.lam), rand = U.rng(2024), pos = new Float32Array(N * 3), warm = new Float32Array(N);
    for (var i = 0; i < N; i++) {
      var t = T0 + (T1 - T0) * (i + rand()) / N, h = 21 * rand(), q = rollAt(T, t);
      pos[3 * i] = (q[0] - T.cx) * T.k; pos[3 * i + 1] = (q[1] - T.cy) * T.k; pos[3 * i + 2] = (h - 10.5) * T.k;
      warm[i] = 1 - (t - T0) / (T1 - T0);
    }
    var a = rollAt(T, TA), b = rollAt(T, TB);
    return { pos: pos, warm: warm, meta: { T: T, chord: Math.hypot(b[0] - a[0], b[1] - a[1]), geo: arcLen(TB) - arcLen(TA) } };
  }
  var roll = {
    id: 'machine-learning', numeral: 'II', field: 'Machine Learning', title: 'The Swiss Roll',
    credit: 'Manifold learning · after Tenenbaum, de Silva and Langford (2000)',
    alt: 'A sheet of points rolled into a spiral, which can be unrolled into a flat strip.',
    view: { yaw: 0.35, pitch: 0.22, zoom: 1.0 }, exposure: 0.95,
    params: [{ k: 'lam', sym: '<i>λ</i>', label: 'unrolled', min: 0, max: 1, step: 0.01, value: 0, dec: 2, fast: true }],
    actions: [{ k: 'unroll', label: 'Unroll' }],
    action: function (k, P, ctx, btn) {
      var target = P.lam < 0.5 ? 1 : 0;
      ctx.animateParam('lam', target, 3.2);
      if (btn) btn.textContent = target ? 'Roll up' : 'Unroll';
    },
    eq: '<div class="eqgrid">' +
      '<span class="l">(<i>x</i>, <i>y</i>, <i>z</i>)</span><span class="r">=</span><span class="x">(<i>t</i> cos <i>t</i>,&ensp;<i>h</i>,&ensp;<i>t</i> sin <i>t</i>)</span>' +
      '<span class="l"><i>t</i></span><span class="r">∼</span><span class="x">U(<span class="frac"><span>3π</span><span>2</span></span>, <span class="frac"><span>9π</span><span>2</span></span>),&ensp;<i>h</i> ∼ U(0, 21)</span>' +
      '<span class="l"><i>s</i>(<i>t</i>)</span><span class="r">=</span><span class="x"><span class="int">∫</span><span class="ss"><sup><i>t</i></sup><sub>3π/2</sub></span> √(1 + <i>u</i><sup>2</sup>)&thinsp;d<i>u</i><span class="eqnote">distance along the sheet</span></span>' +
      '<span class="l"><i>κ</i><sub><span class="p" data-k="lam"><i>λ</i></span></sub>(<i>s</i>)</span><span class="r">=</span><span class="x">(1 &minus; <span class="p" data-k="lam"><i>λ</i></span>)&thinsp;<i>κ</i>(<i>s</i>)<span class="eqnote">curvature while unrolling</span></span>' +
      '</div>',
    note: 'A flat sheet of points rolled into three dimensions, the standard test for learning structure from data. Points A and B sit on neighbouring turns. They are close in a straight line yet far apart along the sheet. Unrolling scales the curvature by 1 &minus; <i>λ</i> and keeps every distance along the sheet, which is the flat map that methods such as Isomap recover from the points alone.',
    generate: function (N, P) { return rollBuild(N, P); },
    fast: function (N, P) { return rollBuild(N, P); },
    overlay: function (P, meta) {
      if (!meta || !meta.T) return null;
      var out = kit.floorRing(kit.empty(), -0.80), T = meta.T, geo = [];
      for (var s = 0; s <= 220; s++) {
        var q = rollAt(T, TA + (TB - TA) * s / 220);
        geo.push([(q[0] - T.cx) * T.k, (q[1] - T.cy) * T.k, 0]);
      }
      var A = geo[0], B = geo[geo.length - 1];
      out.lines.push({ pts: geo, col: C.pale, w: 1.8 });
      out.lines.push({ pts: [A, B], col: C.steel, w: 1.2, dash: [0.016, 0.012] });
      out.points.push({ p: A, s: 9, col: C.pale }); out.points.push({ p: B, s: 9, col: C.pale });
      out.labels.push({ p: [A[0], A[1] + 0.07, A[2]], t: 'A', cls: 'mark big' });
      out.labels.push({ p: [B[0], B[1] + 0.07, B[2]], t: 'B', cls: 'mark big' });
      return out;
    },
    readout: function (P, meta) {
      if (!meta || !meta.geo) return '';
      return '<b>A to B</b> · along the sheet ' + meta.geo.toFixed(1) + ' · straight line ' + meta.chord.toFixed(1) +
        '<br>ratio ' + (meta.geo / Math.max(meta.chord, 1e-6)).toFixed(1) + ' to 1';
    }
  };

  /* ---------------------------------------------------------------- III. Deep learning */
  function gaussInt(f) {
    var n = 800, a = -8, h = 16 / n, s = 0;
    for (var i = 0; i <= n; i++) {
      var z = a + i * h, w = (i === 0 || i === n) ? 1 : (i % 2 ? 4 : 2);
      s += w * f(z) * Math.exp(-z * z / 2);
    }
    return s * h / 3 / Math.sqrt(2 * Math.PI);
  }
  function meanField(sw, sb) {
    var q = 1;
    for (var it = 0; it < 400; it++) {
      var qq = q, qn = sw * sw * gaussInt(function (z) { var t = Math.tanh(Math.sqrt(qq) * z); return t * t; }) + sb * sb;
      if (Math.abs(qn - q) < 1e-10) { q = qn; break; }
      q = qn;
    }
    var chi = sw * sw * gaussInt(function (z) { var t = Math.tanh(Math.sqrt(q) * z), d = 1 - t * t; return d * d; });
    return { q: q, chi: chi };
  }
  function curveLen(H, K, n) {
    var L = 0;
    for (var k = 0; k < K; k++) {
      var a = k * n, b = ((k + 1) % K) * n, s = 0;
      for (var i = 0; i < n; i++) { var d = H[b + i] - H[a + i]; s += d * d; }
      L += Math.sqrt(s);
    }
    return L;
  }
  var deep = {
    id: 'deep-learning', numeral: 'III', field: 'Deep Learning', title: 'A Circle through a Deep Network',
    credit: 'Random tanh network · after Poole et al. (2016)',
    alt: 'A circle of inputs after passing through a deep random network, tangled into a knotted loop.',
    view: { yaw: 0.4, pitch: 0.28, zoom: 1.0 }, exposure: 0.32, pointScale: 1.15,
    params: [
      { k: 'sw', sym: '<i>σ</i><sub><i>w</i></sub>', label: 'weight scale', min: 0.5, max: 4, step: 0.05, value: 2.8, dec: 2 },
      { k: 'depth', sym: '<i>L</i>', label: 'layers', type: 'int', min: 1, max: 12, step: 1, value: 10 }
    ],
    actions: [{ k: 'reseed', label: 'New weights' }],
    action: function (k, P, ctx) { if (k === 'reseed') ctx.setParam('seed', P.seed + 1, { now: true }); },
    eq: '<div class="eqgrid">' +
      '<span class="l"><i>h</i><sup>ℓ</sup></span><span class="r">=</span><span class="x"><i>W</i><sup>ℓ</sup> tanh(<i>h</i><sup>ℓ&minus;1</sup>) + <i>b</i><sup>ℓ</sup>,&ensp;ℓ = 1, …, <span class="p" data-k="depth"><i>L</i></span></span>' +
      '<span class="l"><i>W</i><span class="ss"><sup>ℓ</sup><sub><i>ij</i></sub></span></span><span class="r">∼</span><span class="x">N(0, <span class="p" data-k="sw"><i>σ</i><sub><i>w</i></sub></span><sup>2</sup>/<i>n</i>),&ensp;<i>b</i><span class="ss"><sup>ℓ</sup><sub><i>i</i></sub></span> ∼ N(0, 0.3<sup>2</sup>)</span>' +
      '<span class="l"><i>χ</i><sub>1</sub></span><span class="r">=</span><span class="x"><span class="p" data-k="sw"><i>σ</i><sub><i>w</i></sub></span><sup>2</sup> <span class="int">∫</span> D<i>z</i>&thinsp;[tanh′(√<i>q</i>*&thinsp;<i>z</i>)]<sup>2</sup></span>' +
      '</div>',
    note: 'Sixteen hundred inputs on a circle pass through a deep network with random weights, shown in the first three principal components of its last layer. When <i>χ</i><sub>1</sub> is above one, each layer stretches and folds the curve. Its length then grows exponentially with depth. Below one the layers squeeze it towards a single point. The boundary between the two regimes is called the edge of chaos.',
    generate: async function (N, P) {
      var n = 100, K = 1600, L = Math.round(P.depth), sw = P.sw, sb = 0.3;
      var rand = U.rng(424242 + P.seed * 31), g = U.gaussian(rand), mf = meanField(sw, sb), i, k, r, c;
      var u = new Float64Array(n), v = new Float64Array(n), du = 0, dv = 0, uv = 0;
      for (i = 0; i < n; i++) { u[i] = g(); v[i] = g(); }
      for (i = 0; i < n; i++) du += u[i] * u[i]; du = Math.sqrt(du);
      for (i = 0; i < n; i++) u[i] /= du;
      for (i = 0; i < n; i++) uv += u[i] * v[i];
      for (i = 0; i < n; i++) v[i] -= uv * u[i];
      for (i = 0; i < n; i++) dv += v[i] * v[i]; dv = Math.sqrt(dv);
      for (i = 0; i < n; i++) v[i] /= dv;
      var rad = Math.sqrt(n * mf.q), H = new Float32Array(K * n), A = new Float32Array(K * n), W = new Float32Array(n * n), b = new Float32Array(n);
      for (k = 0; k < K; k++) {
        var th = 2 * Math.PI * k / K, ck = Math.cos(th), sk = Math.sin(th);
        for (i = 0; i < n; i++) H[k * n + i] = rad * (u[i] * ck + v[i] * sk);
      }
      var len0 = curveLen(H, K, n), scaleW = sw / Math.sqrt(n);
      for (var l = 0; l < L; l++) {
        for (i = 0; i < n * n; i++) W[i] = g() * scaleW;
        for (i = 0; i < n; i++) b[i] = g() * sb;
        for (i = 0; i < K * n; i++) A[i] = Math.tanh(H[i]);
        for (k = 0; k < K; k++) {
          var base = k * n;
          for (r = 0; r < n; r++) {
            var s = b[r], wr = r * n;
            for (c = 0; c < n; c++) s += W[wr + c] * A[base + c];
            H[base + r] = s;
          }
        }
        await U.tick();
      }
      var lenL = curveLen(H, K, n);
      // principal components of the last layer
      var mean = new Float64Array(n), Cv = new Float64Array(n * n);
      for (k = 0; k < K; k++) for (i = 0; i < n; i++) mean[i] += H[k * n + i] / K;
      for (k = 0; k < K; k++) {
        var o = k * n;
        for (r = 0; r < n; r++) {
          var dr = H[o + r] - mean[r];
          for (c = r; c < n; c++) Cv[r * n + c] += dr * (H[o + c] - mean[c]);
        }
      }
      for (r = 0; r < n; r++) for (c = 0; c < r; c++) Cv[r * n + c] = Cv[c * n + r];
      var vecs = [];
      for (var e = 0; e < 3; e++) {
        var x = new Float64Array(n);
        for (i = 0; i < n; i++) x[i] = g();
        for (var it = 0; it < 80; it++) {
          var y = new Float64Array(n);
          for (r = 0; r < n; r++) { var acc = 0; for (c = 0; c < n; c++) acc += Cv[r * n + c] * x[c]; y[r] = acc; }
          vecs.forEach(function (w) { var d = 0, j; for (j = 0; j < n; j++) d += y[j] * w[j]; for (j = 0; j < n; j++) y[j] -= d * w[j]; });
          var nr = 0; for (i = 0; i < n; i++) nr += y[i] * y[i]; nr = Math.sqrt(nr) || 1;
          for (i = 0; i < n; i++) x[i] = y[i] / nr;
        }
        vecs.push(x);
      }
      var Pj = new Float32Array(K * 3), rmax = 0;
      for (k = 0; k < K; k++) {
        for (e = 0; e < 3; e++) {
          var sum = 0; for (i = 0; i < n; i++) sum += (H[k * n + i] - mean[i]) * vecs[e][i];
          Pj[3 * k + e] = sum;
        }
        rmax = Math.max(rmax, Math.hypot(Pj[3 * k], Pj[3 * k + 1], Pj[3 * k + 2]));
      }
      var scl = 0.9 / Math.max(rmax, 0.3 * rad);
      var seg = new Float32Array(K);
      for (k = 0; k < K; k++) {
        var k2 = (k + 1) % K;
        seg[k] = Math.hypot(Pj[3 * k2] - Pj[3 * k], Pj[3 * k2 + 1] - Pj[3 * k + 1], Pj[3 * k2 + 2] - Pj[3 * k + 2]);
      }
      var sorted = Array.prototype.slice.call(seg).sort(function (p, q) { return p - q; }), med = sorted[K >> 1] || 1;
      var pos = new Float32Array(N * 3), warm = new Float32Array(N);
      for (i = 0; i < N; i++) {
        var sp = (i + rand()) / N * K, kk = Math.floor(sp) % K, f = sp - Math.floor(sp), kn = (kk + 1) % K;
        for (e = 0; e < 3; e++) pos[3 * i + e] = (Pj[3 * kk + e] + (Pj[3 * kn + e] - Pj[3 * kk + e]) * f) * scl + g() * 0.0075;
        warm[i] = U.clamp(0.85 - 0.32 * Math.log(seg[kk] / med + 1e-6), 0, 1);
      }
      return { pos: pos, warm: warm, meta: { chi: mf.chi, q: mf.q, ratio: lenL / len0, L: L } };
    },
    overlay: function () {
      var out = kit.floorRing(kit.empty(), -0.80);
      [[[0.62, 0, 0], 'PC 1'], [[0, 0.62, 0], 'PC 2'], [[0, 0, 0.62], 'PC 3']].forEach(function (a) {
        out.lines.push({ pts: [[0, 0, 0], a[0]], col: C.steelFaint, w: 1, dash: [0.014, 0.012] });
        out.labels.push({ p: [a[0][0] * 1.1, a[0][1] * 1.1, a[0][2] * 1.1], t: a[1], cls: 'tick' });
      });
      return out;
    },
    readout: function (P, meta) {
      if (!meta || meta.chi === undefined) return '';
      return '<b><i>χ</i><sub>1</sub> = ' + meta.chi.toFixed(2) + '</b> · ' + (meta.chi > 1 ? 'chaotic regime' : 'ordered regime') +
        ' · <i>q</i>* = ' + meta.q.toFixed(2) + '<br>sampled curve length after ' + meta.L + ' layers ×' +
        (meta.ratio >= 10 ? meta.ratio.toFixed(0) : meta.ratio.toFixed(2));
    }
  };

  /* ---------------------------------------------------------------- VI. Mathematics */
  var R0 = 2.8, R1 = 4.0;
  var LX = function (r) { return -0.95 + 1.9 * (r - R0) / (R1 - R0); };
  var LY = function (v) { return -0.55 + 1.1 * v; };
  var LZ = function (v) { return 0.55 - 1.1 * v; };
  function orbitInfo(r) {
    var x = 0.4, i;
    for (i = 0; i < 4000; i++) x = r * x * (1 - x);
    var xs = [], lyap = 0;
    for (i = 0; i < 4000; i++) { lyap += Math.log(Math.abs(r * (1 - 2 * x)) + 1e-300); x = r * x * (1 - x); if (i < 300) xs.push(x); }
    lyap /= 4000;
    var period = 0;
    for (var p = 1; p <= 128 && !period; p++) {
      var ok = true;
      for (i = 0; i + p < xs.length && i < 64; i++) if (Math.abs(xs[i + p] - xs[i]) > 1e-7) { ok = false; break; }
      if (ok) period = p;
    }
    return { lyap: lyap, period: period };
  }
  var logistic = {
    id: 'mathematics', numeral: 'VI', field: 'Mathematics', title: 'The Logistic Map',
    credit: 'May (1976) · Feigenbaum (1978)',
    alt: 'The bifurcation diagram of the logistic map, drawn on the curved sheet of its parabolas.',
    view: { yaw: -0.42, pitch: 0.18, zoom: 1.0 }, exposure: 0.85,
    params: [{ k: 'r', sym: '<i>r</i>', label: 'growth rate', min: 2.8, max: 4, step: 0.001, value: 3.83, dec: 3, regen: false }],
    eq: '<div class="eqgrid">' +
      '<span class="l"><i>x</i><sub><i>n</i>+1</sub></span><span class="r">=</span><span class="x"><span class="p" data-k="r"><i>r</i></span>&thinsp;<i>x</i><sub><i>n</i></sub>(1 &minus; <i>x</i><sub><i>n</i></sub>)</span>' +
      '<span class="l"><i>δ</i></span><span class="r">=</span><span class="x">lim <span class="frac"><span><i>r</i><sub><i>k</i></sub> &minus; <i>r</i><sub><i>k</i>&minus;1</sub></span><span><i>r</i><sub><i>k</i>+1</sub> &minus; <i>r</i><sub><i>k</i></sub></span></span> = 4.6692…</span>' +
      '<span class="l"><i>λ</i>(<span class="p" data-k="r"><i>r</i></span>)</span><span class="r">=</span><span class="x">lim <span class="frac"><span>1</span><span><i>n</i></span></span>&thinsp;Σ ln&thinsp;|<span class="p" data-k="r"><i>r</i></span>(1 &minus; 2<i>x</i><sub><i>k</i></sub>)|<span class="eqnote">Lyapunov exponent</span></span>' +
      '</div>',
    note: 'One quadratic rule, applied again and again. As <i>r</i> rises, the long-run orbit splits into 2, 4, 8 and 16 values at intervals that shrink by Feigenbaum\'s constant <i>δ</i>. Near <i>r</i> ≈ 3.5699 it turns chaotic. Turn the plate on its side and every point falls on the parabola that produced it. The cobweb traces one orbit at the chosen <i>r</i>.',
    generate: function (N) {
      var Cn = Math.max(200, Math.floor(N / 200)), K = Math.floor(N / Cn), extra = N - Cn * K, rand = U.rng(11);
      var pos = new Float32Array(N * 3), warm = new Float32Array(N), i = 0;
      for (var c = 0; c < Cn; c++) {
        var r = R0 + (R1 - R0) * (c + 0.5) / Cn, x = 0.3 + 0.4 * rand(), t;
        for (t = 0; t < 800; t++) x = r * x * (1 - x);
        var k = K + (c < extra ? 1 : 0), xs = new Float64Array(k + 1), ly = 0;
        xs[0] = x;
        for (t = 1; t <= k; t++) { ly += Math.log(Math.abs(r * (1 - 2 * x)) + 1e-12); x = r * x * (1 - x); xs[t] = x; }
        ly /= k;
        var idx = []; for (t = 0; t < k; t++) idx.push(t);
        idx.sort(function (a, b) { return xs[a] - xs[b]; });
        var w = ly < 0 ? 0.92 : 0.22;
        for (t = 0; t < k; t++) {
          var j = idx[t], rr = r + (rand() - 0.5) * (R1 - R0) / Cn;
          pos[3 * i] = LX(rr); pos[3 * i + 1] = LY(xs[j + 1]); pos[3 * i + 2] = LZ(xs[j]); warm[i] = w; i++;
        }
      }
      return { pos: pos, warm: warm, meta: {} };
    },
    overlay: function (P) {
      var out = kit.floorRing(kit.empty(), -0.80), yb = -0.63, zf = 0.62, r = P.r, s;
      var tk = []; for (s = 0; s <= 6; s++) tk.push({ f: s / 6, label: (R0 + s * 0.2).toFixed(1) });
      kit.axis(out, [LX(R0), yb, zf], [LX(R1), yb, zf], tk, [0, 0, 0.03], { title: '<i>r</i>', titleAt: [LX(R1) + 0.08, yb, zf + 0.06] });
      [[3, 'r<sub>1</sub>'], [1 + Math.sqrt(6), 'r<sub>2</sub>'], [3.5699456, 'r<sub>∞</sub>'], [1 + Math.sqrt(8), '1+√8']].forEach(function (m) {
        out.lines.push({ pts: [[LX(m[0]), yb, zf], [LX(m[0]), yb + 0.05, zf]], col: C.gold, w: 1.4 });
        out.labels.push({ p: [LX(m[0]), yb + 0.09, zf], html: m[1], cls: 'mark' });
      });
      var xa = LX(R0) - 0.06;
      kit.axis(out, [xa, LY(0), LZ(1) - 0.02], [xa, LY(1), LZ(1) - 0.02], [{ f: 0, label: '0' }, { f: 0.5, label: '0.5' }, { f: 1, label: '1' }],
        [-0.03, 0, 0], { title: '<i>x</i><sub><i>n</i>+1</sub>', titleAt: [xa, LY(1.1), LZ(1) - 0.02] });
      kit.axis(out, [xa, yb, LZ(0)], [xa, yb, LZ(1)], [{ f: 0, label: '0' }, { f: 0.5, label: '0.5' }, { f: 1, label: '1' }],
        [-0.03, 0, 0], { title: '<i>x</i><sub><i>n</i></sub>', titleAt: [xa - 0.08, yb - 0.06, LZ(0.5)] });
      var X0 = LX(r), par = [], dia = [], web = [], x = 0.2;
      for (s = 0; s <= 80; s++) { var v = s / 80; par.push([X0, LY(r * v * (1 - v)), LZ(v)]); dia.push([X0, LY(v), LZ(v)]); }
      out.lines.push({ pts: [[X0, LY(0), LZ(0)], [X0, LY(1), LZ(0)], [X0, LY(1), LZ(1)], [X0, LY(0), LZ(1)]], closed: true, col: C.steelFaint, w: 1 });
      out.lines.push({ pts: par, col: C.steel, w: 1.3 });
      out.lines.push({ pts: dia, col: C.steelFaint, w: 1 });
      web.push([X0, LY(x), LZ(x)]);
      for (s = 0; s < 70; s++) {
        var nx = r * x * (1 - x);
        web.push([X0, LY(nx), LZ(x)]); web.push([X0, LY(nx), LZ(nx)]);
        x = nx;
      }
      out.lines.push({ pts: web, col: C.pale, w: 1.1 });
      out.labels.push({ p: [X0, LY(1) + 0.07, LZ(0)], html: '<i>r</i> = ' + r.toFixed(3), cls: 'cursor' });
      return out;
    },
    readout: function (P) {
      var o = orbitInfo(P.r);
      var kind = o.period ? 'period ' + o.period : (o.lyap > 0 ? 'chaotic' : 'no period below 128');
      return '<b><i>r</i> = ' + P.r.toFixed(3) + '</b> · ' + kind + ' · <i>λ</i> = ' + OX.fmtSigned(o.lyap) +
        '<br>Lyapunov exponent over 4,000 steps after 4,000 discarded';
    }
  };

  /* ---------------------------------------------------------------- VII. Infrastructure */
  function torusGeom(p) {
    var half = 0.525, sp = 2 * half / (p - 1);
    return { p: p, half: half, c: function (i) { return -half + i * sp; } };
  }
  // A wrap-around link of ring (dim, a, b), from index p-1 back to index 0, at parameter s in 0..1.
  function arcPoint(G, dim, a, b, s, out) {
    var oa = G.c(a), ob = G.c(b), r0 = Math.hypot(oa, ob), da = r0 > 1e-6 ? oa / r0 : 1, db = r0 > 1e-6 ? ob / r0 : 0;
    var Rout = 0.80 + 0.12 * (r0 / (G.half * Math.SQRT2)), sn = Math.sin(Math.PI * s);
    var ax = (G.half + 0.11 * Math.pow(sn, 0.45)) * Math.cos(Math.PI * s);
    var rad = r0 + (Rout - r0) * Math.pow(sn, 1.1), A = da * rad, B = db * rad;
    if (dim === 0) { out[0] = ax; out[1] = A; out[2] = B; }
    else if (dim === 1) { out[0] = A; out[1] = ax; out[2] = B; }
    else { out[0] = A; out[1] = B; out[2] = ax; }
    return out;
  }
  function nodeOf(G, dim, a, b, s, out) {
    if (dim === 0) { out[0] = G.c(s); out[1] = G.c(a); out[2] = G.c(b); }
    else if (dim === 1) { out[0] = G.c(a); out[1] = G.c(s); out[2] = G.c(b); }
    else { out[0] = G.c(a); out[1] = G.c(b); out[2] = G.c(s); }
    return out;
  }
  var PHASES = ['reduce-scatter along <i>x</i>', 'reduce-scatter along <i>y</i>', 'reduce-scatter along <i>z</i>',
    'all-gather along <i>z</i>', 'all-gather along <i>y</i>', 'all-gather along <i>x</i>'];
  var torus = {
    id: 'infrastructure', numeral: 'VII', field: 'Computing Infrastructure', title: 'A Torus of Accelerators',
    credit: 'Three-dimensional torus · ring all-reduce',
    alt: 'Accelerator chips on a cubic lattice whose rows close into rings through looping wrap-around links.',
    view: { yaw: 0.62, pitch: 0.42, zoom: 0.98 }, exposure: 0.8, pointScale: 1.05,
    params: [{ k: 'p', sym: '<i>p</i>', label: 'chips per ring', type: 'int', min: 4, max: 10, step: 1, value: 8 }],
    actions: [{ k: 'run', label: 'Run all-reduce' }],
    action: function (k, P, ctx, btn) {
      if (k !== 'run') return;
      if (torus._run) { torus._run = null; if (btn) btn.textContent = 'Run all-reduce'; ctx.refresh(); return; }
      torus._run = { t0: ctx.clock(), step: -1, btn: btn };
      if (btn) btn.textContent = 'Stop';
      ctx.kick();
    },
    eq: '<div class="eqgrid">' +
      '<span class="l"><i>T</i><sub>ring</sub></span><span class="r">=</span><span class="x">2(<i>p</i> &minus; 1)&thinsp;<i>α</i> + 2&thinsp;<span class="frac"><span><i>p</i> &minus; 1</span><span><i>p</i></span></span>&thinsp;<i>n</i>&thinsp;<i>β</i><span class="eqnote"><i>α</i> latency, <i>β</i> time per number</span></span>' +
      '<span class="l">steps</span><span class="r">=</span><span class="x">2 × 3 × (<span class="p" data-k="p"><i>p</i></span> &minus; 1)<span class="eqnote">one ring dimension at a time</span></span>' +
      '<span class="l">chips</span><span class="r">=</span><span class="x"><span class="p" data-k="p"><i>p</i></span><sup>3</sup>,&ensp;links = 3<span class="p" data-k="p"><i>p</i></span><sup>3</sup></span>' +
      '</div>',
    note: 'Five hundred and twelve chips wired as an 8 × 8 × 8 torus, the topology Google uses in its TPU v4 supercomputer. With the wrap-around links every chip has six neighbours, even on the faces. A training step ends with an all-reduce. Partial sums of the gradients travel round the rings, one dimension at a time, until every chip holds the total.',
    generate: function (N, P) {
      var p = Math.round(P.p), G = torusGeom(p), rand = U.rng(77), g = U.gaussian(rand);
      var pos = new Float32Array(N * 3), warm = new Float32Array(N), i = 0, a, b, s, k, d;
      var nodes = p * p * p, per = Math.floor(N * 0.34 / nodes);
      for (a = 0; a < p; a++) for (b = 0; b < p; b++) for (s = 0; s < p; s++) for (k = 0; k < per; k++) {
        pos[3 * i] = G.c(a) + U.clamp(g() * 0.011, -0.024, 0.024);
        pos[3 * i + 1] = G.c(b) + U.clamp(g() * 0.011, -0.024, 0.024);
        pos[3 * i + 2] = G.c(s) + U.clamp(g() * 0.011, -0.024, 0.024);
        warm[i] = 1; i++;
      }
      var links = 3 * (p - 1) * p * p, perL = Math.floor(N * 0.44 / links), A = [0, 0, 0], B = [0, 0, 0];
      for (d = 0; d < 3; d++) for (a = 0; a < p; a++) for (b = 0; b < p; b++) for (s = 0; s < p - 1; s++) {
        nodeOf(G, d, a, b, s, A); nodeOf(G, d, a, b, s + 1, B);
        for (k = 0; k < perL; k++) {
          var f = 0.1 + 0.8 * rand();
          pos[3 * i] = A[0] + (B[0] - A[0]) * f + g() * 0.0016;
          pos[3 * i + 1] = A[1] + (B[1] - A[1]) * f + g() * 0.0016;
          pos[3 * i + 2] = A[2] + (B[2] - A[2]) * f + g() * 0.0016;
          warm[i] = 0.35; i++;
        }
      }
      var arcs = 3 * p * p, rest = N - i, perA = Math.floor(rest / arcs), q = [0, 0, 0], n = 0;
      for (d = 0; d < 3; d++) for (a = 0; a < p; a++) for (b = 0; b < p; b++) {
        n++;
        var cnt = n === arcs ? N - i : perA;
        for (k = 0; k < cnt; k++) {
          arcPoint(G, d, a, b, 0.03 + 0.94 * (k + rand()) / cnt, q);
          pos[3 * i] = q[0] + g() * 0.0016; pos[3 * i + 1] = q[1] + g() * 0.0016; pos[3 * i + 2] = q[2] + g() * 0.0016;
          warm[i] = 0.2; i++;
        }
      }
      return { pos: pos, warm: warm, meta: { p: p } };
    },
    overlay: function (P) {
      var out = kit.floorRing(kit.empty(), -0.80), h = 0.525;
      out.labels.push({ p: [0, -h - 0.12, h + 0.12], html: '<i>x</i> rings', cls: 'tick' });
      out.labels.push({ p: [h + 0.16, 0, h + 0.1], html: '<i>y</i> rings', cls: 'tick' });
      out.labels.push({ p: [h + 0.14, -h - 0.1, 0], html: '<i>z</i> rings', cls: 'tick' });
      return out;
    },
    animate: function (t, P, ctx) {
      var st = torus._run; if (!st) return null;
      var p = Math.round(P.p), G = torusGeom(p), steps = 6 * (p - 1), dur = ctx.reduced() ? 0.9 : 0.42;
      var el = t - st.t0, k = Math.floor(el / dur);
      if (k >= steps) {
        torus._run = null; if (st.btn) st.btn.textContent = 'Run all-reduce';
        ctx.readout('<b>Done</b> · every chip now holds the sum of all ' + U.fmtInt(p * p * p) + ' gradients<br>' + steps + ' steps, each moving one chunk per link');
        return null;
      }
      var phase = Math.floor(k / (p - 1)), dim = [0, 1, 2, 2, 1, 0][phase], f = U.ease((el - k * dur) / dur);
      if (k !== st.step) {
        st.step = k;
        var chunk = ['<i>n</i>/' + p, '<i>n</i>/' + p * p, '<i>n</i>/' + p * p * p][[0, 1, 2, 2, 1, 0][phase]];
        ctx.readout('<b>' + PHASES[phase] + '</b> · step ' + (k + 1) + ' of ' + steps + '<br>each chip sends a chunk of ' + chunk + ' numbers to its neighbour');
      }
      var size = [7, 5, 3.4, 3.4, 5, 7][phase], cnt = p * p * p, data = new Float32Array(cnt * 8), A = [0, 0, 0], B = [0, 0, 0], j = 0;
      for (var a = 0; a < p; a++) for (var b = 0; b < p; b++) for (var s = 0; s < p; s++) {
        if (s < p - 1) {
          nodeOf(G, dim, a, b, s, A); nodeOf(G, dim, a, b, s + 1, B);
          A[0] += (B[0] - A[0]) * f; A[1] += (B[1] - A[1]) * f; A[2] += (B[2] - A[2]) * f;
        } else arcPoint(G, dim, a, b, f, A);
        data.set([A[0], A[1], A[2], size, 0.98, 0.90, 0.72, 0.85], j * 8); j++;
      }
      return { count: cnt, data: data, live: true };
    },
    readout: function (P) {
      var p = Math.round(P.p);
      return '<b>' + U.fmtInt(p * p * p) + ' chips</b> · ' + U.fmtInt(3 * p * p * p) + ' links · all-reduce in ' + 6 * (p - 1) +
        ' steps<br>' + U.fmtInt(3 * p * p) + ' of the links wrap round the edges';
    }
  };

  /* ---------------------------------------------------------------- shared plates */
  var yields = OX.makeYields({
    id: 'economic-analysis', numeral: 'IV', field: 'Economic and Financial Analysis', title: 'The US Yield Curve, 1990 to 2026',
    credit: 'Data · US Treasury par yield curve, monthly averages',
    alt: 'A surface of 442 monthly US Treasury yield curves from 1990 to 2026.',
    note: 'The plate holds 442 monthly yield curves for US Treasuries, from three-month bills to ten-year notes. Where the surface folds, short rates sit above long ones, as in 2000, 2006, 2019 and from late 2022 to late 2024. The bright line is the chosen month. Beside it, the dashed line is the Nelson and Siegel curve fitted to that month with Diebold and Li\'s fixed <i>λ</i>.'
  });
  var scaling = OX.makeScaling({
    id: 'ai-economy', numeral: 'V', field: 'AI and the New Economy', title: 'A Production Function for Language Models',
    credit: 'Hoffmann et al. (2022) · re-estimated by Besiroglu et al. (2024)',
    alt: 'The fitted loss surface of language models over parameters and training tokens, with isoquants and an expansion path.'
  });

  OX.PLATES_A = [forecast, roll, deep, yields, scaling, logistic, torus];
})();
