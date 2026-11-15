/* Oxlon home page: the ten plates in order, each framed as a field of work.
   The generators live in plates-a.js and plates-b.js; this file sets what the page says about them. */
(function () {
  'use strict';
  var OX = window.OX, all = {};
  (OX.PLATES_A || []).concat(OX.PLATES_B || []).forEach(function (p) { if (!all[p.id]) all[p.id] = p; });
  var ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
  var TEX = { rho: '\\rho', theta: '\\theta', sigma: '\\sigma', lam: '\\lambda', sw: '\\sigma_w', depth: 'L', date: 't', C: 'C', r: 'r', p: 'p', day: 't' };
  var EF = 'Economics and Finance', AD = 'AI and Data', MC = 'Mathematics and Computing';

  var META = [
    { id: 'forecasting', group: EF, field: 'Forecasting', title: 'A Fan of Futures',
      credit: 'Vector autoregression · simulated in real time',
      practice: 'We build forecasting systems for inflation, output, labour markets and asset prices, from nowcasts to full predictive distributions.',
      offer: ['Nowcasting', 'Density Forecasts', 'Scenario Analysis'],
      eq: String.raw`\begin{aligned} z_{t+1} &= A\,z_t + \htmlClass{pk-sigma}{\sigma}\,\varepsilon_{t+1} \\ A &= \htmlClass{pk-rho}{\rho}\begin{pmatrix} \cos\htmlClass{pk-theta}{\theta} & -\sin\htmlClass{pk-theta}{\theta} \\ \sin\htmlClass{pk-theta}{\theta} & \cos\htmlClass{pk-theta}{\theta} \end{pmatrix} \\ \varepsilon_{t+1} &\sim N(0,\,I) \end{aligned}`,
      eqKey: '<i>z</i> holds the inflation gap and the output gap. <i>ε</i> are the shocks.' },
    { id: 'inflation-unemployment', group: EF, field: 'Macroeconomic Analysis', title: 'Inflation, Unemployment and Their Futures',
      credit: 'US data since 1960 · VAR estimated in real time',
      practice: 'We model how prices, jobs and output move together and turn the models into scenarios for policy and planning.',
      offer: ['VAR and BVAR Models', 'Phillips Curves', 'Policy Scenarios'],
      eq: String.raw`\begin{aligned} z_{\htmlClass{pk-date}{t}} &= c + A_1 z_{t-1} + A_2 z_{t-2} + e_t \\ e_t &\sim N(0,\,\Sigma) \\ z_t &= (u_t,\ \pi_t)' \end{aligned}`,
      eqKey: '<i>u</i> is the unemployment rate and <i>π</i> is 12-month CPI inflation.' },
    { id: 'policy-rates', group: EF, field: 'Monetary Policy', title: 'Policy Rates of 28 Central Banks',
      credit: '28 central banks · monthly since 1990',
      practice: 'We analyse central bank decisions, how they pass through to the economy and how central banks communicate them.',
      offer: ['Policy Rates', 'Transmission', 'Central Bank Text'],
      eq: String.raw`\begin{aligned} h_{i,\htmlClass{pk-date}{t}} &= \operatorname{sign}(r_{i,t})\,\sqrt{|r_{i,t}|/57} \\ m_{\htmlClass{pk-date}{t}} &= \operatorname{median}_i\, r_{i,t} \end{aligned}`,
      eqKey: '<i>r</i> is the policy rate of central bank <i>i</i> at the end of month <i>t</i>, <i>h</i> the height of its ribbon and <i>m</i> the median across banks.' },
    { id: 'economic-analysis', group: EF, field: 'Economic and Financial Analysis', title: 'The US Yield Curve since 1990',
      credit: '442 monthly curves · Nelson and Siegel fit',
      practice: 'We analyse bond markets, asset prices and the economy behind them, from term-structure models to competition and market structure.',
      offer: ['Yield Curves', 'Asset Prices', 'Competition and Regulation'],
      eq: String.raw`\begin{aligned} y_{\htmlClass{pk-date}{t}}(\tau) &= \beta_{0t} + \beta_{1t}\,f_1(\tau) + \beta_{2t}\,f_2(\tau) \\ f_1(\tau) &= \frac{1-e^{-\lambda\tau}}{\lambda\tau} \\ f_2(\tau) &= f_1(\tau) - e^{-\lambda\tau} \end{aligned}`,
      eqKey: 'The three <i>β</i> are the level, slope and curvature of each month\'s curve, with <i>λ</i> = 0.0609 per month as in Diebold and Li (2006).' },
    { id: 'volatility', group: EF, field: 'Risk and Volatility', title: 'The VIX on Every Trading Day',
      credit: '9,316 trading days since 1990',
      practice: 'We measure financial risk, from market volatility and tail events to stress tests.',
      offer: ['Volatility Models', 'Tail Risk', 'Stress Testing'],
      eq: String.raw`\begin{aligned} \theta_{\htmlClass{pk-day}{t}} &= 2\pi\,\frac{\text{day}_t}{365.25} \\ \rho_{\htmlClass{pk-day}{t}} &= 0.1 + 0.8\sqrt{(\mathrm{VIX}_t - 9)/74} \end{aligned}`,
      eqKey: '<i>θ</i> is the angle round the coil, which turns once a year. <i>ρ</i> is the distance from its axis.' },
    { id: 'machine-learning', group: AD, field: 'Machine Learning', title: 'The Swiss Roll',
      credit: 'Manifold learning · after Tenenbaum, de Silva and Langford (2000)',
      practice: 'We train models that find structure in large economic, financial and administrative datasets, with or without labels.',
      offer: ['Classification', 'Clustering', 'Text as Data'],
      eq: String.raw`\begin{aligned} (x,y,z) &= (t\cos t,\ h,\ t\sin t) \\ t &\sim U\big(\tfrac{3\pi}{2},\tfrac{9\pi}{2}\big),\ \ h \sim U(0,21) \\ s(t) &= \textstyle\int_{3\pi/2}^{t}\sqrt{1+u^2}\,du \\ \kappa_{\htmlClass{pk-lam}{\lambda}} &= (1-\htmlClass{pk-lam}{\lambda})\,\kappa \end{aligned}`,
      eqKey: '<i>s</i> is distance along the sheet and <i>κ</i> its curvature while it unrolls.' },
    { id: 'deep-learning', group: AD, field: 'Deep Learning', title: 'A Circle through a Deep Network',
      credit: 'Random tanh network · after Poole et al. (2016)',
      practice: 'We design, train and deploy neural networks for time series, text, documents and images.',
      offer: ['Neural Networks', 'Language Models', 'Document AI'],
      eq: String.raw`\begin{aligned} h^{\ell} &= W^{\ell}\tanh(h^{\ell-1}) + b^{\ell},\ \ \ell \le \htmlClass{pk-depth}{L} \\ W^{\ell}_{ij} &\sim N\big(0,\ \htmlClass{pk-sw}{\sigma_w}^{2}/n\big) \\ \chi_1 &= \htmlClass{pk-sw}{\sigma_w}^{2}\textstyle\int Dz\,\big[\tanh'(\sqrt{q^*}\,z)\big]^2 \end{aligned}`,
      eqKey: 'Biases are drawn from N(0, 0.3²). With <i>χ</i><sub>1</sub> above one the network is chaotic, below one it is ordered.' },
    { id: 'ai-economy', group: AD, field: 'AI and the New Economy', title: 'A Production Function for Language Models',
      credit: 'Scaling law of Hoffmann et al. (2022)',
      practice: 'We study how AI changes work, firms and productivity and what its compute costs.',
      offer: ['AI Adoption', 'Labour Markets', 'Cost of Compute'],
      eq: String.raw`\begin{aligned} L(N,D) &= E + \frac{A}{N^{\alpha}} + \frac{B}{D^{\beta}} \\ \htmlClass{pk-C}{C} &\approx 6ND \\ N^{*} &= G\,(\htmlClass{pk-C}{C}/6)^{\beta/(\alpha+\beta)} \end{aligned}`,
      eqKey: '<i>N</i> counts parameters, <i>D</i> training tokens and <i>C</i> compute in FLOP.' },
    { id: 'mathematics', group: MC, field: 'Mathematics', title: 'The Logistic Map',
      credit: 'May (1976) · Feigenbaum (1978)',
      practice: 'Dynamical systems, optimisation, probability and numerical analysis sit under every model we build.',
      offer: ['Dynamical Systems', 'Optimisation', 'Numerical Methods'],
      eq: String.raw`\begin{aligned} x_{n+1} &= \htmlClass{pk-r}{r}\,x_n(1-x_n) \\ \delta &= \lim_{k\to\infty}\frac{r_k - r_{k-1}}{r_{k+1}-r_k} = 4.6692\ldots \\ \lambda(\htmlClass{pk-r}{r}) &= \lim_{n\to\infty}\tfrac{1}{n}\textstyle\sum_{k<n}\ln\lvert \htmlClass{pk-r}{r}(1-2x_k)\rvert \end{aligned}`,
      eqKey: '<i>δ</i> is Feigenbaum\'s constant and <i>λ</i> the Lyapunov exponent.' },
    { id: 'infrastructure', group: MC, field: 'Computing Infrastructure', title: 'A Torus of Accelerators',
      credit: 'Three-dimensional torus · ring all-reduce',
      practice: 'We build data pipelines, GPU computing and AI systems that run on an institution\'s own servers.',
      offer: ['Data Pipelines', 'GPU Clusters', 'On-Premise AI'],
      eq: String.raw`\begin{aligned} T_{\text{ring}} &= 2(p-1)\,\alpha + 2\,\tfrac{p-1}{p}\,n\,\beta \\ \text{steps} &= 6\,(\htmlClass{pk-p}{p}-1) \\ \text{chips} &= \htmlClass{pk-p}{p}^{3} \end{aligned}`,
      eqKey: '<i>α</i> is the latency of a message, <i>β</i> the time per number and <i>n</i> the numbers held by each chip.' }
  ];

  OX.PLATES_SITE = META.map(function (m, i) {
    var p = all[m.id];
    Object.keys(m).forEach(function (k) { if (k !== 'id') p[k] = m[k]; });
    p.numeral = ROMAN[i];
    (p.params || []).forEach(function (d) { if (TEX[d.k]) d.tex = TEX[d.k]; });
    return p;
  });
})();
