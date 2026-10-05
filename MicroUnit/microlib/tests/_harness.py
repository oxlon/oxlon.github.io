"""Minimal pytest-free test harness."""
from __future__ import annotations

import os
import tempfile
import time
import traceback
import warnings

import numpy as np


class Fail(AssertionError):
    pass


def check(cond, msg="check failed"):
    if not cond:
        raise Fail(msg)


def approx(a, b, rtol=1e-8, atol=1e-12, msg=""):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.shape != b.shape:
        raise Fail(f"{msg} shape {a.shape} != {b.shape}")
    d = np.abs(a - b)
    tolv = atol + rtol * np.maximum(np.abs(a), np.abs(b))
    if not np.all((d <= tolv) | (np.isnan(a) & np.isnan(b))):
        i = int(np.argmax(d - tolv))
        raise Fail(f"{msg} not close: max |a-b|={d.max():.3e} at {i} (a={a.ravel()[i]!r}, b={b.ravel()[i]!r})")


def raises(exc, fn, *a, **k):
    try:
        fn(*a, **k)
    except exc:
        return True
    raise Fail(f"expected {exc.__name__}")


def tmpdir():
    base = os.environ.get("MICROLIB_TEST_TMP") or None
    if base:
        os.makedirs(base, exist_ok=True)
    return tempfile.mkdtemp(prefix="microlib_test_", dir=base)


def run_module(mod):
    res = []
    for name in sorted(n for n in dir(mod) if n.startswith("test_")):
        fn = getattr(mod, name)
        if not callable(fn):
            continue
        t0 = time.perf_counter()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fn()
            res.append((mod.__name__.split(".")[-1], name, True, "", time.perf_counter() - t0))
        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc(limit=4)
            res.append((mod.__name__.split(".")[-1], name, False, f"{type(e).__name__}: {e}\n{tb}",
                        time.perf_counter() - t0))
    return res
