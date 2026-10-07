"""Hermetic test setup: all PolicyUnit writes (work/, output/) go to a temporary directory; the real
work/oxlon copy is only READ (env POLICY_OXLON_COPY)."""
import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ["POLICY_NO_NETWORK"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("POLICY_OXLON_COPY", str(ROOT / "work" / "oxlon"))

from policyunit import config  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="pu_test_"))
config.WORK = TMP / "work"
config.OUTPUT = TMP / "output"
config.LOGS = TMP / "logs"
config.WORK.mkdir(parents=True, exist_ok=True)
config.OUTPUT.mkdir(parents=True, exist_ok=True)
atexit.register(shutil.rmtree, TMP, True)
