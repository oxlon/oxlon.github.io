"""Test helpers: a temp PolicyUnit root (copy of config/, tiny outputs, panel) + a server on a free port.
Offline (POLICY_NO_NETWORK=1); heavy engine runs are replaced by `stub_engines()` (synthetic harmonised frame)."""
import json, os, shutil, sys, tempfile, threading, urllib.error, urllib.request, warnings
from pathlib import Path

API = Path(__file__).resolve().parents[1]
PU = API.parent
sys.path.insert(0, str(API))
os.environ.setdefault("POLICY_NO_NETWORK", "1")
warnings.simplefilter("ignore", ResourceWarning)

from apicore import Config, load_tokens  # noqa: E402

TOKENS = "t-read:read,t-write:write"


def _w(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def make_root():
    root = Path(tempfile.mkdtemp(prefix="pu_api_test_"))
    shutil.copytree(PU / "config", root / "config", ignore=shutil.ignore_patterns("_backup", "_arxiv"))
    o = root / "output"
    _w(o / "_catalog.csv", "file,owner,description_az,columns,frequency,rows,updated\n"
                           "P1_headline.csv,core,FR1 başlıq,scenario;indicator;horizon;effect,hər işə salınmada,3,2026-10-06\n")
    _w(o / "P1_headline.csv", "scenario,indicator,horizon,effect\nmw20_2027,gdp_real,qısa,0.8\n"
                              "mw20_2027,gdp_real,orta,0.9\nvat_minus2,gdp_real,qısa,0.4\n")
    _w(o / "P1_run_meta.json", json.dumps({"run_at": "2026-10-06T15:40:22", "seconds": 7.4, "scenarios": ["mw20_2027"],
                                           "vintage": {"micro_vintage": "x", "caem_md5": "y"}}))
    _w(o / "P1_run_status.csv", "scenario,engine,status\nmw20_2027,micro,ok\n")
    _w(root / "panel" / "index.html", "<html>panel</html>")
    _w(root / "docs" / "a.md", "# doc")
    (root / "api").mkdir()
    shutil.copy2(API / "openapi.yaml", root / "api" / "openapi.yaml")
    _w(root / "api" / "OXUYUN.md", "# oxuyun")
    _w(root / "api" / "secret.py", "x=1")
    _w(root / "run_all.py", "print('secret')")
    return root


def stub_frame(s):
    """Synthetic harmonised result: micro + caem rows for the headline indicators (deterministic in the size)."""
    import pandas as pd
    from policyunit import config, engine_base as eb, integrate
    k = sum(float(it["size"]) for it in s["instruments"]) / 10.0
    res = {}
    for e, f in (("micro", 1.0), ("caem", 0.6)):
        rows = []
        for y in config.ALL_YEARS:
            for ind, unit, b, d in (("gdp_real", "mln AZN", 50000.0, 0.01), ("gdp_nonoil_real", "mln AZN", 40000.0, 0.012),
                                    ("gdp_nominal", "mln AZN", 120000.0, 0.01), ("infl", "%", 4.0, 0.1),
                                    ("unemp_rate", "%", 5.0, -0.02), ("employment_hired", "min nəfər", 1700.0, 0.002),
                                    ("budget_balance_pct", "% ÜDM", -2.0, -0.05), ("debt_pct", "% ÜDM", 20.0, 0.1)):
                v = b * (1 + d * k * f) if b > 100 else b + d * k * f
                rows.append(eb.row(ind, ind, unit, y, b, v, "stub", "C", "makro"))
            rows.append(eb.row("fiscal_cost", "fiscal_cost", "mln AZN", y, 0.0, 30.0 * k if y < 2029 else 0.0, "stub", "C", "fiskal"))
        res[e] = eb.Result(e, pd.DataFrame(rows), {"vintage": {"stub": True}})
    frame = integrate.combine(s, res)
    return {"scenario": s, "results": res, "status": {e: {"status": "ok", "rows": len(r.frame), "seconds": 0.0}
                                                     for e, r in res.items()}, "frame": frame, "seconds": 0.01}


def stub_engines(delay=0.0):
    """Replace integrate.run_scenario by the stub (returns a restore function)."""
    import time
    import pu
    I = pu.P("integrate")
    orig = I.run_scenario

    def fake(s, engines=None):
        if delay:
            time.sleep(delay)
        return stub_frame(s)
    I.run_scenario = fake

    def restore():
        I.run_scenario = orig
    return restore


class Live:
    """Server on 127.0.0.1:<free port> with App over `root`; stop() cleans up."""

    def __init__(self, root, refresh_cmd=None, config_dir=None):
        import server
        self.root = Path(root)
        self.tmp = Path(tempfile.mkdtemp(prefix="pu_api_db_"))
        cfg = Config(root=self.root, db=self.tmp / "t.db", refresh_cmd=refresh_cmd, warm=False,
                     config_dir=config_dir or (self.root / "config"))
        self.app = server.App(cfg, load_tokens(TOKENS), log=lambda *a: None)
        self.httpd = server.Server(("127.0.0.1", 0), server.Handler)
        self.httpd.app, self.httpd.quiet = self.app, True
        self.port = self.httpd.server_port
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def url(self, p):
        return "http://127.0.0.1:%d%s" % (self.port, p)

    def req(self, method, path, body=None, token="t-write", raw=False, headers=None):
        data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        r = urllib.request.Request(self.url(path), data=data, method=method)
        if token:
            r.add_header("Authorization", "Bearer " + token)
        for k, v in (headers or {}).items():
            r.add_header(k, v)
        if data is not None:
            r.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                b = resp.read()
                return resp.status, (b if raw else json.loads(b.decode() or "null")), dict(resp.headers)
        except urllib.error.HTTPError as e:
            b = e.read()
            try:
                return e.code, json.loads(b.decode()), dict(e.headers)
            except ValueError:
                return e.code, b, dict(e.headers)

    def stop(self, rm_root=True):
        self.httpd.shutdown()
        self.httpd.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)
        if rm_root:
            shutil.rmtree(self.root, ignore_errors=True)


def rebind_default():
    """Point policyunit.config back at the real PolicyUnit/config after a test module."""
    import pu
    pu.bind(Config())
