"""
scenarios — saxlanmış ssenarilər (SQLite «scenario» cədvəli): stress / miqyaslanma / optimallaşdırma sorğuları
və istəyə görə son nəticə. Nəticə cari bazada yenidən hesablana bilər (/scenarios/saved/{id}/run).
"""
import json

import apidb
from apicore import ApiError, new_id, now_iso

KINDS = ("stress", "scalability", "optimize")
MAX_RESULT = 4 * 1024 * 1024


def _check(kind, request):
    if kind not in KINDS:
        raise ApiError(400, "bad_parameter", "«kind» bunlardan biri olmalıdır: %s" % ", ".join(KINDS))
    if not isinstance(request, dict):
        raise ApiError(400, "bad_parameter", "«request» JSON obyekt olmalıdır (müvafiq /run sorğusunun gövdəsi)")


def _dump(v):
    if v is None:
        return None
    s = json.dumps(v, ensure_ascii=False, default=str)
    if len(s) > MAX_RESULT:
        raise ApiError(413, "too_large", "Saxlanılan nəticə çox böyükdür (maks. 4 MB)")
    return s


class Store:
    def __init__(self, cfg):
        self.cfg = cfg

    def list(self, kind=None):
        sql = "SELECT id,name,kind,request,note,actor,baseline_id,created,updated, (result IS NOT NULL) AS has_result FROM scenario"
        args = ()
        if kind:
            sql += " WHERE kind=?"
            args = (kind,)
        return apidb.query(self.cfg.db, sql + " ORDER BY updated DESC", args, ("request",))

    def get(self, sid):
        rows = apidb.query(self.cfg.db, "SELECT * FROM scenario WHERE id=?", (sid,), ("request", "result"))
        if not rows:
            raise ApiError(404, "not_found", "Ssenari tapılmadı: %s" % sid)
        return rows[0]

    def create(self, body, actor, baseline_id=None):
        if not isinstance(body, dict):
            raise ApiError(400, "bad_json", "JSON obyekt gözlənilir")
        name = str(body.get("name") or "").strip()
        if not name:
            raise ApiError(400, "bad_parameter", "«name» tələb olunur")
        kind, req = body.get("kind"), body.get("request")
        _check(kind, req)
        sid, t = new_id("SC"), now_iso()
        apidb.execute(self.cfg.db, "INSERT INTO scenario(id,name,kind,request,result,note,actor,baseline_id,created,updated) "
                      "VALUES(?,?,?,?,?,?,?,?,?,?)", (sid, name[:200], kind, _dump(req), _dump(body.get("result")),
                                                      str(body.get("note") or "")[:2000], actor, baseline_id, t, t))
        apidb.event(self.cfg.db, "scenario.saved", "Ssenari saxlanıldı: %s (%s)" % (name[:80], kind), {"id": sid})
        return self.get(sid)

    def update(self, sid, body, actor):
        cur = self.get(sid)
        if not isinstance(body, dict):
            raise ApiError(400, "bad_json", "JSON obyekt gözlənilir")
        name = str(body.get("name", cur["name"]) or "").strip()
        if not name:
            raise ApiError(400, "bad_parameter", "«name» boş ola bilməz")
        kind = body.get("kind", cur["kind"])
        req = body.get("request", cur["request"])
        _check(kind, req)
        result = body["result"] if "result" in body else cur["result"]
        apidb.execute(self.cfg.db, "UPDATE scenario SET name=?,kind=?,request=?,result=?,note=?,actor=?,updated=? WHERE id=?",
                      (name[:200], kind, _dump(req), _dump(result), str(body.get("note", cur["note"]) or "")[:2000],
                       actor, now_iso(), sid))
        return self.get(sid)

    def set_result(self, sid, result, baseline_id=None):
        apidb.execute(self.cfg.db, "UPDATE scenario SET result=?, baseline_id=COALESCE(?, baseline_id), updated=? WHERE id=?",
                      (_dump(result), baseline_id, now_iso(), sid))

    def delete(self, sid):
        self.get(sid)
        apidb.execute(self.cfg.db, "DELETE FROM scenario WHERE id=?", (sid,))
        apidb.event(self.cfg.db, "scenario.deleted", "Ssenari silindi: %s" % sid, {"id": sid})
        return {"deleted": sid}
