/* Oxlon interactive plates engine.
   WebGL point-density renderer with dual Light/Dark shading, smooth plate morphing,
   3D projected overlays/labels, Canvas 2D fallback, and on-demand rendering (0% idle GPU). */
(function () {
  'use strict';
  var OX = (window.OX = window.OX || {});

  /* ------------------------------------------------------------------ utilities */
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gaussian(rand) {
    var spare = null;
    return function () {
      if (spare !== null) { var s = spare; spare = null; return s; }
      var u = 0;
      while (u <= 1e-12) u = rand();
      var v = rand(), r = Math.sqrt(-2 * Math.log(u)), th = 2 * Math.PI * v;
      spare = r * Math.sin(th);
      return r * Math.cos(th);
    };
  }
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function smoothstep(a, b, x) { var t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }
  function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }
  function pchip(xs, ys) {
    var n = xs.length, h = [], d = [], m = new Array(n), i;
    for (i = 0; i < n - 1; i++) { h[i] = xs[i + 1] - xs[i]; d[i] = (ys[i + 1] - ys[i]) / h[i]; }
    m[0] = d[0]; m[n - 1] = d[n - 2];
    for (i = 1; i < n - 1; i++) {
      if (d[i - 1] * d[i] <= 0) m[i] = 0;
      else { var w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1]; m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]); }
    }
    return function (x) {
      var k = 0;
      while (k < n - 2 && x > xs[k + 1]) k++;
      var t = (x - xs[k]) / h[k], t2 = t * t, t3 = t2 * t;
      return (2 * t3 - 3 * t2 + 1) * ys[k] + (t3 - 2 * t2 + t) * h[k] * m[k] +
        (-2 * t3 + 3 * t2) * ys[k + 1] + (t3 - t2) * h[k] * m[k + 1];
    };
  }
  function fmtInt(n) { return Math.round(n).toLocaleString('en-GB'); }
  function tick() { return new Promise(function (r) { setTimeout(r, 0); }); }
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function monthLabel(start, i) {
    var p = start.split('-'), y = +p[0], m = +p[1] - 1 + i;
    return MONTHS[((m % 12) + 12) % 12] + ' ' + (y + Math.floor(m / 12));
  }
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }
  function sci(x, digits) {
    if (!isFinite(x) || x === 0) return String(x);
    var e = Math.floor(Math.log10(Math.abs(x))), m = x / Math.pow(10, e);
    if (+m.toFixed(digits) >= 10) { m /= 10; e += 1; }
    return m.toFixed(digits) + '&thinsp;&times;&thinsp;10<sup>' + e + '</sup>';
  }
  function big(x) {
    var a = Math.abs(x);
    if (a >= 1e12) return (x / 1e12).toFixed(a >= 1e13 ? 0 : 1) + '&thinsp;T';
    if (a >= 1e9) return (x / 1e9).toFixed(a >= 1e10 ? 0 : 1) + '&thinsp;B';
    if (a >= 1e6) return (x / 1e6).toFixed(a >= 1e7 ? 0 : 1) + '&thinsp;M';
    return fmtInt(x);
  }
  OX.util = {
    rng: rng, gaussian: gaussian, clamp: clamp, lerp: lerp, smoothstep: smoothstep, ease: ease,
    pchip: pchip, fmtInt: fmtInt, tick: tick, monthLabel: monthLabel, sci: sci, big: big, MONTHS: MONTHS
  };

  /* ------------------------------------------------------------------ theme palettes */
  var PALETTES = {
    dark: {
      steel: [0.58, 0.69, 0.82, 0.56],
      steelFaint: [0.58, 0.69, 0.82, 0.22],
      gold: [0.87, 0.70, 0.39, 0.96],
      pale: [0.97, 0.93, 0.84, 0.96],
      claret: [0.90, 0.42, 0.46, 0.96],
      packet: [0.98, 0.91, 0.74, 0.94]
    },
    light: {
      steel: [0.22, 0.31, 0.44, 0.62],
      steelFaint: [0.22, 0.31, 0.44, 0.20],
      gold: [0.64, 0.39, 0.08, 0.96],
      pale: [0.08, 0.14, 0.26, 0.96],
      claret: [0.72, 0.16, 0.22, 0.96],
      packet: [0.74, 0.18, 0.16, 0.96]
    }
  };
  OX.C = {};
  function syncPalette(isLight) {
    var src = isLight ? PALETTES.light : PALETTES.dark;
    Object.keys(src).forEach(function (k) { OX.C[k] = src[k]; });
  }
  function currentTheme() {
    var attr = document.documentElement.getAttribute('data-theme');
    return attr === 'dark' ? 'dark' : 'light';
  }
  syncPalette(currentTheme() === 'light');

  /* ------------------------------------------------------------------ shaders */
  var VS_POINTS = [
    'precision highp float;',
    'attribute vec3 aFrom; attribute vec3 aTo; attribute float aWF; attribute float aWT;',
    'attribute float aSeed; attribute vec3 aDir;',
    'uniform mat3 uRot; uniform vec2 uScale; uniform vec2 uOff; uniform float uDist;',
    'uniform float uMix; uniform float uStag; uniform float uDrift; uniform float uSag;',
    'uniform float uPx; uniform float uEnergy; uniform float uShadow; uniform float uFloor;',
    'varying float vE; varying float vW;',
    'float ease(float t){ return t < 0.5 ? 4.0*t*t*t : 1.0 - pow(-2.0*t + 2.0, 3.0) * 0.5; }',
    'void main(){',
    '  float p = clamp((uMix - aSeed * uStag) / max(1.0 - uStag, 0.001), 0.0, 1.0);',
    '  float e = ease(p);',
    '  float arc = sin(3.14159265 * e);',
    '  vec3 pos = mix(aFrom, aTo, e) + aDir * (uDrift * arc) - vec3(0.0, uSag * arc, 0.0);',
    '  vW = mix(aWF, aWT, e);',
    '  if (uShadow > 0.5) pos.y = uFloor;',
    '  vec3 r = uRot * pos;',
    '  float k = uDist / (uDist - r.z);',
    '  gl_Position = vec4(r.xy * k * uScale + uOff, 0.0, 1.0);',
    '  float near = clamp(0.5 + r.z * 0.40, 0.0, 1.0);',
    '  float size = uPx * k;',
    '  gl_PointSize = max(size, 1.0);',
    '  vE = uEnergy * min(1.0, size * size) * (0.64 + 0.36 * near);',
    '}'
  ].join('\n');

  var FS_POINTS = [
    'precision highp float;',
    'varying float vE; varying float vW; uniform float uShadow;',
    'void main(){',
    '  vec2 c = gl_PointCoord - 0.5; float r2 = dot(c, c);',
    '  if (r2 > 0.25) discard;',
    '  float e = vE * (1.0 - 4.0 * r2);',
    '  if (uShadow > 0.5) gl_FragColor = vec4(0.0, 0.0, e, 0.0);',
    '  else gl_FragColor = vec4(e, e * vW, 0.0, 0.0);',
    '}'
  ].join('\n');

  // Fallback when floating-point FBO is unavailable.
  var FS_POINTS_DIRECT = [
    'precision highp float;',
    'varying float vE; varying float vW; uniform float uShadow; uniform float uLight;',
    'void main(){',
    '  vec2 c = gl_PointCoord - 0.5; float r2 = dot(c, c);',
    '  if (r2 > 0.25) discard;',
    '  float e = vE * (1.0 - 4.0 * r2);',
    '  if (uLight > 0.5) {',
    '    vec3 col = uShadow > 0.5 ? vec3(0.68, 0.67, 0.64) : mix(vec3(0.10, 0.22, 0.39), vec3(0.64, 0.36, 0.08), vW);',
    '    gl_FragColor = vec4(col, clamp(e * 0.72, 0.0, 0.85));',
    '  } else {',
    '    vec3 col = uShadow > 0.5 ? vec3(0.20, 0.32, 0.47) : mix(vec3(0.84, 0.64, 0.33), vec3(0.98, 0.90, 0.74), vW);',
    '    gl_FragColor = vec4(col * e * 0.55, 0.0);',
    '  }',
    '}'
  ].join('\n');

  var VS_QUAD = [
    'attribute vec2 aP; varying vec2 vUv;',
    'void main(){ vUv = aP * 0.5 + 0.5; gl_Position = vec4(aP, 0.0, 1.0); }'
  ].join('\n');

  // Dual-theme optical tone-mapping shader:
  // Dark mode: luminous bronze/gold filaments on deep Oxford slate.
  // Light mode: copperplate Oxford-navy & antique-bronze ink absorption on archival ivory paper.
  var FS_TONE = [
    'precision highp float;',
    'uniform sampler2D uTex; uniform vec2 uRes; uniform float uExpo; uniform float uDust; uniform float uLight;',
    'varying vec2 vUv;',
    'float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }',
    'void main(){',
    '  vec4 a = texture2D(uTex, vUv);',
    '  float L = 1.0 - exp(-a.r * uExpo);',
    '  float w = clamp(a.g / max(a.r, 1e-5), 0.0, 1.0);',
    '  float s = 1.0 - exp(-a.b * uExpo);',
    '  vec2 q = vUv - vec2(0.5); q.x *= uRes.x / uRes.y;',
    '  float v = length(q);',
    '  vec3 col;',
    '  if (uLight > 0.5) {',
    '    vec3 bg = mix(vec3(0.988, 0.980, 0.961), vec3(0.949, 0.935, 0.904), smoothstep(0.0, 0.95, v));',
    '    vec3 paperShadow = vec3(0.75, 0.74, 0.70);',
    '    vec3 baseCol = mix(bg, paperShadow, s * 0.36 * (1.0 - L * 0.8));',
    '    vec3 coolInk = mix(vec3(0.14, 0.28, 0.47), vec3(0.05, 0.12, 0.24), smoothstep(0.35, 0.95, L));',
    '    vec3 warmInk = mix(vec3(0.70, 0.42, 0.10), vec3(0.47, 0.24, 0.04), smoothstep(0.35, 0.95, L));',
    '    vec3 ink = mix(coolInk, warmInk, smoothstep(0.14, 0.86, w));',
    '    float alpha = clamp(pow(L, 0.80) * 0.94 * uDust, 0.0, 0.96);',
    '    col = mix(baseCol, ink, alpha);',
    '    col += (hash(gl_FragCoord.xy) - 0.5) * 0.005;',
    '  } else {',
    '    vec3 bronze = vec3(0.36, 0.24, 0.11), gold = vec3(0.86, 0.67, 0.35), pale = vec3(0.98, 0.93, 0.81);',
    '    vec3 dust = mix(vec3(0.0), bronze, smoothstep(0.0, 0.30, L));',
    '    dust = mix(dust, gold, smoothstep(0.22, 0.70, L));',
    '    dust = mix(dust, pale, smoothstep(0.64, 1.0, L));',
    '    dust = mix(dust, dust * vec3(1.03, 1.0, 0.90) + vec3(0.05, 0.04, 0.01) * L, w);',
    '    vec3 bg = mix(vec3(0.055, 0.086, 0.145), vec3(0.032, 0.051, 0.088), smoothstep(0.0, 0.95, v));',
    '    col = bg + vec3(0.19, 0.31, 0.46) * s * 0.38 * (1.0 - L) + dust * uDust;',
    '    col += (hash(gl_FragCoord.xy) - 0.5) * 0.008;',
    '  }',
    '  gl_FragColor = vec4(col, 1.0);',
    '}'
  ].join('\n');

  var VS_LINES = [
    'precision highp float;',
    'attribute vec3 aA; attribute vec3 aB; attribute vec2 aT; attribute vec4 aCol; attribute float aW;',
    'uniform mat3 uRot; uniform vec2 uScale; uniform vec2 uOff; uniform float uDist; uniform vec2 uRes; uniform float uAlpha;',
    'varying vec4 vCol;',
    'vec3 proj(vec3 p){ vec3 r = uRot * p; float k = uDist / (uDist - r.z); return vec3(r.xy * k * uScale + uOff, r.z); }',
    'void main(){',
    '  vec3 a = proj(aA), b = proj(aB);',
    '  vec2 h = uRes * 0.5;',
    '  vec2 d = (b.xy - a.xy) * h; float len = length(d);',
    '  d = len > 1e-5 ? d / len : vec2(1.0, 0.0);',
    '  vec2 n = vec2(-d.y, d.x);',
    '  vec3 p = mix(a, b, aT.x);',
    '  vec2 px = p.xy * h + n * aT.y * aW * 0.5;',
    '  gl_Position = vec4(px / h, 0.0, 1.0);',
    '  vCol = vec4(aCol.rgb, aCol.a * uAlpha * clamp(0.68 + p.z * 0.35, 0.32, 1.0));',
    '}'
  ].join('\n');
  var FS_LINES = [
    'precision highp float; varying vec4 vCol;',
    'void main(){ gl_FragColor = vec4(vCol.rgb * vCol.a, vCol.a); }'
  ].join('\n');

  var VS_SPRITES = [
    'precision highp float;',
    'attribute vec3 aP; attribute float aS; attribute vec4 aC;',
    'uniform mat3 uRot; uniform vec2 uScale; uniform vec2 uOff; uniform float uDist; uniform float uDpr; uniform float uAlpha;',
    'varying vec4 vC;',
    'void main(){ vec3 r = uRot * aP; float k = uDist / (uDist - r.z);',
    '  gl_Position = vec4(r.xy * k * uScale + uOff, 0.0, 1.0); gl_PointSize = max(2.0, aS * uDpr * k); vC = vec4(aC.rgb, aC.a * uAlpha); }'
  ].join('\n');
  var FS_SPRITES = [
    'precision highp float; varying vec4 vC;',
    'void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;',
    '  float a = smoothstep(1.0, 0.28, r);',
    '  gl_FragColor = vec4(vC.rgb * vC.a * a, vC.a * a); }'
  ].join('\n');

  /* ------------------------------------------------------------------ theme controller */
  var activeInstance = null;
  function updateThemeMeta(theme) {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', theme === 'light' ? '#F7F5F0' : '#0B111C');
    document.querySelectorAll('[data-theme-btn]').forEach(function (btn) {
      btn.setAttribute('aria-pressed', String(btn.dataset.themeBtn === theme));
    });
  }
  OX.setTheme = function (theme) {
    var mode = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', mode);
    try { localStorage.setItem('oxlon-theme', mode); } catch (e) { /* storage disabled */ }
    syncPalette(mode === 'light');
    updateThemeMeta(mode);
    if (activeInstance) activeInstance.onThemeChange(mode === 'light');
  };

  /* ------------------------------------------------------------------ engine */
  OX.start = function (cfg) {
    var root = cfg.root, plates = cfg.plates;
    var canvas = root.querySelector('canvas.stage');
    var layer = root.querySelector('.labels3d');
    var ui = {};
    ['numeral', 'field', 'title', 'credit', 'eq', 'params', 'readout', 'note', 'actions',
      'group', 'practice', 'offer', 'eqkey', 'index', 'tour', 'live', 'hint', 'reset',
      'prev', 'next', 'zoomIn', 'zoomOut', 'status'].forEach(function (k) {
      ui[k] = root.querySelector('[data-ui="' + k + '"]');
    });

    var isLight = currentTheme() === 'light';
    syncPalette(isLight);
    updateThemeMeta(isLight ? 'light' : 'dark');

    // Bind header theme buttons.
    document.querySelectorAll('[data-theme-btn]').forEach(function (btn) {
      btn.addEventListener('click', function () { OX.setTheme(btn.dataset.themeBtn); });
    });

    var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
    var reduced = !!(mq && mq.matches);
    var narrow = (window.innerWidth || 1200) < 900;
    var weak = (navigator.deviceMemory && navigator.deviceMemory <= 4) ||
      (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4);
    var N = cfg.N || ((narrow || weak) ? 50000 : 95000);
    var POINT_PX = narrow ? 1.95 : 1.80;
    var DIST = 3.4, FLOOR = -0.80;

    var seeds = new Float32Array(N), dirs = new Float32Array(N * 3);
    (function () {
      var r = rng(7), g = gaussian(r);
      for (var i = 0; i < N; i++) {
        seeds[i] = r();
        var x = g(), y = g(), z = g(), l = Math.sqrt(x * x + y * y + z * z) || 1;
        dirs[3 * i] = x / l; dirs[3 * i + 1] = y / l; dirs[3 * i + 2] = z / l;
      }
    })();
    var from = new Float32Array(N * 3), to = new Float32Array(N * 3);
    var wFrom = new Float32Array(N), wTo = new Float32Array(N);
    var morph = { t0: 0, dur: 0, stag: 0.25, drift: 0.05, sag: 0.03 };
    var sweep = null, fade = null;

    var params = plates.map(function (p) {
      var o = { seed: 1 };
      (p.params || []).forEach(function (d) { o[d.k] = d.value; });
      return o;
    });
    var cache = plates.map(function () { return null; });
    var metas = plates.map(function () { return {}; });
    var active = -1, first = true, busy = false;

    var clock0 = performance.now();
    function clock() { return (performance.now() - clock0) / 1000; }

    /* ------------------------------------------------ camera */
    var cam = { yaw: 0, pitch: 0.3, zoom: 1, vy: 0, vp: 0, target: null, sway: 0, gain: 0 };
    function wrapPi(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }
    function camEase(v, dur) {
      if (!dur) { cam.yaw = v.yaw; cam.pitch = v.pitch; cam.zoom = v.zoom || 1; cam.target = null; return; }
      cam.target = {
        y0: cam.yaw, p0: cam.pitch, z0: cam.zoom,
        y1: cam.yaw + wrapPi(v.yaw - cam.yaw), p1: v.pitch, z1: v.zoom || 1,
        t0: clock(), dur: dur
      };
    }
    function freezeSway() { cam.yaw += cam.gain * 0.22 * Math.sin(cam.sway); cam.gain = 0; }
    function touchInput() { freezeSway(); stopTour(); }
    var rot = new Float32Array(9);
    function rotMatrix(yaw, pitch, out) {
      var cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
      out[0] = cy; out[3] = 0; out[6] = sy;
      out[1] = sp * sy; out[4] = cp; out[7] = -sp * cy;
      out[2] = -cp * sy; out[5] = sp; out[8] = cp * cy;
      return out;
    }
    function updateCamera(t, dt) {
      if (cam.target) {
        var k = clamp((t - cam.target.t0) / cam.target.dur, 0, 1), e = ease(k);
        cam.yaw = lerp(cam.target.y0, cam.target.y1, e);
        cam.pitch = lerp(cam.target.p0, cam.target.p1, e);
        cam.zoom = lerp(cam.target.z0, cam.target.z1, e);
        if (k >= 1) cam.target = null;
      }
      if (!drag) {
        cam.yaw += cam.vy * dt; cam.pitch = clamp(cam.pitch + cam.vp * dt, -0.35, 1.3);
        var damp = Math.exp(-dt * 4.2); cam.vy *= damp; cam.vp *= damp;
        if (Math.abs(cam.vy) < 2e-4) cam.vy = 0;
        if (Math.abs(cam.vp) < 2e-4) cam.vp = 0;
      }
      // Subtle sway only when user explicitly enables Auto-tour (0% GPU burn when idle!).
      var want = (!reduced && tour.on && !drag) ? 1 : 0;
      cam.gain = want < cam.gain ? Math.max(0, cam.gain - dt * 3) : lerp(cam.gain, want, Math.min(1, dt * 2));
      if (cam.gain > 0.001) cam.sway += dt * 0.22;
    }
    function viewYaw() { return cam.yaw + cam.gain * 0.22 * Math.sin(cam.sway); }

    /* ------------------------------------------------ layout */
    var cssW = 1, cssH = 1, dpr = 1, devW = 1, devH = 1, maxDpr = narrow ? 1.5 : 1.75;
    var fit = { cx: 0, cy: 0, r: 100 };
    var scale = new Float32Array(2), off = new Float32Array(2);
    function measure() {
      var r = canvas.getBoundingClientRect();
      cssW = Math.max(1, r.width); cssH = Math.max(1, r.height);
      fit.cx = cssW / 2; fit.cy = cssH / 2;
      fit.r = Math.max(60, Math.min(cssW, cssH) / 2 * 0.82);
      dpr = Math.min(maxDpr, window.devicePixelRatio || 1);
      devW = Math.max(1, Math.round(cssW * dpr)); devH = Math.max(1, Math.round(cssH * dpr));
      if (canvas.width !== devW || canvas.height !== devH) { canvas.width = devW; canvas.height = devH; resizeTargets(); }
      kick();
    }
    function computeScale() {
      var R = fit.r / 1.12 * cam.zoom;
      scale[0] = R / (cssW / 2); scale[1] = R / (cssH / 2);
      off[0] = 0; off[1] = 0.04;
      return R;
    }
    function project(p, out) {
      var M = rot;
      var x = M[0] * p[0] + M[3] * p[1] + M[6] * p[2];
      var y = M[1] * p[0] + M[4] * p[1] + M[7] * p[2];
      var z = M[2] * p[0] + M[5] * p[1] + M[8] * p[2];
      var k = DIST / (DIST - z);
      out[0] = ((x * k * scale[0] + off[0]) * 0.5 + 0.5) * cssW;
      out[1] = (0.5 - (y * k * scale[1] + off[1]) * 0.5) * cssH;
      out[2] = z;
      return out;
    }

    /* ------------------------------------------------ GL setup */
    var gl = null, isGL2 = false, mode = 'none';
    var prog = {}, buf = {}, target = null;
    function compile(type, src) {
      var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.warn(gl.getShaderInfoLog(s)); return null; }
      return s;
    }
    function program(vs, fs, attrs, unis) {
      var v = compile(gl.VERTEX_SHADER, vs), f = compile(gl.FRAGMENT_SHADER, fs);
      if (!v || !f) return null;
      var p = gl.createProgram(); gl.attachShader(p, v); gl.attachShader(p, f); gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) { console.warn(gl.getProgramInfoLog(p)); return null; }
      var o = { p: p, a: {}, u: {} };
      attrs.forEach(function (a) { o.a[a] = gl.getAttribLocation(p, a); });
      unis.forEach(function (u) { o.u[u] = gl.getUniformLocation(p, u); });
      return o;
    }
    var CAM_U = ['uRot', 'uScale', 'uOff', 'uDist'];
    function initGL() {
      var opts = { antialias: true, alpha: false, premultipliedAlpha: false, preserveDrawingBuffer: false, powerPreference: 'default' };
      try { gl = canvas.getContext('webgl2', opts); isGL2 = !!gl; if (!gl) gl = canvas.getContext('webgl', opts) || canvas.getContext('experimental-webgl', opts); } catch (e) { gl = null; }
      if (!gl) return false;
      target = makeTarget(4, 4);
      var fsPts = target ? FS_POINTS : FS_POINTS_DIRECT;
      prog.pts = program(VS_POINTS, fsPts, ['aFrom', 'aTo', 'aWF', 'aWT', 'aSeed', 'aDir'],
        CAM_U.concat(['uMix', 'uStag', 'uDrift', 'uSag', 'uPx', 'uEnergy', 'uShadow', 'uFloor', 'uLight']));
      prog.tone = target ? program(VS_QUAD, FS_TONE, ['aP'], ['uTex', 'uRes', 'uExpo', 'uDust', 'uLight']) : null;
      prog.lines = program(VS_LINES, FS_LINES, ['aA', 'aB', 'aT', 'aCol', 'aW'], CAM_U.concat(['uRes', 'uAlpha']));
      prog.spr = program(VS_SPRITES, FS_SPRITES, ['aP', 'aS', 'aC'], CAM_U.concat(['uDpr', 'uAlpha']));
      if (!prog.pts || !prog.lines || !prog.spr || (target && !prog.tone)) { gl = null; return false; }
      ['from', 'to', 'wf', 'wt', 'seed', 'dir', 'quad', 'lines', 'spr', 'dyn'].forEach(function (k) { buf[k] = gl.createBuffer(); });
      upload('seed', seeds); upload('dir', dirs);
      upload('quad', new Float32Array([-1, -1, 3, -1, -1, 3]));
      mode = target ? 'gl' : 'gl-direct';
      canvas.addEventListener('webglcontextlost', function (e) { e.preventDefault(); lost(); }, false);
      return true;
    }
    function upload(k, arr) { gl.bindBuffer(gl.ARRAY_BUFFER, buf[k]); gl.bufferData(gl.ARRAY_BUFFER, arr, gl.DYNAMIC_DRAW); }
    function makeTarget(w, h) {
      var type = null, internal = null;
      if (isGL2) {
        if (!gl.getExtension('EXT_color_buffer_float') && !gl.getExtension('EXT_color_buffer_half_float')) return null;
        type = gl.HALF_FLOAT; internal = gl.RGBA16F;
      } else {
        var ext = gl.getExtension('OES_texture_half_float');
        gl.getExtension('EXT_color_buffer_half_float');
        if (!ext) return null;
        type = ext.HALF_FLOAT_OES; internal = gl.RGBA;
      }
      var tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, internal, w, h, 0, gl.RGBA, type, null);
      var fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
      var ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      if (!ok) { gl.deleteTexture(tex); gl.deleteFramebuffer(fbo); return null; }
      return { tex: tex, fbo: fbo, type: type, internal: internal, w: w, h: h };
    }
    function resizeTargets() {
      if (!gl || !target) return;
      gl.bindTexture(gl.TEXTURE_2D, target.tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, target.internal, devW, devH, 0, gl.RGBA, target.type, null);
      target.w = devW; target.h = devH;
    }
    function attrib(p, name, k, size) {
      var loc = p.a[name]; if (loc < 0) return;
      gl.bindBuffer(gl.ARRAY_BUFFER, buf[k]); gl.enableVertexAttribArray(loc);
      gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
    }
    function camUniforms(p) {
      gl.uniformMatrix3fv(p.u.uRot, false, rot);
      gl.uniform2fv(p.u.uScale, scale); gl.uniform2fv(p.u.uOff, off); gl.uniform1f(p.u.uDist, DIST);
    }
    function disableAll() { for (var i = 0; i < 8; i++) gl.disableVertexAttribArray(i); }

    /* ------------------------------------------------ overlays */
    var ov = { lines: 0, spr: 0, labels: [], alpha: 0, t0: 0 };
    var lineData = null, sprData = null;
    function dashify(pts, dash) {
      var out = [], on = dash[0], offL = dash[1], acc = 0, state = true, cur = [pts[0]];
      for (var i = 1; i < pts.length; i++) {
        var a = pts[i - 1], b = pts[i];
        var dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2], L = Math.sqrt(dx * dx + dy * dy + dz * dz), s = 0;
        while (s < L) {
          var lim = state ? on : offL, room = lim - acc, step = Math.min(room, L - s);
          s += step; acc += step;
          var q = [a[0] + dx * s / L, a[1] + dy * s / L, a[2] + dz * s / L];
          if (state) cur.push(q);
          if (acc >= lim - 1e-9) {
            if (state) { if (cur.length > 1) out.push(cur); }
            state = !state; acc = 0; cur = state ? [q] : null;
          }
        }
      }
      if (state && cur && cur.length > 1) out.push(cur);
      return out;
    }
    function buildOverlay(o) {
      o = o || {};
      var polys = [];
      (o.lines || []).forEach(function (l) {
        var pts = l.pts;
        if (l.closed) pts = pts.concat([pts[0]]);
        if (l.dash) dashify(pts, l.dash).forEach(function (d) { polys.push({ pts: d, col: l.col, w: l.w }); });
        else polys.push({ pts: pts, col: l.col, w: l.w });
      });
      var segs = 0;
      polys.forEach(function (p) { segs += Math.max(0, p.pts.length - 1); });
      lineData = new Float32Array(segs * 6 * 13);
      var j = 0;
      var corners = [[0, -1], [1, -1], [1, 1], [0, -1], [1, 1], [0, 1]];
      polys.forEach(function (p) {
        var c = p.col || OX.C.steel, w = (p.w || 1) * dpr;
        for (var i = 0; i < p.pts.length - 1; i++) {
          var A = p.pts[i], B = p.pts[i + 1];
          for (var v = 0; v < 6; v++) {
            lineData[j++] = A[0]; lineData[j++] = A[1]; lineData[j++] = A[2];
            lineData[j++] = B[0]; lineData[j++] = B[1]; lineData[j++] = B[2];
            lineData[j++] = corners[v][0]; lineData[j++] = corners[v][1];
            lineData[j++] = c[0]; lineData[j++] = c[1]; lineData[j++] = c[2]; lineData[j++] = c[3];
            lineData[j++] = w;
          }
        }
      });
      ov.lines = segs * 6;
      var sp = o.points || [];
      sprData = new Float32Array(sp.length * 8);
      sp.forEach(function (s, i) {
        var c = s.col || OX.C.pale;
        sprData.set([s.p[0], s.p[1], s.p[2], s.s || 6, c[0], c[1], c[2], c[3]], i * 8);
      });
      ov.spr = sp.length;
      if (gl) {
        gl.bindBuffer(gl.ARRAY_BUFFER, buf.lines); gl.bufferData(gl.ARRAY_BUFFER, lineData, gl.DYNAMIC_DRAW);
        gl.bindBuffer(gl.ARRAY_BUFFER, buf.spr); gl.bufferData(gl.ARRAY_BUFFER, sprData, gl.DYNAMIC_DRAW);
      }
      var frag = document.createDocumentFragment();
      ov.labels = (o.labels || []).map(function (L) {
        var d = el('div', 'lab ' + (L.cls || ''), L.html !== undefined ? L.html : '');
        if (L.html === undefined) d.textContent = L.t;
        frag.appendChild(d);
        return { p: L.p, node: d, w: 0 };
      });
      layer.textContent = '';
      layer.appendChild(frag);
      // Batch measure label widths once outside the RAF loop (zero layout thrashing).
      for (var k = 0; k < ov.labels.length; k++) {
        ov.labels[k].w = ov.labels[k].node.offsetWidth || 40;
      }
      kick();
    }
    var tmp = new Float32Array(3);
    function placeLabels() {
      for (var i = 0; i < ov.labels.length; i++) {
        var L = ov.labels[i];
        project(L.p, tmp);
        var half = L.w / 2 + 4;
        var vis = tmp[0] > half && tmp[0] < cssW - half && tmp[1] > 10 && tmp[1] < cssH - 10;
        L.node.style.transform = 'translate3d(' + tmp[0].toFixed(1) + 'px,' + tmp[1].toFixed(1) + 'px,0)';
        L.node.style.opacity = vis ? (ov.alpha * clamp(0.78 + tmp[2] * 0.26, 0.56, 1)).toFixed(3) : '0';
      }
    }
    function lines2D(ctx2) {
      if (!lineData) return;
      ctx2.save(); ctx2.globalAlpha = ov.alpha;
      var a = new Float32Array(3), b = new Float32Array(3);
      for (var j = 0; j < lineData.length; j += 78) {
        project([lineData[j], lineData[j + 1], lineData[j + 2]], a);
        project([lineData[j + 3], lineData[j + 4], lineData[j + 5]], b);
        ctx2.strokeStyle = 'rgba(' + Math.round(lineData[j + 8] * 255) + ',' + Math.round(lineData[j + 9] * 255) + ',' + Math.round(lineData[j + 10] * 255) + ',' + lineData[j + 11] + ')';
        ctx2.lineWidth = lineData[j + 12];
        ctx2.beginPath(); ctx2.moveTo(a[0] * dpr, a[1] * dpr); ctx2.lineTo(b[0] * dpr, b[1] * dpr); ctx2.stroke();
      }
      ctx2.restore();
    }

    /* ------------------------------------------------ morph */
    function mixAt(t) { return morph.dur > 0 ? clamp((t - morph.t0) / morph.dur, 0, 1) : 1; }
    function snapshot(t) {
      var m = mixAt(t);
      if (m >= 1) { from.set(to); wFrom.set(wTo); return; }
      var st = morph.stag, inv = 1 / Math.max(1 - st, 1e-3), dr = morph.drift, sg = morph.sag;
      for (var i = 0; i < N; i++) {
        var p = (m - seeds[i] * st) * inv; p = p < 0 ? 0 : p > 1 ? 1 : p;
        var e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
        var a = Math.sin(Math.PI * e), j = 3 * i;
        from[j] += (to[j] - from[j]) * e + dirs[j] * dr * a;
        from[j + 1] += (to[j + 1] - from[j + 1]) * e + dirs[j + 1] * dr * a - sg * a;
        from[j + 2] += (to[j + 2] - from[j + 2]) * e + dirs[j + 2] * dr * a;
        wFrom[i] += (wTo[i] - wFrom[i]) * e;
      }
    }
    function uploadAll() { if (!gl) return; upload('from', from); upload('to', to); upload('wf', wFrom); upload('wt', wTo); }
    function morphTo(pos, warm, kind) {
      var t = clock();
      if (reduced || kind === 'instant') {
        to.set(pos); wTo.set(warm); from.set(pos); wFrom.set(warm); morph.dur = 0;
        if (kind !== 'instant') fade = { t0: t, dur: 0.35 };
      } else {
        snapshot(t);
        to.set(pos); wTo.set(warm);
        if (kind === 'plate') { morph.dur = 0.85; morph.stag = 0.24; morph.drift = 0.05; morph.sag = 0.03; }
        else { morph.dur = 0.50; morph.stag = 0.10; morph.drift = 0.01; morph.sag = 0; }
        morph.t0 = t;
      }
      uploadAll(); kick();
    }
    function setLive(pos, warm) {
      to.set(pos); wTo.set(warm); from.set(pos); wFrom.set(warm); morph.dur = 0;
      uploadAll(); kick();
    }

    /* ------------------------------------------------ drawing */
    function energyFor(R) {
      var pl = plates[active] || {};
      var Rdev = R * dpr, px = POINT_PX * dpr * (pl.pointScale || 1);
      var lightBoost = isLight ? 1.22 : 1.0;
      return 2.4 * lightBoost * (pl.exposure || 1) * (Rdev * Rdev) / (N * px * px);
    }
    function drawGL(t, count) {
      var R = computeScale();
      rotMatrix(viewYaw(), cam.pitch, rot);
      var pl = plates[active] || {};
      var m = mixAt(t), energy = energyFor(R);
      var px = POINT_PX * dpr * (pl.pointScale || 1);
      var dust = 1;
      if (fade) { var f = clamp((t - fade.t0) / fade.dur, 0, 1); dust = f < 0.4 ? 1 - f / 0.4 : (f - 0.4) / 0.6; if (f >= 1) fade = null; }
      if (sweep) dust *= 0.30 + 0.70 * easeOut(clamp((t - sweep.t0) / sweep.dur, 0, 1));
      gl.disable(gl.DEPTH_TEST);
      var P = prog.pts;
      if (target) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, target.fbo);
        gl.viewport(0, 0, devW, devH);
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
      } else {
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        gl.viewport(0, 0, devW, devH);
        if (isLight) gl.clearColor(0.984, 0.976, 0.957, 1);
        else gl.clearColor(0.035, 0.059, 0.102, 1);
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.enable(gl.BLEND);
        if (isLight) gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        else gl.blendFunc(gl.ONE, gl.ONE);
      }
      gl.useProgram(P.p);
      disableAll();
      attrib(P, 'aFrom', 'from', 3); attrib(P, 'aTo', 'to', 3); attrib(P, 'aWF', 'wf', 1); attrib(P, 'aWT', 'wt', 1);
      attrib(P, 'aSeed', 'seed', 1); attrib(P, 'aDir', 'dir', 3);
      camUniforms(P);
      gl.uniform1f(P.u.uMix, m); gl.uniform1f(P.u.uStag, morph.stag); gl.uniform1f(P.u.uDrift, morph.drift); gl.uniform1f(P.u.uSag, morph.sag);
      gl.uniform1f(P.u.uPx, px); gl.uniform1f(P.u.uFloor, FLOOR);
      if (P.u.uLight !== null && P.u.uLight !== undefined) gl.uniform1f(P.u.uLight, isLight ? 1.0 : 0.0);
      var e = target ? energy : energy * dust;
      if (pl.shadow !== false && shadowOn) {
        gl.uniform1f(P.u.uShadow, 1); gl.uniform1f(P.u.uEnergy, e * 0.28);
        gl.drawArrays(gl.POINTS, 0, count);
      }
      gl.uniform1f(P.u.uShadow, 0); gl.uniform1f(P.u.uEnergy, e);
      gl.drawArrays(gl.POINTS, 0, count);
      disableAll();
      if (target) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        gl.viewport(0, 0, devW, devH);
        gl.disable(gl.BLEND);
        var T = prog.tone;
        gl.useProgram(T.p);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, target.tex);
        gl.uniform1i(T.u.uTex, 0); gl.uniform2f(T.u.uRes, devW, devH);
        gl.uniform1f(T.u.uExpo, 1.0); gl.uniform1f(T.u.uDust, dust); gl.uniform1f(T.u.uLight, isLight ? 1.0 : 0.0);
        attrib(T, 'aP', 'quad', 2);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        disableAll();
      }
      // overlay lines
      gl.enable(gl.BLEND);
      if (ov.lines) {
        var Lp = prog.lines;
        gl.useProgram(Lp.p);
        gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
        camUniforms(Lp); gl.uniform2f(Lp.u.uRes, devW, devH); gl.uniform1f(Lp.u.uAlpha, ov.alpha);
        gl.bindBuffer(gl.ARRAY_BUFFER, buf.lines);
        var stride = 13 * 4;
        [['aA', 3, 0], ['aB', 3, 3], ['aT', 2, 6], ['aCol', 4, 8], ['aW', 1, 12]].forEach(function (a) {
          var loc = Lp.a[a[0]]; if (loc < 0) return;
          gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, a[1], gl.FLOAT, false, stride, a[2] * 4);
        });
        gl.drawArrays(gl.TRIANGLES, 0, ov.lines);
        disableAll();
      }
      // sprites (markers and live all-reduce packets)
      var dyn = pl.animate ? pl.animate(t, params[active], ctx) : null;
      if (ov.spr || (dyn && dyn.count)) {
        var S = prog.spr;
        gl.useProgram(S.p);
        gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
        camUniforms(S); gl.uniform1f(S.u.uDpr, dpr);
        var drawSpr = function (k, n, alpha) {
          gl.uniform1f(S.u.uAlpha, alpha);
          gl.bindBuffer(gl.ARRAY_BUFFER, buf[k]);
          [['aP', 3, 0], ['aS', 1, 3], ['aC', 4, 4]].forEach(function (a) {
            var loc = S.a[a[0]]; if (loc < 0) return;
            gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, a[1], gl.FLOAT, false, 32, a[2] * 4);
          });
          gl.drawArrays(gl.POINTS, 0, n);
          disableAll();
        };
        if (ov.spr) drawSpr('spr', ov.spr, ov.alpha);
        if (dyn && dyn.count) {
          gl.bindBuffer(gl.ARRAY_BUFFER, buf.dyn); gl.bufferData(gl.ARRAY_BUFFER, dyn.data, gl.DYNAMIC_DRAW);
          drawSpr('dyn', dyn.count, 1);
        }
      }
      gl.disable(gl.BLEND);
      return !!(dyn && dyn.live);
    }

    // Canvas 2D fallback (theme-aware)
    var c2d = null, acc2 = null, img2 = null, sub = 1;
    function init2D() {
      try { c2d = canvas.getContext('2d'); } catch (e) { c2d = null; }
      if (!c2d) return false;
      mode = '2d'; sub = Math.max(1, Math.floor(N / 30000)); maxDpr = 1;
      return true;
    }
    function draw2D(t, count) {
      computeScale();
      rotMatrix(viewYaw(), cam.pitch, rot);
      if (!acc2 || acc2.length !== devW * devH) { acc2 = new Float32Array(devW * devH); img2 = c2d.createImageData(devW, devH); }
      acc2.fill(0);
      var m = mixAt(t), M = rot;
      for (var i = 0; i < count; i += sub) {
        var p = clamp((m - seeds[i] * morph.stag) / Math.max(1 - morph.stag, 1e-3), 0, 1), e = ease(p), j = 3 * i;
        var x = from[j] + (to[j] - from[j]) * e, y = from[j + 1] + (to[j + 1] - from[j + 1]) * e, z = from[j + 2] + (to[j + 2] - from[j + 2]) * e;
        var rx = M[0] * x + M[3] * y + M[6] * z, ry = M[1] * x + M[4] * y + M[7] * z, rz = M[2] * x + M[5] * y + M[8] * z;
        var k = DIST / (DIST - rz);
        var sx = ((rx * k * scale[0] + off[0]) * 0.5 + 0.5) * devW | 0, sy = ((0.5 - (ry * k * scale[1] + off[1]) * 0.5)) * devH | 0;
        if (sx >= 0 && sy >= 0 && sx < devW && sy < devH) acc2[sy * devW + sx] += 1;
      }
      var d = img2.data, kk = 0.24 * devW * devH / Math.max(1, count / sub) * (plates[active].exposure || 1);
      for (var q = 0, o = 0; q < acc2.length; q++, o += 4) {
        var L = 1 - Math.exp(-acc2[q] * kk);
        if (isLight) {
          d[o] = 251 - 210 * L; d[o + 1] = 249 - 185 * L; d[o + 2] = 244 - 140 * L; d[o + 3] = 255;
        } else {
          d[o] = 11 + 236 * L * (0.86 + 0.12 * L); d[o + 1] = 18 + 216 * L * (0.72 + 0.2 * L); d[o + 2] = 30 + 158 * L * L; d[o + 3] = 255;
        }
      }
      c2d.putImageData(img2, 0, 0);
      lines2D(c2d);
      return false;
    }

    /* ------------------------------------------------ render loop (strictly on demand) */
    var raf = 0, lastT = 0, inView = true, frames = 0, slowFrames = 0, shadowOn = !weak, packetsLive = false;
    function kick() { if (!raf && inView && !document.hidden) raf = requestAnimationFrame(frame); }
    function frame() {
      raf = 0;
      var t = clock(), realDt = Math.max(0, t - lastT), dt = Math.min(0.05, realDt); lastT = t;
      updateCamera(t, dt);
      if (paramAnim) stepParamAnim(t);
      var count = N;
      if (sweep) {
        var s = clamp((t - sweep.t0) / sweep.dur, 0, 1);
        count = Math.max(1, Math.floor(N * easeOut(s)));
        if (s >= 1) sweep = null;
      }
      var ovTarget = (morph.dur > 0 && mixAt(t) < 0.65) || sweep ? 0 : 1;
      ov.alpha = ovTarget < ov.alpha ? Math.max(0, ov.alpha - realDt * 5) : Math.min(1, ov.alpha + Math.min(realDt, 0.5) * 2.4);
      if (mode === 'gl' || mode === 'gl-direct') packetsLive = drawGL(t, count);
      else if (mode === '2d') packetsLive = draw2D(t, count);
      placeLabels();
      frames++;
      if (frames > 20 && frames < 100 && dt > 0.034) slowFrames++;
      if (frames === 100 && slowFrames > 35 && dpr > 1) { maxDpr = 1; shadowOn = false; measure(); }
      var moving = cam.target || Math.abs(cam.vy) > 0 || Math.abs(cam.vp) > 0 || drag || cam.gain > 0.001 ||
        mixAt(t) < 1 || sweep || fade || paramAnim || packetsLive || (ov.alpha > 0 && ov.alpha < 1);
      if (moving) kick();
    }

    /* ------------------------------------------------ input */
    var drag = null, pointers = {}, pinch = null;
    function bindInput() {
      canvas.addEventListener('pointerdown', function (e) {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
        var ids = Object.keys(pointers);
        if (ids.length === 2) {
          var a = pointers[ids[0]], b = pointers[ids[1]];
          pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), z: cam.zoom }; drag = null;
        } else {
          drag = { id: e.pointerId, x: e.clientX, y: e.clientY, t: performance.now(), type: e.pointerType };
        }
        try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
        cam.vy = cam.vp = 0; cam.target = null;
        touchInput(); hideHint(); kick();
      });
      canvas.addEventListener('pointermove', function (e) {
        if (!pointers[e.pointerId]) return;
        pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
        if (pinch) {
          var ids = Object.keys(pointers); if (ids.length < 2) return;
          var a = pointers[ids[0]], b = pointers[ids[1]];
          cam.zoom = clamp(pinch.z * Math.hypot(a.x - b.x, a.y - b.y) / Math.max(pinch.d, 1), 0.65, 2.5);
          kick(); return;
        }
        if (!drag || e.pointerId !== drag.id) return;
        var now = performance.now(), dx = e.clientX - drag.x, dy = e.clientY - drag.y, dtm = Math.max(1, now - drag.t);
        drag.x = e.clientX; drag.y = e.clientY; drag.t = now;
        cam.yaw += dx * 0.0062;
        if (drag.type !== 'touch') cam.pitch = clamp(cam.pitch + dy * 0.0045, -0.35, 1.3);
        cam.vy = dx * 0.0062 / (dtm / 1000) * 0.4; cam.vp = drag.type !== 'touch' ? dy * 0.0045 / (dtm / 1000) * 0.4 : 0;
        kick();
      });
      function endPointer(e) {
        delete pointers[e.pointerId];
        if (Object.keys(pointers).length < 2) pinch = null;
        if (drag && e.pointerId === drag.id) {
          if (performance.now() - drag.t > 80) { cam.vy = 0; cam.vp = 0; }
          drag = null;
        }
        kick();
      }
      canvas.addEventListener('pointerup', endPointer);
      canvas.addEventListener('pointercancel', endPointer);
      canvas.addEventListener('dblclick', function () { resetView(); });
      canvas.addEventListener('wheel', function (e) {
        if (!e.ctrlKey && !e.metaKey) return;
        e.preventDefault();
        cam.zoom = clamp(cam.zoom * Math.exp(-e.deltaY * 0.004), 0.65, 2.5);
        touchInput(); kick();
      }, { passive: false });
    }
    function resetView() { touchInput(); camEase(plates[active].view, reduced ? 0 : 0.65); kick(); }
    function zoomBy(f) { cam.target = null; cam.zoom = clamp(cam.zoom * f, 0.65, 2.5); touchInput(); kick(); }
    document.addEventListener('keydown', function (e) {
      if (e.metaKey || e.ctrlKey || e.altKey || !inView) return;
      var tg = e.target;
      if (tg && tg.closest && tg.closest('input, textarea, select, [role="slider"]')) return;
      var k = e.key, n = plates.length;
      if (k === 'ArrowRight') select((active + 1) % n);
      else if (k === 'ArrowLeft') select((active + n - 1) % n);
      else if (/^[1-9]$/.test(k) && +k <= n) select(+k - 1);
      else if (k === '+' || k === '=') zoomBy(1.14);
      else if (k === '-' || k === '_') zoomBy(1 / 1.14);
      else if (k === '0') resetView();
      else return;
      e.preventDefault(); stopTour();
    });
    if (ui.reset) ui.reset.addEventListener('click', resetView);
    if (ui.zoomIn) ui.zoomIn.addEventListener('click', function () { zoomBy(1.16); });
    if (ui.zoomOut) ui.zoomOut.addEventListener('click', function () { zoomBy(1 / 1.16); });
    if (ui.prev) ui.prev.addEventListener('click', function () { stopTour(); select((active + plates.length - 1) % plates.length); });
    if (ui.next) ui.next.addEventListener('click', function () { stopTour(); select((active + 1) % plates.length); });

    var hintHidden = false;
    function hideHint() { if (!hintHidden && ui.hint) { hintHidden = true; ui.hint.classList.add('gone'); } }

    /* ------------------------------------------------ parameters */
    function pdef(i, k) { return (plates[i].params || []).filter(function (d) { return d.k === k; })[0]; }
    function regenKey(i) {
      var o = {}, P = params[i];
      Object.keys(P).forEach(function (k) { var d = pdef(i, k); if (!d || d.regen !== false) o[k] = P[k]; });
      return JSON.stringify(o);
    }
    function getData(i) {
      var k = regenKey(i), c = cache[i];
      if (c && c.key === k) return c.promise;
      var pr = Promise.resolve().then(function () { return plates[i].generate(N, params[i], ctx); }).then(function (r) {
        metas[i] = r.meta || {};
        return r;
      });
      cache[i] = { key: k, promise: pr };
      return pr;
    }
    function fmtParam(d, v) {
      if (d.fmt) return d.fmt(v, ctx);
      if (d.type === 'int') return String(Math.round(v));
      return Number(v).toFixed(d.dec === undefined ? 2 : d.dec);
    }
    function quant(d, v) {
      if (d.type === 'log') return Math.pow(10, clamp(Math.log10(v), Math.log10(d.min), Math.log10(d.max)));
      v = clamp(v, d.min, d.max);
      if (d.type === 'int' || d.type === 'month') return Math.round(v);
      var s = d.step || 0.01; return Math.round(v / s) * s;
    }
    var regenTimer = 0, paramAnim = null;
    function setParam(i, k, v, opt) {
      opt = opt || {};
      var d = pdef(i, k); if (!d) { params[i][k] = v; return; }
      v = d.type === 'choice' ? v : quant(d, v);
      if (params[i][k] === v && !opt.force) return;
      params[i][k] = v;
      syncParamUI(i, k);
      if (i !== active) return;
      if (d.fast && plates[i].fast) {
        var r = plates[i].fast(N, params[i], ctx);
        metas[i] = r.meta || metas[i];
        cache[i] = { key: regenKey(i), promise: Promise.resolve(r) };
        setLive(r.pos, r.warm);
        refreshOverlay(); return;
      }
      if (d.regen === false) { refreshOverlay(); return; }
      clearTimeout(regenTimer);
      regenTimer = setTimeout(function () {
        var tok = selectToken;
        setBusy(true);
        getData(i).then(function (r) {
          if (tok !== selectToken || i !== active) return;
          setBusy(false);
          morphTo(r.pos, r.warm, 'param');
          refreshOverlay();
        });
      }, opt.now ? 0 : 100);
    }
    function animateParam(k, targetVal, dur) {
      var i = active, v0 = params[i][k];
      paramAnim = { i: i, k: k, v0: v0, v1: targetVal, t0: clock(), dur: reduced ? 0.01 : dur };
      kick();
    }
    function stepParamAnim(t) {
      var a = paramAnim, f = clamp((t - a.t0) / a.dur, 0, 1);
      if (a.i !== active) { paramAnim = null; return; }
      setParam(a.i, a.k, lerp(a.v0, a.v1, ease(f)), { force: true });
      if (f >= 1) paramAnim = null;
    }
    function texHTML(tex, display) {
      if (window.katex) {
        try {
          return window.katex.renderToString(tex, {
            displayMode: !!display, throwOnError: false, strict: 'ignore',
            trust: function (c) { return c.command === '\\htmlClass'; }
          });
        } catch (e) { /* fallback */ }
      }
      return '<code class="tex">' + tex.replace(/</g, '&lt;') + '</code>';
    }
    OX.util.tex = texHTML;
    function rangeOf(d) {
      if (d.type === 'log') return { mn: Math.log10(d.min), mx: Math.log10(d.max), st: 0.01, raw: function (v) { return Math.log10(v); }, val: function (r) { return Math.pow(10, r); } };
      var st = (d.type === 'int' || d.type === 'month') ? 1 : (d.step || 0.01);
      return { mn: d.min, mx: d.max, st: st, raw: function (v) { return v; }, val: function (r) { return r; } };
    }
    function syncParamUI(i, k) {
      if (i !== active || !ui.params) return;
      var row = ui.params.querySelector('.param[data-k="' + k + '"]'); if (!row) return;
      var d = pdef(i, k), v = params[i][k];
      if (d.type === 'choice') {
        row.querySelectorAll('button.choice').forEach(function (b, j) { b.setAttribute('aria-pressed', String(j === v)); });
        return;
      }
      var R = rangeOf(d), inp = row.querySelector('input'), out = row.querySelector('.pval'), raw = R.raw(v);
      out.innerHTML = fmtParam(d, v);
      if (+inp.value !== raw) inp.value = raw;
      inp.style.setProperty('--fill', (clamp((raw - R.mn) / (R.mx - R.mn), 0, 1) * 100).toFixed(1) + '%');
      inp.setAttribute('aria-valuetext', out.textContent);
    }
    function buildParams(i) {
      var box = ui.params; if (!box) return;
      box.textContent = '';
      var shown = (plates[i].params || []).filter(function (d) { return !d.hidden; });
      shown.forEach(function (d) {
        var row = el('div', 'param' + (d.type === 'choice' ? ' param-choice' : ''));
        row.dataset.k = d.k;
        var sym = d.tex ? texHTML(d.tex, false) : (d.sym || '');
        if (d.type === 'choice') {
          row.innerHTML = '<div class="prow"><span class="plabel">' + d.label + '</span></div>';
          var seg = el('div', 'seg');
          d.choices.forEach(function (c, j) {
            var b = el('button', 'choice', c); b.type = 'button';
            b.setAttribute('aria-pressed', String(params[i][d.k] === j));
            b.addEventListener('click', function () { stopTour(); setParam(i, d.k, j, { now: true }); });
            seg.appendChild(b);
          });
          row.appendChild(seg);
        } else {
          var R = rangeOf(d);
          row.innerHTML = '<div class="prow"><span class="sym">' + sym + '</span><span class="plabel">' + d.label + '</span>' +
            '<output class="pval" title="Double-click to reset"></output></div>' +
            '<input class="range" type="range" min="' + R.mn + '" max="' + R.mx + '" step="' + R.st + '">';
          var inp = row.querySelector('input');
          inp.setAttribute('aria-label', d.label);
          inp.addEventListener('input', function () { stopTour(); setParam(i, d.k, R.val(+inp.value)); });
          row.querySelector('.pval').addEventListener('dblclick', function () { setParam(i, d.k, d.value); });
        }
        row.addEventListener('mouseenter', function () { highlightEq(d.k, true); });
        row.addEventListener('mouseleave', function () { highlightEq(d.k, false); });
        box.appendChild(row);
        syncParamUI(i, d.k);
      });
      root.classList.toggle('no-controls', !shown.length && !(plates[i].actions || []).length);
    }
    function highlightEq(k, on) {
      if (!ui.eq) return;
      ui.eq.querySelectorAll('.pk-' + k).forEach(function (s) { s.classList.toggle('hl', on); });
    }
    function buildActions(i) {
      if (!ui.actions) return;
      ui.actions.textContent = '';
      (plates[i].actions || []).forEach(function (a) {
        var b = el('button', 'act', a.label); b.type = 'button'; b.dataset.k = a.k;
        b.addEventListener('click', function () { stopTour(); plates[i].action(a.k, params[i], ctx, b); });
        ui.actions.appendChild(b);
      });
    }
    function refreshOverlay() {
      if (active < 0) return;
      var pl = plates[active];
      buildOverlay(pl.overlay ? pl.overlay(params[active], metas[active], ctx) : null);
      if (ui.readout) ui.readout.innerHTML = pl.readout ? pl.readout(params[active], metas[active], ctx) : '';
    }

    /* ------------------------------------------------ grouped index, text, opt-in tour */
    function buildIndex() {
      if (!ui.index) return;
      ui.index.textContent = '';
      var groups = [], byName = {};
      plates.forEach(function (p, i) {
        var gname = p.group || 'Areas';
        if (!byName[gname]) {
          byName[gname] = { name: gname, items: [] };
          groups.push(byName[gname]);
        }
        byName[gname].items.push({ plate: p, index: i });
      });
      groups.forEach(function (g, gi) {
        var box = el('div', 'idx-group idx-group--' + g.items.length);
        box.dataset.groupIdx = String(gi);
        box.appendChild(el('div', 'idx-group-title', g.name));
        var list = el('div', 'idx-group-items');
        g.items.forEach(function (item) {
          var p = item.plate, i = item.index;
          var b = el('button', 'pl');
          b.type = 'button';
          b.dataset.plateIdx = String(i);
          b.innerHTML = '<span class="rn">' + p.numeral + '</span><span class="nm">' + p.field + '</span><span class="bar" aria-hidden="true"></span>';
          b.addEventListener('click', function () { stopTour(); select(i); });
          list.appendChild(b);
        });
        box.appendChild(list);
        ui.index.appendChild(box);
      });
    }
    function updateIndex() {
      if (!ui.index) return;
      ui.index.querySelectorAll('button.pl').forEach(function (b) {
        var i = +b.dataset.plateIdx;
        if (i === active) b.setAttribute('aria-current', 'true');
        else b.removeAttribute('aria-current');
        b.classList.remove('touring');
      });
      document.querySelectorAll('[data-goto]').forEach(function (b) {
        b.classList.toggle('is-active', +b.dataset.goto === active);
      });
    }
    var textTimer = 0;
    function setText(i) {
      var p = plates[i];
      var apply = function () {
        if (ui.numeral) ui.numeral.textContent = p.numeral;
        if (ui.field) ui.field.textContent = p.field;
        if (ui.title) ui.title.innerHTML = p.title;
        if (ui.credit) ui.credit.innerHTML = p.credit || '';
        if (ui.group) ui.group.textContent = p.group || '';
        if (ui.practice) ui.practice.innerHTML = p.practice || '';
        if (ui.offer) ui.offer.innerHTML = (p.offer || []).map(function (o) { return '<li>' + o + '</li>'; }).join('');
        if (ui.eq) ui.eq.innerHTML = p.eq ? texHTML(p.eq, true) : '';
        if (ui.eqkey) ui.eqkey.innerHTML = p.eqKey || '';
        if (ui.note) ui.note.innerHTML = p.note || '';
        buildParams(i); buildActions(i);
        if (ui.readout) ui.readout.innerHTML = (p.readout && i === active) ? p.readout(params[i], metas[i], ctx) : '';
        root.classList.remove('swapping');
        if (ui.live) ui.live.textContent = p.field + '. ' + p.titleText;
        canvas.setAttribute('aria-label', 'Interactive model for ' + p.field + '. ' + (p.alt || ''));
      };
      clearTimeout(textTimer);
      if (first || reduced) { apply(); return; }
      root.classList.add('swapping');
      textTimer = setTimeout(apply, 140);
    }
    function setBusy(b) {
      busy = b;
      root.classList.toggle('is-busy', b);
      if (ui.status) ui.status.textContent = b ? 'Computing…' : '';
    }

    // Auto-tour is strictly opt-in (off by default so it never hijacks reading!).
    var tour = { on: !reduced && cfg.tour === true, timer: 0, dwell: cfg.dwell || 14 };
    function syncTourButton() {
      if (!ui.tour) return;
      ui.tour.setAttribute('aria-pressed', String(tour.on));
      ui.tour.innerHTML = tour.on
        ? '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><rect x="3.5" y="3" width="3.2" height="10" rx="0.8" fill="currentColor"/><rect x="9.3" y="3" width="3.2" height="10" rx="0.8" fill="currentColor"/></svg><span>Pause tour</span>'
        : '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 3.2L12.5 8l-8 4.8V3.2z" fill="currentColor"/></svg><span>Auto-tour</span>';
    }
    function scheduleTour() {
      clearTimeout(tour.timer);
      if (!tour.on || !ui.index) return;
      var b = ui.index.querySelector('button.pl[data-plate-idx="' + active + '"]');
      if (b) { b.classList.remove('touring'); void b.offsetWidth; b.style.setProperty('--dwell', tour.dwell + 's'); b.classList.add('touring'); }
      tour.timer = setTimeout(function () { if (tour.on) select((active + 1) % plates.length, { tour: true }); }, tour.dwell * 1000);
      kick();
    }
    function stopTour() {
      if (!tour.on) return;
      tour.on = false; clearTimeout(tour.timer); syncTourButton();
      if (ui.index) ui.index.querySelectorAll('button.pl').forEach(function (b) { b.classList.remove('touring'); });
    }
    if (ui.tour) ui.tour.addEventListener('click', function () {
      tour.on = !tour.on; syncTourButton();
      if (tour.on) scheduleTour(); else stopTour();
    });

    /* ------------------------------------------------ selection */
    var selectToken = 0;
    function select(i, opt) {
      opt = opt || {};
      if (i === active && !opt.force) return;
      var tok = ++selectToken, wasFirst = first;
      active = i;
      paramAnim = null;
      updateIndex(); setText(i);
      if (!wasFirst) setBusy(true);
      if (cfg.hash !== false && !wasFirst) {
        try { history.replaceState(null, '', '#' + plates[i].id); } catch (e) { /* file preview */ }
      }
      getData(i).then(function (r) {
        if (tok !== selectToken) return;
        setBusy(false);
        if (wasFirst) {
          first = false;
          to.set(r.pos); wTo.set(r.warm); from.set(r.pos); wFrom.set(r.warm); morph.dur = 0; uploadAll();
          camEase(plates[i].view, 0);
          sweep = reduced ? null : { t0: clock(), dur: 0.65 };
        } else {
          morphTo(r.pos, r.warm, 'plate');
          camEase(plates[i].view, reduced ? 0 : 0.85);
        }
        refreshOverlay();
        if (tour.on) scheduleTour();
        kick();
      });
    }

    /* ------------------------------------------------ context for plates */
    var ctx = {
      get N() { return N; },
      util: OX.util,
      C: OX.C,
      FLOOR: FLOOR,
      setParam: function (k, v, o) { setParam(active, k, v, o); },
      animateParam: animateParam,
      regen: function () { cache[active] = null; setParam(active, 'seed', params[active].seed, { force: true, now: true }); },
      refresh: refreshOverlay,
      kick: kick,
      clock: clock,
      params: function () { return params[active]; },
      readout: function (html) { if (ui.readout) ui.readout.innerHTML = html; },
      reduced: function () { return reduced; }
    };
    plates.forEach(function (p) {
      p.params = p.params || [];
      if (!p.params.some(function (d) { return d.k === 'seed'; })) p.params.push({ k: 'seed', value: 1, hidden: true, type: 'int', min: 1, max: 1e9 });
      p.titleText = (p.title || '').replace(/<[^>]+>/g, '');
    });

    /* ------------------------------------------------ boot */
    buildIndex(); syncTourButton();
    document.querySelectorAll('[data-goto]').forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.preventDefault(); stopTour();
        var targetEl = document.getElementById('workbench') || root;
        targetEl.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
        select(+b.dataset.goto);
      });
    });
    function lost() { mode = 'none'; root.classList.add('no-gl'); }
    if (!initGL()) {
      gl = null;
      var fresh = canvas.cloneNode(false);
      canvas.parentNode.replaceChild(fresh, canvas); canvas = fresh;
      if (!init2D()) root.classList.add('no-gl');
      root.classList.add('is-2d');
    }
    bindInput();
    measure();
    var resizeTimer = 0;
    if (typeof ResizeObserver === 'function') {
      new ResizeObserver(function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () { measure(); if (active >= 0) refreshOverlay(); }, 50);
      }).observe(canvas);
    } else {
      window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () { measure(); if (active >= 0) refreshOverlay(); }, 50);
      });
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { inView = es[0].isIntersecting; if (inView) kick(); }, { threshold: 0.02 }).observe(canvas);
    }
    document.addEventListener('visibilitychange', function () { if (!document.hidden) kick(); });
    if (mq) {
      var onPref = function (e) { reduced = e.matches; if (reduced) stopTour(); };
      if (mq.addEventListener) mq.addEventListener('change', onPref); else if (mq.addListener) mq.addListener(onPref);
    }
    var start = 0, h = (location.hash || '').slice(1);
    plates.forEach(function (p, i) { if (p.id === h) start = i; });
    select(start, { force: true });

    activeInstance = {
      select: select,
      ctx: ctx,
      onThemeChange: function (lightNow) {
        isLight = lightNow;
        refreshOverlay();
        kick();
      }
    };
    return activeInstance;
  };
})();
