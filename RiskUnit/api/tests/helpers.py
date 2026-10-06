"""Test helpers: a tiny synthetic RiskUnit root + a server on a free port (offline, no riskunit import)."""
import json, os, shutil, sys, tempfile, threading, urllib.error, urllib.request, warnings
from pathlib import Path

API = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API))
os.environ.setdefault("RISK_NO_NETWORK", "1")
warnings.simplefilter("ignore", ResourceWarning)

import apidb  # noqa: E402
from apicore import Config, load_tokens  # noqa: E402

TOKENS = "t-read:read,t-write:write"


def _w(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def make_root():
    root = Path(tempfile.mkdtemp(prefix="risk_api_test_"))
    o, i = root / "output", root / "input"
    _w(i / "risk_reyestri.csv", "risk_id,aile,ad,gosterici,caem_kateqoriya\nR01,MAL,Neft qiyməti,brent,Oil\n"
                                "R12,DAX,İnflyasiya,cpi,Inflation\n")
    _w(o / "FR2_risk_scores.csv", "sira,risk_id,ad,ufuq,ehtimal,skor,prioritet,baseline_id\n1,R12,İnflyasiya,2027,0.57,20,yüksək,B-test\n"
                                  "2,R01,Neft qiyməti,2027,0.48,16,yüksək,B-test\n")
    _w(o / "FR2_alerts.csv", "as_of,tip,ciddilik,risk_id,mesaj,baseline_id\n2026-10-06,yüksək prioritet,yüksək,R01,Neft,B-test\n")
    _w(o / "FR2_heatmap.csv", "P_bal,I_bal,skor,riskler\n4,4,16,R01\n")
    _w(o / "FR2_score_history.csv", "hesablandi_utc,risk_id,skor\n2026-10-01T00:00:00Z,R01,12\n2026-10-06T00:00:00Z,R01,16\n")
    _w(o / "FR3_measures_register.csv", "tedbir_id,risk_idler,tedbir,status\nT01,R01;R11,Konservativ Brent,təklif\n")
    _w(o / "FR3_residual_risk.csv", "risk_id,ad,skor,skor_hedef\nR01,Neft,16,9\nR12,İnfl,20,15\n")
    _w(o / "S0_factor_sigma.csv", "amil,amil_ad,risk_idler,sigma\nbrent,Brent,R01;R03,0.29\n")
    _w(o / "D5_daily_monitor.csv", "indicator,label_az,latest,signal\nbrent_spot,Brent,114,xəbərdarlıq ↑\ncbar_usd,USD,1.7,normal\n")
    _w(o / "D6_forecast_impact.csv", "driver,target_id,label_az,year,delta\nbrent,fr1:rgdpnon,Qeyri-neft,2027,0.5\n"
                                    "brent,fr1:other,Digər,2027,0.1\nfx,fr1:infl,İnfl,2027,0.2\n")
    _w(o / "D7_changes.csv", "kind,item,change\naxın,bfb,36\n")
    _w(o / "D2_feed_status.csv", "feed,source,last_obs,yas_gun,tazelik,status\ncbar_fx,AMB,2026-10-05,1,təzə,ok\n")
    _w(o / "_catalog_v2.csv", "file,owner_module,description_az,columns,update_frequency,updated_utc\n"
                              "D5_daily_monitor.csv,monitor,Gündəlik monitor,indicator; latest,gündəlik,2026-10-06T00:00:00Z\n")
    (o / "_run_summary_v2.json").write_text(json.dumps({"baseline_id": "B-test", "as_of": "2026-10-06", "qiymetlendirme_ili": 2027,
                                                        "merheleler": [{"stage": "A0", "name": "x", "status": "ok", "seconds": 0.1}],
                                                        "yuksek_prioritet": ["R12", "R01"]}), encoding="utf-8")
    _w(o / "forecast_archive" / "a.csv", "x\n1\n")
    _w(root / "reports" / "r.xlsx", "not really xlsx")
    _w(root / "panel" / "index.html", "<html>panel</html>")
    _w(root / "site" / "index.html", "<html>site</html>")
    _w(root / "docs" / "a.md", "# doc")
    _w(root / "run_all.py", "print('secret')")
    return root


class Live:
    """Server on 127.0.0.1:<free port> with App over `root`; stop() cleans up."""

    def __init__(self, root, refresh_cmd=None, real=False):
        import server
        self.root = Path(root)
        self.tmp = Path(tempfile.mkdtemp(prefix="risk_api_db_"))
        cfg = Config(root=self.root, db=self.tmp / "t.db", refresh_cmd=refresh_cmd, warm=False)
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
