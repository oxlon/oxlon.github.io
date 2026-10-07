"""
instruments — siyasət alətləri kataloqu (config/instruments.csv + adapters.csv) və NFR4: yeni alətin konfiqurasiya ilə
əlavəsi. Yeni alət MÖVCUD mühərrik girişinə adapter sətri ilə bağlanır (kod yazılmır); yoxlama: statik qaydalar
(instrument_rules.py) + konfiqurasiyanın müvəqqəti surətində default_size ilə sınaq hesablaması (mühərrik xətası
və ya sıfır təsir → xəta/xəbərdarlıq).
"""
import csv, io, shutil, tempfile
from pathlib import Path

import apidb, pu
from apicore import ApiError, now_iso, stamp
from instrument_rules import static_errors, target_keys, TRANSFORMS

NEEDS_TARGET = {"market_entry": "fr12_market"}


def _records(df):
    return df.astype(object).where(df.notna(), None).to_dict("records")


class Catalogue:
    def __init__(self, cfg):
        self.cfg = cfg

    def api_added(self):
        rows = apidb.query(self.cfg.db, "SELECT id, action FROM instrument_log ORDER BY time")
        st = {}
        for r in rows:
            st[r["id"]] = r["action"]
        return {k for k, v in st.items() if v == "add"}

    def list(self, family=None):
        reg, c = pu.P("registry"), pu.P("config")
        with pu.ENGINE_LOCK:
            ins, ad = reg.instruments().copy(), reg.adapters().copy()
            errs = reg.validate_catalogue()
        added = self.api_added()
        out = []
        for r in _records(ins):
            if family and r["family"] != family:
                continue
            r["engines"] = [e.strip() for e in str(r["engines"]).split(";") if e.strip()]
            r["unit_az"] = pu.UNIT_AZ.get(r["unit"], r["unit"])
            r["needs_target"] = NEEDS_TARGET.get(r["id"])
            r["adapters"] = _records(ad[ad["instrument"] == r["id"]])
            r["origin"] = "api" if r["id"] in added else "config"
            out.append(r)
        fams = reg.FAMILIES
        return {"instruments": out, "n": len(out), "families": fams,
                "units": [{"id": u, "label_az": pu.UNIT_AZ.get(u, u)} for u in reg.UNITS],
                "engines": pu.engines(), "financing": [{"id": k, "label_az": v} for k, v in pu.FINANCING_AZ.items()],
                "catalogue_errors": errs}

    def get(self, iid, scenarios=None):
        for r in self.list()["instruments"]:
            if r["id"] == iid:
                if scenarios is not None:
                    r["used_by"] = [s["id"] for s in scenarios.list() if iid in s["instruments"]]
                return r
        raise ApiError(404, "not_found", "Alət tapılmadı: %s" % iid)

    def schema(self):
        reg = pu.P("registry")
        return {"fields": [
                    {"id": "id", "label_az": "Alətin id-si (kiçik latın hərfləri, rəqəm, _)", "required": True},
                    {"id": "name_az", "label_az": "Ad (Azərbaycan dilində)", "required": True},
                    {"id": "family", "label_az": "Ailə", "required": True, "enum": reg.FAMILIES},
                    {"id": "unit", "label_az": "Vahid", "required": True, "enum": reg.UNITS},
                    {"id": "default_size", "label_az": "Standart ölçü", "required": True, "type": "number"},
                    {"id": "min", "label_az": "Minimum", "required": True, "type": "number"},
                    {"id": "max", "label_az": "Maksimum", "required": True, "type": "number"},
                    {"id": "engines", "label_az": "Mühərriklər (verilməsə — adapterlərdən)", "enum": pu.P("config").ENGINE_ORDER},
                    {"id": "description_az", "label_az": "Təsvir"},
                    {"id": "cost_rule", "label_az": "Fiskal xərc qaydası", "default": "none"},
                    {"id": "cost_in_fr1", "label_az": "Xərc MikroUnit FR1 büdcəsində var (yes/no)", "default": "no"}],
                "transforms": TRANSFORMS, "target_keys": target_keys(),
                "cost_rules": ["none", "spend", "revenue:<vat|cit|pit|customs>", "benefit:<fiscal_params.csv parametri>",
                               "mw_budget"],
                "procedure_az": PROCEDURE_AZ}

    # ------------------------------------------------------------ NFR4: new instrument
    def _rows(self, body):
        if not isinstance(body, dict) or not isinstance(body.get("instrument"), dict):
            raise ApiError(400, "bad_json", "Gövdə {instrument: {...}, adapters: [...]} formatında olmalıdır")
        ins = dict(body["instrument"])
        ads = [dict(a, instrument=ins.get("id")) for a in (body.get("adapters") or []) if isinstance(a, dict)]
        if not ins.get("engines"):
            ins["engines"] = sorted({a.get("engine") for a in ads if a.get("engine")},
                                    key=lambda e: pu.P("config").ENGINE_ORDER.index(e) if e in pu.P("config").ENGINE_ORDER else 99)
        if isinstance(ins.get("engines"), str):
            ins["engines"] = [e.strip() for e in ins["engines"].split(";") if e.strip()]
        ins.setdefault("description_az", "")
        ins.setdefault("cost_rule", "none")
        ins.setdefault("cost_in_fr1", "no")
        return ins, ads

    def check(self, body, test_run=True):
        ins, ads = self._rows(body)
        errs, warns = static_errors(ins, ads, existing=self.list()["instruments"])
        test = None
        if not errs and test_run:
            test = self.trial(ins, ads)
            errs += test.pop("errors")
            warns += test.pop("warnings")
        return {"valid": not errs, "errors": errs, "warnings": warns, "instrument": ins, "adapters": ads, "test_run": test}

    def trial(self, ins, ads):
        """Copy config/ to a temp dir, append the rows, run a default-size scenario there (config restored after)."""
        tmp = Path(tempfile.mkdtemp(prefix="pu_instr_"))
        errs, warns = [], []
        try:
            shutil.copytree(self.cfg.config_dir, tmp / "config", ignore=shutil.ignore_patterns("_backup", "_arxiv"))
            _append(tmp / "config", ins, ads)
            c = pu.P("config")
            saved = {k: getattr(c, k) for k in ("CONFIG", "SCENARIOS", "INSTRUMENTS_CSV", "ADAPTERS_CSV")}
            with pu.ENGINE_LOCK:
                try:
                    c.CONFIG, c.SCENARIOS = tmp / "config", tmp / "config" / "scenarios"
                    c.INSTRUMENTS_CSV, c.ADAPTERS_CSV = tmp / "config" / "instruments.csv", tmp / "config" / "adapters.csv"
                    pu.reload()
                    reg = pu.P("registry")
                    errs += ["kataloq: %s" % e for e in reg.validate_catalogue() if e.startswith(ins["id"]) or ins["id"] in e]
                    s = {"id": "sinaq_" + ins["id"], "name_az": "Sınaq: " + str(ins.get("name_az")), "start_year": 2026,
                         "instruments": [{"instrument": ins["id"], "years": "all", "size": float(ins["default_size"]),
                                          "unit": ins["unit"], "target": None, "financing": None}]}
                    v = pu.P("scenario").validate(s)
                    errs += ["sınaq ssenarisi: %s" % e for e in v]
                    res = pu.P("integrate").run_scenario(pu.P("scenario").normalise(s)) if not v else None
                finally:
                    for k, val in saved.items():
                        setattr(c, k, val)
                    pu.reload()
            out = {"engines": {}, "headline": []}
            if res is not None:
                for e, st in res["status"].items():
                    out["engines"][e] = {k: st.get(k) for k in ("status", "rows", "seconds", "message_az")}
                    if st["status"] == "xəta":
                        errs.append("%s mühərriki adapteri qəbul etmədi: %s" % (e, str(st.get("message_az"))[:300]))
                f = res["frame"]
                if len(f):
                    nz = f[f["delta"].abs() > 1e-9]
                    for e in ins["engines"]:
                        if out["engines"].get(e, {}).get("status") == "ok" and not len(nz[nz.engine == e]):
                            warns.append("%s: sınaq hesablamasında təsir sıfırdır — adapter xəritəsini yoxlayın" % e)
                    hl = pu.P("integrate").headline(f)
                    out["headline"] = _records(hl.head(30)) if len(hl) else []
                out["seconds"] = res["seconds"]
            return {**out, "errors": errs, "warnings": warns}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def add(self, body, actor):
        dry = bool(body.get("dry_run")) if isinstance(body, dict) else False
        r = self.check(body, test_run=body.get("test_run", True) if isinstance(body, dict) else True)
        if not r["valid"]:
            raise ApiError(422, "invalid_instrument", "Alət yoxlanışı uğursuz oldu (%d xəta)" % len(r["errors"]),
                           extra={"errors": r["errors"], "warnings": r["warnings"], "test_run": r["test_run"]})
        if dry:
            return dict(r, dry_run=True, files_changed=[])
        bdir = self.cfg.backup_dir / ("instrument_%s_%s" % (r["instrument"]["id"], stamp()))
        bdir.mkdir(parents=True, exist_ok=True)
        for f in ("instruments.csv", "adapters.csv"):
            shutil.copy2(self.cfg.config_dir / f, bdir / f)
        with pu.ENGINE_LOCK:
            _append(self.cfg.config_dir, r["instrument"], r["adapters"])
            pu.reload()
        import json
        apidb.execute(self.cfg.db, "INSERT INTO instrument_log(id,action,body,backup,actor,time) VALUES(?,?,?,?,?,?)",
                      (r["instrument"]["id"], "add", json.dumps({"instrument": r["instrument"], "adapters": r["adapters"]},
                                                                ensure_ascii=False), str(bdir), actor, now_iso()))
        apidb.event(self.cfg.db, "instrument.added", "Yeni alət əlavə edildi: %s" % r["instrument"]["id"],
                    {"id": r["instrument"]["id"], "backup": str(bdir)})
        return dict(r, dry_run=False, backup=str(bdir), files_changed=["config/instruments.csv", "config/adapters.csv"])

    def delete(self, iid, scenarios, actor):
        if iid not in self.api_added():
            raise ApiError(409, "not_api", "Yalnız API ilə əlavə edilmiş alət silinə bilər (digərləri config/instruments.csv-də "
                                           "əl ilə redaktə olunur): %s" % iid)
        used = [s["id"] for s in scenarios.list() if iid in s["instruments"]]
        if used:
            raise ApiError(409, "in_use", "Alət ssenarilərdə istifadə olunur: %s" % ", ".join(used))
        bdir = self.cfg.backup_dir / ("instrument_%s_del_%s" % (iid, stamp()))
        bdir.mkdir(parents=True, exist_ok=True)
        with pu.ENGINE_LOCK:
            for f, col in (("instruments.csv", "id"), ("adapters.csv", "instrument")):
                p = self.cfg.config_dir / f
                shutil.copy2(p, bdir / f)
                _rewrite_without(p, col, iid)
            pu.reload()
        apidb.execute(self.cfg.db, "INSERT INTO instrument_log(id,action,body,backup,actor,time) VALUES(?,?,?,?,?,?)",
                      (iid, "delete", None, str(bdir), actor, now_iso()))
        apidb.event(self.cfg.db, "instrument.deleted", "Alət silindi: %s" % iid, {"id": iid, "backup": str(bdir)})
        return {"deleted": iid, "backup": str(bdir)}


def _append(cdir, ins, ads):
    for fn, rows in (("instruments.csv", [ins]), ("adapters.csv", ads)):
        p = Path(cdir) / fn
        text = p.read_text(encoding="utf-8")
        header = next(csv.reader([text.splitlines()[0]]))
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        for r in rows:
            w.writerow([";".join(r[h]) if isinstance(r.get(h), list) else ("" if r.get(h) is None else r.get(h)) for h in header])
        p.write_text(text + ("" if text.endswith("\n") else "\n") + buf.getvalue(), encoding="utf-8")


def _rewrite_without(p, col, iid):
    with open(p, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    i = rows[0].index(col)
    keep = [rows[0]] + [r for r in rows[1:] if r and r[i] != iid]
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(keep)
    Path(p).write_text(buf.getvalue(), encoding="utf-8")


PROCEDURE_AZ = [
    "1. Mövcud alətlər arasında oxşarını tapın (GET /api/v1/instruments) — onun adapter sətirləri nümunədir.",
    "2. Alətin sahələrini doldurun: id, ad, ailə, vahid, standart ölçü, min/max (GET /api/v1/instruments/schema).",
    "3. Hər mühərrik üçün adapter: engine + target_key (mühərrikin mövcud girişi) + transform (pct|add|level|... və ya "
    "mövcud custom:<funksiya>), istəyə görə miqyas *k.",
    "4. POST /api/v1/instruments/validate — xətalar Azərbaycan dilində; sınaq hesablaması təsirin sıfır olmadığını yoxlayır.",
    "5. POST /api/v1/instruments/new — sətirlər config/instruments.csv və adapters.csv sonuna yazılır (ehtiyat nüsxə).",
    "6. Yeni alətlə ssenari yaradın (POST /api/v1/scenarios), yoxlayın və hesablayın (POST /api/v1/scenarios/{id}/run).",
    "Ümumi müddət: konfiqurasiya 1–2 saat, metodoloji yoxlama (elastiklik/ötürmə əmsalının əsaslandırılması, mənbə) "
    "qalan iş günü — 1 iş günü ərzində. Yeni ötürmə MEXANİZMİ (mövcud girişlərlə ifadə olunmayan) kod tələb edir.",
]
