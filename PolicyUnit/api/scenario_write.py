"""
scenario_write — ssenarilərin yaradılması, dəyişdirilməsi, silinməsi, surəti, idxalı və rəsmiləşdirilməsi (NFR4).
Rəsmi fayllar atomik yazılır (müvəqqəti fayl + os.replace); dəyişiklikdən əvvəl ehtiyat nüsxə config/_backup/scenarios/.
"""
import json, os, shutil

import apidb
from apicore import ApiError, now_iso, stamp
from scenarios import ID_RE, Store, _dump


class Writer(Store):
    def _backup(self, sid):
        p = self._path(sid)
        if not p.is_file():
            return None
        d = self.cfg.backup_dir / "scenarios"
        d.mkdir(parents=True, exist_ok=True)
        b = d / ("%s.%s.json" % (sid, stamp()))
        shutil.copy2(p, b)
        return str(b)

    def _write_official(self, s):
        self.cfg.scenarios_dir.mkdir(parents=True, exist_ok=True)
        p = self._path(s["id"])
        tmp = p.with_name(".%s.tmp" % p.name)
        tmp.write_text(_dump(s), encoding="utf-8")
        os.replace(tmp, p)
        return p

    @staticmethod
    def _clean(body):
        """Stored form = what the user wrote (not the normalised expansion), minus API-only keys."""
        return {k: v for k, v in body.items() if not str(k).startswith("_")}

    def create(self, body, actor, store="draft", overwrite=False, origin="api"):
        if store not in ("draft", "official"):
            raise ApiError(400, "bad_parameter", "«store» draft və ya official olmalıdır")
        v = self._require_valid(body)
        sid = body["id"]
        if self.exists(sid) and not overwrite:
            raise ApiError(409, "exists", "Bu id ilə ssenari artıq var: %s (başqa id seçin və ya surət çıxarın)" % sid)
        body = self._clean(body)
        t = now_iso()
        if store == "official":
            backup = self._backup(sid)
            self._write_official(body)
            apidb.execute(self.cfg.db, "DELETE FROM draft WHERE id=?", (sid,))
            apidb.event(self.cfg.db, "scenario.official", "Rəsmi ssenari yazıldı: %s" % sid, {"id": sid, "backup": backup})
        else:
            if self._path(sid).is_file():
                raise ApiError(409, "exists", "Bu id ilə rəsmi ssenari var: %s" % sid)
            apidb.execute(self.cfg.db, "INSERT OR REPLACE INTO draft(id,body,note,actor,origin,created,updated) "
                          "VALUES(?,?,?,?,?,COALESCE((SELECT created FROM draft WHERE id=?),?),?)",
                          (sid, json.dumps(body, ensure_ascii=False), body.get("note"), actor, origin, sid, t, t))
            apidb.event(self.cfg.db, "scenario.saved", "Ssenari qaralaması saxlanıldı: %s" % sid, {"id": sid})
        return self.get(sid)

    def update(self, sid, body, actor):
        if not isinstance(body, dict):
            raise ApiError(400, "bad_json", "JSON obyekt gözlənilir")
        src, cur, _ = self.raw(sid)
        body = dict(body)
        if body.get("id", sid) != sid:
            raise ApiError(400, "bad_parameter", "Ssenarinin id-si dəyişdirilə bilməz (surət çıxarın: /duplicate)")
        body = {"id": sid, **{k: v for k, v in body.items() if k != "id"}}
        self._require_valid(body)
        body = self._clean(body)
        if src == "official":
            backup = self._backup(sid)
            self._write_official(body)
            apidb.event(self.cfg.db, "scenario.official", "Rəsmi ssenari dəyişdirildi: %s" % sid, {"id": sid, "backup": backup})
        else:
            apidb.execute(self.cfg.db, "UPDATE draft SET body=?, actor=?, updated=? WHERE id=?",
                          (json.dumps(body, ensure_ascii=False), actor, now_iso(), sid))
            apidb.event(self.cfg.db, "scenario.saved", "Ssenari qaralaması dəyişdirildi: %s" % sid, {"id": sid})
        return self.get(sid)

    def delete(self, sid, force=False):
        src, _, _ = self.raw(sid)
        if src == "official":
            if not force:
                raise ApiError(409, "official", "Rəsmi ssenari yalnız ?force=1 ilə silinir (fayl config/scenarios/_arxiv/-ə köçürülür)")
            arc = self.cfg.scenarios_dir / "_arxiv"
            arc.mkdir(parents=True, exist_ok=True)
            dst = arc / ("%s.%s.json" % (sid, stamp()))
            shutil.move(str(self._path(sid)), str(dst))
            apidb.event(self.cfg.db, "scenario.deleted", "Rəsmi ssenari arxivə köçürüldü: %s" % sid, {"id": sid})
            return {"deleted": sid, "source": src, "archived": str(dst)}
        apidb.execute(self.cfg.db, "DELETE FROM draft WHERE id=?", (sid,))
        apidb.event(self.cfg.db, "scenario.deleted", "Ssenari qaralaması silindi: %s" % sid, {"id": sid})
        return {"deleted": sid, "source": src}

    def free_id(self, base):
        base = (base[:52] or "ssenari")
        if not self.exists(base):
            return base
        for i in range(2, 1000):
            c = "%s_%d" % (base, i)
            if not self.exists(c):
                return c
        raise ApiError(409, "exists", "Boş id tapılmadı")

    def duplicate(self, sid, body, actor):
        _, cur, _ = self.raw(sid)
        body = body or {}
        new_id = body.get("new_id") or self.free_id(sid + "_kopya")
        if not ID_RE.match(str(new_id)):
            raise ApiError(400, "bad_parameter", "new_id yalnız kiçik latın hərfləri, rəqəmlər və '_' ola bilər")
        s = dict(cur, id=new_id, name_az=body.get("name_az") or ("%s (surət)" % cur.get("name_az", sid)))
        return self.create(s, actor, store="draft", origin="surət: %s" % sid)

    def promote(self, sid, actor):
        src, body, _ = self.raw(sid)
        if src == "official":
            raise ApiError(409, "official", "Ssenari artıq rəsmidir: %s" % sid)
        return self.create(body, actor, store="official", overwrite=True)

    def import_(self, body, actor, store="draft", overwrite=False):
        if isinstance(body, dict) and isinstance(body.get("scenarios"), list):
            items = body["scenarios"]
        elif isinstance(body, list):
            items = body
        else:
            items = [body]
        done, errors = [], {}
        for i, s in enumerate(items, 1):
            key = str(s.get("id")) if isinstance(s, dict) and s.get("id") else "#%d" % i
            try:
                self.create(s, actor, store=store, overwrite=overwrite, origin="idxal")
                done.append(key)
            except ApiError as e:
                errors[key] = (e.extra or {}).get("errors") or [e.message]
        if done:
            apidb.event(self.cfg.db, "scenario.import", "İdxal: %d ssenari" % len(done), {"ids": done})
        return {"imported": done, "errors": errors, "n": len(items)}

    def export(self, sid):
        _, body, _ = self.raw(sid)
        return _dump(body).encode("utf-8")
