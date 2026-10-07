"""
scenarios — ssenari saxlancı (NFR4): rəsmi ssenarilər `config/scenarios/<id>.json` (run_all.py onları görür),
istifadəçi qaralamaları SQLite «draft» cədvəlində. Yoxlama policyunit.scenario.validate ilə (Azərbaycan dilində
xətalar) + API xəbərdarlıqları; rəsmi fayl dəyişdirilməzdən əvvəl config/_backup/scenarios/-a köçürülür.
"""
import json, re

import apidb, pu
from apicore import ApiError, read_json

ID_RE = re.compile(r"^[a-z0-9_]{1,60}$")
KNOWN_KEYS = {"id", "name_az", "description_az", "start_year", "instruments", "tags", "author", "note"}
INSTR_KEYS = {"instrument", "years", "size", "unit", "target", "financing", "note"}


def _dump(s):
    return json.dumps(s, ensure_ascii=False, indent=1) + "\n"


def target_codes():
    """Known target codes: IO sectors (config/io_sectors.csv) + FR12 markets + FR1 groups."""
    import csv
    codes = set(pu.P("scenario").FR12_MARKETS)
    p = pu.P("config").IO_SECTORS_CSV
    try:
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                codes.add(r.get("code", ""))
                for k in ("fr1_group",):
                    if r.get(k):
                        codes.add(r[k])
    except OSError:
        pass
    return {c for c in codes if c}


class Store:
    def __init__(self, cfg):
        self.cfg = cfg

    # ------------------------------------------------------------ validation
    def validate(self, body):
        """{valid, errors[], warnings[], normalised, engines} — never raises for a bad scenario."""
        scn, integ = pu.P("scenario"), pu.P("integrate")
        if not isinstance(body, dict):
            return {"valid": False, "errors": ["ssenari JSON obyekti olmalıdır ({...})"], "warnings": [], "normalised": None,
                    "engines": []}
        try:
            with pu.ENGINE_LOCK:
                errs = list(scn.validate(body))
        except Exception as e:
            errs = ["konfiqurasiya oxunmadı: %s" % e]
        if "id" in body and not ID_RE.match(str(body["id"])):
            if not any("id '" in x for x in errs):
                errs.append("id '%s' yalnız kiçik latın hərfləri, rəqəmlər və '_' ola bilər (maks. 60 simvol)" % body["id"])
        if "name_az" in body and not str(body.get("name_az") or "").strip():
            errs.append("'name_az' (ssenarinin adı) boş ola bilməz")
        warns = []
        extra = sorted(set(body) - KNOWN_KEYS)
        if extra:
            warns.append("naməlum sahə(lər) nəzərə alınmayacaq: %s" % ", ".join(extra))
        codes = target_codes()
        for i, it in enumerate(body.get("instruments") or [], 1):
            if not isinstance(it, dict):
                continue
            ex = sorted(set(it) - INSTR_KEYS)
            if ex:
                warns.append("alət #%d: naməlum sahə(lər): %s" % (i, ", ".join(ex)))
            t = it.get("target")
            if t not in (None, "") and codes and str(t) not in codes:
                warns.append("alət #%d: hədəf '%s' məlum sektor/bazar kodu deyil (config/io_sectors.csv, FR12)" % (i, t))
        norm, engines = None, []
        if not errs:
            try:
                with pu.ENGINE_LOCK:
                    norm = scn.normalise(body)
                    engines = integ.engines_for_scenario(norm)
            except Exception as e:
                errs.append("normallaşdırma alınmadı: %s" % e)
            avail = {e["id"]: e for e in pu.engines()}
            for e in engines:
                if e in avail and not avail[e]["available"]:
                    warns.append("%s: %s" % (avail[e]["label_az"], avail[e]["message_az"]))
        return {"valid": not errs, "errors": errs, "warnings": warns, "normalised": norm, "engines": engines}

    def _require_valid(self, body):
        v = self.validate(body)
        if not v["valid"]:
            raise ApiError(422, "invalid_scenario", "Ssenari yoxlanışı uğursuz oldu (%d xəta)" % len(v["errors"]),
                           extra={"errors": v["errors"], "warnings": v["warnings"]})
        return v

    # ------------------------------------------------------------ read
    def _path(self, sid):
        return self.cfg.scenarios_dir / ("%s.json" % sid)

    def _draft(self, sid):
        rows = apidb.query(self.cfg.db, "SELECT * FROM draft WHERE id=?", (sid,), ("body",))
        return rows[0] if rows else None

    def exists(self, sid):
        return self._path(sid).is_file() or self._draft(sid) is not None

    def raw(self, sid):
        """(source, body, meta) — the stored JSON as written."""
        if not ID_RE.match(str(sid)):
            raise ApiError(400, "bad_parameter", "Ssenari id-si yanlışdır: %r" % str(sid)[:80])
        p = self._path(sid)
        if p.is_file():
            try:
                body = json.loads(p.read_text(encoding="utf-8"))
            except ValueError as e:
                body = {"id": sid, "_json_error": str(e)}
            st = p.stat()
            from datetime import datetime, timezone
            t = datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return "official", body, {"created": None, "updated": t, "actor": None, "note": None}
        d = self._draft(sid)
        if d is None:
            raise ApiError(404, "not_found", "Ssenari tapılmadı: %s" % sid)
        return "draft", d["body"], {k: d[k] for k in ("created", "updated", "actor", "note", "origin")}

    def last_run(self, sid):
        r = apidb.query(self.cfg.db, "SELECT id,finished,seconds,vintage_id FROM run WHERE scenario_id=? AND status='ok' "
                        "ORDER BY finished DESC LIMIT 1", (sid,))
        return {"run_id": r[0]["id"], **{k: r[0][k] for k in ("finished", "seconds", "vintage_id")}} if r else None

    def get(self, sid):
        src, body, meta = self.raw(sid)
        if "_json_error" in body:
            v = {"valid": False, "errors": ["JSON sintaksis xətası: %s" % body["_json_error"]], "warnings": [], "engines": []}
        else:
            v = self.validate(body)
        return {"id": sid, "source": src, "scenario": body, "valid": v["valid"], "errors": v["errors"],
                "warnings": v["warnings"], "engines": v["engines"], **meta, "last_run": self.last_run(sid)}

    def list(self, source="all", tag=None, q=None):
        out = []
        if source in ("all", "official"):
            for p in sorted(self.cfg.scenarios_dir.glob("*.json")):
                b = read_json(p) or {"id": p.stem}
                out.append(self._summary(p.stem, "official", b))
        if source in ("all", "draft"):
            for d in apidb.query(self.cfg.db, "SELECT * FROM draft ORDER BY updated DESC", (), ("body",)):
                out.append(self._summary(d["id"], "draft", d["body"], d["updated"]))
        if tag:
            out = [s for s in out if tag in (s["tags"] or [])]
        if q:
            ql = q.lower()
            out = [s for s in out if ql in (s["id"] + " " + s["name_az"] + " " + s["description_az"]).lower()]
        return out

    def _summary(self, sid, src, b, updated=None):
        ins = b.get("instruments") if isinstance(b.get("instruments"), list) else []
        return {"id": sid, "source": src, "name_az": str(b.get("name_az") or ""),
                "description_az": str(b.get("description_az") or ""), "start_year": b.get("start_year"),
                "tags": b.get("tags") or [], "instruments": [i.get("instrument") for i in ins if isinstance(i, dict)],
                "updated": updated, "last_run": self.last_run(sid)}

    def load(self, sid):
        """Normalised, validated scenario for a run (422 when invalid)."""
        src, body, _ = self.raw(sid)
        return self._require_valid(body)["normalised"], src
