"""Unit tests (offline): schedule parsing, watcher, error translation, override merge, filters, tokens."""
import shutil, tempfile, time, unittest
from datetime import datetime
from pathlib import Path

import helpers  # noqa: F401  (sys.path)
import pandas as pd

import autonomous
from analysis_base import merge_overrides
from analysis_stress import validate_ru
from apicore import ApiError, Config, as_list, load_tokens, safe_relpath
from az_errors import az_exc
from data_views import filter_frame


class ScheduleTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(autonomous.parse_schedule("06:30"), [(6, 30, "full")])
        self.assertEqual(autonomous.parse_schedule("13:00, 06:30,18:30"),
                         [(6, 30, "daily"), (13, 0, "full"), (18, 30, "daily")])      # first *given* time is full
        self.assertEqual(autonomous.parse_schedule("06:30=daily,07:00@full"), [(6, 30, "daily"), (7, 0, "full")])
        for bad in ("", "6", "25:00", "06:61", "06:30=weekly", "06:30,06:30", "ab:cd"):
            with self.assertRaises(ValueError, msg=bad):
                autonomous.parse_schedule(bad)

    def test_next_run(self):
        slots = autonomous.parse_schedule("06:30,13:00")
        t, m = autonomous.next_run(slots, datetime(2026, 10, 6, 7, 0))
        self.assertEqual((t, m), (datetime(2026, 10, 6, 13, 0), "daily"))
        t, m = autonomous.next_run(slots, datetime(2026, 10, 6, 13, 0))            # strictly after
        self.assertEqual((t, m), (datetime(2026, 10, 7, 6, 30), "full"))

    def test_scheduler_fire_busy(self):
        class Runs:
            def __init__(self):
                self.calls = []

            def start(self, **kw):
                self.calls.append(kw)
                if len(self.calls) > 1:
                    raise ApiError(409, "busy", "məşğul")
                return {"id": "R1"}
        tmp = Path(tempfile.mkdtemp())
        try:
            cfg = Config(root=tmp, db=tmp / "t.db")
            import apidb
            apidb.init(cfg.db)
            s = autonomous.Scheduler(cfg, Runs(), autonomous.parse_schedule("06:30"), log=lambda *a: None)
            self.assertEqual(s.fire("full")["job_id"], "R1")
            self.assertEqual(s.fire("daily")["skipped"], "məşğul")
            self.assertEqual(s.runs.calls[0]["trigger"], "cədvəl")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class WatcherTest(unittest.TestCase):
    def test_new_vintage_triggers_full_run(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "output").mkdir()
            up = tmp / "up.csv"
            up.write_text("a\n1\n")
            sha = autonomous.sha256(up)
            (tmp / "output" / "spine_manifest.csv").write_text("unit,key,path,sha256,rows\nm,fl,%s,%s,1\n" % (up, sha))
            cfg = Config(root=tmp, db=tmp / "t.db")
            import apidb
            apidb.init(cfg.db)

            class Runs:
                busy, calls = False, []

                def start(self, **kw):
                    if self.busy:
                        raise ApiError(409, "busy", "məşğul")
                    self.calls.append(kw)
                    return {"id": "R%d" % len(self.calls)}
            runs = Runs()
            w = autonomous.Watcher(cfg, runs, poll=1, log=lambda *a: None, files={"fl": up})
            self.assertEqual(w.scan(), [])                       # same hash as the last run → nothing
            self.assertEqual(runs.calls, [])
            time.sleep(0.01)
            up.write_text("a\n2\n")                              # new vintage
            runs.busy = True
            self.assertEqual(w.scan(), ["fl"])
            self.assertEqual(w.state()["pending"], ["fl"])       # busy → kept pending
            runs.busy = False
            w.scan()
            self.assertEqual((len(runs.calls), runs.calls[0]["mode"], w.state()["pending"]), (1, "full", []))
            self.assertIn("izləmə", runs.calls[0]["trigger"])
            w.scan()
            self.assertEqual(len(runs.calls), 1)                 # unchanged stat → no re-trigger
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ErrorsTest(unittest.TestCase):
    def test_translation(self):
        self.assertEqual(az_exc(FileNotFoundError("x")), "fayl tapılmadı")
        self.assertIn("5 dəyər", az_exc(ValueError("operands could not be broadcast together with shapes (5,) (2,)")))
        self.assertIn("override", az_exc(RuntimeError("x: override nəzərə alınmadı → [..]")))
        self.assertIn("microlib", az_exc(ModuleNotFoundError("No module named 'microlib'")))
        self.assertIn("RuntimeError", az_exc(RuntimeError("???")))
        self.assertIn("sütun", az_exc(KeyError("skor")))


class HelpersTest(unittest.TestCase):
    def test_tokens(self):
        t = load_tokens("a:read, b:write, c:read|write")
        self.assertEqual(t, {"a": {"read"}, "b": {"read", "write"}, "c": {"read", "write"}})

    def test_paths_and_lists(self):
        self.assertEqual(safe_relpath("forecast_archive/a.csv"), "forecast_archive/a.csv")
        for bad in ("../x.csv", "/etc/passwd", ".hidden", "a/../../b", "a\\b"):
            with self.assertRaises(ApiError, msg=bad):
                safe_relpath(bad)
        self.assertEqual(as_list("a, b,,c"), ["a", "b", "c"])

    def test_filter_frame(self):
        df = pd.DataFrame({"a": ["x", "y", "z"], "n": [1, 2, 3], "f": [1.0, 2.5, None]})
        self.assertEqual(list(filter_frame(df, {"a": ["x,z"]})["n"]), [1, 3])
        self.assertEqual(list(filter_frame(df, {"n": ["2"]})["a"]), ["y"])
        self.assertEqual(list(filter_frame(df, {"f": ["2.5"]})["a"]), ["y"])
        self.assertEqual(list(filter_frame(df, {"sort": ["-n"]})["n"]), [3, 2, 1])
        self.assertEqual(list(filter_frame(df, {"cols": ["a"]}).columns), ["a"])
        with self.assertRaises(ApiError):
            filter_frame(df, {"zz": ["1"]})

    def test_merge_overrides(self):
        base = {"FR1.G4_infl|const": 1.0}
        a = {"FR1": {"exogenous": {"brent": {"pct": 10.0}}, "coefficients": {"FR1.G4_infl|const": 1.5}}}
        b = {"FR1": {"exogenous": {"brent": {"pct": 10.0}, "fx": {"add": 1}}, "coefficients": {"FR1.G4_infl|const": 1.25},
                     "levers": {"x": 1}}}
        m, notes = merge_overrides([a, b], base.__getitem__)
        self.assertAlmostEqual(m["FR1"]["exogenous"]["brent"]["pct"], 21.0)            # compounded
        self.assertAlmostEqual(m["FR1"]["coefficients"]["FR1.G4_infl|const"], 1.75)    # summed shifts
        self.assertEqual((m["FR1"]["exogenous"]["fx"], m["FR1"]["levers"], notes), ({"add": 1}, {"x": 1}, []))
        m, notes = merge_overrides([a, {"FR1": {"exogenous": {"brent": {"add": 3}}}}], base.__getitem__)
        self.assertEqual((m["FR1"]["exogenous"]["brent"], len(notes)), ({"add": 3}, 1))

    def test_merge_ru_addf_sums(self):
        a = {"FR1": {}, "RU": {"addf": {"infl": [0, 0.7, 0.3, 0, 0]}}}
        b = {"FR1": {}, "RU": {"addf": {"infl": [0, 0.5, 0.2, 0, 0], "rhhdisp": [0, 0.01, 0, 0, 0]}}}
        m, notes = merge_overrides([a, b, {"RU": {"overlays": False}}], {}.__getitem__)
        self.assertEqual([round(x, 9) for x in m["RU"]["addf"]["infl"]], [0, 1.2, 0.5, 0, 0])   # summed, not last-wins
        self.assertEqual((m["RU"]["addf"]["rhhdisp"], m["RU"]["overlays"], notes), ([0, 0.01, 0, 0, 0], False, []))

    def test_validate_ru(self):
        yrs = [2026, 2027, 2028, 2029, 2030]
        self.assertEqual(validate_ru({"spi": [0, -2, 0, 0, 0], "deval_year": 2027}, 5, yrs)["deval_year"], 2027)
        for bad in ({"spi": [0, 1]}, {"nope": [0] * 5}, {"deval_year": 2040}, {"brent_path": [0, 1, 1, 1, 1]},
                    {"spi": ["a"] * 5}):
            with self.assertRaises(ApiError, msg=str(bad)):
                validate_ru(bad, 5, yrs)


if __name__ == "__main__":
    unittest.main()
