/* ============================================================
   Course catalogue — BSc Economics @ Qarabağ Universiteti
   Each entry powers the click-to-expand course modal.
   ============================================================ */

window.COURSES = {

  /* ───── Year 1 · Semester 1 ─────────────────────────────── */

  'ict-101': {
    code: 'GEN 101', credits: 4, type: 'Core',
    title: 'Information and Communication Technologies',
    semester: 'Year 1 · Semester 1',
    summary: 'A working command of the digital tools an economist relies on every day — spreadsheets, document workflows, citation managers and the responsible use of AI assistants.',
    outcomes: [
      'Build and audit non-trivial spreadsheet models using formulas, lookups and pivot tables',
      'Produce clean academic documents with LaTeX, Markdown and a reference manager',
      'Reason about file formats, version control and data hygiene in collaborative projects',
      'Use AI assistants critically as a study aid without outsourcing judgement'
    ],
    topics: ['Spreadsheets', 'LaTeX', 'Reference managers', 'Cloud workflows', 'Search & retrieval', 'AI literacy'],
    assessment: 'Portfolio 60% · Practical exam 40%'
  },

  'az-lang': {
    code: 'AZE 101', credits: 4, type: 'Core / Obligatory',
    title: 'Communication Skills in Azerbaijani Language',
    semester: 'Year 1 · Semester 1',
    summary: 'Refines written and spoken Azerbaijani for academic and professional registers, with emphasis on the vocabulary an economics undergraduate will need across the degree.',
    outcomes: [
      'Compose well-structured academic essays and reports in Azerbaijani',
      'Deliver fluent presentations on technical and policy topics',
      'Translate core economics terminology between Azerbaijani and English',
      'Read and summarise Azerbaijani policy documents and media accurately'
    ],
    topics: ['Academic writing', 'Public speaking', 'Translation', 'Policy register', 'Bilingual terminology'],
    assessment: 'Written exam 40% · Oral presentation 30% · Coursework 30%'
  },

  'eng-int-1': {
    code: 'ENG 101', credits: 6, type: 'Core / Obligatory',
    title: 'Intensive English I',
    semester: 'Year 1 · Semester 1',
    summary: 'Brings every student up to a confident B2 reading and listening baseline so the rest of the curriculum can be delivered in English without compromise.',
    outcomes: [
      'Read and summarise medium-length English texts on economic topics',
      'Take structured lecture notes in English at conversational speed',
      'Hold a 10-minute discussion on a current-affairs topic',
      'Pass a standardised B2-equivalent assessment'
    ],
    topics: ['Reading comprehension', 'Listening', 'Vocabulary building', 'Note-taking', 'Speaking fluency'],
    assessment: 'Continuous assessment 40% · Final exam 60%'
  },

  'eng-pra-1': {
    code: 'ENG 102', credits: 4, type: 'Core / Obligatory',
    title: 'Practical English I',
    semester: 'Year 1 · Semester 1',
    summary: 'A workshop companion to Intensive English I — drills the four skills against real economic texts: newspaper analysis, IMF briefs, central-bank statements.',
    outcomes: [
      'Identify economic argument structure in journalistic prose',
      'Write a 600-word op-ed in clear, well-edited English',
      'Engage in structured debate with citation of sources',
      'Use English-language economics dictionaries with confidence'
    ],
    topics: ['Op-ed writing', 'Debate', 'Press analysis', 'Pronunciation', 'Discipline-specific vocabulary'],
    assessment: 'Portfolio 50% · Oral assessment 30% · Quizzes 20%'
  },

  'glob-hist': {
    code: 'ECO 101', credits: 6, type: 'Core',
    title: 'Global Economic History',
    semester: 'Year 1 · Semester 1',
    summary: 'A long-arc tour from the agricultural revolution to the present financial system — the empirical canvas every theoretical model later in the degree will sit on top of.',
    outcomes: [
      'Narrate the divergence of living standards across regions over the last five centuries',
      'Identify the institutional pre-conditions for industrial take-off',
      'Compare historical episodes of globalisation, crisis and de-globalisation',
      'Locate Azerbaijan and the wider Caucasus in the global economic timeline'
    ],
    topics: ['Pre-industrial economies', 'Industrial Revolution', 'Imperialism & trade', 'Bretton Woods', '20th-century divergence', 'Caucasus economic history'],
    assessment: 'Mid-term essay 30% · Final essay 40% · Seminar participation 30%'
  },

  'eco-modern': {
    code: 'ECO 102', credits: 6, type: 'Core',
    title: 'Economics in the Modern World',
    semester: 'Year 1 · Semester 1',
    summary: 'The "science and art" of economics: what economists actually do, the questions the discipline can and cannot answer, and how the modern policy ecosystem is structured.',
    outcomes: [
      'Distinguish positive and normative economic claims',
      'Explain how central banks, treasuries and multilaterals interact',
      'Critically read a Financial Times or Economist article',
      'Pose a researchable economic question with a credible identification strategy in plain language'
    ],
    topics: ['What is economics?', 'Markets & states', 'Policy institutions', 'Globalisation', 'Climate & inequality', 'Reading economists'],
    assessment: 'Reading log 30% · Final essay 50% · Tutorial 20%'
  },

  /* ───── Year 1 · Semester 2 ─────────────────────────────── */

  'az-hist': {
    code: 'AZE 102', credits: 4, type: 'Core / Obligatory',
    title: 'Azerbaijani History & Culture',
    semester: 'Year 1 · Semester 2',
    summary: 'Anchors the economist-in-training in the political, cultural and territorial story of Azerbaijan — context for everything from energy economics to regional trade.',
    outcomes: [
      'Trace the political economy of the South Caucasus from antiquity to the present',
      'Identify cultural and institutional factors shaping modern Azerbaijan',
      'Discuss the economic significance of Karabakh and post-2020 reconstruction',
      'Write a short historical-economic case study with primary sources'
    ],
    topics: ['Caucasus antiquity', 'Khanates & empires', 'ADR & Soviet period', 'Independence economy', 'Karabakh reconstruction'],
    assessment: 'Exam 50% · Case-study essay 30% · Tutorial 20%'
  },

  'eng-int-2': {
    code: 'ENG 201', credits: 6, type: 'Core / Obligatory',
    title: 'Intensive English II',
    semester: 'Year 1 · Semester 2',
    summary: 'Builds from B2 toward a confident C1 — the level required to read research papers, follow lectures and write coursework in English from Year 2 onward.',
    outcomes: [
      'Read working papers and journal abstracts unaided',
      'Write a structured 1,500-word essay with citations',
      'Follow extended academic lectures and take usable notes',
      'Sit a C1-equivalent placement exam'
    ],
    topics: ['Academic reading', 'Argumentative writing', 'Listening for arguments', 'Advanced grammar', 'Discourse markers'],
    assessment: 'Continuous assessment 40% · Final exam 60%'
  },

  'eng-pra-2': {
    code: 'ENG 202', credits: 4, type: 'Core / Obligatory',
    title: 'Practical English II',
    semester: 'Year 1 · Semester 2',
    summary: 'Workshop second half — moves the student from "reading" economics in English to "doing" economics in English: presentations, white-papers, policy briefs.',
    outcomes: [
      'Deliver a 15-minute presentation on a current economic issue',
      'Write a one-page policy brief in standard policy register',
      'Chair and minute a meeting in English',
      'Edit peers\' writing constructively'
    ],
    topics: ['Policy brief writing', 'Presenting data', 'Meeting English', 'Peer review'],
    assessment: 'Portfolio 50% · Presentation 30% · Quizzes 20%'
  },

  'stats-intro': {
    code: 'ECO 201', credits: 6, type: 'Core',
    title: 'Introduction to Statistics with Python / R / Stata',
    semester: 'Year 1 · Semester 2',
    summary: 'A from-zero, hands-keyboard introduction to statistical thinking — the entry point to the data-and-code spine that runs the length of the degree.',
    outcomes: [
      'Manipulate, summarise and visualise real datasets in Python and R',
      'Apply descriptive statistics, hypothesis testing and confidence intervals correctly',
      'Read and replicate the empirical results of a short published paper',
      'Document and version-control a reproducible statistical project'
    ],
    topics: ['Descriptive stats', 'Probability basics', 'Sampling & inference', 'Hypothesis tests', 'Intro to Python & R', 'Reproducibility'],
    assessment: 'Lab portfolio 40% · Practical exam 30% · Project 30%'
  },

  'thought-hist': {
    code: 'ECO 202', credits: 6, type: 'Core',
    title: 'History of Economic Thought',
    semester: 'Year 1 · Semester 2',
    summary: 'From Smith to Stiglitz — the long argument about what an economy is for, told as a sequence of competing answers rather than a march toward consensus.',
    outcomes: [
      'Distinguish the central claims of classical, marginalist, Keynesian and modern schools',
      'Place a contemporary policy debate inside a longer intellectual lineage',
      'Read primary texts (Smith, Marx, Keynes, Friedman) at undergraduate depth',
      'Write a 2,000-word historiographical essay'
    ],
    topics: ['Classical economics', 'Marx', 'Marginalism', 'Keynes & macroeconomics', 'Chicago school', 'Modern heterodoxy'],
    assessment: 'Essay 40% · Final exam 40% · Seminar 20%'
  },

  /* ───── Year 2 · Semester 1 ─────────────────────────────── */

  'micro-1': {
    code: 'ECO 211', credits: 7, type: 'Core',
    title: 'Principles of Microeconomics',
    semester: 'Year 2 · Semester 1',
    summary: 'Households, firms, markets, prices. The standard first course in microeconomic reasoning — diagrams, intuitions and the algebra to back them.',
    outcomes: [
      'Derive demand and supply from consumer and firm optimisation',
      'Analyse market equilibrium, surplus and the welfare cost of intervention',
      'Reason about elasticity, externalities and public goods',
      'Solve quantitative problem sets using calculus tools'
    ],
    topics: ['Consumer theory', 'Firm theory', 'Market structure', 'Welfare', 'Externalities', 'Game-theory primer'],
    assessment: 'Problem sets 30% · Mid-term 25% · Final 45%'
  },

  'macro-1': {
    code: 'ECO 212', credits: 7, type: 'Core',
    title: 'Principles of Macroeconomics',
    semester: 'Year 2 · Semester 1',
    summary: 'Aggregates: output, employment, inflation, the balance of payments. The toolkit for reading central-bank statements and IMF country reports.',
    outcomes: [
      'Define and decompose GDP, inflation and unemployment',
      'Use AS-AD and IS-LM models to analyse short-run fluctuations',
      'Explain the mechanics of monetary and fiscal policy',
      'Interpret real-time macro data for Azerbaijan and comparator economies'
    ],
    topics: ['National accounts', 'Money & banking', 'AS-AD', 'IS-LM', 'Open economy basics', 'Business cycles'],
    assessment: 'Problem sets 30% · Mid-term 25% · Final 45%'
  },

  'maths-eco': {
    code: 'MAT 211', credits: 6, type: 'Core',
    title: 'Essential Maths for Economics',
    semester: 'Year 2 · Semester 1',
    summary: 'The mathematical machinery — calculus, linear algebra, basic optimisation — that the intermediate and econometrics sequence will assume from Day 1.',
    outcomes: [
      'Differentiate and integrate functions used in economic models',
      'Work with matrices, eigenvectors and systems of linear equations',
      'Solve unconstrained and constrained optimisation problems',
      'Translate verbal economic problems into formal mathematical statements'
    ],
    topics: ['Calculus (single & multi-variable)', 'Linear algebra', 'Lagrangians', 'Difference & differential equations'],
    assessment: 'Weekly problem sets 30% · Mid-term 25% · Final 45%'
  },

  'research-methods': {
    code: 'ECO 213', credits: 4, type: 'Core',
    title: 'Research Methods & Academic Writing in Economics',
    semester: 'Year 2 · Semester 1',
    summary: 'How economists construct, test and report empirical claims — and how to write the result up so that another economist could replicate it.',
    outcomes: [
      'Move from research question to identification strategy to dataset',
      'Critique the empirical strategy of a published paper',
      'Structure an economics research paper (intro, lit, data, results, conclusion)',
      'Pre-register and document a small-scale empirical exercise'
    ],
    topics: ['Research design', 'Causality vs. correlation', 'Replication', 'Pre-registration', 'Writing & figures'],
    assessment: 'Research proposal 50% · Replication exercise 30% · Seminar 20%'
  },

  'data-1': {
    code: 'DAT 211', credits: 6, type: 'Core · Data Spine',
    title: 'Economics Data Lab & Programming: Fundamentals',
    semester: 'Year 2 · Semester 1',
    summary: 'Stage 1 of the four-semester data spine. Python and the modern data stack as a fluent second language for the working economist.',
    outcomes: [
      'Write idiomatic Python for data cleaning, joining and reshaping',
      'Produce publication-grade charts in matplotlib / seaborn / ggplot',
      'Build a reproducible pipeline with git, virtual environments and notebooks',
      'Scrape and clean a small economic dataset from public sources'
    ],
    topics: ['Python fundamentals', 'pandas', 'Tidy data', 'Visualisation', 'Web scraping basics', 'Git & reproducibility'],
    assessment: 'Lab portfolio 50% · Capstone notebook 50%'
  },

  /* ───── Year 2 · Semester 2 ─────────────────────────────── */

  'micro-2': {
    code: 'ECO 221', credits: 7, type: 'Core',
    title: 'Intermediate Microeconomics',
    semester: 'Year 2 · Semester 2',
    summary: 'The intermediate sequence: a rigorous, calculus-based treatment of consumer, firm and market theory, with a first pass at information economics.',
    outcomes: [
      'Derive Marshallian and Hicksian demand and use Slutsky decomposition',
      'Analyse firm behaviour under different market structures formally',
      'Treat uncertainty, expected utility and basic asymmetric-information problems',
      'Solve general-equilibrium problems in small economies'
    ],
    topics: ['Consumer choice', 'Producer theory', 'Imperfect competition', 'Uncertainty', 'Asymmetric information', 'GE basics'],
    assessment: 'Problem sets 30% · Mid-term 25% · Final 45%'
  },

  'macro-2': {
    code: 'ECO 222', credits: 7, type: 'Core',
    title: 'Intermediate Macroeconomics',
    semester: 'Year 2 · Semester 2',
    summary: 'Dynamic macroeconomics: growth models, intertemporal choice and a first encounter with the New-Keynesian framework underlying modern central banking.',
    outcomes: [
      'Work with Solow, Ramsey and OLG growth models',
      'Analyse intertemporal consumption and savings behaviour',
      'Set up and interpret a basic New-Keynesian model',
      'Read a central-bank inflation report critically'
    ],
    topics: ['Growth theory', 'Intertemporal choice', 'Real business cycles', 'New-Keynesian basics', 'Monetary policy rules'],
    assessment: 'Problem sets 30% · Mid-term 25% · Final 45%'
  },

  'econ-1': {
    code: 'ECO 223', credits: 7, type: 'Core',
    title: 'Econometrics I — Cross-Sectional',
    semester: 'Year 2 · Semester 2',
    summary: 'The OLS workhorse from first principles: assumptions, diagnostics, departures. The course that turns "regression" from a word into a tool.',
    outcomes: [
      'Derive the OLS estimator and interpret its properties',
      'Diagnose and correct heteroscedasticity, multicollinearity and mis-specification',
      'Use instrumental variables and difference-in-differences appropriately',
      'Replicate a published cross-sectional result in Python or Stata'
    ],
    topics: ['OLS', 'Gauss-Markov', 'Hypothesis testing', 'IV', 'Diff-in-diff', 'Limited dependent variables'],
    assessment: 'Problem sets 30% · Empirical project 30% · Final 40%'
  },

  'fin-risk': {
    code: 'FIN 221', credits: 5, type: 'Core',
    title: 'Financial Risk Management',
    semester: 'Year 2 · Semester 2',
    summary: 'A practitioner-oriented first course in financial risk — market, credit, liquidity — calibrated to the size and structure of the Azerbaijani financial system.',
    outcomes: [
      'Quantify and interpret VaR, expected shortfall and stress-test outputs',
      'Distinguish market, credit, liquidity and operational risk',
      'Build a small risk dashboard in Python for a sample portfolio',
      'Read a Basel-style supervisory disclosure'
    ],
    topics: ['Risk taxonomy', 'VaR & ES', 'Credit risk', 'Stress testing', 'Basel framework', 'Risk in EM banking'],
    assessment: 'Risk-dashboard project 40% · Mid-term 25% · Final 35%'
  },

  'data-2': {
    code: 'DAT 221', credits: 6, type: 'Core · Data Spine',
    title: 'Economics Data Lab & Programming: Machine Learning',
    semester: 'Year 2 · Semester 2',
    summary: 'Stage 2 of the data spine. The supervised- and unsupervised-learning toolkit, framed throughout as an extension of econometric thinking.',
    outcomes: [
      'Choose between regression, tree-based and kernel methods for an economic task',
      'Train, regularise and validate a model without leaking the test set',
      'Interpret ML output with SHAP / partial-dependence tools',
      'Compare an ML prediction to a structural-econometric one'
    ],
    topics: ['Supervised learning', 'Trees & forests', 'Regularisation', 'Cross-validation', 'Interpretability', 'Econ-ML interface'],
    assessment: 'Lab portfolio 40% · Kaggle-style competition 30% · Final report 30%'
  },

  /* ───── Year 3 · Semester 1 ─────────────────────────────── */

  'game-theory': {
    code: 'ECO 311', credits: 6, type: 'Core',
    title: 'Strategic Thinking & Game Theory',
    semester: 'Year 3 · Semester 1',
    summary: 'Decision-making when payoffs depend on what others do — from auction design to bargaining to the structure of international agreements.',
    outcomes: [
      'Solve simultaneous- and sequential-move games',
      'Apply Nash, subgame-perfect and Bayesian equilibrium concepts',
      'Design and analyse simple auctions and mechanisms',
      'Use game-theoretic reasoning to dissect a current policy story'
    ],
    topics: ['Nash equilibrium', 'Extensive-form games', 'Repeated games', 'Bayesian games', 'Auction & mechanism design'],
    assessment: 'Problem sets 30% · Game tournament 20% · Final 50%'
  },

  'int-fin': {
    code: 'FIN 311', credits: 6, type: 'Core',
    title: 'International Finance',
    semester: 'Year 3 · Semester 1',
    summary: 'Exchange rates, capital flows and the international monetary system — vital for an open, oil-exporting, emerging-market economy.',
    outcomes: [
      'Explain spot, forward and option pricing in FX markets',
      'Analyse balance-of-payments dynamics and currency crises',
      'Compare exchange-rate regimes and their macroeconomic implications',
      'Interpret SDR, IMF and BIS reports'
    ],
    topics: ['FX markets', 'Parity conditions', 'Currency crises', 'Exchange-rate regimes', 'International monetary system'],
    assessment: 'Problem sets 30% · Mid-term 25% · Final 45%'
  },

  'econ-2': {
    code: 'ECO 312', credits: 7, type: 'Core',
    title: 'Econometrics II — Time-Series',
    semester: 'Year 3 · Semester 1',
    summary: 'The time dimension: from autocorrelation and stationarity to ARIMA, VARs and the structural identification of macroeconomic shocks.',
    outcomes: [
      'Test for and handle non-stationarity and cointegration',
      'Estimate and forecast with ARIMA and VAR models',
      'Identify structural shocks using sign restrictions or Cholesky',
      'Produce a publication-quality forecast for an Azerbaijani macro series'
    ],
    topics: ['Stationarity', 'ARIMA', 'VAR & SVAR', 'Cointegration', 'Forecasting', 'Volatility models'],
    assessment: 'Problem sets 30% · Forecasting project 30% · Final 40%'
  },

  'data-3': {
    code: 'DAT 311', credits: 6, type: 'Core · Data Spine',
    title: 'Economics Data Lab & Programming: Deep Learning',
    semester: 'Year 3 · Semester 1',
    summary: 'Stage 3 of the data spine. Neural networks as a flexible function approximator, with applications to text, images and high-dimensional economic data.',
    outcomes: [
      'Build, train and tune a feed-forward and a convolutional network',
      'Apply embeddings to text and tabular economic problems',
      'Recognise the limits of deep learning for causal questions',
      'Use modern frameworks (PyTorch / JAX) confidently'
    ],
    topics: ['Neural network basics', 'CNNs', 'NLP embeddings', 'Sequence models', 'Causal ML caveats', 'PyTorch'],
    assessment: 'Lab portfolio 40% · Group project 40% · Critique essay 20%'
  },

  'dev-econ': {
    code: 'ECO 313', credits: 6, type: 'Core',
    title: 'Development Economics',
    semester: 'Year 3 · Semester 1',
    summary: 'Why are some countries rich and others poor? Theories, evidence, RCT-based microeconomics of development, with strong reference to the South Caucasus.',
    outcomes: [
      'Compare structural and institutional theories of growth',
      'Read and critique a development RCT',
      'Analyse poverty, inequality and human-development metrics',
      'Apply development thinking to Azerbaijan\'s post-oil diversification agenda'
    ],
    topics: ['Growth & convergence', 'Institutions', 'Health & education', 'RCT methodology', 'Trade & development', 'Resource economies'],
    assessment: 'Essay 40% · RCT critique 25% · Final 35%'
  },

  /* ───── Year 3 · Semester 2 ─────────────────────────────── */

  'public-econ': {
    code: 'ECO 321', credits: 6, type: 'Core',
    title: 'Public Economics',
    semester: 'Year 3 · Semester 2',
    summary: 'Markets fail, governments intervene, interventions have costs. The theory and empirics of taxation, public spending and the design of the public sector.',
    outcomes: [
      'Analyse the welfare effects of taxation using deadweight-loss tools',
      'Compare tax systems on efficiency-equity grounds',
      'Evaluate public expenditure using cost-benefit analysis',
      'Discuss the political economy of fiscal reform in resource-rich states'
    ],
    topics: ['Tax incidence', 'Optimal taxation', 'Public goods', 'Cost-benefit analysis', 'Fiscal federalism', 'Sovereign-wealth management'],
    assessment: 'Policy memo 30% · Mid-term 25% · Final 45%'
  },

  'econ-3': {
    code: 'ECO 322', credits: 7, type: 'Core',
    title: 'Econometrics III — Panel Data',
    semester: 'Year 3 · Semester 2',
    summary: 'Combining the cross-section and the time series: fixed and random effects, dynamic panels, the panel-IV toolkit, with hands-on application.',
    outcomes: [
      'Choose between pooled, FE, RE and dynamic-panel estimators',
      'Apply Arellano-Bond / system GMM to a macro panel',
      'Use panel data to address endogeneity in firm and country studies',
      'Replicate a published panel-data result'
    ],
    topics: ['Fixed & random effects', 'Hausman tests', 'Dynamic panels', 'GMM', 'Panel-IV', 'Spatial panels (intro)'],
    assessment: 'Problem sets 30% · Empirical project 40% · Final 30%'
  },

  'io': {
    code: 'ECO 323', credits: 6, type: 'Core',
    title: 'Industrial Organization',
    semester: 'Year 3 · Semester 2',
    summary: 'How firms compete in imperfect markets — pricing, entry, mergers, platforms. The microeconomics behind competition policy and antitrust.',
    outcomes: [
      'Model firm conduct under oligopoly with the standard models',
      'Analyse pricing strategies including bundling and price discrimination',
      'Evaluate the welfare effects of a merger or entry decision',
      'Discuss the IO of digital platforms and network effects'
    ],
    topics: ['Cournot & Bertrand', 'Entry & deterrence', 'Mergers', 'Vertical relations', 'Platforms', 'Competition policy'],
    assessment: 'Problem sets 25% · Merger case 30% · Final 45%'
  },

  'behav': {
    code: 'ECO 324', credits: 6, type: 'Core',
    title: 'Behavioural Economics',
    semester: 'Year 3 · Semester 2',
    summary: 'How people actually decide — biases, heuristics, social preferences — and what this means for policy design, finance and consumer welfare.',
    outcomes: [
      'Catalogue the major deviations from expected-utility theory',
      'Design a simple behavioural experiment',
      'Apply behavioural insights to savings, health and energy policy',
      'Critique behavioural-economics methodology and its replication record'
    ],
    topics: ['Prospect theory', 'Time preferences', 'Social preferences', 'Heuristics', 'Nudges', 'Behavioural finance preview'],
    assessment: 'Experimental design 30% · Reading log 20% · Final 50%'
  },

  'fin-econ': {
    code: 'FIN 321', credits: 6, type: 'Core',
    title: 'Financial Economics',
    semester: 'Year 3 · Semester 2',
    summary: 'The theory of asset pricing and portfolio choice — the bridge between intermediate macro/micro and the financial electives in Year 4.',
    outcomes: [
      'Apply mean-variance and CAPM frameworks to portfolio choice',
      'Price simple derivatives using arbitrage arguments',
      'Test asset-pricing models on real return data',
      'Discuss market efficiency and its anomalies'
    ],
    topics: ['Portfolio theory', 'CAPM & factor models', 'Efficient markets', 'Options & arbitrage', 'Empirical asset pricing'],
    assessment: 'Problem sets 30% · Empirical exercise 30% · Final 40%'
  },

  /* ───── Year 4 · Semester 1 ─────────────────────────────── */

  'thesis-1': {
    code: 'THE 411', credits: 9, type: 'Thesis',
    title: 'Thesis Project — Part I',
    semester: 'Year 4 · Semester 1',
    summary: 'First half of the dissertation. Students choose a topic, build a literature review, lock in data and identification, and produce a defended proposal.',
    outcomes: [
      'Formulate a researchable economic question with a credible identification strategy',
      'Produce a critical literature review of 4,000–5,000 words',
      'Acquire, clean and document a dataset suitable for the question',
      'Defend the proposal in front of a faculty panel'
    ],
    topics: ['Literature review', 'Data acquisition', 'Identification strategy', 'Pre-analysis plan', 'Proposal defence'],
    assessment: 'Proposal 60% · Defence 40%'
  },

  'energy-az': {
    code: 'ECO 411', credits: 6, type: 'Core',
    title: 'Economy of Azerbaijan: Energy Economics & Resource Management',
    semester: 'Year 4 · Semester 1',
    summary: 'The signature applied course of the programme — the structure, history and future of the Azerbaijani economy, with oil, gas and renewables at its centre.',
    outcomes: [
      'Map the structure of the Azerbaijani economy and its key flows',
      'Apply resource-economics tools (Hotelling, Dutch disease) to a real case',
      'Evaluate SOFAZ and the post-oil diversification strategy',
      'Analyse the renewables transition for a Caspian-littoral economy'
    ],
    topics: ['Hotelling & extraction', 'Dutch disease', 'SOFAZ', 'Pipeline geopolitics', 'Energy transition', 'Karabakh reconstruction economics'],
    assessment: 'Country brief 40% · Mid-term 20% · Final 40%'
  },

  'int-trade': {
    code: 'ECO 412', credits: 6, type: 'Core',
    title: 'International Trade',
    semester: 'Year 4 · Semester 1',
    summary: 'From Ricardo to Melitz: why countries trade, who gains, who loses, and the design of trade policy in a world of value chains.',
    outcomes: [
      'Derive comparative-advantage and increasing-returns trade patterns',
      'Analyse the distributional consequences of trade liberalisation',
      'Evaluate tariffs, NTBs and trade agreements',
      'Discuss firm-level trade and global value chains'
    ],
    topics: ['Ricardian & H-O models', 'New trade theory', 'Heterogeneous-firm models', 'Trade policy', 'GVCs', 'WTO architecture'],
    assessment: 'Policy paper 35% · Mid-term 25% · Final 40%'
  },

  /* ───── Year 4 · Semester 2 ─────────────────────────────── */

  'thesis-2': {
    code: 'THE 421', credits: 12, type: 'Thesis',
    title: 'Thesis Project — Part II',
    semester: 'Year 4 · Semester 2',
    summary: 'Execution and defence: empirical work, write-up, viva. The capstone deliverable of the BSc.',
    outcomes: [
      'Execute the empirical strategy with full code and data documentation',
      'Produce a thesis of 10,000–12,000 words to publication-style standards',
      'Defend results, robustness and limitations in a 45-minute viva',
      'Deposit a reproducible replication package'
    ],
    topics: ['Empirical execution', 'Robustness & sensitivity', 'Academic writing', 'Replication package', 'Viva preparation'],
    assessment: 'Thesis 80% · Viva 20%'
  },

  'pol-econ': {
    code: 'ECO 421', credits: 6, type: 'Core',
    title: 'Political Economy',
    semester: 'Year 4 · Semester 2',
    summary: 'Where economics meets politics: voting, lobbying, institutions, the political determinants of economic outcomes. Closes the loop opened in Global Economic History.',
    outcomes: [
      'Apply public-choice and political-agency models to real cases',
      'Analyse the political economy of reform and resource curses',
      'Discuss democratic and authoritarian models of growth',
      'Write a political-economy briefing on a current event'
    ],
    topics: ['Public choice', 'Voting models', 'Institutions & growth', 'Lobbying & rent-seeking', 'Resource curse', 'PE of climate policy'],
    assessment: 'Briefing 40% · Mid-term 20% · Final 40%'
  },

  /* ───── Elective Library ────────────────────────────────── */

  'el-health': {
    code: 'ECO 451', credits: 6, type: 'Elective',
    title: 'Health Economics',
    semester: 'Year 4 · Elective',
    summary: 'Markets where information is asymmetric, externalities are everywhere and the demand curve is the patient. Tools for designing and evaluating health systems.',
    outcomes: [
      'Apply demand-and-supply analysis to healthcare markets',
      'Compare Bismarckian, Beveridgean and mixed health systems',
      'Evaluate a health intervention using QALY-based CBA',
      'Analyse healthcare reform in Azerbaijan'
    ],
    topics: ['Insurance', 'Provider payment', 'QALYs & CBA', 'Pharma markets', 'Health system reform'],
    assessment: 'Policy paper 50% · Final 50%'
  },

  'el-env': {
    code: 'ECO 452', credits: 6, type: 'Elective',
    title: 'Environmental Economics',
    semester: 'Year 4 · Elective',
    summary: 'Pricing the unpriced — externalities, public goods, the climate problem and the policy instruments economists have on offer.',
    outcomes: [
      'Quantify environmental externalities and design Pigouvian instruments',
      'Compare cap-and-trade, carbon taxes and standards',
      'Evaluate non-market valuation methods',
      'Analyse climate policy for an oil-exporting economy'
    ],
    topics: ['Externalities', 'Carbon pricing', 'Non-market valuation', 'Climate macroeconomics', 'Just transition'],
    assessment: 'Policy paper 50% · Final 50%'
  },

  'el-ai': {
    code: 'ECO 453', credits: 6, type: 'Elective',
    title: 'Economics of Artificial Intelligence (Digital Economics)',
    semester: 'Year 4 · Elective',
    summary: 'AI as a general-purpose technology — labour-market impacts, market structure of platforms, antitrust and the political economy of a frontier industry.',
    outcomes: [
      'Analyse the labour-market effects of automation and AI',
      'Model two-sided platforms and their welfare implications',
      'Discuss data as an economic input',
      'Evaluate AI-specific regulation (EU AI Act etc.)'
    ],
    topics: ['Automation & jobs', 'Platforms & networks', 'Data economics', 'AI regulation', 'AI macro effects'],
    assessment: 'Research note 50% · Final 50%'
  },

  'el-mbf': {
    code: 'FIN 451', credits: 6, type: 'Elective',
    title: 'Economics of Money, Banking & Financial Markets',
    semester: 'Year 4 · Elective',
    summary: 'How money is created, how banks intermediate, how markets fail — and the supervisory architecture built around them.',
    outcomes: [
      'Trace money creation through the banking system',
      'Analyse bank balance sheets and the run / liquidity trade-off',
      'Discuss financial-stability frameworks (Basel, macroprudential)',
      'Apply these tools to the Azerbaijani banking sector'
    ],
    topics: ['Money supply', 'Bank intermediation', 'Financial crises', 'Macroprudential policy', 'Central-bank balance sheets'],
    assessment: 'Bank case 40% · Final 60%'
  },

  'el-corpfin': {
    code: 'FIN 452', credits: 6, type: 'Elective',
    title: 'Corporate Finance',
    semester: 'Year 4 · Elective',
    summary: 'Capital structure, dividend policy, M&A. The financial decisions of the firm, taught with both the textbook model and the practitioner reality.',
    outcomes: [
      'Compute WACC and value a company under DCF',
      'Analyse capital-structure decisions under information asymmetry',
      'Evaluate an M&A deal from synergy and governance angles',
      'Read a 10-K / annual report fluently'
    ],
    topics: ['Capital budgeting', 'Capital structure', 'Dividends & buybacks', 'M&A', 'Corporate governance'],
    assessment: 'Valuation project 50% · Final 50%'
  },

  'el-intfin': {
    code: 'FIN 453', credits: 6, type: 'Elective',
    title: 'International Finance (Advanced Elective)',
    semester: 'Year 4 · Elective',
    summary: 'Advanced extensions: emerging-market crises, capital-flow management, sovereign debt — taken after the Year-3 International Finance core.',
    outcomes: [
      'Model sovereign-debt sustainability and default',
      'Analyse capital-flow surges and reversals',
      'Discuss CFM and macroprudential FX policy',
      'Evaluate an EM bond prospectus'
    ],
    topics: ['Sovereign debt', 'Sudden stops', 'CFMs', 'EM crises', 'Global financial cycle'],
    assessment: 'Country study 50% · Final 50%'
  },

  'el-bfap': {
    code: 'FIN 454', credits: 6, type: 'Elective',
    title: 'Behavioural Finance & Asset Pricing',
    semester: 'Year 4 · Elective',
    summary: 'Where Year-3 Behavioural Economics meets Year-3 Financial Economics: biases, limits to arbitrage, and the empirical anomalies of asset prices.',
    outcomes: [
      'Catalogue the major behavioural anomalies in asset prices',
      'Analyse limits to arbitrage and their empirical signatures',
      'Test a behavioural asset-pricing prediction with real data',
      'Discuss bubbles and crashes through a behavioural lens'
    ],
    topics: ['Anomalies', 'Limits to arbitrage', 'Investor psychology', 'Bubbles', 'Behavioural macro-finance'],
    assessment: 'Empirical exercise 50% · Final 50%'
  },

  'el-monetary': {
    code: 'FIN 455', credits: 6, type: 'Elective',
    title: 'Monetary Economics & Central Banking',
    semester: 'Year 4 · Elective',
    summary: 'The modern central bank — inflation targeting, unconventional policy, balance-sheet policy, communication. A career-launcher for the public sector.',
    outcomes: [
      'Set up and solve a small New-Keynesian model',
      'Analyse inflation-targeting frameworks and their alternatives',
      'Discuss QE, forward guidance and balance-sheet policy',
      'Evaluate CBAR\'s monetary framework'
    ],
    topics: ['Inflation targeting', 'NK models', 'Unconventional policy', 'Communication', 'EM monetary frameworks'],
    assessment: 'Policy paper 50% · Final 50%'
  },

  'el-fintech': {
    code: 'FIN 456', credits: 6, type: 'Elective',
    title: 'Fintech & The Future of Money',
    semester: 'Year 4 · Elective',
    summary: 'Payments, crypto, CBDCs, open banking, embedded finance. The institutional plumbing of finance as it is being rewired.',
    outcomes: [
      'Map the modern payments stack and its margins',
      'Compare crypto, stablecoins and CBDCs analytically',
      'Discuss the economics of open banking and embedded finance',
      'Evaluate a fintech business model'
    ],
    topics: ['Payments', 'Crypto & DeFi', 'CBDCs', 'Open banking', 'Fintech regulation'],
    assessment: 'Pitch / business case 50% · Final 50%'
  },

  'el-labour': {
    code: 'ECO 454', credits: 6, type: 'Elective',
    title: 'Labour Economics',
    semester: 'Year 4 · Elective',
    summary: 'The economics of work — supply, demand, wages, discrimination, mobility — with strong empirical micro content and a Caucasus lens.',
    outcomes: [
      'Model labour supply and demand and analyse policy interventions',
      'Apply causal-inference tools to the minimum-wage and immigration debates',
      'Analyse wage gaps and discrimination',
      'Evaluate active labour-market programmes'
    ],
    topics: ['Labour supply', 'Human capital', 'Wage determination', 'Minimum wage', 'Migration', 'Discrimination'],
    assessment: 'Empirical paper 50% · Final 50%'
  }

};
