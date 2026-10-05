"""Engine state I/O: <module>_state.json + <module>_state.npz (plain data only; no pickle)."""
from __future__ import annotations

import json
import math
import os

import numpy as np
import pandas as pd

from .._util import to_jsonable
from .. import project_root


def engine_dir(root=None):
    return os.path.join(root or project_root(), "output", "engine")


def _enc(o, arrs):
    if isinstance(o, dict):
        return {str(k): _enc(v, arrs) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_enc(v, arrs) for v in o]
    if isinstance(o, np.ndarray):
        key = f"a{len(arrs)}"
        arrs[key] = o
        return {"__npz__": key}
    if isinstance(o, pd.DataFrame):
        num = all(pd.api.types.is_numeric_dtype(t) for t in o.dtypes)
        rec = {"columns": _enc(list(o.columns), arrs), "index": _idx(o.index), "dtypes": [str(t) for t in o.dtypes]}
        if num and o.shape[1]:
            rec["npz"] = _enc(o.to_numpy(float), arrs)
        else:
            rec["data"] = to_jsonable(o.astype(object).where(o.notna(), None).values.tolist())
        return {"__df__": rec}
    if isinstance(o, pd.Series):
        num = pd.api.types.is_numeric_dtype(o.dtype)
        rec = {"name": to_jsonable(o.name), "index": _idx(o.index)}
        rec.update({"npz": _enc(o.to_numpy(float), arrs)} if num else {"data": to_jsonable(o.tolist())})
        return {"__series__": rec}
    if isinstance(o, (float, np.floating)) and not math.isfinite(float(o)):
        return {"__float__": str(float(o))}
    return to_jsonable(o)


def _idx(ix):
    if isinstance(ix, pd.MultiIndex):
        return {"__mi__": to_jsonable([list(t) for t in ix]), "names": list(ix.names)}
    return {"values": to_jsonable(list(ix)), "name": ix.name}


def _unidx(d):
    if "__mi__" in d:
        return pd.MultiIndex.from_tuples([tuple(t) for t in d["__mi__"]], names=d["names"])
    return pd.Index(d["values"], name=d.get("name"))


def _dec(o, arrs):
    if isinstance(o, list):
        return [_dec(v, arrs) for v in o]
    if not isinstance(o, dict):
        return o
    if "__npz__" in o:
        return arrs[o["__npz__"]]
    if "__float__" in o:
        return float(o["__float__"])
    if "__df__" in o:
        r = o["__df__"]
        cols, ix = _dec(r["columns"], arrs), _unidx(r["index"])
        if "npz" in r:
            return pd.DataFrame(_dec(r["npz"], arrs), index=ix, columns=cols)
        return pd.DataFrame(r["data"], index=ix, columns=cols)
    if "__series__" in o:
        r = o["__series__"]
        vals = _dec(r["npz"], arrs) if "npz" in r else r["data"]
        return pd.Series(vals, index=_unidx(r["index"]), name=r.get("name"))
    return {k: _dec(v, arrs) for k, v in o.items()}


def save_state(module, state, root=None, out_dir=None):
    """Write <out_dir>/<module>_state.json (+ .npz with every array). Plain data only (no functions)."""
    out_dir = out_dir or engine_dir(root)
    os.makedirs(out_dir, exist_ok=True)
    arrs = {}
    js = _enc(state, arrs)
    base = os.path.join(out_dir, f"{module.upper()}_state")
    with open(base + ".json", "w", encoding="utf-8") as fh:
        json.dump({"module": module.upper(), "format": "microlib-state-1", "state": js}, fh,
                  ensure_ascii=False, allow_nan=False)
    if arrs:
        np.savez_compressed(base + ".npz", **arrs)
    elif os.path.exists(base + ".npz"):
        os.remove(base + ".npz")
    return base + ".json"


def load_state(module, root=None, in_dir=None):
    base = os.path.join(in_dir or engine_dir(root), f"{module.upper()}_state")
    with open(base + ".json", encoding="utf-8") as fh:
        js = json.load(fh)
    arrs = {}
    if os.path.exists(base + ".npz"):
        with np.load(base + ".npz", allow_pickle=False) as z:
            arrs = {k: z[k] for k in z.files}
    return _dec(js.get("state", js), arrs)
