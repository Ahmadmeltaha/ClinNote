"""
Regenerate all patient summaries with full anomaly detection.
Run once to fix existing JSONs that have empty lab/vital alerts.

  cd ClinNote
  python scripts/regenerate_summaries.py
"""
import sys
import json
import glob
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

from configs.paths import PATHS
from api.pipeline_runner import run_for_patient

summaries_dir = PATHS.summaries_dir
files = [f for f in glob.glob(str(summaries_dir / "patient_*.json")) if "_report" not in f]

# Collect unique (subject_id, hadm_id) pairs — skip fake/test patients
to_run = []
for f in files:
    d = json.load(open(f))
    if not isinstance(d, dict):
        continue
    sid = d.get("subject_id")
    hid = d.get("hadm_id")
    if sid and int(sid) > 1_000_000:
        to_run.append(int(sid))

subject_ids = sorted(set(to_run))
print(f"Regenerating summaries for {len(subject_ids)} patients: {subject_ids}\n")

ok, failed = 0, []
for i, sid in enumerate(subject_ids, 1):
    print(f"[{i}/{len(subject_ids)}] subject_id={sid} ...", end=" ", flush=True)
    try:
        run_for_patient(str(sid))
        print("OK")
        ok += 1
    except Exception as e:
        print(f"FAILED: {e}")
        failed.append((sid, str(e)))

print(f"\nDone: {ok} succeeded, {len(failed)} failed")
if failed:
    for sid, err in failed:
        print(f"  {sid}: {err}")
