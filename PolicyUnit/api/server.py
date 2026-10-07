#!/usr/bin/env python3
"""
MİİS §15.5.4 — İqtisadi siyasətlərin təsir analizi modulunun (PolicyUnit) API-si, canlı hesablama və avtonom icra
serveri. HTTP qatı yalnız standart kitabxanadır (ThreadingHTTPServer, SQLite); hesablama policyunit paketinin açıq
funksiyalarını çağırır (numpy/pandas/scipy olan Python lazımdır). RiskUnit ilə yalnız HTTP (8791). Müqavilə: openapi.yaml.

    python3 api/server.py                                    # http://127.0.0.1:8792/panel/
    python3 api/server.py --schedule 06:30,18:30 --watch      # avtonom rejim

Nişanlar: POLICY_API_TOKENS (və ya API_TOKENS) = "oxu_nişanı:read,yaz_nişanı:write".
Standart (yalnız yerli sınaq üçün): demo-read / demo-write — GET üçün read, POST/PUT/DELETE üçün write.
"""
import argparse, os, sys, threading, time
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import apidb, pu                                                         # noqa: E402
from apicore import API_VERSION, DEFAULT_PORT, DEFAULT_ROOT, Config, load_tokens, now_iso, using_default_tokens  # noqa: E402
from data_views import Views, records                                    # noqa: E402
from http_handler import Handler                                         # noqa: E402
from instruments import Catalogue                                        # noqa: E402
from run_manager import RefreshManager                                   # noqa: E402
from runs import Runs                                                    # noqa: E402
from scenario_write import Writer                                        # noqa: E402


class App:
    def __init__(self, cfg, tokens, log=print):
        apidb.init(cfg.db)
        cfg.output.mkdir(parents=True, exist_ok=True)
        pu.bind(cfg)
        self.cfg, self.tokens, self.log, self.version = cfg, tokens, log, API_VERSION
        self.views = Views(cfg)
        self.store = Writer(cfg)
        self.instruments = Catalogue(cfg)
        self.runs = Runs(cfg, log=log)
        self.refresh = RefreshManager(cfg, log=log)
        self.refresh.on_finish.append(lambda job: (self.views._cache.clear(), pu.reload(), pu._ENG.update(rows=None)))
        self.started_at = now_iso()
        self.watcher = self.scheduler = None
        self.warm_state = {"status": "gözlənilir"}
        self.risk_state = {"status": "başladılmayıb"}
        self._risk_stop = threading.Event()

    def autonomous_state(self):
        return {"schedule": self.scheduler.state() if self.scheduler else None,
                "watch": self.watcher.state() if self.watcher else None,
                "no_network": os.environ.get("POLICY_NO_NETWORK") == "1"}

    def status(self):
        meta = pu.last_run_meta(self.cfg)
        vin = pu.vintage(self.cfg)
        last_v = meta.get("vintage") or {}
        changed = [k for k in ("micro_vintage", "caem_md5") if last_v.get(k) and last_v.get(k) != vin.get(k)]
        rs = self.views.frame("P1_run_status.csv", required=False)
        n_off = len(list(self.cfg.scenarios_dir.glob("*.json")))
        n_dr = (apidb.query(self.cfg.db, "SELECT COUNT(*) AS n FROM draft") or [{"n": 0}])[0]["n"]
        return {"last_run": {k: meta.get(k) for k in ("run_at", "seconds", "scenarios", "long_end", "catalogue_errors")},
                "vintage": vin, "vintage_last_run": last_v, "vintage_changed": bool(changed), "vintage_changed_keys": changed,
                "engines": pu.engines(), "run_status": records(rs), "scenarios": {"official": n_off, "draft": n_dr},
                "risk_api": pu.risk_api_state(self.cfg), "risk_autostart": self.risk_state, "analysis_ready": self.warm_state,
                "refresh": self.refresh.active(), "busy": self.refresh.busy(), "runs_active": self.runs.busy(),
                "autonomous": self.autonomous_state(), "horizons": pu.HORIZON_AZ, "version": API_VERSION}

    def warm(self):
        """Background warm-up: MicroUnit chain baseline + CAEM workbook (first scenario run is then fast)."""
        def job():
            t0 = time.time()
            self.warm_state = {"status": "isinir", "started": now_iso()}
            try:
                ids = sorted(p.stem for p in self.cfg.scenarios_dir.glob("*.json"))
                if ids:
                    s, _ = self.store.load(ids[0])
                    pu.call(pu.P("integrate").run_scenario, s)
                self.warm_state = {"status": "hazır", "seconds": round(time.time() - t0, 1), "at": now_iso()}
            except Exception as e:
                self.warm_state = {"status": "xəta", "detail": "%s: %s" % (type(e).__name__, str(e)[:300])}
            self.log("mühərrik keşi: %s" % self.warm_state)
        threading.Thread(target=job, daemon=True, name="warm").start()

    def risk_autostart(self):
        """Keep a RiskUnit API (scratch DB) running for this server's lifetime if none answers on its port."""
        def job():
            RL = pu.P("risk_link")
            self.risk_state = {"status": "yoxlanılır", "at": now_iso()}
            try:
                c = RL.Client(base=self.cfg.risk_api)
                if c.offline:
                    self.risk_state = {"status": "söndürülüb (POLICY_NO_NETWORK=1) — keş"}
                    return
                if c.alive():
                    self.risk_state = {"status": "artıq işləyir", "url": c.base}
                    return
                with RL.server(c, log=self.log):
                    self.risk_state = {"status": "başladıldı" if c.alive() else "cavab vermir", "url": c.base, "at": now_iso()}
                    self._risk_stop.wait()
            except Exception as e:
                self.risk_state = {"status": "xəta", "detail": "%s: %s" % (type(e).__name__, str(e)[:300])}
        self._risk_thread = threading.Thread(target=job, daemon=True, name="risk-autostart")
        self._risk_thread.start()

    def stop(self):
        self._risk_stop.set()
        t = getattr(self, "_risk_thread", None)
        if t is not None:
            t.join(15)                                  # lets risk_link.server() stop the RiskUnit it started


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128


def build_app(a, log=print):
    cfg = Config(root=Path(a.root), db=Path(a.db) if a.db else None, python=a.python, warm=not a.no_warm,
                 config_dir=Path(a.config_dir) if a.config_dir else None, risk_api=a.risk_api)
    app = App(cfg, load_tokens(), log=log)
    import autonomous
    if a.schedule:
        app.scheduler = autonomous.Scheduler(cfg, app.refresh, autonomous.parse_schedule(a.schedule), log=log)
    if a.watch:
        app.watcher = autonomous.Watcher(cfg, app.refresh, poll=a.watch_interval, log=log)
    return app


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="MİİS §15.5.4 siyasət təsiri modulunun API-si və avtonom icra serveri")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("POLICY_API_PORT", DEFAULT_PORT)))
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="PolicyUnit qovluğu (standart: api/-nin üst qovluğu)")
    ap.add_argument("--db", default=None, help="SQLite faylı (standart: <root>/api/policy.db)")
    ap.add_argument("--config-dir", default=None, help="konfiqurasiya qovluğu (standart: <root>/config)")
    ap.add_argument("--python", default=None, help="run_all.py üçün Python (standart: bu Python)")
    ap.add_argument("--risk-api", default=None, help="RiskUnit API ünvanı (standart: POLICY_RISK_API və ya 127.0.0.1:8791)")
    ap.add_argument("--no-risk-autostart", action="store_true", help="RiskUnit API işləmirsə onu avtomatik başlatma")
    ap.add_argument("--schedule", default=None, help="gündəlik cədvəl HH:MM[,HH:MM] (yerli vaxt) → run_all.py")
    ap.add_argument("--watch", action="store_true", help="yuxarı axın vintajlarını izlə (yeni hash → run_all.py)")
    ap.add_argument("--watch-interval", type=float, default=300.0, help="izləmə intervalı, saniyə (standart 300)")
    ap.add_argument("--no-warm", action="store_true", help="mühərrik keşini başlanğıcda isitmə")
    ap.add_argument("--quiet", action="store_true", help="sorğu jurnalını çap etmə")
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    if using_default_tokens():
        if a.host not in ("127.0.0.1", "localhost", "::1"):
            sys.exit("XƏTA: standart sınaq nişanları ilə şəbəkəyə açıla bilməz.\n"
                     '      Əvvəlcə nişanları təyin edin, məsələn: export POLICY_API_TOKENS="siyaset-oxu:read,siyaset-yaz:write"')
        print("XƏBƏRDARLIQ: standart sınaq nişanları istifadə olunur (demo-read / demo-write). "
              "İstehsalda POLICY_API_TOKENS mühit dəyişənini təyin edin.", file=sys.stderr)
    if a.schedule:
        import autonomous
        try:
            autonomous.parse_schedule(a.schedule)
        except ValueError as e:
            sys.exit("XƏTA: --schedule: %s (məs. 06:30,18:30)" % e)
    app = build_app(a)
    httpd = Server((a.host, a.port), Handler)
    httpd.app, httpd.quiet = app, a.quiet
    for t in (app.watcher, app.scheduler):
        if t:
            t.start()
    if app.cfg.warm:
        app.warm()
    if not a.no_risk_autostart:
        app.risk_autostart()
    host = "[%s]" % a.host if ":" in a.host else a.host
    print("SiyasətModel API %s  http://%s:%d/api/v1/health   panel: http://%s:%d/panel/" % (API_VERSION, host, httpd.server_port,
                                                                                         host, httpd.server_port))
    print("kök: %s   baza: %s   şəbəkə: %s" % (app.cfg.root, app.cfg.db, "söndürülüb (POLICY_NO_NETWORK=1)"
                                               if os.environ.get("POLICY_NO_NETWORK") == "1" else "açıq"))
    if app.scheduler:
        print("cədvəl: %s; növbəti: %s" % (", ".join(app.scheduler.state()["slots"]), app.scheduler.next.isoformat(timespec="minutes")))
    if app.watcher:
        print("izləmə: yuxarı axın faylları hər %.0f s yoxlanılır (yeni vintaj → run_all.py)" % app.watcher.poll)
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\ndayandırıldı")
    finally:
        app.stop()


if __name__ == "__main__":
    main()
