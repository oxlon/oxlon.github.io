"""Unit tests: schedule parsing, upstream watcher (manifest → change → stable → run), tokens, az_errors, safe paths."""
import json, shutil, tempfile, unittest, warnings
from datetime import datetime
from pathlib import Path

import helpers  # noqa: F401  (sys.path, offline env)
import apidb, autonomous
from apicore import ApiError, Config, load_tokens, safe_relpath
from az_errors import az_exc


class FakeRuns:
    def __init__(self):
        self.started, self.on_start, self.on_finish, self.busy = [], [], [], False

    def start(self, actor="api", trigger="api", note=None, opts=None):
        if self.busy:
            raise ApiError(409, "busy", "məşğul")
        jid = "R%d" % len(self.started)
        self.started.append((jid, trigger, note))
        for cb in self.on_start:
            cb(jid)
        return {"id": jid}


class UnitTest(unittest.TestCase):
    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)

    def test_schedule(self):
        self.assertEqual(autonomous.parse_schedule("18:30, 06:05"), [(6, 5), (18, 30)])
        for bad in ("", "25:00", "6.30", "07:00,07:00"):
            with self.assertRaises(ValueError):
                autonomous.parse_schedule(bad)
        nx = autonomous.next_run([(6, 0), (18, 0)], now=datetime(2026, 10, 6, 12, 0))
        self.assertEqual(nx, datetime(2026, 10, 6, 18, 0))
        nx = autonomous.next_run([(6, 0)], now=datetime(2026, 10, 6, 12, 0))
        self.assertEqual(nx.day, 7)

    def test_watcher(self):
        tmp = Path(tempfile.mkdtemp(prefix="pu_watch_"))
        try:
            cfg = Config(root=tmp, db=tmp / "w.db", config_dir=tmp / "config")
            apidb.init(cfg.db)
            f = tmp / "up.csv"
            f.write_text("a\n1\n")
            runs = FakeRuns()
            w = autonomous.Watcher(cfg, runs, poll=999, log=lambda *a: None, files=lambda: {"micro:up.csv": f})
            w.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            w.manifest_path.write_text(json.dumps({"files": {"micro:up.csv": autonomous.sha256(f)}}))
            self.assertEqual(w.scan(), [])
            f.write_text("a\n2\n")
            self.assertEqual(w.scan(), ["micro:up.csv"])           # first detection: wait until stable
            self.assertEqual(runs.started, [])
            runs.busy = True
            w.scan()                                                # stable but busy → stays pending
            self.assertEqual(w.state()["pending"], ["micro:up.csv"])
            runs.busy = False
            w.scan()
            self.assertEqual(len(runs.started), 1)
            self.assertIn("izləmə", runs.started[0][1])
            w._on_finish({"id": "R0", "status": "ok"})              # manifest updated → no further trigger
            self.assertEqual(w.scan(), [])
            ev = apidb.events(cfg.db)
            self.assertTrue(any(e["kind"] == "watch.vintage" for e in ev))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_upstream_files(self):
        files = autonomous.upstream_files(Config())
        groups = {k.split(":")[0] for k in files}
        self.assertTrue({"micro", "config", "caem"} <= groups, groups)

    def test_tokens_errors_paths(self):
        t = load_tokens("a:read,b:write")
        self.assertEqual(t["b"], {"read", "write"})
        self.assertEqual(az_exc(FileNotFoundError("x")), "fayl tapılmadı")
        self.assertIn("ən azı 5", az_exc(ValueError("ən azı 5 fərqli göstərici")))
        for bad in ("../x.csv", "/etc/passwd", ".hidden", "a/../../b"):
            with self.assertRaises(ApiError):
                safe_relpath(bad)
        self.assertEqual(safe_relpath("P1_headline.csv"), "P1_headline.csv")


if __name__ == "__main__":
    unittest.main()
