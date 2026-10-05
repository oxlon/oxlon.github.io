"""
upload_store — yüklənən faylların saxlanması (data/inbox/<upload_id>/), yoxlanılması və tətbiqi.

Tətbiq (apply): əvəz olunan fayl data/_replaced/<vaxt>_<upload_id>/ altına köçürülür, yeni fayl dəftərlərin
oxuduğu dəqiq yola yazılır. Real adlı fayllar: data/firm_panel/FR10_firm_panel.csv|xlsx,
data/business_register/FR12_business_register.csv|xlsx — *_SYNTHETIC* / *_TEMPLATE* fayllarının üzərinə
HEÇ VAXT yazılmır.
"""
import hashlib, json, os, re, shutil, threading
from pathlib import Path

import apidb
import nbextract
from apicore import ApiError, DB_LOCK, MODULES, new_id, now_iso, safe_filename, stamp, within, write_json
from validate_dsk import DSK_DIRS, infer_subfolder, norm_subfolder, validate_dsk

KINDS = ("workbook", "dsk", "firm_panel", "business_register", "series")
KIND_AZ = {"workbook": "iş kitabı (Statistik data dinamika)", "dsk": "DSK cədvəli (.xls)",
           "firm_panel": "FR10 müəssisə paneli", "business_register": "FR12 biznes reyestri", "series": "müşahidələr (JSON)"}
FIRST_STAGE = {"workbook": "FR1", "firm_panel": "FR10", "business_register": "FR12", "series": None}
APPLY_LOCK = threading.Lock()


def classify(filename):
    """Fayl adına görə növ (avtonom rejim üçün): (kind, səbəb)."""
    n = filename.lower()
    if re.match(r"^statistik data dinamika.*\.xlsx$", n):
        return "workbook", None
    if re.match(r"^fr10_firm_panel.*\.(csv|xlsx)$", n):
        return "firm_panel", None
    if re.match(r"^fr12_business_register.*\.(csv|xlsx)$", n):
        return "business_register", None
    if n.endswith(".xls"):
        return "dsk", None
    if n.endswith(".json"):
        return "series", None
    return None, "Fayl adına görə növ müəyyən edilmədi: %s" % filename


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class UploadStore:
    def __init__(self, cfg, runs=None, catalog=None):
        self.cfg, self.runs, self.catalog = cfg, runs, catalog

    # ------------------------------------------------------------ create
    def create(self, kind, filename, data=None, stream=None, length=None, subfolder=None, actor=None, note=None, source="api"):
        if kind not in KINDS:
            raise ApiError(400, "bad_kind", "Naməlum yükləmə növü: %r. Mümkün olanlar: %s" % (kind, ", ".join(KINDS)))
        fn = safe_filename(filename)
        uid = new_id("u")
        d = self.cfg.inbox / uid
        d.mkdir(parents=True, exist_ok=True)
        path = d / fn
        h, n = hashlib.sha256(), 0
        with open(path, "wb") as f:
            if data is not None:
                f.write(data)
                h.update(data)
                n = len(data)
            else:
                left = length
                while left > 0:
                    blk = stream.read(min(1 << 20, left))
                    if not blk:
                        break
                    f.write(blk)
                    h.update(blk)
                    n += len(blk)
                    left -= len(blk)
                if n != length:
                    shutil.rmtree(d, ignore_errors=True)
                    raise ApiError(400, "incomplete_body", "Sorğu gövdəsi tam alınmadı (%d / %d bayt)" % (n, length))
        if n == 0:
            shutil.rmtree(d, ignore_errors=True)
            raise ApiError(400, "empty_file", "Fayl boşdur")
        try:
            rep = self.validate(path, kind, fn, subfolder)
        except Exception as e:                                  # a validator crash is a rejection, not a 500
            rep = {"ok": False, "kind": kind, "errors": [{"message": "Yoxlama zamanı gözlənilməz xəta: %s" % e}],
                   "warnings": [], "summary": {}}
        rep["upload_id"] = uid
        rep["checked_at"] = now_iso()
        write_json(d / "validation.json", rep)
        meta = {"id": uid, "kind": kind, "filename": fn, "subfolder": rep.get("subfolder"), "bytes": n,
                "sha256": h.hexdigest(), "actor": actor or "api", "note": note, "source": source,
                "created_at": now_iso(), "target": rep.get("target")}
        write_json(d / "meta.json", meta)
        con = apidb.conn(self.cfg.db)
        with DB_LOCK:
            con.execute("INSERT INTO upload(id,kind,filename,subfolder,stored_path,bytes,sha256,actor,note,source,status,valid,"
                        "report,target,affected,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (uid, kind, fn, rep.get("subfolder"), str(path.relative_to(self.cfg.root)), n, meta["sha256"],
                         meta["actor"], note, source, "validated" if rep["ok"] else "rejected", 1 if rep["ok"] else 0,
                         json.dumps(rep, ensure_ascii=False, default=str), rep.get("target"),
                         json.dumps(rep.get("affected_stages") or []), meta["created_at"]))
            con.commit()
        apidb.event(self.cfg.db, "upload", "%s yükləndi: %s — %s" % (KIND_AZ[kind], fn, "qəbul edildi" if rep["ok"] else "rədd edildi"),
                    {"upload_id": uid, "ok": rep["ok"], "errors": len(rep.get("errors") or [])})
        return self.get(uid)

    # ------------------------------------------------------------ validate
    def target_for(self, kind, filename, subfolder):
        data = self.cfg.data
        ext = Path(filename).suffix.lower()
        if kind == "workbook":
            return data / nbextract.workbook_name(self.cfg.root)
        if kind == "dsk":
            return data / subfolder / filename
        if kind == "firm_panel":
            return data / "firm_panel" / ("FR10_firm_panel" + ext)
        if kind == "business_register":
            return data / "business_register" / ("FR12_business_register" + ext)
        return None

    def validate(self, path, kind, filename, subfolder=None):
        root = self.cfg.root
        sub = None
        if kind == "workbook":
            from validate_workbook import validate_workbook
            if not filename.lower().endswith(".xlsx"):
                return {"ok": False, "kind": kind, "errors": [{"message": "İş kitabı .xlsx olmalıdır"}], "warnings": [], "summary": {}}
            ref = self.target_for(kind, filename, None)
            rep = validate_workbook(path, root, reference=ref if ref.exists() else None)
        elif kind == "dsk":
            if not filename.lower().endswith(".xls"):
                return {"ok": False, "kind": kind, "errors": [{"message": "DSK cədvəli .xls olmalıdır"}], "warnings": [], "summary": {}}
            sub = norm_subfolder(subfolder) if subfolder else None
            cands = []
            if not sub:
                sub, cands = infer_subfolder(root, filename)
            if not sub:
                msg = ("Alt qovluğu göstərin (subfolder): fayl bir neçə yerdə var: %s" % ", ".join(cands)) if cands else \
                      ("Alt qovluğu göstərin (subfolder) — fayl adı tanınmır. Mümkün olanlar: %s" % ", ".join(DSK_DIRS))
                return {"ok": False, "kind": kind, "errors": [{"message": msg}], "warnings": [], "summary": {"candidates": cands}}
            rep = validate_dsk(path, filename, sub, root)
        elif kind in ("firm_panel", "business_register"):
            from validate_tables import validate_table
            if Path(filename).suffix.lower() not in (".csv", ".xlsx"):
                return {"ok": False, "kind": kind, "errors": [{"message": "Fayl .csv və ya .xlsx olmalıdır"}], "warnings": [], "summary": {}}
            rep = validate_table(path, root, kind)
        else:
            rep = self.validate_series(path)
        rep["subfolder"] = sub
        tgt = self.target_for(kind, filename, sub) if (kind != "dsk" or sub in DSK_DIRS) else None
        if tgt is not None:
            if re.search(r"(SYNTHETIC|TEMPLATE)", tgt.name, re.I) or not within(self.cfg.data, tgt):
                raise ApiError(500, "unsafe_target", "Təhlükəli hədəf yolu: %s" % tgt)
            rep["target"] = str(tgt.relative_to(self.cfg.root)).replace(os.sep, "/")
        else:
            rep["target"] = "sqlite:observation" if kind == "series" else None
        first = DSK_DIRS.get(sub) if kind == "dsk" else FIRST_STAGE[kind]
        rep["first_stage"] = first
        if first:
            import run_manager
            rep["affected_stages"] = run_manager.downstream([first])
        return rep

    def validate_series(self, path):
        """Makro API-dəki kimi müşahidələr: {"actor","source","note","items":[{"id":"fr1:rgdp" | "module"+"code", "period", "value"}]}."""
        try:
            body = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except Exception as e:
            return {"ok": False, "kind": "series", "errors": [{"message": "JSON oxunmadı: %s" % e}], "warnings": [], "summary": {}}
        items = body.get("items") if isinstance(body, dict) else body
        if not isinstance(items, list) or not items:
            return {"ok": False, "kind": "series", "errors": [{"message": "«items» massivi gözlənilir"}], "warnings": [], "summary": {}}
        if len(items) > 20000:
            return {"ok": False, "kind": "series", "errors": [{"message": "Bir faylda maksimum 20 000 nöqtə"}], "warnings": [], "summary": {}}
        known = self.catalog() if self.catalog else None
        errors, warnings, mods, pers = [], [], set(), set()
        for i, it in enumerate(items):
            try:
                module, code, per, val = parse_obs(it)
            except (KeyError, ValueError, TypeError) as ex:
                errors.append({"index": i, "reason": "bad_item", "message": str(ex)})
                continue
            if per < 1990 or per > 2100:
                errors.append({"index": i, "reason": "period_out_of_range", "message": "İl 1990–2100 aralığında olmalıdır"})
                continue
            sid = "%s:%s" % (module.lower(), code)
            if known is not None and known.get(module) is not None and sid not in known[module]:
                errors.append({"index": i, "id": sid, "reason": "unknown_series", "message": "Bu identifikatorla göstərici kataloqda yoxdur"})
                continue
            mods.add(module)
            pers.add(per)
        if known is None or any(known.get(m) is None for m in mods):
            warnings.append({"message": "Göstərici kataloqu (output/FRx_indicator_catalog.csv) olmayan modullar üçün kodlar yoxlanılmadı"})
        return {"ok": not errors, "kind": "series", "errors": errors[:500], "warnings": warnings,
                "summary": {"items": len(items), "modules": sorted(mods), "periods": [min(pers), max(pers)] if pers else None,
                            "actor": body.get("actor") if isinstance(body, dict) else None,
                            "source": body.get("source") if isinstance(body, dict) else None}}

    # ------------------------------------------------------------ apply
    def apply(self, uid, actor=None):
        with APPLY_LOCK:
            r = self.get(uid)
            if not r:
                raise ApiError(404, "not_found", "Yükləmə tapılmadı: %s" % uid)
            if r["status"] == "applied":
                raise ApiError(409, "already_applied", "Bu yükləmə artıq tətbiq olunub (%s)" % r["applied_at"])
            if not r["valid"]:
                raise ApiError(409, "not_valid", "Yoxlamadan keçməyən fayl tətbiq edilə bilməz — hesabatdakı səhvləri düzəldib yenidən yükləyin")
            if self.runs and self.runs.busy():
                raise ApiError(409, "busy", "Hazırda model icra olunur — giriş faylları icra bitdikdən sonra dəyişdirilə bilər")
            src = self.cfg.root / r["stored_path"]
            if not src.exists() or sha256_file(src) != r["sha256"]:
                raise ApiError(409, "changed", "Saxlanmış fayl yoxlamadan sonra dəyişib və ya silinib — yenidən yükləyin")
            res = self._apply_series(r, src, actor) if r["kind"] == "series" else self._apply_file(r, src, actor)
            con = apidb.conn(self.cfg.db)
            with DB_LOCK:
                con.execute("UPDATE upload SET status='applied', applied_at=?, backup=?, affected=? WHERE id=?",
                            (now_iso(), res.get("backup"), json.dumps(res.get("affected_stages") or []), uid))
                con.commit()
            apidb.event(self.cfg.db, "apply", "%s tətbiq olundu: %s → %s" % (KIND_AZ[r["kind"]], r["filename"], r["target"]),
                        {"upload_id": uid, **{k: v for k, v in res.items() if k != "items"}})
            out = self.get(uid)
            out["apply"] = res
            return out

    def _apply_file(self, r, src, actor):
        root, data = self.cfg.root, self.cfg.data
        tgt = root / r["target"]
        if not within(data, tgt) or re.search(r"(SYNTHETIC|TEMPLATE)", tgt.name, re.I):
            raise ApiError(500, "unsafe_target", "Təhlükəli hədəf yolu: %s" % r["target"])
        others = [tgt]
        if r["kind"] in ("firm_panel", "business_register"):
            base = tgt.with_suffix("")
            others = [base.with_suffix(".csv"), base.with_suffix(".xlsx")]
        bdir = self.cfg.replaced / ("%s_%s" % (stamp(), r["id"]))
        replaced = []
        for p in others:
            if p.exists():
                dst = bdir / p.relative_to(data)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
                replaced.append({"path": str(p.relative_to(root)), "sha256": sha256_file(dst),
                                 "backup": str(dst.relative_to(root))})
                if p != tgt:                     # the other extension would shadow the new file (csv is read first)
                    p.unlink()
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tmp = tgt.with_name(".%s.tmp-%s" % (tgt.name, r["id"]))
        shutil.move(str(src), str(tmp))
        os.replace(tmp, tgt)
        res = {"target": r["target"], "sha256": r["sha256"], "replaced": replaced,
               "backup": str(bdir.relative_to(root)) if replaced else None, "actor": actor or r.get("actor"),
               "affected_stages": (r.get("report") or {}).get("affected_stages") or []}
        if replaced:
            write_json(bdir / "manifest.json", {"upload_id": r["id"], "at": now_iso(), **res, "original_filename": r["filename"]})
        write_json(src.parent / "meta.json", {**{k: r[k] for k in ("id", "kind", "filename", "sha256")},
                                               "applied_to": r["target"], "applied_at": now_iso()})
        return res

    def _apply_series(self, r, src, actor):
        body = json.loads(Path(src).read_text(encoding="utf-8-sig"))
        items = body.get("items") if isinstance(body, dict) else body
        meta = body if isinstance(body, dict) else {}
        actor = actor or meta.get("actor") or r.get("actor") or "api"
        con, ts, n_ins, n_upd = apidb.conn(self.cfg.db), now_iso(), 0, 0
        with DB_LOCK:
            for it in items:
                module, code, per, val = parse_obs(it)
                prev = con.execute("SELECT value,revision FROM observation WHERE module=? AND code=? AND period=?",
                                   (module, code, per)).fetchone()
                sq, rev = apidb.next_seq(con), (prev["revision"] + 1) if prev else 1
                con.execute("INSERT INTO observation(module,code,period,value,source,actor,note,revision,upload_id,updated_at,seq) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(module,code,period) DO UPDATE SET value=excluded.value,"
                            "source=excluded.source, actor=excluded.actor, note=excluded.note, revision=excluded.revision,"
                            "upload_id=excluded.upload_id, updated_at=excluded.updated_at, seq=excluded.seq",
                            (module, code, per, val, it.get("source", meta.get("source", "upload")), actor,
                             it.get("note", meta.get("note")), rev, r["id"], ts, sq))
                con.execute("INSERT INTO observation_history(module,code,period,old_value,new_value,source,actor,note,upload_id,at) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?)", (module, code, per, prev["value"] if prev else None, val,
                                                           it.get("source", meta.get("source", "upload")), actor,
                                                           it.get("note", meta.get("note")), r["id"], ts))
                n_upd, n_ins = (n_upd + 1, n_ins) if prev else (n_upd, n_ins + 1)
            con.commit()
        return {"target": "sqlite:observation", "inserted": n_ins, "updated": n_upd, "backup": None, "affected_stages": []}

    # ------------------------------------------------------------ read
    def get(self, uid):
        con = apidb.conn(self.cfg.db)
        r = apidb.row(con.execute("SELECT * FROM upload WHERE id=?", (uid,)).fetchone(), ("report", "affected"))
        if r:
            r["valid"] = bool(r["valid"])
        return r

    def list(self, limit=100, kind=None, status=None):
        where, args = [], []
        if kind:
            where.append("kind=?"); args.append(kind)
        if status:
            where.append("status=?"); args.append(status)
        sql = "SELECT id,kind,filename,subfolder,bytes,sha256,actor,source,status,valid,target,created_at,applied_at,run_id FROM upload"
        sql += (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY created_at DESC, id DESC LIMIT ?"
        rows = [dict(x) for x in apidb.conn(self.cfg.db).execute(sql, args + [limit])]
        for x in rows:
            x["valid"] = bool(x["valid"])
        return rows

    def set_run(self, uid, run_id):
        con = apidb.conn(self.cfg.db)
        with DB_LOCK:
            con.execute("UPDATE upload SET run_id=? WHERE id=?", (run_id, uid))
            con.commit()


def parse_obs(it):
    if not isinstance(it, dict):
        raise ValueError("element obyekt olmalıdır")
    if it.get("id"):
        mod, _, code = str(it["id"]).partition(":")
        module = mod.upper()
    else:
        module, code = str(it["module"]).upper(), str(it["code"])
    if module not in MODULES:
        raise ValueError("naməlum modul: %s" % module)
    if not code:
        raise ValueError("kod boşdur")
    per = int(it["period"])
    val = it.get("value")
    if val is not None:
        val = float(val)
        if val != val or val in (float("inf"), float("-inf")):
            raise ValueError("dəyər ədəd deyil")
    return module, code, per, val
